import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def pain_point_detective(
    target_company: str,
    return_messages: bool = True,
    max_results: int = 5
) -> dict:
    """
    Uses a retrieval-augmented LLM to find and summarize the top pain points of a company.
    """

    utils.print_html("Pain Point Detective", "🕵️‍♂️")

    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    # 🔍 1. Retrieve live context
    query = (
        f"{target_company} pain points OR challenges OR customer complaints "
        f"site:reddit.com OR site:glassdoor.com OR site:medium.com OR site:trustpilot.com"
    )

    search = tavily.search(query=query, max_results=max_results)

    if not search or not search.get("results"):
        context = "No relevant online sources found."
    else:
        context = "\n\n".join(
            [f"- {r['title']}\n{r['content']}" for r in search["results"]]
        )

    # 🧠 2. Prompt with retrieved context
    prompt_ = f"""
You are a company detective tasked with identifying the main pain points of "{target_company}".

Use the following retrieved context from real web sources:

---
{context}
---

Your goal:
1. Summarize the top 2–3 **pain points**, focusing on customer, technical, or organizational challenges.
2. Return the result as a JSON object with keys "pain_points" (list) and "summary" (string).
3. Today's date is {datetime.now().strftime("%Y-%m-%d")}.
"""

    messages = [{"role": "user", "content": prompt_}]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )

        content = response.choices[0].message.content.strip()

        # Clean and parse JSON
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        clean = re.sub(r"```$", "", clean).strip()

        try:
            parsed = json.loads(clean)
            pain_points_payload = parsed
        except json.JSONDecodeError:
            pain_points_payload = {"raw_text": content}

        result = {
            "company": target_company,
            "pain_points": pain_points_payload,
            "retrieval_sources": [r["url"] for r in search.get("results", [])],
        }

        if return_messages:
            result["messages"] = messages

        return result

    except Exception as e:
        return {
            "company": target_company,
            "pain_points": None,
            "error": str(e),
            "retrieval_sources": [r["url"] for r in search.get("results", [])],
        }
