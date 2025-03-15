import importlib
from textwrap import dedent
from pydantic import BaseModel, Field
from typing_extensions import Literal

from utils.memories import get_session_history

from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableFieldSpec, RunnableLambda, chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from dotenv import load_dotenv

load_dotenv()

# llm 모델 호출
model = ChatOpenAI(model="gpt-4o-mini")

@chain
def intent(query):
    """llm에 기본 질문/이전 질문의 파생 질문인지 확인하는 chain"""
    class Flag(BaseModel):
        flag: Literal["new", "continue"] = Field(None, description="사용자 query가 이전 query와 이어지는 것인지 새로운 query인지에 대한 구분값. 이전에 한 query와 이어지는 경우 'continue'를 새로운 query일 경우 'new'를 저장한다.")
        
    # Augment the LLM with schema for structured output
    intent_result = model.with_structured_output(Flag)

    messages = [
        ("system", dedent("""너는 사용자의 질문(query)을 분석해서 의도를 파악하고 [`new`, `continue`] 둘 중에 하나로 return하는 ai야.
        `continue`로 분류해야하는 경우는 다음과 같아. 사용자가 이전에 네가 이전에 대답한 것(history)에 관련해서 추가 정보 요청 등을 요구할 때, 메뉴 이름만 언급하거나 번호만 언급하는 경우,
        메뉴 이름을 언급한 했으며 history에 그 요리 이름이 있는 경우 등 이전 질문과 관련있을 때만 `continue`로 분류해. 이외의 경우는 전부 `new`로 분류해.""")),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{query}")
    ]

    intent_prompt = ChatPromptTemplate(messages)

    chk_intent_chain = intent_prompt | intent_result
    return chk_intent_chain

contents = []
def format_docs(docs):
    """retriever 결과 형태 변환 함수"""
    for doc in docs:
        content = {}
        txt = doc.page_content.split(" ||| ")
        keys = ["name", "ingrdients", "recipe", "category", "info", "intro"][:len(txt)]
        content.update(dict(zip(keys, txt)))
        content.update(doc.metadata)
        formating = {"role":"ai", "content":str(content)}
        contents.append(formating)
    return contents

def mkch():
    def chain_runner(x):
        selected_chain = select_chain(x)
        selection = importlib.import_module("utils.agents")
        return selected_chain.invoke(x) if selected_chain == getattr(selection, "normal") else selected_chain.invoke({**x, "content": contents})
    base_chain = RunnableLambda(chain_runner)
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
    selection = importlib.import_module("utils.agents")
    chk = intent.invoke({"query": x["question"], "history": history})
    return getattr(selection, "derived") if chk.flag == "continue" else getattr(selection, "normal")