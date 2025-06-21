from sentence_transformers import SentenceTransformer
import numpy as np

class CodeEmbedder:
    """
    Wrapper class for generating embeddings for code snippets using a sentence transformer model.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initializes the embedding model.
        
        Args:
            model_name (str): Name of the transformer model to load.
                              Default is 'all-MiniLM-L6-v2'.
        """
        self.model = SentenceTransformer(model_name)

    def get_embeddings(self, snippets):
        """
        Generates embeddings for a list of code snippets.

        Args:
            snippets (list of str): Code snippets to encode.

        Returns:
            numpy.ndarray: Array of embeddings where each row corresponds to a snippet.

        Raises:
            TypeError: If the input is not a list.
        """
        # Ensure the input is a list
        if not isinstance(snippets, list):
            raise TypeError("Expected a list of code strings")

        # Compute embeddings, return as numpy array
        return self.model.encode(snippets, convert_to_numpy=True)

if __name__ == "__main__":
    # Example usage when script is run directly
    
    # Instantiate the embedder
    embedder = CodeEmbedder()
    
    # Example code snippets to embed
    code_samples = [
        "def greet(name):\n    return f'Hello, {name}!'",
        "class MathOps:\n    def square(self, x):\n        return x * x"
    ]
    
    # Generate embeddings for code samples
    embeddings = embedder.get_embeddings(code_samples)
    
    # Print the shape of each embedding vector
    for i, vec in enumerate(embeddings):
        print(f"Snippet {i} embedding shape: {vec.shape}")
