# llm_decider.py
# ---------------------------------------------------------------
# LLM-based agent selector for the Hierarchical CRO Orchestrator
# ---------------------------------------------------------------

import json
import os
from openai import OpenAI

# IMPORTANT: the API key is loaded earlier in cro/__init__.py
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

"""
LLM-based agent selector for Hierarchical CRO
"""

import json
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ask_llm_for_next_agent(state: dict) -> dict:
    """
    LLM decides which agent to run next.

    The decision is based on:
    - target_company / origin_company
    - previous outputs
    - run_counts (how many times each agent has run)
    - total available agents
    """

    # Extract a readable history summary
    history_text = json.dumps(state["history"], indent=2)

    # Make run_counts JSON-safe
    run_counts = state.get("run_counts", {})
    run_counts_text = json.dumps(run_counts, indent=2)

    # List agents
    all_agents = list(state["agent_registry"].keys())

    # Build LLM prompt
    system_prompt = """
You are the Hierarchical CRO Orchestrator.
Your job is to pick the BEST NEXT AGENT to run.

You have full freedom, BUT you must reason strategically.

### RULES ###
1. Prefer agents that have NOT run yet.
2. Avoid running the same agent more than 1–2 times unless absolutely necessary.
3. If an agent already ran AND produced a valid output, prefer to move forward.
4. Use retries ONLY when:
   - The agent failed
   - Or missing essential output stops progress
5. Avoid infinite loops — do NOT keep reselecting the same agent.
6. Once pain points, value prop, match score, and selling arguments exist,
   strongly prefer moving to:
   - outreach_email_builder
   - offer_note_builder
   - summarizer_agent
   - or STOP
7. Choose STOP only if:
   - All essential agents have run, OR
   - You cannot make further meaningful progress.

### OUTPUT FORMAT (strict JSON):
{
  "agent": "<agent_name or STOP>",
  "reason": "<why you selected this agent>"
}
"""

    user_prompt = f"""
You are orchestrating the workflow for:

- Target company: {state['target_company']}
- Origin company: {state['origin_company']}

### RUN COUNTS ###
(How many times each agent was executed)
{run_counts_text}

### HISTORY ###
{history_text}

### AVAILABLE AGENTS ###
{all_agents}

Decide which agent should run NEXT.
Follow the rules carefully.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        decision = json.loads(content)

        return decision

    except Exception as e:
        return {
            "agent": "STOP",
            "reason": f"⚠️ LLM decision failed: {e}"
        }