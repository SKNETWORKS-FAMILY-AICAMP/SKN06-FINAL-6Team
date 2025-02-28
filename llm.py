import random
import string
import sqlite3
import pandas as pd
from typing import List
from textwrap import dedent
from pydantic import BaseModel, Field

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
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
    """인메모리 히스토리 클래스"""
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
    if case == "funs":
        conn = sqlite3.connect("funs.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    elif case == "ref":
        conn = sqlite3.connect("fridges.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    else:
        conn = sqlite3.connect("man.db")
        df = pd.read_sql("SELECT * FROM processed_data", conn)

        df['page_content'] = df['name'] + " ||| " + df['ingredients'] + " ||| " + df['recipe'] + " ||| " + df['category'] + " ||| " + df['info'] + " ||| " + df['intro']
        df.drop(columns=['name', 'ingredients', 'recipe', "info", "intro"], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(model_name='gpt-4o-mini', chunk_size=1000, chunk_overlap=0)
        docs = loader.load_and_split(splitter)
        return docs

def load_retriever(case, faiss_path):
    """ retriever 로드 함수"""
    docs = load(case)

    # vectordb 로드
    fais = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)

    # BM25 retriever, FAISS retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    
    return bm25_retr, fais_retr

def mkch():
    # Prompt Template 생성
    messages = [
            ("system", dedent("""
            # instruction
            너는 사용자의 질문(question)에 맞는 요리를 알려주는 ai야.

            사용자에게 요리를 알려줄 때 요리는 context 항목에 있는 요리 중에서 알려줘야해.
            다음 조건을 참고해서 요리를 알려주면 돼.
            1. 사용자에게 요리를 추천할 때 요리 3가지를 추천한다. 그러나 사용자가 특정 요리의 레시피를 물어본 경우 해당하는 요리에 대한 정보를 제공한다. 
            2. 요리를 소개할 때 요리 이름을 먼저 언급한 뒤 간단한 요리 소개(한줄 분량), 재료, 사진 순으로 소개한다.
            2-1. 요리 이름에서 요리사 이름을 알 수 있다면 요리사 이름도 요리 이름과 같이 알려준다.
            2-2. 사진은 context에서 `img`에 있는 해당 요리의 사진 링크를 알려준다. 만약 `img`에 사진 링크가 없다면 "제공할 수 있는 사진이 없습니다."라고 답한다.
            2-3. 사진 링크를 임의로 생성하거나 다른 요리의 사진을 절대 알려주지 않는다.
            
            3. 요리 추천 시 정렬 기준은 다음과 같다.
            3-1. 사용자가 재료를 입력했을 경우, 해당 재료는 많은 순으로 먼저 정렬하고, 우선 순위가 같은 요리에 대해서는 부가적인 재료가 적은 순으로 정렬한다.
            
            4. 사용자가 요리를 고르면 레시피와 영상을 알려준다. 이때 레시피는 요약하지말고, 있는 그대로 순서대로 알려줘야한다.
            4-1. 영상은 context의 `video`에 저장된 링크 주소를 알려준다. `video`에 영상 링크가 없으면 "제공할 수 있는 영상이 없습니다." 이라고 답해야한다.
            4-2. 영상 링크 임의로 생성하거나 다른 요리의 영상 링크를 절대 알려주지 않는다.
            
            `사용자의 질문의 답을 context에서 적절한 요리를 찾지 못하면 필요에 따라 추가 정보를 사용자로부터 더 수집한 뒤 답변하고, 그럼에도 답변할 내용을 context에서 찾을 수 없으면 답변을 생성하지 말고 모른다고 대답해`
            
            # context
            
    {context}""")),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{question}"),
        ]
    prompt_template = ChatPromptTemplate(messages)

    # retriever 로드 => 추후 함수 선택 코드 넣어야 함
    rbm25_retr, rfais_retr = load_retriever("ref", "ref_faiss") # 냉장고를 부탁해
    fbm25_retr, ffais_retr = load_retriever("funs", "fun_faiss") # 편스토랑
    mbm25_retr, mfais_retr = load_retriever("man", "man_faiss") # 만개의 레시피

    retriever = EnsembleRetriever(retrievers=[rbm25_retr, rfais_retr, fbm25_retr, ffais_retr, mbm25_retr, mfais_retr],) # weights=[0.25, 0.25, 0.25, 0.25],) # weight: retriever 별 가중치 조절 가능

    # chatting Chain 구성 retriever(관련 문서 조회) -> prompt_template(prompt 생성) model(정답) -> output parser
    chatting = {"context": itemgetter("question") | retriever, "question": itemgetter("question"), "history": itemgetter("history")} | prompt_template | model | StrOutputParser()

    chain = RunnableWithMessageHistory(
        chatting, get_session_history=get_session_history, input_messages_key="question", history_messages_key="history",
        history_factory_config=[
            ConfigurableFieldSpec(id="user_id", annotation=str, name="User ID", description="사용자 id(Unique)", default="", is_shared=True),
            ConfigurableFieldSpec(id="history_id", annotation=str, name="History ID", description="대화 기록 id(Unique)", default="", is_shared=True),
        ]
    )
    return chain

def save_history(user_id, history_id, messages):
    """대화 내용 저장 함수 -> 추후 장고 db에 맞춰서 수정해야함"""
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS chat_history (user_id TEXT, history_id TEXT, messages TEXT)")
    cursor.execute("INSERT INTO chat_history VALUES (?, ?, ?)", (user_id, history_id, str(messages)))
    conn.commit()
    conn.close()

def mkhisid(user_id):
    """history_id 생성 함수"""
    while True:
        history_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        if user_id + history_id not in store.keys():
            # user_id와 history_id가 없는 경우 종료
            return history_id

def chat(user_id):
    history_id = mkhisid(user_id)
    chain = mkch()
    while True:
        query = input("메시지 입력 > ")
        if query == "종료":
            break
        res = chain.invoke({"question": query}, config={"configurable": {"user_id": user_id, "history_id": history_id}})
        print(res)

chat("suy")