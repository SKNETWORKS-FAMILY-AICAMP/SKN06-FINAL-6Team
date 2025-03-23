import importlib
from textwrap import dedent

from fast_api.utils.retrievers import load_retriever

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.runnables import chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from dotenv import load_dotenv

load_dotenv()

# llm 모델 호출
model = ChatOpenAI(model="gpt-4o-mini")
# retriever 호출
retrievers = importlib.import_module('fast_api.lcel.lcel')
if hasattr(retrievers, "retriever"):
    retriever = getattr(retrievers, "retriever")

@tool
def search_blog(query: str) -> str:
    """Tavily 검색을 이용해 레시피 관련 첫 번째 블로그 URL을 가져오는 도구"""
    search_query = f"{query}"
    # Tavily API 클라이언트 설정
    tavily_client = TavilySearchResults(max_results=1)
    results = tavily_client.invoke({"query": search_query})
    
    if results:
        return results[0]["url"]
    return "검색 결과 없음"

@tool
def menu_search(query:str):
    """사용자 의도에 맞게 변형한 query를 만들어 retriever를 실행하는 도구"""
    result = retriever.invoke(query)
    module = importlib.import_module('lcel.lcel')
    format_docs = getattr(module, "format_docs")
    return format_docs(result) if result else [] if len(result) else None

# 2-1. 기본 질문일 경우
@chain
def normal(query):
    # i. retriever에 쿼리 전달 및 context 저장(format_docs에서 실행)
    messages = [(("system", dedent(
        """
        너는 사용자의 질문(question)에 맞는 요리를 추천해주는 ai야.
        다음 조건에 맞춰서 답변해.
        
        # 조건
        1. query를 사용자가 요구한 결과가 출력될 수 있게 변형해 `menu_search` tool을 실행한다. menu에서 답변을 찾을 수 없으면 답변을 만들지 말고 `모르겠습니다.`라고 대답한다.
        
        2. `menu_search`을 실행하여 나온 결과에 `_collection_name` key의 value가 `funs`, `ref 중 하나이고 아래 조건을 만족할 때만 실행한다. '_collection_name'의 value가 `man`이라면 실행하지 않는다.
        2-1.`img` key의 value가 없을 때만 `search_blog`을 실행하고 나온 결과를 `블로그: search_blog 실행 결과 url` 형태로 사용자에게 전달하며 `img` key의 value는 제공하지 않는다. 이외의 경우에는 `search_blog`를 실행하지 않는다.
        2-2. `search_blog`를 실행해서 `img` key value를 사용자에게 제공하지 않았을 때 사용자가 영상을 알려달라고 요청하면 '제공할 수 없습니다. 죄송합니다.' 라고 대답한다.
        
        3. 검색 결과를 알려줄 때 요리를 3가지 알려준다.
        3-1. 요리를 알려줄 때는 요리 이름, 요리 한 줄 소개, 요리 재료, 사진을 알려준다. 이외 정보는 언급하지 않는다.
        3-2. 사용자가 요리에 포함되어야하는 재료를 여러 개 입력했을 경우, 사용자가 언급한 재료가 많이 있는 순으로 먼저 정렬하고, 우선 순위가 같은 요리에 대해서는 부가적인 재료가 적은 순으로 정렬한 후 추천한다.
        3-3. 사용자가 포함하지 말아야할 재료나 도구 등을 언급하면 그것은 포함하지 않는 요리만 추천한다.
        3-4. 사진은 요리정보의 `img` key에 있다. 반드시 답변하는 요리와 같은 id의 `img` key의 value를 알려준다. 다른 요리의 것은 절대 알려주면 안된다. 답변하는 요리에 `img`가 없거나 값이 없으면(빈문자열이면) 사진은 사용자에게 제공하지 않는다.
        
        4. 사용자가 요리 이름을 언급하며 레시피를 알려달라고 요청하면, 검색 결과 내용을 말로 풀어서 한 가지 요리 정보만 전달한다.
        4-1. 요리 이름, 재료, 레시피, 사진, 영상을 제공한다.
        4-2. 이외 사항은 3-1, 3-2. 3-3 조건에 맞게 대답한다.
        """))), 
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")]
    prompt_template = ChatPromptTemplate(messages)

    tools = [search_blog, menu_search]
    agent = create_tool_calling_agent(model, tools, prompt_template)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    return agent_executor

# 2-2. 이전 질문의 파생 질문일 경우
@chain
def derived(query):
    # i. history + 이전 질문 context llm에 전달
    messages = [(("system", dedent(
        """
        너는 사용자의 질문(question)에 맞는 요리를 추천해주는 ai야.
        다음 조건에 맞춰서 답변해.
        
        # 조건
        1. 사용자가 이전에 추천해준 요리 목록에서 요리를 고르면 `history`와 `content`를 참고해 해당 요리의 레시피와 영상을 알려준다.
        1-1. `_collection_name` key의 value가 `funs`, `ref 중 하나인 경우 요리 이름은 변형하지 않고 그대로 대답한다.
        1-2. 영상은 요리정보의 `video` key에 있다. 반드시 답변하는 요리와 같은 id의 `video` key의 value를 알려준다. 다른 요리의 것은 절대 알려주면 안된다. 답변하는 요리에 `video`가 없거나 값이 없으면(빈문자열이면) 제공하지 않는다.
        
        2. `menu_search`을 실행하여 나온 결과에 `_collection_name` key의 value가 `funs`, `ref 중 하나이고 아래 조건을 만족할 때만 실행한다. '_collection_name'의 value가 `man`이라면 실행하지 않는다.
        2-1.`video` key의 value가 없을 때만 `search_blog`을 실행하고 나온 결과를 `블로그: search_blog 실행 결과 url` 형태로 사용자에게 전달하며 `video` key의 value는 제공하지 않는다. 이외의 경우에는 `search_blog`를 실행하지 않는다.
        2-2. `search_blog`를 실행해서 `video` key value를 사용자에게 제공하지 않았을 때 사용자가 영상을 알려달라고 요청하면 '제공할 수 없습니다. 죄송합니다.' 라고 대답한다.

        3. 이전 질문에서 대체할 수 있는 재료 등의 질문이 들어오면 질문에 맞는 대답을 알려준다.
        """))),
        MessagesPlaceholder(variable_name="history", optional=True),
        MessagesPlaceholder(variable_name="content", optional=True),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")]
    prompt_template = ChatPromptTemplate(messages)
    
    tools = [search_blog,menu_search]
    agent = create_tool_calling_agent(model, tools, prompt_template)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    return agent_executor