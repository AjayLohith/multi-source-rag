from sentence_transformers import SentenceTransformer


model = SentenceTransformer("BAAI/bge-small-en-v1.5")

text = "Multi-source RAG retrieves information from different data sources."

embedding = model.encode(text)

print("Embedding type:", type(embedding))
print("Embedding dimensions:", len(embedding))