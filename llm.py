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
        conn = sqlite3.connect("data.db")
        df = pd.read_sql("SELECT * FROM processed_data", conn)

        df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipe'] + " " + df['category'] + " " + df['info'] + " " + df['intro']
        df.drop(columns=['name', 'ingredients', 'recipe', "info", "intro"], inplace=True)
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
    
    ## vecotrdb 로드
    fais = FAISS.load_local("fun_faiss", embeddings, allow_dangerous_deserialization=True) # 로컬 저장 로드

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    return bm25_retr, fais_retr

def ref(query=None):
    '''
    냉장고를 부탁해 retriever
    '''
    ## load
    docs = load("ref")

    ## vectordb 로드
    fais = FAISS.load_local("ref_faiss", embeddings, allow_dangerous_deserialization=True)

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    return bm25_retr, fais_retr

def man(query=None):
    '''
    만개의 레시피 retriever
    '''
    ## load
    docs = load("man")

    # vectordb 로드
    fais = FAISS.load_local("man_faiss", embeddings, allow_dangerous_deserialization=True)

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    return bm25_retr, fais_retr

def mkch():
    # Prompt Template 생성
    messages = [
            ("ai", """
            너는 사용자의 질문(question)에 맞는 요리를 알려주는 ai야.

            요리 소개할 때 이름을 언급한 뒤, 한 줄 정도 간단한 요리 소개를 하고 재료를 알려줘.
            요리 이름은 이름에서 만든 사람을 알 수 있다면 요리사도 같이 알려줘.
            사용자가 네가 추천해준 요리 안에서 요리를 선택하면 사진 혹은 영상과 함께 레시피를 알려줘.
            만약 해당 요리의 사진, 영상이 모두 없으면, 알려주지말고 하나라도 있으면 같이 첨부해서 알려줘.
            요리는 기본적으로 세 가지 추천주고, 사용자가 특정 요리 하나를 질문한 경우에만 해당하는 요리 한가지만 알려줘.
            사용자의 질문의 답을 context에서 적절한 요리를 찾지 못하면 추가 정보를 좀 더 수집한 뒤 답변해.
            답변을 context에서 찾을 수 없으면 답변을 생성하지 말고 모른다고 대답해.
    {context}"""),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{question}"),
        ]
    prompt_template = ChatPromptTemplate(messages)

    # 메모리
    def load_history(input):
        return memory.load_memory_variables({})["history"]

    # retriever 로드 => 추후 함수 선택 코드 넣어야 함
    rbm25_retr, rfais_retr = ref() # 냉장고를 부탁해
    fbm25_retr, ffais_retr = func() # 편스토랑
    mbm25_retr, mfais_retr = man() # 만개의 레시피

    retriever = EnsembleRetriever(retrievers=[rbm25_retr, rfais_retr, fbm25_retr, ffais_retr, mbm25_retr, mfais_retr],) # weights=[0.25, 0.25, 0.25, 0.25],) # weight: retriever 별 가중치 조절 가능

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