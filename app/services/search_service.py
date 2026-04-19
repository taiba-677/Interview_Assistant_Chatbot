# from typing import List, Dict
# from tavily import TavilyClient

# from app.core.config import settings


# class SearchService:
#     def __init__(self):
#         self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

#     def get_web_links(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results,
#                 include_answer=False,
#                 include_raw_content=False
#             )

#             results = response.get("results", [])
#             links = []

#             for item in results:
#                 title = item.get("title")
#                 url = item.get("url")

#                 if title and url:
#                     links.append({
#                         "title": title,
#                         "url": url
#                     })

#             return links
#         except Exception as e:
#             # Fallback for search failures
#             print(f"Search Error: {str(e)}")
#             return []





# uf


from typing import List, Dict
from tavily import TavilyClient
from app.core.config import settings


class SearchService:
    def __init__(self):
        """Initialize TavilyClient with the provided API key."""
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    def get_web_links(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a search for the given query using Tavily, returning a list of relevant links.
        Returns an empty list in case of error.
        """
        try:
            # Append year to query to prioritize latest 2026 info
            search_query = f"{query} latest 2026"
            
            response = self.client.search(
                query=search_query,
                search_depth="basic",
                max_results=max_results,
                include_answer=False,
                include_raw_content=False
            )

            results = response.get("results", [])
            links = []

            for item in results:
                title = item.get("title")
                url = item.get("url")

                if title and url:
                    links.append({
                        "title": title,
                        "url": url
                    })

            return links
        
        except Exception as e:
            # Log the error but return an empty list so the main chat flow isn't interrupted
            print(f"Search Service Warning (links skipped): {str(e)}")
            return []
