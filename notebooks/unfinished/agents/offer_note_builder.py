import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def offer_note_builder(
    target_company: str,
    pain_json: dict,
    value_json: dict,
    match_json: dict,
    sell_json: dict,
    email_json: dict
) -> dict:
    """
    Creates a concise one-page Offer Note summarizing the opportunity context,
    proposed value, solution outline, expected outcomes, and next steps.
    """

    # ---- Extract safe data ----
    pain_points = pain_json.get("pain_points", {}).get("pain_points", [])
    value_prop = value_json.get("value_proposition", {})
    value_arguments = value_prop.get("value_arguments", [])
    match_summary = match_json.get("matching_result", {}).get("summary", "")
    selling_arguments = sell_json.get("selling_arguments", [])
    outreach_body = email_json.get("outreach_email", {}).get("email", {}).get("body", "")

    prompt = f"""
You are a solution consultant drafting a one-page Offer Note for {target_company}.

Today's date: {datetime.now().strftime("%Y-%m-%d")}

Pain Points:
{json.dumps(pain_points, indent=2)}

Value Proposition:
{json.dumps(value_arguments, indent=2)}

Matching Summary:
{match_summary}

Selling Arguments:
{json.dumps(selling_arguments, indent=2)}

Outreach Email Summary:
{outreach_body}

Your task:
1. Build a structured **Offer Note** that fits on one page (≈ A4) with keys:
   {{
     "context": str,
     "proposed_value": [str],
     "solution_outline": {{"approach": str, "timeline": str, "resources": str}},
     "expected_outcomes": [str],
     "next_steps": [str]
   }}
2. Keep the tone professional, crisp, and outcome-driven.
3. Return strictly valid JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content.strip()

        # Clean possible JSON fences
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        clean = re.sub(r"```$", "", clean).strip()

        parsed = json.loads(clean)

    except Exception as e:
        parsed = {
            "context": f"⚠️ Offer note generation failed: {e}",
            "proposed_value": [],
            "solution_outline": {
                "approach": "",
                "timeline": "",
                "resources": ""
            },
            "expected_outcomes": [],
            "next_steps": []
        }

    return {
        "company": target_company,
        "offer_note": parsed
    }
