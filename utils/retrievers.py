from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import MergerRetriever
from langchain_qdrant import FastEmbedSparse, RetrievalMode, QdrantVectorStore

from dotenv import load_dotenv

load_dotenv()

def load_retriever(isref=True, isfun=True, isman=True):
    """local에서 vector db load하는 함수"""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
    url = "http://localhost:6333/"
    def ref():
        """냉장고를 부탁해 retriever 호출 함수"""
        qdrant = QdrantVectorStore.from_existing_collection(embedding=embeddings, sparse_embedding=sparse_embeddings, collection_name="ref", url=url, retrieval_mode=RetrievalMode.HYBRID)
        return qdrant.as_retriever(search_type="mmr", search_kwargs={"k": 3})

    def fun():
        """편스토랑 retriever 호출 함수"""
        qdrant = QdrantVectorStore.from_existing_collection(embedding=embeddings, sparse_embedding=sparse_embeddings, collection_name="funs", url=url, retrieval_mode=RetrievalMode.HYBRID)
        return qdrant.as_retriever(search_type="mmr", search_kwargs={"k": 3})

    def man():
        """만개의 레시피 retriever 호출 함수"""
        qdrant = QdrantVectorStore.from_existing_collection(embedding=embeddings, sparse_embedding=sparse_embeddings, collection_name="man", url=url, retrieval_mode=RetrievalMode.HYBRID)
        return qdrant.as_retriever(search_type="mmr", search_kwargs={"k": 3})
    
    retrievers = []
    if isref:
        ensemble = ref()
        retrievers.append(ensemble)
    if isfun:
        ensemble = fun()
        retrievers.append(ensemble)
    if isman:
        ensemble = man()
        retrievers.append(ensemble)

    if len(retrievers) == 1:
        # 선택한 것이 한 개인 경우 -> 한 개 리트리버만 반환
        return retrievers[0]
    
    else:
        # 선택한 것이 여러 개인 경우 -> 선택한 개수만큼 리트리버 반환
        if not retrievers:
            retrievers = [ref(), fun(), man()]
        retriever = MergerRetriever(retrievers=retrievers)
        return retriever
    
# load_retriever(False, False, False)