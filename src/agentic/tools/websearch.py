from ddgs import DDGS
from bs4 import BeautifulSoup
from RAW.modals import Tool
from RAW.modals.tools import ToolParam
import httpx
async def fetch_page(url: str) -> str:
    try:
        soup = BeautifulSoup(httpx.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True).text, "html.parser")
        [t.decompose() for t in soup(["script", "style", "nav", "footer"])]
        return " ".join(soup.get_text(separator=" ", strip=True).split())[:3000]
    except: return ""
async def duckduckgo_search(query: str) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5)) or list(ddgs.news(query, max_results=5))
    if not results: return "No results found."
    return "\n\n".join([f"Title: {r.get('title','')}\nSummary: {r.get('body', r.get('excerpt', ''))}\nContent: {fetch_page(r.get('href', r.get('url', '')))}" for r in results])
duckduckgo_search_tool = Tool(
    name="duckduckgo_search",
    description="Search the web for real-time prices, news, and live data. ALWAYS call this first. NEVER use training data.",
    parameters=[ToolParam(name="query", type="string", description="Search query", required=True)],
    function=duckduckgo_search
)