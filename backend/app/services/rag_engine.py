import os
import re
import math
import hashlib
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api.types import Documents, Embeddings
from app.config import settings
from app.services.gemini_client import gemini_service

logger = logging.getLogger("CognivoraAI.RAGEngine")


class FastCurriculumEmbedder(chromadb.EmbeddingFunction):
    """
    High-speed, zero-dependency 384-dimensional normalized vector embedder.
    Works offline with zero external downloads, providing immediate deterministic
    cosine similarity for educational curriculum text.
    If Gemini API key is configured, uses Gemini gemini-embedding-001 with 384 dimensions.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim

    def name(self) -> str:
        return "FastCurriculumEmbedder"

    def __call__(self, input: Documents) -> Embeddings:
        # Check if Gemini live embeddings can be used
        if gemini_service.is_live() and hasattr(gemini_service.client, "models"):
            try:
                from google.genai import types
                embeddings = []
                batch_size = 16
                for i in range(0, len(input), batch_size):
                    batch = [d[:2048] for d in input[i:i + batch_size]]
                    res = gemini_service.client.models.embed_content(
                        model=settings.EMBEDDING_MODEL,
                        contents=batch,
                        config=types.EmbedContentConfig(output_dimensionality=self.dim)
                    )
                    raw_embs = []
                    if hasattr(res, "embeddings") and res.embeddings:
                        raw_embs = [e.values[:self.dim] for e in res.embeddings]
                    elif hasattr(res, "embedding") and hasattr(res.embedding, "values"):
                        raw_embs = [res.embedding.values[:self.dim]]

                    for vec in raw_embs:
                        norm = math.sqrt(sum(v * v for v in vec))
                        if norm > 1e-9:
                            vec = [v / norm for v in vec]
                        embeddings.append(vec)

                if len(embeddings) == len(input):
                    return embeddings
            except Exception as e:
                logger.warning(f"Gemini live embedding call failed: {e}. Using fast local embedder.")

        # Local deterministic curriculum embedding
        embeddings = []
        for doc in input:
            embeddings.append(self._embed_text(doc))
        return embeddings

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return vec

        for token in tokens:
            # Deterministic hash bucket
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            weight = math.log(1.0 + len(token))
            vec[idx] += sign * weight

        # L2 Normalization
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-9:
            vec = [v / norm for v in vec]
        return vec


class RAGEngine:
    """
    Retrieval-Augmented Generation (RAG) Engine with ChromaDB vector storage,
    metadata pre-filtering, and cosine similarity citation ranking.
    """

    def __init__(self):
        self.embedder = FastCurriculumEmbedder(dim=384)
        self.chroma_client = None
        self.collection = None
        self._memory_chunks: Dict[str, List[Dict[str, Any]]] = {}
        self._init_chroma()

    def _init_chroma(self):
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY
            )
            try:
                self.collection = self.chroma_client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    embedding_function=self.embedder,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as ef_err:
                logger.info(f"Connecting to existing collection: {ef_err}")
                try:
                    self.collection = self.chroma_client.get_collection(
                        name=settings.CHROMA_COLLECTION_NAME,
                        embedding_function=self.embedder
                    )
                except Exception:
                    self.chroma_client.delete_collection(name=settings.CHROMA_COLLECTION_NAME)
                    self.collection = self.chroma_client.create_collection(
                        name=settings.CHROMA_COLLECTION_NAME,
                        embedding_function=self.embedder,
                        metadata={"hnsw:space": "cosine"}
                    )
            logger.info("ChromaDB vector store connected with FastCurriculumEmbedder.")
        except Exception as e:
            logger.warning(f"Could not initialize ChromaDB client: {e}. In-memory vector store active.")
            self.chroma_client = None
            self.collection = None

    def index_document_chunks(
        self,
        document_id: str,
        document_name: str,
        subject: str,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Embeds and stores chunks in vector database with rich metadata.
        Returns total number of chunks indexed.
        """
        if not chunks:
            return 0

        if document_id not in self._memory_chunks:
            self._memory_chunks[document_id] = []

        ids = []
        documents = []
        metadatas = []

        for c in chunks:
            chunk_id = f"{document_id}_p{c.get('page_number', 1)}_idx{c.get('chunk_index', 0)}"
            text = c.get("text", "").strip()
            if not text:
                continue

            meta = {
                "document_id": document_id,
                "document_name": document_name,
                "subject": subject,
                "page_number": int(c.get("page_number", 1)),
                "chunk_index": int(c.get("chunk_index", 0))
            }

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append(meta)

            self._memory_chunks[document_id].append({
                "id": chunk_id,
                "text": text,
                **meta
            })

        if self.collection and ids:
            try:
                embeddings = self.embedder(documents)
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                logger.info(f"Indexed {len(ids)} chunks for document '{document_name}' in ChromaDB.")
            except Exception as e:
                logger.error(f"Error inserting into ChromaDB: {e}. In-memory fallback retained.")

        return len(ids)

    def get_document_chunks(
        self,
        document_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieves chunks belonging strictly to the specified document_id,
        guaranteeing zero cross-document contamination.
        """
        chunks = []
        # 1. Fetch from ChromaDB if available
        if self.collection:
            try:
                res = self.collection.get(
                    where={"document_id": document_id},
                    limit=limit
                )
                if res and res.get("documents"):
                    docs = res["documents"]
                    metas = res.get("metadatas", [{}] * len(docs))
                    for idx, (doc_text, meta) in enumerate(zip(docs, metas)):
                        chunks.append({
                            "text": doc_text,
                            "document_id": meta.get("document_id", document_id),
                            "document_name": meta.get("document_name", "Academic Note"),
                            "page_number": int(meta.get("page_number", 1)),
                            "chunk_index": int(meta.get("chunk_index", idx)),
                            "similarity_score": 1.0
                        })
                    if chunks:
                        return chunks
            except Exception as e:
                logger.warning(f"Error fetching document chunks from ChromaDB for {document_id}: {e}")

        # 2. Check in-memory chunks
        if document_id in self._memory_chunks:
            for idx, c in enumerate(self._memory_chunks[document_id][:limit]):
                chunks.append({
                    "text": c["text"],
                    "document_id": c.get("document_id", document_id),
                    "document_name": c.get("document_name", "Academic Note"),
                    "page_number": int(c.get("page_number", 1)),
                    "chunk_index": int(c.get("chunk_index", idx)),
                    "similarity_score": 1.0
                })

        return chunks

    def retrieve_relevant_chunks(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 4,
        similarity_threshold: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k semantically relevant chunks with similarity scores and page metadata.
        Strictly isolates retrieval to document_id if provided.
        """
        effective_threshold = 0.05 if document_id else similarity_threshold

        if self.collection:
            try:
                query_vec = self.embedder([query])
                where_filter = {"document_id": document_id} if document_id else None
                results = self.collection.query(
                    query_embeddings=query_vec,
                    n_results=min(top_k * 2, 10),
                    where=where_filter
                )

                retrieved = []
                if results and "documents" in results and results["documents"] and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                    distances = results["distances"][0] if "distances" in results and results["distances"] else [0.2] * len(docs)

                    for doc_text, meta, dist in zip(docs, metas, distances):
                        # Cosine distance to similarity: sim = 1.0 - (dist / 2.0)
                        sim_score = max(0.0, min(1.0, 1.0 - float(dist or 0.2)))
                        # Ensure chunk belongs strictly to requested document_id
                        chunk_doc_id = meta.get("document_id", "")
                        if document_id and chunk_doc_id != document_id:
                            continue

                        if sim_score >= effective_threshold:
                            retrieved.append({
                                "text": doc_text,
                                "document_id": chunk_doc_id or document_id or "",
                                "document_name": meta.get("document_name", "Academic Note"),
                                "page_number": meta.get("page_number", 1),
                                "chunk_index": meta.get("chunk_index", 0),
                                "similarity_score": float(round(sim_score, 3))
                            })

                if retrieved:
                    return sorted(retrieved, key=lambda x: x["similarity_score"], reverse=True)[:top_k]

            except Exception as e:
                logger.warning(f"ChromaDB query fallback: {e}")

        # In-memory vector cosine similarity fallback (strictly isolated)
        fallback_res = self._fallback_cosine_retrieval(query, document_id, top_k)
        if fallback_res:
            return fallback_res

        # If document_id is specified and no chunks found via search query, get document chunks directly
        if document_id:
            return self.get_document_chunks(document_id, limit=top_k)

        return []

    def _fallback_cosine_retrieval(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """Local vector cosine similarity over cached chunks with strict document isolation."""
        q_vec = self.embedder([query])[0]
        candidates = []
        if document_id:
            if document_id in self._memory_chunks:
                target_docs = [self._memory_chunks[document_id]]
            else:
                # Strictly isolate: NEVER query other documents when document_id is specified!
                target_docs = []
        else:
            target_docs = list(self._memory_chunks.values())

        cutoff = 0.05 if document_id else 0.20

        for chunk_list in target_docs:
            for item in chunk_list:
                doc_vec = self.embedder([item["text"]])[0]
                dot = sum(q * d for q, d in zip(q_vec, doc_vec))
                if dot >= cutoff:
                    candidates.append({
                        "text": item["text"],
                        "document_id": item.get("document_id", document_id or ""),
                        "document_name": item.get("document_name", "Academic Note"),
                        "page_number": item.get("page_number", 1),
                        "chunk_index": item.get("chunk_index", 0),
                        "similarity_score": float(round(dot, 3))
                    })

        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return candidates[:top_k]

    def delete_document_chunks(self, document_id: str):
        """Deletes all chunks belonging to a document."""
        if self.collection:
            try:
                self.collection.delete(where={"document_id": document_id})
                logger.info(f"Deleted vector chunks for document {document_id}")
            except Exception as e:
                logger.warning(f"Error deleting from ChromaDB: {e}")

        if document_id in self._memory_chunks:
            del self._memory_chunks[document_id]


# Global singleton
rag_engine = RAGEngine()
