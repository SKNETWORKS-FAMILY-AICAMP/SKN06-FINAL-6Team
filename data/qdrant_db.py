import sqlite3
import pandas as pd

from langchain_community.document_loaders import DataFrameLoader
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, RetrievalMode, QdrantVectorStore
from dotenv import dotenv_values
from dotenv import load_dotenv
load_dotenv()


def load(case):
    if case == "funs":
        conn = sqlite3.connect("db/funs.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    elif case == "ref":
        conn = sqlite3.connect("db/fridges.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe', 'ingredients_list'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    else:
        conn = sqlite3.connect("db/man.db")
        df = pd.read_sql("SELECT * FROM recipes", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe'] + " ||| " + df['category'] + " ||| " + df['info'] + " ||| " + df['intro']
        df.drop(columns=['name', 'ingredients', 'recipe', "info", "intro"], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
url = dotenv_values()["QDRANT_SERVER_URL"]
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

fdocs = load("funs")
QdrantVectorStore.from_documents(fdocs, embedding=embeddings, sparse_embedding=sparse_embeddings, url=url, collection_name="funs", retrieval_mode=RetrievalMode.HYBRID)

rdocs = load("ref")
qdrant2 = QdrantVectorStore.from_documents(rdocs, embedding=embeddings, sparse_embedding=sparse_embeddings, url=url, collection_name="ref", retrieval_mode=RetrievalMode.HYBRID)

mdocs = load("man")
qdrant3 = QdrantVectorStore.from_documents(mdocs, embedding=embeddings, sparse_embedding=sparse_embeddings, url=url, collection_name="man", retrieval_mode=RetrievalMode.HYBRID)