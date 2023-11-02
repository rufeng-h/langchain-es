from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores.elasticsearch import ElasticsearchStore

model_name = r"D:\models\bge-large-zh-v1.5"
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': True}
embeddings = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
    query_instruction="为这个句子生成表示以用于检索相关文章："
)

vector_store = ElasticsearchStore(index_name='book_test', embedding=embeddings, es_user="elastic",
                                  es_password="yq7UbfMeNNGkvFh2gBf_")

vector_store.as_retriever()
