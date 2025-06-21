import os
import logging
import chromadb
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model and collection name from environment or default
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "code_snippets_collection")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Initialize model and DB
model = SentenceTransformer(EMBED_MODEL)
client = chromadb.Client()
try:
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    logger.info(f"Connected to ChromaDB collection: {COLLECTION_NAME}")
except Exception as e:
    logger.error(f"ChromaDB collection error: {e}")
    raise

def populate_chromadb_with_snippets(snippets_data: dict):
    documents, ids, metadatas, embeddings = [], [], [], []

    for snippet_id, snippet_content in snippets_data.items():
        if snippet_content.strip():
            documents.append(snippet_content)
            ids.append(f"snippet_{snippet_id}")
            metadatas.append({"type": "code_snippet", "original_id": snippet_id})
            embeddings.append(model.encode([snippet_content])[0].tolist())

    try:
        logger.info(f"Adding {len(documents)} snippets to ChromaDB...")
        collection.add(documents=documents, ids=ids, metadatas=metadatas, embeddings=embeddings)
        logger.info("Snippets added successfully.")
    except Exception as e:
        logger.error(f"Error adding to ChromaDB: {e}")

def search_snippet(query: str, k: int = 1):
    try:
        query_embedding = model.encode([query]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        if results and results["documents"]:
            return [
                {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                } for i in range(len(results["documents"][0]))
            ]
        else:
            return []
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

def demo():
    dummy_snippets_data = {
        "101": "def calculate_sum(a, b): return a + b",
        "102": "class MyClass: def __init__(self): self.value = 0",
        "103": "import os; print(os.getcwd())",
        "104": "def find_max(arr): return max(arr)",
        "105": "This is a non-code document about general programming concepts.",
        "106": "function greet(name) { console.log('Hello, ' + name); }"
    }

    populate_chromadb_with_snippets(dummy_snippets_data)

    queries = [
        ("sum function", "how to calculate the sum of two numbers in python", 2),
        ("directory operations", "how to get current working directory", 1),
        ("JavaScript greeting", "how to greet someone in javascript", 1)
    ]

    for title, query, k in queries:
        print(f"\n--- Searching for '{title}' ---")
        results = search_snippet(query, k)
        if results:
            for i, res in enumerate(results):
                print(f"Result {i+1}:")
                print(f"  Content: {res['content']}")
                print(f"  Metadata: {res['metadata']}")
                print(f"  Distance: {res['distance']:.4f}")
        else:
            print("No results found.")

if __name__ == "__main__":
    demo()
