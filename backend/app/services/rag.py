from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    source: str
    collection: str
    heading: str = ""


@dataclass(frozen=True)
class SearchHit:
    text: str
    source: str
    collection: str
    score: float
    heading: str = ""


class KnowledgeLoader:
    def load_file(self, path: Path, collection: str) -> list[DocumentChunk]:
        content = path.read_text(encoding="utf-8")
        chunks: list[DocumentChunk] = []
        heading = ""
        paragraphs: list[str] = []
        def flush() -> None:
            if paragraphs:
                chunks.append(DocumentChunk("\n".join(paragraphs).strip(), path.name, collection, heading))
                paragraphs.clear()
        for line in content.splitlines():
            if line.startswith("#"):
                flush()
                heading = line.lstrip("#").strip()
            elif not line.strip():
                flush()
            elif line.strip():
                paragraphs.append(line.strip())
        flush()
        return chunks

    def load_directory(self, directory: Path, collection: str) -> list[DocumentChunk]:
        return [chunk for path in sorted(directory.glob("*.md")) for chunk in self.load_file(path, collection)]


class VectorIndex:
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
        self.chunks: list[DocumentChunk] = []
        self.matrix = None

    def add(self, chunks: list[DocumentChunk]) -> int:
        self.chunks.extend(chunks)
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in self.chunks])
        return len(chunks)

    def search(self, query: str, top_k: int = 5, collection: str | None = None) -> list[SearchHit]:
        if self.matrix is None or not self.chunks:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        candidates = [(index, score) for index, score in enumerate(scores) if score > 0 and (collection is None or self.chunks[index].collection == collection)]
        candidates.sort(key=lambda item: item[1], reverse=True)
        return [SearchHit(self.chunks[index].text, self.chunks[index].source, self.chunks[index].collection, round(float(score), 6), self.chunks[index].heading) for index, score in candidates[:top_k]]

class RAGService:
    def __init__(self, index: VectorIndex | None = None) -> None:
        self.index = index or VectorIndex()
        self.loader = KnowledgeLoader()

    def index_directory(self, directory: Path, collection: str) -> int:
        return self.index.add(self.loader.load_directory(directory, collection))

    def query(self, query: str, collection: str | None = None, top_k: int = 5) -> list[SearchHit]:
        return self.index.search(query, top_k=top_k, collection=collection)
