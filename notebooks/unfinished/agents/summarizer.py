import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarizer_agent(
    target_company: str,
    origin_company: str,
    match_json: dict,
    sell_json: dict,
    email_json: dict,
    return_messages: bool = True
) -> dict:
    """
    Synthesizes the overall opportunity into an executive summary:
    - Who is the target & provider
    - How strong is the fit
    - Key selling narrative
    - Recommended next steps
    """

    utils.print_html("CRO Executive Summarizer", "🧠")

    # ---- Safe extraction from inputs ----
    match_result = match_json.get("matching_result", {}) or {}
    score = match_result.get("score")
    match_summary = match_result.get("summary", "")

    selling_arguments = sell_json.get("selling_arguments", [])
    sales_narrative = sell_json.get("sales_narrative", "")

    outreach = email_json.get("outreach_email", {}) or {}
    outreach_email = outreach.get("email", {}) or {}
    outreach_subject = outreach_email.get("subject", "")
    outreach_body = outreach_email.get("body", "")
    target_contact = outreach.get("target_contact", {}) or {}

    prompt = f"""
You are a senior sales strategist summarizing an opportunity between two companies.

Target company (prospect): {target_company}
Origin company (solution provider): {origin_company}
Today's date: {datetime.now().strftime("%Y-%m-%d")}

Matching result:
Score: {score}
Summary:
{match_summary}

Selling arguments:
{json.dumps(selling_arguments, indent=2)}

Sales narrative:
{sales_narrative}

Outreach plan:
Target contact:
{json.dumps(target_contact, indent=2)}

Email subject: {outreach_subject}
Email body:
{outreach_body}

Your task:
1. Write a concise **executive_summary** (max 150 words) explaining:
   - Why this opportunity matters for {target_company}
   - How {origin_company} creates value
   - How strong the fit is overall.
2. Propose 3–5 **recommended_next_steps** for the sales team (meetings, discovery, PoC, stakeholder mapping, etc.).
3. Optionally, refine the **sales_narrative** into a sharper, board-level storyline.
4. Return a STRICT JSON object with the keys:
{{
  "executive_summary": str,
  "fit_score": int,          # reuse or refine the score 0–100
  "refined_sales_narrative": str,
  "recommended_next_steps": [str]
}}
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )

        content = response.choices[0].message.content.strip()

        # Clean possible markdown fences
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        clean = re.sub(r"```$", "", clean).strip()

        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            # Fallback: wrap raw text
            parsed = {
                "executive_summary": clean,
                "fit_score": score if isinstance(score, int) else 0,
                "refined_sales_narrative": sales_narrative,
                "recommended_next_steps": [],
            }

        result = {
            "company_pair": f"{target_company} -> {origin_company}",
            "summary": {
                "executive_summary": parsed.get("executive_summary", ""),
                "fit_score": parsed.get("fit_score", score if isinstance(score, int) else 0),
                "refined_sales_narrative": parsed.get("refined_sales_narrative", sales_narrative),
                "recommended_next_steps": parsed.get("recommended_next_steps", []),
            },
        }

        if return_messages:
            result["messages"] = messages

        return result

    except Exception as e:
        return {
            "company_pair": f"{target_company} -> {origin_company}",
            "summary": {
                "executive_summary": f"⚠️ Summarizer failed: {e}",
                "fit_score": score if isinstance(score, int) else 0,
                "refined_sales_narrative": sales_narrative,
                "recommended_next_steps": [],
            },
            "error": str(e),
        }
