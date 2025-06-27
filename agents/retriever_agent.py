import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

class RetrieverAgent:
    def __init__(self, persist_directory="storage/chromadb"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="book_versions",
            embedding_function=SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        )

    def retrieve_similar(self, query: str, top_k: int = 2):
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            print("[RetrieverAgent] No matching results found.")
            return None

        print(f"\n[RetrieverAgent] Found top {top_k} similar version(s):\n")
        for doc, meta in zip(documents, metadatas):
            print(f"Version Type: {meta['version_type']}")
            print(f"Author: {meta['author']}")
            print(f"Timestamp: {meta['timestamp']}")
            print(f"Content:\n{doc}\n{'-'*60}")

        return {"matched_versions": documents, "metadata": metadatas}