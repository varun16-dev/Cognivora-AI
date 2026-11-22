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

        if not pages or all(len(p["text"].strip()) == 0 for p in pages):
            raise ValueError(f"The PDF document '{path.name}' contains no extractable text layer.")
        return pages

    @staticmethod
    def _parse_docx(file_path: str) -> List[Dict[str, Any]]:
        path = Path(file_path)
        try:
            doc = DocxDocument(file_path)
            full_text = []
            for p in doc.paragraphs:
                if p.text.strip():
                    full_text.append(p.text.strip())
            
            combined_text = "\n\n".join(full_text)
            if not combined_text.strip():
                raise ValueError(f"The DOCX document '{path.name}' contains no readable text.")
            
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
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to parse DOCX document '{file_path}': {str(e)}")

    @staticmethod
    def _parse_txt(file_path: str) -> List[Dict[str, Any]]:
        path = Path(file_path)
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = ""
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if not content or not content.strip():
            raise ValueError(f"The text document '{path.name}' is empty.")

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
        Extracts subject and syllabus topics from document headings and curriculum keywords.
        """
        all_text = "\n".join([p["text"] for p in pages])
        subject = "General Studies"
        topics = []

        # 1. Check for Subject/Course header
        subj_match = re.search(r"(?:^|\n)\s*#{0,3}\s*(?:Subject|Course):\s*([^\n\r]+)", all_text, re.IGNORECASE)
        if subj_match:
            subject = subj_match.group(1).strip()
        else:
            first_line = all_text.strip().split("\n")[0]
            clean_title = re.sub(r"^[#\s\-\*]+", "", first_line).strip()
            if "—" in clean_title:
                subject = clean_title.split("—")[0].strip()
            elif ":" in clean_title and len(clean_title.split(":")[0]) <= 35:
                subject = clean_title.split(":")[0].strip()

        # 2. Extract topics from headings (Markdown #, ##, ###, Chapter/Unit/Module, numbered items)
        raw_headings = re.findall(
            r"(?:^|\n)\s*(?:#{1,4}|\b(?:Chapter|Unit|Module|Section)\s*(?:\d+)?[:\.\-]?|\d+\.)\s*([^\n\r]{3,90})",
            all_text,
            re.IGNORECASE
        )

        ignore_labels = {
            "subject", "course", "target audience", "table of contents",
            "page", "notes", "author", "instructor", "professor", "chapter",
            "unit", "module", "section", "lecture notes", "references"
        }

        for h in raw_headings:
            cleaned = h.strip()
            cleaned = re.sub(r"^[#\-\*\•\d\.\s:]+", "", cleaned).strip()
            cleaned = re.sub(r"^(?:Chapter|Unit|Module|Section)\s*(?:\d+)?[:\.\-]?\s*", "", cleaned, flags=re.IGNORECASE).strip()

            if ":" in cleaned:
                prefix = cleaned.split(":", 1)[0].strip().lower()
                if prefix in ignore_labels:
                    cleaned = cleaned.split(":", 1)[1].strip()

            lower = cleaned.lower()
            if not cleaned or len(cleaned) < 3 or lower in ignore_labels:
                continue

            if lower.startswith(("the ", "in a ", "when ", "note:", "http", "www")):
                continue

            if cleaned not in topics and len(cleaned) <= 80:
                topics.append(cleaned)

        # 3. If fewer than 2 topics found from headings, extract key conceptual phrases
        if len(topics) < 2:
            concept_patterns = [
                r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s+(?:is|are|algorithm|cipher|protocol|model|technique|method)\b",
                r"\b(?:The|A)\s+([A-Za-z]+(?:\s+[A-Za-z]+){1,2})\s+(?:algorithm|cipher|technique|protocol|concept)\b"
            ]
            for pat in concept_patterns:
                for match in re.findall(pat, all_text):
                    m_clean = match.strip()
                    if m_clean.lower() not in [t.lower() for t in topics] and m_clean.lower() not in ignore_labels:
                        topics.append(m_clean)
                    if len(topics) >= 6:
                        break

        if not topics:
            topics = [f"{subject} Fundamentals", f"{subject} Methodologies", f"{subject} Applications"]

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
