import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def outreach_email_builder(
    target_company: str,
    pain_json: dict,
    value_json: dict,
    match_json: dict,
    sell_json: dict
) -> dict:
    """
    Builds a personalized outreach email to the most relevant decision-maker,
    based on company context and selling arguments.
    """

    # Extract safe data
    pain_points = pain_json.get("pain_points", {}).get("pain_points", [])
    value_prop = value_json.get("value_proposition", {})
    value_arguments = value_prop.get("value_arguments", [])
    match_summary = match_json.get("matching_result", {}).get("summary", "")
    selling_arguments = sell_json.get("selling_arguments", [])

    prompt = f"""
You are an enterprise sales assistant preparing an outreach email.

Target company: {target_company}
Today's date: {datetime.now().strftime("%Y-%m-%d")}

Pain Points:
{json.dumps(pain_points, indent=2)}

Value Proposition:
{json.dumps(value_arguments, indent=2)}

Matching Summary:
{match_summary}

Selling Arguments:
{json.dumps(selling_arguments, indent=2)}

Your task:
1. Identify the most relevant target contact (role/title, department, reason to reach out).
2. Write a concise, professional outreach email (max 150 words) that includes:
   - Subject line
   - Body referencing the pain points and proposed value
   - Clear, respectful call to action
3. Return **valid JSON** with keys:
{{
  "target_contact": {{"role": str, "department": str, "reason": str}},
  "email": {{"subject": str, "body": str}},
  "tone": str
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content.strip()

        # Clean JSON fences
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        clean = re.sub(r"```$", "", clean).strip()

        parsed = json.loads(clean)

    except Exception as e:
        parsed = {
            "target_contact": {"role": "", "department": "", "reason": ""},
            "email": {
                "subject": "N/A",
                "body": f"⚠️ Email generation failed: {e}"
            },
            "tone": "neutral"
        }

    return {
        "company": target_company,
        "outreach_email": parsed
    }
