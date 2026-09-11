import chromadb
from collections import Counter

CHROMA_DIR = r"C:\Users\preet\Projects\wellness_chroma"
COLLECTION_NAME = "wellness_knowledge"

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection(COLLECTION_NAME)

data = collection.get(include=["metadatas"])

source_ids = [
    metadata["source_id"]
    for metadata in data["metadatas"]
]

counts = Counter(source_ids)

print("=" * 60)
print("CHUNK DISTRIBUTION BY SOURCE")
print("=" * 60)

total = sum(counts.values())

for source_id, count in sorted(counts.items()):
    percentage = count / total * 100
    print(
        f"Source {source_id}: "
        f"{count:3d} chunks "
        f"({percentage:5.1f}%)"
    )

print("-" * 60)
print(f"Total chunks: {total}")
print("=" * 60)