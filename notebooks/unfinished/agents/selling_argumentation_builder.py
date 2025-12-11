import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def selling_argumentation_builder(
    target_company: str,
    pain_json: dict,
    value_json: dict,
    match_json: dict
) -> dict:
    """
    Builds persuasive selling arguments linking pain points to value propositions,
    supported by reasoning from the matching result.
    """

    utils.print_html("Selling Argumentation Builder", "🧩")

    # ---- Extract safe data ----
    pain_points = pain_json.get("pain_points", {}).get("pain_points", [])
    value_prop = value_json.get("value_proposition", {})
    value_args = value_prop.get("value_arguments", [])
    match_summary = match_json.get("matching_result", {}).get("summary", "")

    # ---- Build prompt ----
    prompt = f"""
You are a B2B sales strategist tasked with building persuasive, evidence-based selling arguments.

Target Company: {target_company}
Date: {datetime.now().strftime("%Y-%m-%d")}

Pain Points:
{json.dumps(pain_points, indent=2)}

Value Proposition:
{json.dumps(value_args, indent=2)}

Matching Summary:
{match_summary}

Your task:
1. For each major pain point, create a clear selling argument showing how the value proposition solves it.
2. Include (if possible) one supporting proof point per argument (case study, technical rationale, measurable outcome).
3. Provide a concise 'sales_narrative' paragraph summarizing the commercial storyline.
4. Return **valid JSON** with the keys:
   {{
     "selling_arguments": [
         {{ "pain_point": str, "argument": str, "proof": str }}
     ],
     "sales_narrative": str
   }}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content.strip()

    # Clean JSON fences
    clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
    clean = re.sub(r"```$", "", clean).strip()

    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = {
            "selling_arguments": [],
            "sales_narrative": content
        }

    # Always return normalized structure
    return {
        "company": target_company,
        "selling_arguments": parsed.get("selling_arguments", []),
        "sales_narrative": parsed.get("sales_narrative", ""),
    }
