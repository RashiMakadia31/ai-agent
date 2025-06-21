import chromadb
from chromadb.config import Settings
from services.embedder import CodeEmbedder
from LLM import call_gemini  
import os

# === Config ===
CHROMA_DIR = "vector_db"
COLLECTION_NAME = "code_snippets"

# === Initialize ChromaDB client ===
client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_DIR))

# === Get or create collection ===
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# === Add new code snippets ===
def add_code_snippets(snippets):
    embedder = CodeEmbedder()
    embeddings = embedder.get_embeddings(snippets)

    ids = [f"code_{collection.count() + i}" for i in range(len(snippets))]

    collection.add(
        documents=snippets,
        embeddings=[embedding.tolist() for embedding in embeddings],
        ids=ids
    )
    print(f"✅ Added {len(snippets)} snippets to ChromaDB.")

# === Query and generate response ===
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

    return call_gemini(full_prompt)  # or call_deepseek(full_prompt)

# === CLI for testing ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ChromaDB-based RAG Code Assistant")
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
