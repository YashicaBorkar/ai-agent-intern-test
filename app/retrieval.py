import hashlib
import re
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import CHROMA_DIR, EMBEDDING_MODEL, KNOWLEDGE_BASE_DIR
from app.models import DocumentChunk, RetrievedChunk


class KnowledgeBase:
    def __init__(
        self,
        knowledge_base_dir: Path = KNOWLEDGE_BASE_DIR,
        chroma_dir: Path = CHROMA_DIR,
        embedding_model: str = EMBEDDING_MODEL,
    ):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.chroma_dir = Path(chroma_dir)

        self.embedding_model = SentenceTransformer(
            embedding_model
        )

        self.client = chromadb.PersistentClient(
            path=str(self.chroma_dir)
        )

        self.collection = self.client.get_or_create_collection(
            name="aster_row_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

    def _parse_front_matter(
        self,
        content: str,
    ) -> tuple[dict[str, Any], str]:
        metadata: dict[str, Any] = {}

        if not content.startswith("---"):
            return metadata, content

        parts = content.split("---", 2)

        if len(parts) != 3:
            return metadata, content

        front_matter = parts[1].strip()
        body = parts[2].strip()

        for line in front_matter.splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = key.strip()
            value = value.strip()

            if value.lower() in {"true", "false"}:
                value = value.lower() == "true"

            metadata[key] = value

        return metadata, body

    def _split_into_sections(
        self,
        text: str,
    ) -> list[tuple[str, str]]:
        lines = text.splitlines()

        sections: list[tuple[str, list[str]]] = []
        current_heading = "General"
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("#"):
                if current_lines:
                    sections.append(
                        (
                            current_heading,
                            current_lines,
                        )
                    )

                current_heading = re.sub(
                    r"^#+\s*",
                    "",
                    stripped,
                ).strip()

                current_lines = []

            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                (
                    current_heading,
                    current_lines,
                )
            )

        return [
            (
                heading,
                "\n".join(lines).strip(),
            )
            for heading, lines in sections
            if "\n".join(lines).strip()
        ]

    def _chunk_text(
        self,
        text: str,
        max_chars: int = 1200,
        overlap: int = 150,
    ) -> list[str]:
        text = text.strip()

        if len(text) <= max_chars:
            return [text]

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = min(
                start + max_chars,
                len(text),
            )

            if end < len(text):
                split_at = text.rfind(
                    "\n",
                    start,
                    end,
                )

                if split_at <= start:
                    split_at = text.rfind(
                        " ",
                        start,
                        end,
                    )

                if split_at > start:
                    end = split_at

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = max(
                end - overlap,
                start + 1,
            )

        return chunks

    def load_documents(self) -> list[DocumentChunk]:
        documents: list[DocumentChunk] = []

        files = sorted(
            self.knowledge_base_dir.glob("*.md")
        )

        for file_path in files:
            content = file_path.read_text(
                encoding="utf-8"
            )

            metadata, body = self._parse_front_matter(
                content
            )

            sections = self._split_into_sections(body)

            for section_index, (
                heading,
                section_text,
            ) in enumerate(sections):
                chunks = self._chunk_text(
                    section_text
                )

                for chunk_index, chunk_text in enumerate(
                    chunks
                ):
                    chunk_id_source = (
                        f"{file_path.name}:"
                        f"{section_index}:"
                        f"{chunk_index}:"
                        f"{chunk_text}"
                    )

                    chunk_id = hashlib.sha256(
                        chunk_id_source.encode("utf-8")
                    ).hexdigest()[:16]

                    chunk_metadata = {
                        **metadata,
                        "filename": file_path.name,
                        "heading": heading,
                        "section_index": section_index,
                        "chunk_index": chunk_index,
                    }

                    documents.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            text=chunk_text,
                            filename=file_path.name,
                            heading=heading,
                            metadata=chunk_metadata,
                        )
                    )

        return documents

    def build_index(self) -> int:
        documents = self.load_documents()

        if not documents:
            return 0

        texts = [
            document.text
            for document in documents
        ]

        embeddings = self.embedding_model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).tolist()

        self.collection.upsert(
            ids=[
                document.chunk_id
                for document in documents
            ],
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                document.metadata
                for document in documents
            ],
        )

        return len(documents)

    def _authority_score(
        self,
        metadata: dict[str, Any],
    ) -> float:
        score = 0.0

        status = str(
            metadata.get(
                "status",
                "",
            )
        ).lower()

        audience = str(
            metadata.get(
                "audience",
                "",
            )
        ).lower()

        authority = str(
            metadata.get(
                "policy_authority",
                "",
            )
        ).lower()

        document_type = str(
            metadata.get(
                "document_type",
                "",
            )
        ).lower()

        if status == "active":
            score += 2.5

        elif status == "superseded":
            score -= 6.0

        elif status in {
            "draft",
            "internal",
        }:
            score -= 5.0

        if authority == "official":
            score += 2.5

        elif authority in {
            "internal",
            "unofficial",
        }:
            score -= 3.0

        if audience in {
            "customer",
            "customers",
            "public",
        }:
            score += 1.0

        if document_type == "policy":
            score += 1.0

        return score

    def _tokenize(self, text: str) -> set[str]:
        return set(
            re.findall(
                r"\b[a-z0-9]+\b",
                text.lower(),
            )
        )

    def _lexical_score(
        self,
        query: str,
        text: str,
        heading: str,
    ) -> float:
        query_terms = self._tokenize(query)

        if not query_terms:
            return 0.0

        text_terms = self._tokenize(text)
        heading_terms = self._tokenize(heading)

        text_overlap = len(
            query_terms & text_terms
        ) / len(query_terms)

        heading_overlap = len(
            query_terms & heading_terms
        ) / len(query_terms)

        return (
            text_overlap * 2.0
            + heading_overlap * 3.0
        )

    def _query_intent_score(
        self,
        query: str,
        filename: str,
        heading: str,
        text: str,
    ) -> float:
        query_lower = query.lower()
        filename_lower = filename.lower()
        heading_lower = heading.lower()
        text_lower = text.lower()

        score = 0.0

        intent_groups = [
            (
                [
                    "return window",
                    "how long",
                    "how many days",
                    "return period",
                ],
                [
                    "return",
                    "window",
                    "return window",
                ],
            ),
            (
                [
                    "return fee",
                    "shipping fee",
                    "deducted",
                    "cost to return",
                ],
                [
                    "return shipping",
                    "refund",
                    "fee",
                ],
            ),
            (
                [
                    "warranty",
                    "covered",
                    "warranty period",
                ],
                [
                    "warranty",
                    "coverage",
                ],
            ),
            (
                [
                    "ship internationally",
                    "international shipping",
                    "ship to",
                    "shipping to",
                ],
                [
                    "international",
                    "shipping",
                    "destinations",
                ],
            ),
            (
                [
                    "dishwasher",
                    "dishwasher safe",
                    "wash",
                    "clean",
                ],
                [
                    "dishwasher",
                    "wash",
                    "care",
                ],
            ),
            (
                [
                    "address change",
                    "change address",
                ],
                [
                    "address",
                    "change",
                ],
            ),
        ]

        for query_phrases, content_terms in intent_groups:
            if any(
                phrase in query_lower
                for phrase in query_phrases
            ):
                if any(
                    term in heading_lower
                    for term in content_terms
                ):
                    score += 4.0

                if any(
                    term in text_lower
                    for term in content_terms
                ):
                    score += 2.0

                if any(
                    term in filename_lower
                    for term in content_terms
                ):
                    score += 1.0

        return score

    def search(
        self,
        query: str,
        top_k: int = 8,
    ) -> list[RetrievedChunk]:
        query_embedding = self.embedding_model.encode(
            [query],
            normalize_embeddings=True,
        ).tolist()[0]

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(
                top_k * 4,
                40,
            ),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        documents = result.get(
            "documents",
            [[]],
        )[0]

        metadatas = result.get(
            "metadatas",
            [[]],
        )[0]

        distances = result.get(
            "distances",
            [[]],
        )[0]

        retrieved: list[RetrievedChunk] = []

        for text, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):
            filename = str(
                metadata.get(
                    "filename",
                    "unknown",
                )
            )

            heading = str(
                metadata.get(
                    "heading",
                    "General",
                )
            )

            chunk_id = hashlib.sha256(
                f"{filename}:{heading}:{text}".encode(
                    "utf-8"
                )
            ).hexdigest()[:16]

            similarity = 1.0 - float(distance)

            lexical_score = self._lexical_score(
                query,
                text,
                heading,
            )

            authority_score = self._authority_score(
                metadata
            )

            intent_score = self._query_intent_score(
                query,
                filename,
                heading,
                text,
            )

            final_score = (
                similarity
                + lexical_score
                + authority_score
                + intent_score
            )

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                text=text,
                filename=filename,
                heading=heading,
                metadata=metadata,
            )

            retrieved.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=final_score,
                )
            )

        retrieved.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return retrieved[:top_k]

    def format_sources(
        self,
        results: list[RetrievedChunk],
    ) -> list[str]:
        seen: set[str] = set()
        sources: list[str] = []

        for result in results:
            source = (
                f"{result.chunk.filename} — "
                f"{result.chunk.heading}"
            )

            if source not in seen:
                seen.add(source)
                sources.append(source)

        return sources