import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

app = FastAPI()

model = SentenceTransformer('D:/models/bge-large-zh-v1.5')
query_instruction = "为这个句子生成表示以用于检索相关文章："
es_client = AsyncElasticsearch("http://localhost:9200")


@app.get('/knn_search')
async def knn_search(query: str):
    print(query)
    knn = {
        "field": "info_vector",
        "k": 10,
        "query_vector": model.encode(query_instruction + query, normalize_embeddings=True),
        "num_candidates": 50
    }

    response = await es_client.search(index='book', knn=knn)
    return response.body


if __name__ == '__main__':
    uvicorn.run(app)
