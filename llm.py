import sqlite3
import pandas as pd
from typing import List
from pydantic import BaseModel, Field

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from operator import itemgetter

from dotenv import load_dotenv

load_dotenv()

class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """인메모리 채팅 히스토리 클래스"""
    messages: List[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

## 임베딩 모델
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

## 모델
model = ChatOpenAI(model="gpt-4o-mini")

# 메모리 정의
store = {}
def get_session_history(user_id: str, history_id: str) -> BaseChatMessageHistory:
    if (user_id, history_id) not in store:
        store[(user_id, history_id)] = InMemoryHistory()
    print(f"현재 저장된 히스토리: {store}") # 디버깅용
    return store[(user_id, history_id)]

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

            요리 소개할 때 요리 이름을 언급한 뒤, 한 줄 정도 간단한 요리 소개를 하고 재료, 사진을 알려줘.
            요리 이름은 이름에서 만든 사람을 알 수 있다면 요리사도 같이 알려주고, 사진은 context에서 해당하는 요리의 사진을 알려주면 돼. 없으면 알려주지마.
            요리는 기본적으로 3가지 추천 해주고, 사용자가 특정 요리 하나를 질문한 경우에만 해당하는 요리 1가지만 알려줘.
            요리 추천 기준은 사용자가 재료를 입력했을 경우, 해당 재료는 많은 순으로 먼저 정렬하고, 우선 순위가 같은 요리에 대해서는 부가적인 재료가 적은 순으로 재정렬해줘.
            레시피는 요약하지말고, 있는 그대로 순서대로 알려줘.
            레시피 알려줄 때 영상도 같이 알려줘야해. 만약 영상이 없으면 알려주지마. context에 네가 알려줄 요리의 영상이이 있을 때만 같이 첨부해서 알려줘.
            사용자의 질문의 답을 context에서 적절한 요리를 찾지 못하면 필요에 따라 추가 정보를 좀 더 수집한 뒤 답변하고, 그럼에도 답변할 내용을 context에서 찾을 수 없으면 답변을 생성하지 말고 모른다고 대답해.
    {context}"""),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{question}"),
        ]
    prompt_template = ChatPromptTemplate(messages)

    # retriever 로드 => 추후 함수 선택 코드 넣어야 함
    rbm25_retr, rfais_retr = ref() # 냉장고를 부탁해
    fbm25_retr, ffais_retr = func() # 편스토랑
    mbm25_retr, mfais_retr = man() # 만개의 레시피

    retriever = EnsembleRetriever(retrievers=[rbm25_retr, rfais_retr, fbm25_retr, ffais_retr, mbm25_retr, mfais_retr],) # weights=[0.25, 0.25, 0.25, 0.25],) # weight: retriever 별 가중치 조절 가능

    # chatting Chain 구성 retriever(관련 문서 조회) -> prompt_template(prompt 생성) model(정답) -> output parser
    chatting = {"context": itemgetter("question") | retriever, "question": itemgetter("question"), "history": itemgetter("history")} | prompt_template | model | StrOutputParser()

    # 메모리 결합 체인
    chain = RunnableWithMessageHistory(
        chatting, get_session_history=get_session_history, input_messages_key="question", history_messages_key="history",
        history_factory_config=[
            ConfigurableFieldSpec(id="user_id", annotation=str, name="User ID", description="사용자 id(Unique)", default="", is_shared=True),
            ConfigurableFieldSpec(id="history_id", annotation=str, name="History ID", description="대화 기록 id(Unique)", default="", is_shared=True),
        ]
    )
    return chain

def chat(user_id, history_id):
    chain = mkch()
    while True:
        query = input("메시지 입력 > ")
        if query == "종료":
            break
        res = chain.invoke({"question": query}, config={"configurable": {"user_id": user_id, "history_id": history_id}})
        print(res)

chat()