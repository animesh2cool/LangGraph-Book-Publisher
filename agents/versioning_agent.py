import chromadb
from chromadb import PersistentClient
import uuid
from datetime import datetime
from typing import Literal

class VersioningAgent:
    def __init__(self, persist_directory="storage/chromadb"):
        self.client = PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("book_versions")

    def save_version(
        self,
        chapter_id: str,
        version_type: Literal["raw", "rewrite", "review", "final"],
        content: str,
        author: Literal["scraper", "writer", "reviewer", "human"],
        metadata: dict = None
    ):
        doc_id = f"{chapter_id}-{version_type}-{str(uuid.uuid4())[:8]}"
        timestamp = datetime.now().isoformat()

        self.collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[{
                "chapter_id": chapter_id,
                "version_type": version_type,
                "author": author,
                "timestamp": timestamp,
                **(metadata or {})
            }]
        )
        print(f"[VersioningAgent] Saved {version_type} version for chapter {chapter_id}")

    def get_versions(self, chapter_id: str):
        results = self.collection.get(
            where={"chapter_id": chapter_id},
            include=["documents", "metadatas"]
        )
        return results