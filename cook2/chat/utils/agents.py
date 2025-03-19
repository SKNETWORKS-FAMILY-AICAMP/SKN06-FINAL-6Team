from langchain.tools import Tool
from langchain_community.tools import TavilySearchResults

from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilySearchResults(max_results=1)

def search_tavily_recipe(query):
    """Tavily 웹 검색을 이용해 레시피 관련 첫 번째 블로그 URL을 가져오는 함수"""
    search_query = f"{query}"
    results = tavily_client.run(search_query)
    
    if results:
        return results[0]["url"]  # 첫 번째 결과 URL 반환
    return "검색 결과 없음"

tavily_search = Tool(name="Tavily Recipe Search", func=search_tavily_recipe, description="Tavily 검색을 이용해 레시피 관련 첫 번째 블로그 URL을 가져오는 도구")