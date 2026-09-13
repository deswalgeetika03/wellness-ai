import chromadb
import json

CHROMA = r"C:\Users\preet\Projects\wellness_chroma"
OUTPUT = r".\deployment_experiments\bge_retrieval\minilm_smoke_test.ndjson"

client = chromadb.PersistentClient(path=CHROMA)
collection = client.get_collection("wellness_knowledge")

data = collection.get(
    limit=5,
    include=["embeddings", "metadatas"],
)

with open(OUTPUT, "w", encoding="utf-8") as f:
    for i, vector_id in enumerate(data["ids"]):
        metadata = data["metadatas"][i]

        record = {
            "id": vector_id,
            "values": data["embeddings"][i].tolist(),
            "metadata": {
                "source_id": metadata["source_id"],
                "chunk_id": metadata["chunk_id"],
                "title": metadata["title"],
                "filename": metadata["filename"],
            },
        }

        f.write(json.dumps(record) + "\n")

print("Created:", OUTPUT)
print("Vectors:", len(data["ids"]))
print("Dimension:", len(data["embeddings"][0]))
print("IDs:", data["ids"])
