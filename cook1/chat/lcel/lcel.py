from textwrap import dedent
from operator import itemgetter
from pydantic import BaseModel, Field
from typing_extensions import Literal

from chat.utils.retrievers import load_retriever
from chat.utils.memories import get_session_history
from chat.utils.agents import tavily_search

from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableFieldSpec, RunnableLambda, chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv

load_dotenv()

# llm 모델 정의
model = ChatOpenAI(model="gpt-4o-mini")
# 이전 대화 retriever 결과 contents 저장 변수
contents = []

def format_docs(docs):
    """retriever 결과 형태 변환 함수"""
    for doc in docs:
        content = {}
        txt = doc.page_content.split(" ||| ")
        keys = ["name", "ingredients", "recipe", "category", "info", "intro"][:len(txt)]
        content.update(dict(zip(keys, txt)))
        content.update(doc.metadata)
        # funs 데이터이고 video 값이 비어있다면 Tavily 검색 수행
        if content.get("_collection_name") == "funs" and not content.get("video"):
            query = f"{content.get('name')}"
            video_url = tavily_search.invoke(query)
            content["video"] = video_url if video_url != "검색 결과 없음" else ""
        contents.append(content)
    return contents


# 1. llm에 기본 질문/이전 질문의 파생 질문인지 확인하기
@chain
def intent(query):
    class Flag(BaseModel):
        flag: Literal["new", "continue"] = Field(None, description="사용자 query가 이전 query와 이어지는 것인지 새로운 query인지에 대한 구분값. 이전에 한 query와 이어지는 경우 'continue'를 새로운 query일 경우 'new'를 저장한다.")
        
    # Augment the LLM with schema for structured output
    intent_result = model.with_structured_output(Flag)

    messages = [
        ("system", dedent("""너는 사용자의 질문(query)을 분석해서 의도를 파악하고 [`new`, `continue`] 둘 중에 하나로 return하는 ai야.
        `continue`로 분류해야하는 경우는 다음과 같아. 사용자가 이전에 네가 이전에 대답한 것(history)에 관련해서 추가 정보 요청 등을 요구할 때, 메뉴 이름만 언급하거나 번호만 언급하는 경우,
        메뉴 이름을 언급한 했으며 history에 그 요리 이름이 있는 경우 등 이전 질문과 관련있을 때만 `continue`로 분류해. 이외의 경우는 전부 `new`로 분류해. 재료만 입력할 경우 무조건 `new`로 분류해""")),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{query}")
    ]

    intent_prompt = ChatPromptTemplate(messages)

    chk_intent_chain = intent_prompt | intent_result
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
        1. context에서 답변을 찾을 수 없으면 답변을 만들지 말고 `모르겠습니다.`라고 대답한다.
        
        2. 검색 결과를 알려줄 때 요리를 3가지 알려준다.
        2-1. 요리를 알려줄 때는 요리 이름, 요리 한 줄 소개, 요리 재료, 사진을 알려준다. 이외 정보는 언급하지 않는다.
        2-2. 사용자가 요리에 포함되어야하는 재료를 여러 개 입력했을 경우, 사용자가 언급한 재료가 많이 있는 순으로 먼저 정렬하고, 우선 순위가 같은 요리에 대해서는 부가적인 재료가 적은 순으로 정렬한 후 추천한다.
        2-3. 사용자가 포함하지 말아야할 재료나 도구 등을 언급하면 그것은 포함하지 않는 요리만 추천한다.
        2-4. 사진은 요리정보의 `img` key에 있다. 반드시 답변하는 요리와 같은 id의 `img` key의 value를 알려준다. 다른 요리의 것은 절대 알려주면 안된다. 답변하는 요리에 `img`가 없거나 값이 없으면(빈문자열이면) 사진은 사용자에게 제공하지 않는다.
        
        3. 사용자가 요리 이름을 언급하며 레시피를 알려달라고 요청하면, 검색 결과 내용을 말로 풀어서 한 가지 요리 정보만 전달한다.
        3-1. 요리 이름, 재료, 레시피, 사진, 영상을 제공한다.
        3-2. 이외 사항은 2-1, 2-2. 2-3, 2-4 조건에 맞게 대답한다.
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
        1. 사용자가 이전에 추천해준 요리 목록에서 요리를 고르면 `history`를 참고해 사용자가 요구하는 요리의 레시피와 영상을 `content`에서 찾아 알려준다.
        1-1. `_collection_name` key의 value가 `funs`, `ref 중 하나인 경우 요리 이름은 변형하지 않고 그대로 대답한다.
        1-2. 영상은 요리정보의 `video` key에 있다. 반드시 답변하는 요리와 같은 id의 `video` key의 value를 알려준다. 다른 요리의 것은 절대 알려주면 안된다. 답변하는 요리에 `video`가 없거나 값이 없으면(빈문자열이면) 제공하지 않는다.

        2. 이전 질문에서 대체할 수 있는 재료 등의 질문이 들어오면 질문에 맞는 대답을 알려준다.
        # content
        {content}
        # context
        {context}
        """))),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}")]
    prompt_template = ChatPromptTemplate(messages)
    dchain = {"question": itemgetter("question"), "history": itemgetter("history"), "content": itemgetter("content"), "context": itemgetter("question") | retriever | format_docs} | prompt_template | model | StrOutputParser()
    return dchain

def mkch(isref=True, isfun=True, isman=True):
    global retriever
    retriever = load_retriever(isref, isfun, isman)
    base_chain = RunnableLambda(lambda x: (lambda chain:chain.invoke({**x, "content": contents if chain == derived else []}))(select_chain(x)))
    mkchain = RunnableWithMessageHistory(
        base_chain, get_session_history=get_session_history, input_messages_key="question", history_messages_key="history",
        history_factory_config=[
            ConfigurableFieldSpec(id="user_id", annotation=str, name="User ID", description="사용자 id(Unique)", default="", is_shared=True),
            ConfigurableFieldSpec(id="history_id", annotation=str, name="History ID", description="대화 기록 id(Unique)", default="", is_shared=True),
        ]
    )
    return mkchain

def select_chain(x):
    """intent 분석 결과에 따라 실행할 체인을 선택"""
    history = x['history'][:-6]
    chk = intent.invoke({"query": x["question"], "history": history})
    if chk.flag == "continue":
        return derived
    return normal