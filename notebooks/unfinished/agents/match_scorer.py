import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def match_scorer(target_company: str, origin_company: str, 
                    pain_json: dict, value_json: dict,
                    return_messages: bool = True) -> dict:
    """
    Computes a matching score between the pain points of target_company and 
    the value proposition of origin_company, with RAG context and reasoning.
    """

    # Extract retrieved context from both companies (with safe defaults)
    pain_data = pain_json.get("pain_points") or {}
    value_data = value_json.get("value_proposition") or {}

    pain_context = "\n".join(pain_data.get("pain_points", [])) if isinstance(pain_data, dict) else str(pain_data)
    pain_sources = pain_json.get("retrieval_sources", [])

    value_context = "\n".join(value_data.get("value_arguments", [])) if isinstance(value_data, dict) else str(value_data)
    value_sources = value_json.get("retrieval_sources", [])

    if not pain_context:
        pain_context = f"(No pain points available for {target_company})"
    if not value_context:
        value_context = f"(No value proposition data available for {origin_company})"
    
    # Build a prompt that uses both textual and provenance evidence
    prompt_ = f"""
You are a business solution matchmaker.
Compare the **pain points** of {target_company} with the **value proposition** of {origin_company}.

Today's date: {datetime.now().strftime("%Y-%m-%d")}

Context (pain points from {target_company}):
{pain_context}

Sources (pain points):
{json.dumps(pain_sources, indent=2)}

Context (value proposition from {origin_company}):
{value_context}

Sources (value proposition):
{json.dumps(value_sources, indent=2)}

Your tasks:
1. Assess how well the value proposition of {origin_company} addresses the main pain points of {target_company}.
2. Provide:
   - "score": an integer 0–100 (0 = poor match, 100 = perfect fit)
   - "arguments_for": list of 2–3 reasons supporting the match
   - "arguments_against": list of 2–3 caveats or limitations
   - "summary": a short paragraph summarizing the fit
3. Include relevant URLs in your reasoning when possible.
4. Return a **valid JSON** object with these keys.
"""

    messages = [{"role": "user", "content": prompt_}]

    try:
        # Call the model
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
        )

        content = response.choices[0].message.content.strip()

        # Clean and parse JSON fences
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        clean = re.sub(r"```$", "", clean).strip()

        try:
            parsed = json.loads(clean)
            match_payload = parsed
        except json.JSONDecodeError:
            match_payload = {"raw_text": content}

        result = {
            "company_pair": f"{target_company} -> {origin_company}",
            "matching_result": match_payload,
            "pain_sources": pain_sources,
            "value_sources": value_sources,
        }

        if return_messages:
            result["messages"] = messages

        return result

    except Exception as e:
        return {
            "company_pair": f"{target_company} -> {origin_company}",
            "matching_result": None,
            "error": str(e),
            "pain_sources": pain_sources,
            "value_sources": value_sources,
        }
