import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def value_prop_engineer(
    origin_company: str,
    return_messages: bool = True,
    max_results: int = 5
) -> dict:
    """
    Uses a retrieval-augmented LLM to analyze and summarize the value proposition
    of a given origin_company. Returns a dict with keys:
        - origin_company
        - value_proposition (JSON or raw text)
        - retrieval_sources
    """

    utils.print_html("Value Proposition Engineer", "🧱")

    # Initialize clients
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    # 🔍 1. Retrieve live context
    query = (
        f"{origin_company} value proposition OR product offering OR competitive advantage "
        f"site:{origin_company} OR site:linkedin.com OR site:medium.com OR site:techcrunch.com"
    )

    search = tavily.search(query=query, max_results=max_results)

    if not search or not search.get("results"):
        context = "No relevant origin_company information found online."
    else:
        context = "\n\n".join(
            [f"- {r['title']}\n{r['content']}" for r in search["results"]]
        )

    # 🧠 2. Build the LLM prompt
    prompt_ = f"""
You are a value proposition analyst for the company "{origin_company}".

Use the following retrieved context from real online sources:

---
{context}
---

Your goal:
1. Summarize the company's **core value proposition**, focusing on product, data, architecture, software, hardware, and commercial differentiators.
2. Return the result as a JSON object with keys:
   {{
     "value_arguments": [str],
     "summary": str
   }}
3. Today's date is {datetime.now().strftime("%Y-%m-%d")}.
"""

    messages = [{"role": "user", "content": prompt_}]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )

        content = response.choices[0].message.content.strip()

        # Clean & parse JSON
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        clean = re.sub(r"```$", "", clean).strip()

        try:
            parsed = json.loads(clean)
            value_prop_payload = parsed
        except json.JSONDecodeError:
            value_prop_payload = {"raw_text": content}

        result = {
            "origin_company": origin_company,
            "value_proposition": value_prop_payload,
            "retrieval_sources": [r["url"] for r in search.get("results", [])],
        }

        if return_messages:
            result["messages"] = messages

        return result

    except Exception as e:
        return {
            "origin_company": origin_company,
            "value_proposition": None,
            "error": str(e),
            "retrieval_sources": [r["url"] for r in search.get("results", [])],
        }
