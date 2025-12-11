import os
import json
import re
from datetime import datetime
from cro import utils
from tavily import TavilyClient

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def meta_reasoner_agent(
    target_company: str,
    origin_company: str,
    pain_json: dict,
    value_json: dict,
    match_json: dict,
    sell_json: dict,
    email_json: dict,
    offer_json: dict,
    return_messages: bool = True
) -> dict:
    """
    A higher-order reasoning agent that evaluates the overall opportunity,
    identifies gaps, risks, missing information, and suggests discovery questions
    and recommended strategic moves.

    It does NOT act as an orchestrator. It performs business-level meta-analysis.
    """

    utils.print_html("Meta Reasoner Agent", "🧠")

    # ---- Extract safe data ----
    pain_points = pain_json.get("pain_points", {}).get("pain_points", [])
    value_arguments = value_json.get("value_proposition", {}).get("value_arguments", [])
    match_result = match_json.get("matching_result", {}) or {}
    match_score = match_result.get("score")
    match_summary = match_result.get("summary", "")

    selling_arguments = sell_json.get("selling_arguments", [])
    sales_narrative = sell_json.get("sales_narrative", "")

    outreach_email = email_json.get("outreach_email", {}) or {}
    email_body = outreach_email.get("email", {}).get("body", "")
    email_target_contact = outreach_email.get("target_contact", {})

    offer_note = offer_json.get("offer_note", {}) or {}

    prompt = f"""
You are a senior GTM strategist performing a **meta-analysis** of an opportunity.

Your role:
- NOT orchestration
- NOT rewriting any outputs
- BUT evaluating the overall opportunity from a business perspective

Target company (prospect): {target_company}
Origin company (solution provider): {origin_company}

Today's date: {datetime.now().strftime("%Y-%m-%d")}

---

🩺 Pain Points:
{json.dumps(pain_points, indent=2)}

💎 Value Proposition:
{json.dumps(value_arguments, indent=2)}

🎯 Matching Summary (score={match_score}):
{match_summary}

🧩 Selling Arguments:
{json.dumps(selling_arguments, indent=2)}

✉️ Outreach Snippet:
{email_body}

📄 Offer Note Snapshot:
{json.dumps(offer_note, indent=2)}

---

Your tasks:
1. Provide a **viability_assessment** answering:
   - "Is this a strong opportunity?"
   - "Is the match believable?"
   - "Is there enough evidence to proceed?"
   - "What are the major risks?"

2. Provide a list of **critical_gaps**:
   Missing data, missing reasoning, unclear problem areas, or unclear proof points.

3. Provide **strategic_recommendations**:
   3–6 concrete next steps to strengthen the opportunity:
   - discovery areas
   - technical validation
   - commercial positioning
   - stakeholder alignment

4. Provide **discovery_questions**:
   The 5–7 highest-value questions to ask the prospect in the first meeting.

5. Return STRICT JSON with keys:
{{
  "viability_assessment": str,
  "critical_gaps": [str],
  "strategic_recommendations": [str],
  "discovery_questions": [str]
}}
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
        )

        content = response.choices[0].message.content.strip()

        # Remove possible fencing
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        clean = re.sub(r"```$", "", clean)

        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            parsed = {
                "viability_assessment": clean,
                "critical_gaps": [],
                "strategic_recommendations": [],
                "discovery_questions": [],
            }

        result = {
            "company_pair": f"{target_company} -> {origin_company}",
            "meta_reasoning": {
                "viability_assessment": parsed.get("viability_assessment", ""),
                "critical_gaps": parsed.get("critical_gaps", []),
                "strategic_recommendations": parsed.get("strategic_recommendations", []),
                "discovery_questions": parsed.get("discovery_questions", []),
            }
        }

        if return_messages:
            result["messages"] = messages

        return result

    except Exception as e:
        return {
            "company_pair": f"{target_company} -> {origin_company}",
            "meta_reasoning": {
                "viability_assessment": f"⚠️ Meta reasoning failed: {e}",
                "critical_gaps": [],
                "strategic_recommendations": [],
                "discovery_questions": [],
            },
            "error": str(e),
        }
