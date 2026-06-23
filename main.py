from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from ddgs import DDGS
import requests
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")
LLM_URL = "http://172.21.10.147:1234/v1/chat/completions" # replace here
MODEL = "google/gemma-4-12b-quat"


# -------------------------
# TOOL
# -------------------------
def web_search(query):

    results = []

    with DDGS() as ddgs:

        for r in ddgs.text(
            query,
            max_results=5
        ):
            results.append(
                f"""
Title: {r["title"]}
Body: {r["body"]}
URL: {r["href"]}
"""
            )

    return "\n\n".join(results)


# -------------------------
# WEB PAGE
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


# -------------------------
# CHAT ENDPOINT
# -------------------------
@app.post("/chat")
async def chat(data: dict):
    user_message = data["message"]
    messages = [
        {
            "role": "system",
            "content": """
            You have access to tools.

            When information may be missing,
            use web_search.

            Never invent search results.
            """
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the internet",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    MAX_STEPS = 10
    

    for _ in range(MAX_STEPS):
        response = requests.post(
            LLM_URL,
            json={
                "model": MODEL,
                "messages": messages,
                "tools": tools
            }
        ).json()

        assistant = response["choices"][0]["message"]
        print("=" * 50)
        print("TOOL CALLS:")
        print(assistant.get("tool_calls"))
        print("=" * 50)
        messages.append(assistant)

        if not assistant.get("tool_calls"):
            return {
                "response": assistant["content"]
            }

        for tool_call in assistant["tool_calls"]:
            args = json.loads(tool_call["function"]["arguments"])
            result = web_search(args["query"])

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": "web_search",
                "content": result
            })

    return {
        "response": "Agent exceeded max steps."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)