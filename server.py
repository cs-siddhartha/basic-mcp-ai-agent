from fastmcp import FastMCP
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

mcp = FastMCP("My MCP Server")


@mcp.tool
def health_check() -> str:
  """Basic server health probe for agent smoke tests."""
  return "ok"


@mcp.tool
def internet_search(query: str, top_k: int = 5) -> str:
  """
  Search the public DuckDuckGo instant answer endpoint.
  Returns a compact JSON string with title/url/snippet rows.
  """
  q = quote_plus(query)
  url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
  request = Request(url, headers={"User-Agent": "basic-mcp-ai-agent/0.1"})

  try:
    with urlopen(request, timeout=15) as response:
      body = response.read().decode("utf-8")
      data = json.loads(body)
  except HTTPError as e:
    return json.dumps({"ok": False, "error": f"http_error:{e.code}"})
  except URLError as e:
    return json.dumps({"ok": False, "error": f"url_error:{e.reason}"})
  except Exception as e:
    return json.dumps({"ok": False, "error": str(e)})

  results = []
  for item in data.get("RelatedTopics", []):
    if "Text" in item and "FirstURL" in item:
      results.append(
        {
          "title": item["Text"].split(" - ")[0][:120],
          "url": item["FirstURL"],
          "snippet": item["Text"][:220],
        }
      )
    elif "Topics" in item:
      for nested in item["Topics"]:
        if "Text" in nested and "FirstURL" in nested:
          results.append(
            {
              "title": nested["Text"].split(" - ")[0][:120],
              "url": nested["FirstURL"],
              "snippet": nested["Text"][:220],
            }
          )
    if len(results) >= max(1, top_k):
      break

  return json.dumps(
    {"ok": True, "query": query, "count": min(len(results), max(1, top_k)), "results": results[: max(1, top_k)]}
  )


if __name__ == "__main__":
  mcp.run()