from langchain.tools import Tool
from langchain_community.tools import TavilySearchResults  # ✅ Tavily 검색 도구 추가

from dotenv import load_dotenv

load_dotenv()

# ✅ Tavily API 클라이언트 설정
tavily_client = TavilySearchResults(max_results=1)

def search_tavily_recipe(query):
    """Tavily 웹 검색을 이용해 레시피 관련 첫 번째 블로그 URL을 가져오는 함수"""
    search_query = f"{query}"
    results = tavily_client.run(search_query)
    
    if results:
        return results[0]["url"]  # 첫 번째 결과의 URL 반환
    return "검색 결과 없음"

# ✅ LangChain Tool 정의
tavily_recipe_search_tool = Tool(
    name="Tavily Recipe Search",
    func=search_tavily_recipe,
    description="Tavily 검색을 이용해 레시피 관련 첫 번째 블로그 URL을 가져오는 도구"
)
