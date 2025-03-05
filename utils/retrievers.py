import sqlite3
import pandas as pd

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever, MergerRetriever

from dotenv import load_dotenv

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def load(case):
    if case == "funs":
        conn = sqlite3.connect("./db/funs.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    elif case == "ref":
        conn = sqlite3.connect("./db/fridges.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    else:
        conn = sqlite3.connect("./db/man.db")
        df = pd.read_sql("SELECT * FROM recipes", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe'] + " ||| " + df['category'] + " ||| " + df['info'] + " ||| " + df['intro']
        df.drop(columns=['name', 'ingredients', 'recipe', "info", "intro"], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(model_name='gpt-4o-mini', chunk_size=1000, chunk_overlap=0)
        docs = loader.load_and_split(splitter)
        return docs

def load_retriever():
    def mkretr(case, faiss_path):
        """ retriever 정의의 함수"""
        docs = load(case)

        # vectordb 로드
        fais = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)

        # BM25 retriever, FAISS retriever 앙상블
        bm25_retr = BM25Retriever.from_documents(docs)
        bm25_retr.k = 3
        fais_retr = fais.as_retriever(search_kwargs={"k": 3})
        
        return bm25_retr, fais_retr

    # retriever 로드 => 추후 함수 선택 코드 넣어야 함
    rbm25_retr, rfais_retr = mkretr("ref", "./faiss/ref_faiss") # 냉장고를 부탁해
    fbm25_retr, ffais_retr = mkretr("funs", "./faiss/fun_faiss") # 편스토랑
    mbm25_retr, mfais_retr = mkretr("man", "./faiss/man_faiss") # 만개의 레시피

    ensemble1 = EnsembleRetriever(retrievers=[rbm25_retr, rfais_retr],) # weights=[0.25, 0.25, 0.25, 0.25],) # weight: retriever 별 가중치 조절 가능
    ensemble2 = EnsembleRetriever(retrievers=[fbm25_retr, ffais_retr],) # weights=[0.25, 0.25, 0.25, 0.25],) # weight: retriever 별 가중치 조절 가능
    ensemble3 = EnsembleRetriever(retrievers=[mbm25_retr, mfais_retr],) # weights=[0.25, 0.25, 0.25, 0.25],) # weight: retriever 별 가중치 조절 가능
    retriever = MergerRetriever(retrievers=[ensemble1, ensemble2, ensemble3])
    return retriever