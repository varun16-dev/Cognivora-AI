import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pymupdf  # Modern PyMuPDF API (replacing deprecated fitz)
from docx import Document as DocxDocument


class DocumentParser:
    """Multi-format academic document parser with semantic chunking."""

    @staticmethod
    def extract_text_from_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts structured text from PDF, DOCX, or TXT file.
        Returns a list of page dicts: [{"page_number": int, "text": str}]
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return DocumentParser._parse_pdf(file_path)
        elif ext == ".docx":
            return DocumentParser._parse_docx(file_path)
        elif ext == ".txt":
            return DocumentParser._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported document format: '{ext}'. Allowed: .pdf, .docx, .txt")

    @staticmethod
    def _parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        pages = []
        try:
            doc = pymupdf.open(file_path)
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text").strip()
                if text:
                    pages.append({
                        "page_number": page_idx + 1,
                        "text": text
                    })
            doc.close()
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF document '{file_path}': {str(e)}")

        if not pages:
            # Fallback if document is scanned or text is empty
            pages.append({
                "page_number": 1,
                "text": "Document appears to contain scanned images or no extractable digital text layer."
            })
        return pages

    @staticmethod
    def _parse_docx(file_path: str) -> List[Dict[str, Any]]:
        try:
            doc = DocxDocument(file_path)
            full_text = []
            for p in doc.paragraphs:
                if p.text.strip():
                    full_text.append(p.text.strip())
            
            combined_text = "\n\n".join(full_text)
            # Break large docx files into pseudo-pages (~3000 chars per page)
            if not combined_text:
                combined_text = "Empty DOCX document."
            
            char_limit = 2500
            pages = []
            start = 0
            page_num = 1
            while start < len(combined_text):
                chunk = combined_text[start:start + char_limit]
                pages.append({"page_number": page_num, "text": chunk})
                start += char_limit
                page_num += 1
            return pages
        except Exception as e:
            raise RuntimeError(f"Failed to parse DOCX document '{file_path}': {str(e)}")

    @staticmethod
    def _parse_txt(file_path: str) -> List[Dict[str, Any]]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = ""
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if not content:
            raise RuntimeError(f"Could not read text file '{file_path}' with supported encodings.")

        # Chunk into pseudo-pages for citation consistency
        char_limit = 2500
        pages = []
        start = 0
        page_num = 1
        while start < len(content):
            chunk = content[start:start + char_limit]
            pages.append({"page_number": page_num, "text": chunk.strip()})
            start += char_limit
            page_num += 1
        return pages

    @staticmethod
    def extract_topics_and_subject(pages: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        Extracts subject and syllabus topics from document headings.
        """
        all_text = "\n".join([p["text"] for p in pages])
        subject = "General Studies"
        topics = []

        # Check for Subject header
        subj_match = re.search(r"##?\s*(?:Subject|Course):\s*([^\n\r]+)", all_text, re.IGNORECASE)
        if subj_match:
            subject = subj_match.group(1).strip()

        # Check for Chapter or Section headers
        headings = re.findall(
            r"(?:###?|\d+\.|\bChapter\s+\d+:|\bUnit\s+\d+:|\bSection\s+\d+:)\s*([A-Za-z0-9\s,\-\(\)\'\"]{4,80})",
            all_text
        )
        for h in headings:
            cleaned = h.strip()
            # Filter non-topic lines
            if cleaned and not cleaned.lower().startswith(("the", "in a", "when", "table of contents", "page", "note")):
                if cleaned not in topics and len(cleaned) > 3:
                    topics.append(cleaned)

        if not topics:
            # Fallback default topics
            topics = ["Introduction & Core Concepts", "Key Principles & Theories", "Methodologies & Algorithms", "Practical Applications & Summary"]

        return subject, topics[:10]

    @staticmethod
    def semantic_chunk_pages(
        pages: List[Dict[str, Any]],
        chunk_size_chars: int = 1500,
        overlap_chars: int = 250
    ) -> List[Dict[str, Any]]:
        """
        Splits extracted pages into overlapping semantic chunks.
        Each chunk contains: chunk_index, page_number, text, char_length.
        """
        chunks = []
        chunk_index = 0

        for page_data in pages:
            page_num = page_data["page_number"]
            page_text = page_data["text"]

            # Split paragraphs
            paragraphs = page_text.split("\n\n")
            current_chunk = ""

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                if len(current_chunk) + len(para) < chunk_size_chars:
                    current_chunk += ("\n\n" if current_chunk else "") + para
                else:
                    if current_chunk:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "page_number": page_num,
                            "text": current_chunk.strip()
                        })
                        chunk_index += 1
                        # Retain overlap from end of current_chunk
                        overlap = current_chunk[-overlap_chars:] if len(current_chunk) > overlap_chars else ""
                        current_chunk = overlap + "\n\n" + para
                    else:
                        # Single paragraph exceeds chunk size, split by sentences
                        sentences = re.split(r"(?<=[.!?])\s+", para)
                        for sent in sentences:
                            if len(current_chunk) + len(sent) < chunk_size_chars:
                                current_chunk += (" " if current_chunk else "") + sent
                            else:
                                if current_chunk:
                                    chunks.append({
                                        "chunk_index": chunk_index,
                                        "page_number": page_num,
                                        "text": current_chunk.strip()
                                    })
                                    chunk_index += 1
                                current_chunk = sent

            if current_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "page_number": page_num,
                    "text": current_chunk.strip()
                })
                chunk_index += 1

        return chunks
