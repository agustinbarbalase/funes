from fastembed import TextEmbedding
from app.embeddings.embedding import Embedder


def prepare_for_embedding(title: str, description: str, type: str, date: str) -> str:
    sentences = description.split(".")[:2]
    short_desc = ". ".join(s.strip() for s in sentences if s.strip())
    return f"{type} | {date} | {title} | {short_desc}"


class FastEmbedEmbedding(Embedder):

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, text: str) -> list[float]:
        return list(self._model.embed([text]))[0].tolist()

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self._model.embed(texts)]
