from textwrap import dedent
from operator import itemgetter
from utils.retrievers import load_retriever
from utils.memories import get_session_history, mkhisid, save_history

from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableFieldSpec, RunnableLambda, chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv

load_dotenv()

# llm 모델, retriever 정의
model = ChatOpenAI(model="gpt-4o-mini")
retriever = load_retriever()
contexts = [] # 이전 대화 retriever 결과 contexts 저장

def format_docs(docs):
    """retriever 결과 형태 변환 함수"""
    for doc in docs:
        content = {}
        txt = doc.page_content.split(" ||| ")
        keys = ["name", "ingrdients", "recipe", "category", "info", "intro"][:len(txt)]
        content.update(dict(zip(keys, txt)))
        content.update(doc.metadata)
        contexts.append(content)
    return contexts


# 1. llm에 기본 질문/이전 질문의 파생 질문인지 확인하기
@chain
def intent(query):
    intent_messages = [("system", dedent(
        """
        너는 사용자의 질문(question)을 분석해서 의도를 파악하고 [`기본 질문`, `레시피_영상 요청`] 둘 중에 하나로 return하는 ai야.
        `레시피_영상 요청`은 사용자가 이전에 네가 답변한 답변에서 추가 질문을 하는건데 메뉴 이름만 언급할 수도 있고, 번호만 말할 수도 있어.
        메뉴 이름을 언급한 경우에는 history에 그 요리 이름이 있으면 그 메뉴에 대한 `레시피_영상 요청`이고, 없으면 기본 질문으로 판단해.
        단, "'요리 이름' 레시피 알려줘"처럼 요리 이름과 레시피 알려달라는 말을 같이하면 기본 질문이야.
        이외 답변은 기본 질문으로 분류해. 답변은 [`기본 질문`, `레시피_영상 요청`] 중에 하나로만 답해. '-입니다'도 붙이지 말고 네가 분류한 결과가 무엇인지만 대답해.
        """)),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}")]
    intent_prompt = ChatPromptTemplate(messages=intent_messages)

    chk_intent_chain = intent_prompt | model | StrOutputParser()
    return chk_intent_chain

# 2-1. 기본 질문일 경우
@chain
def normal(query):
    # i. retriever에 쿼리 전달 및 context 저장(format_docs에서 실행)
    messages = [(("system", dedent(
        """
        너는 사용자의 질문(question)에 맞는 요리를 추천해주는 ai야.
        다음 조건에 맞춰서 답변해.
        
        # 조건
        1. context에서 답변을 찾을 수 없으면 답변을 만들지 말고 `모르겠습니다.`라고 대답해.
        
        2. 사용자의 question 대답을 할 때 요리를 3가지 알려준다.
        2-1. 요리를 알려줄 때는 요리 이름, 요리 한 줄 소개, 요리 재료, 사진을 알려준다.
        2-2. 사진은 요리정보의 `img` key에 있다. 반드시 답변하는 요리와 같은 id의 `img` key의 value를 알려준다. 다른 요리의 것은 절대 알려주면 안된다. 답변하는 요리에 `img`가 없거나 값이 없으면(빈문자열이면) `사진이 없습니다`라고 답한다.
        
        3. 사용자가 요리 이름을 언급하며 레시피를 알려달라고 요청하면, context의 내용을 말로 풀어서 요리 이름, 재료, 레시피, 사진, 영상을 제공한다.
        3-1. context에 내용이 빠져있다면 그 내용만 대답하지 말고 있는 정보는 대답한다.
        # context
        {context}
        """))), 
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}")]
    prompt_template = ChatPromptTemplate(messages)

    nchain = {"context": itemgetter("question") | retriever | format_docs, "question": itemgetter("question"), "history": itemgetter("history")} | prompt_template | model | StrOutputParser()
    # ii. llm에 retrieving 결과 + history 전달
    return nchain

# 2-2. 이전 질문의 파생 질문일 경우
@chain
def derived(query):
    # i. history + 이전 질문 context llm에 전달
    messages = [(("system", dedent(
        """
        너는 사용자의 질문(question)에 맞는 요리를 추천해주는 ai야.
        다음 조건에 맞춰서 답변해.
        
        # 조건
        1. context에서 답변을 찾을 수 없으면 답변을 만들지 말고 `모르겠습니다.`라고 대답해.

        2. 사용자가 요리를 고르면 해당 요리의 레시피와 영상을 알려준다.
        2-1. 영상은 요리정보의 `video` key에 있다. 반드시 답변하는 요리와 같은 id의 `video` key의 value를 알려준다. 다른 요리의 것은 절대 알려주면 안된다. 답변하는 요리에 `video`가 없거나 값이 없으면(빈문자열이면) 알려주지 않는다.    
        
        # context
        {context}
        """))),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}")]
    prompt_template = ChatPromptTemplate(messages)
    dchain = {"question": itemgetter("question"), "history": itemgetter("history"), "context": itemgetter("contexts")} | prompt_template | model | StrOutputParser()
    return dchain

def mkch():
    base_chain = RunnableLambda(lambda x: select_chain(x["question"]).invoke({**x, "contexts": contexts if select_chain(x["question"]) == derived else []}))
    mkchain = RunnableWithMessageHistory(
        base_chain, get_session_history=get_session_history, input_messages_key="question", history_messages_key="history",
        history_factory_config=[
            ConfigurableFieldSpec(id="user_id", annotation=str, name="User ID", description="사용자 id(Unique)", default="", is_shared=True),
            ConfigurableFieldSpec(id="history_id", annotation=str, name="History ID", description="대화 기록 id(Unique)", default="", is_shared=True),
        ]
    )
    return mkchain

def select_chain(query):
    """intent 분석 결과에 따라 실행할 체인을 선택"""
    chk = intent.invoke({"question": query})  # intent 실행
    if chk == "레시피_영상 요청":
        return derived
    return normal

# 3. llm 응답
def chat(user_id):
    history_id = mkhisid(user_id)
    cchain = mkch()
    while True:
        query = input("메시지 입력 > ")
        if query == "종료":
            break
        res = cchain.invoke({"question": query}, config={"configurable": {"user_id": user_id, "history_id": history_id}})
        print(res)
        save_history(user_id, history_id, {query:res}) # 장고 맞춰서 수정 필요

chat("suy")