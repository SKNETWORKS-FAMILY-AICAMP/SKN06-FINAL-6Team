from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, RetrievalMode, QdrantVectorStore
from dotenv import load_dotenv
load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

url = "3.36.90.250:6333"
sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
qdrant = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    sparse_embedding=sparse_embeddings,
    collection_name="funs",
    url=url,
    retrieval_mode=RetrievalMode.HYBRID,
)
print(qdrant.as_retriever().invoke("마라 짜장"))