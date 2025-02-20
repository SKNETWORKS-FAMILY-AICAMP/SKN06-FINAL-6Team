import pandas as pd
import sqlite3

from langchain_community.document_loaders import DataFrameLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory

from dotenv import load_dotenv

load_dotenv()

### 임베딩 모델
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 모델
model = ChatOpenAI(model="gpt-4o-mini")

### 메모리
memory = ConversationBufferMemory(llm=model, max_token_limit=200, return_messages=True, memory_key="history")

def load(case):
    if case == "func":
        conn = sqlite3.connect("funs.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    elif case == "ref":
        conn = sqlite3.connect("fridges.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipes']
        df.drop(columns=['name', 'ingredients', 'recipes'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    else:
        conn = sqlite3.connect("만개.db") # 이름 맞게 수정 필요
        df = pd.read_sql("SELECT * FROM recipes", conn)

        df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipe'] + " " + df['category']
        df.drop(columns=['name', 'ingredients', 'recipes'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs

def func(query=None):
    '''
    편스토랑 retriever
    '''
    ## load
    docs = load("func")

    ## vecotrdb 저장 -> 최초 일회만 실행
    fais = FAISS.from_documents(documents=docs, embedding=embeddings) # 편스토랑 임베딩 후 db
    fais.save_local("fun_faiss") # 로컬 저장
    
    ## vecotrdb 로드
    fais = FAISS.load_local("fun_faiss", embeddings, allow_dangerous_deserialization=True) # 로컬 저장 로드

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    # fensemble = EnsembleRetriever(retrievers=[fbm25_retr, fais_retr], weights=[0.5, 0.5],)
    # res = fensemble.invoke(query)
    return bm25_retr, fais_retr

def ref(query=None):
    '''
    냉장고를 부탁해 retriever
    '''
    ## load
    docs = load("ref")

    ## vectordb 저장
    fais = FAISS.from_documents(documents=docs, embedding=embeddings) # 냉부 임베딩 후 db
    fais.save_local("ref_faiss") # 로컬 저장

    ## vectordb 로드
    fais = FAISS.load_local("ref_faiss", embeddings, allow_dangerous_deserialization=True)

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    # rensemble = EnsembleRetriever(retrievers=[bm25_retr, fais_retr], weights=[0.5, 0.5],)
    # res = rensemble.invoke(query)
    return bm25_retr, fais_retr

# def man(query=None):
#     '''
#     만개의 레시피 retriever
#     '''
#     ## load
#     docs = load("man")

#     ## vectordb 저장
#     fais = FAISS.from_documents(documents=docs, embedding=embeddings) # 만개 임베딩 후 db
#     fais.save_local("man_faiss") # 로컬 저장

#     # vectordb 로드
#     fais = FAISS.load_local("man_faiss", embeddings, allow_dangerous_deserialization=True)

#     ## bm25 retriever, faiss retriever 앙상블
#     bm25_retr = BM25Retriever.from_documents(docs)
#     bm25_retr.k = 3
#     fais_retr = fais.as_retriever(search_kwargs={"k": 3})
#     # mensemble = EnsembleRetriever(retrievers=[bm25_retr, fais_retr], weights=[0.5, 0.5],)
#     # res = mensemble.invoke(query)
#     return bm25_retr, fais_retr

def mkch():
    # Prompt Template 생성
    messages = [
            ("ai", """
            너는 사용자의 질문(question)에 맞는 요리를 알려주는 ai야.
    {context}"""),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{question}"),
        ]
    prompt_template = ChatPromptTemplate(messages)

    # 메모리
    def load_history(input):
        return memory.load_memory_variables({})["history"]

    # retriever 로드 => 추후 함수 선택 코드 넣어야 함
    rbm25_retr, rfais_retr = ref()
    fbm25_retr, ffais_retr = func()

    retriever = EnsembleRetriever(retrievers=[rbm25_retr, rfais_retr, fbm25_retr, ffais_retr], weights=[0.25, 0.25, 0.25, 0.25],)

    # Chain 구성 retriever(관련 문서 조회) -> prompt_template(prompt 생성) model(정답) -> output parser
    chain = RunnableLambda(lambda x:x['question']) | {"context": retriever, "question":RunnablePassthrough() , "history": RunnableLambda(load_history)}  | prompt_template | model | StrOutputParser()
    return chain

def chat():
    chain = mkch()
    while True:
        query = input("메시지 입력 > ")
        if query == "종료":
            break
        res = chain.invoke({"question": query})
        memory.save_context(inputs={"human": query}, outputs={"ai":res})
        print(res)

chat()