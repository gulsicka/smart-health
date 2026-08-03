from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2") #model is loaded once at module level so it doesnt reload on every request

def embed(text: str) -> list[float]:
    return model.encode(text).tolist() #retur numpy vector array