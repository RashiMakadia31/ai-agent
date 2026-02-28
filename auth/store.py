import chromadb
from chromadb.config import Settings
from services.embedder import CodeEmbedder
from services.llm import call_gemini
import boto3
import json
import os
import uuid
from datetime import datetime

# === Config ===
CHROMA_DIR = "vector_db"
COLLECTION_NAME = "code_snippets"
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "your-bucket-name")
S3_CODE_FILE = os.environ.get("S3_CODE_FILE", "snippets.json")

s3_client = boto3.client("s3")

# === Init ChromaDB ===
client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_DIR))
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# === Load Snippets from S3 (for tracking) ===
def load_snippets_from_s3():
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_CODE_FILE)
        return json.loads(obj['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        return []
    except Exception as e:
        print("❌ Error loading snippets:", e)
        return []

# === Save Snippets to S3 ===
def save_snippets_to_s3(snippets):
    try:
        s3_client.put_object(Bucket=S3_BUCKET, Key=S3_CODE_FILE, Body=json.dumps(snippets))
        print(f"✅ Saved {len(snippets)} snippets to S3.")
    except Exception as e:
        print("❌ Error saving snippets:", e)

# === Add New Snippets ===
def add_code_snippets(snippets):
    embedder = CodeEmbedder()
    embeddings = embedder.get_embeddings(snippets)

    ids = [f"code_{collection.count() + i}" for i in range(len(snippets))]
    collection.add(
        documents=snippets,
        embeddings=[embedding.tolist() for embedding in embeddings],
        ids=ids
    )

    # Save raw snippets to S3
    all_snippets = load_snippets_from_s3()
    for text in snippets:
        all_snippets.append({
            "id": str(uuid.uuid4()),
            "code": text,
            "timestamp": datetime.utcnow().isoformat()
        })
    save_snippets_to_s3(all_snippets)

# === Query ===
def query_rag(prompt, top_k=3):
    embedder = CodeEmbedder()
    query_embedding = embedder.get_embeddings([prompt])[0]

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    retrieved_docs = results['documents'][0]
    if not retrieved_docs:
        return "❌ No relevant code snippets found."

    context = "\n\n".join(retrieved_docs)
    full_prompt = f"""Use the following code snippets to answer the question:

{context}

Question: {prompt}
Answer:"""

    return call_gemini(full_prompt)

# === CLI ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", nargs='+', help="Add code snippets")
    parser.add_argument("--query", type=str, help="Ask a question")
    args = parser.parse_args()

    if args.add:
        add_code_snippets(args.add)
    elif args.query:
        answer = query_rag(args.query)
        print(f"\n🧠 Answer:\n{answer}")
    else:
        print("Use --add or --query")
