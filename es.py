from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.elasticsearch import ElasticsearchStore
# from langchain.embeddings import HuggingFaceBgeEmbeddings
# vectorstore = ElasticsearchStore(
#     embedding=OpenAIEmbeddings(),
#     index_name="langchain-demo",
#     es_url="http://localhost:9200"
# )


from sentence_transformers import SentenceTransformer

queries = ['query_1', 'query_2']
passages = ["样例文档-1", "样例文档-2"]
instruction = "为这个句子生成表示以用于检索相关文章："

model = SentenceTransformer(r'D:/models/bge-large-zh-v1.5')
q_embeddings = model.encode([instruction + q for q in queries], normalize_embeddings=True)
p_embeddings = model.encode(passages, normalize_embeddings=True)
scores = q_embeddings @ p_embeddings.T

print(scores)
