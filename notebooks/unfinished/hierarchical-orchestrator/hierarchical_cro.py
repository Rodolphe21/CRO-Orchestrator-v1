"""
Hierarchical CRO Orchestrator (target_company / origin_company version)

- LLM-driven hierarchical multi-agent system
- Orchestrator executes agents
- LLM decider chooses the next agent
- No agent-to-agent communication
"""

import os
import json
from datetime import datetime
from openai import OpenAI

# Local imports
from .agent_registry import AGENT_SPEC, AVAILABLE_AGENTS
from .llm_decider import ask_llm_for_next_agent
from .json_utils import save_json

from .agent_registry import AGENT_SPEC

client = OpenAI()

# ----------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ----------------------------------------------------------------------

def CRO_hierarchical_orchestrator(
    target_company: str,
    origin_company: str,
    output_dir: str = "HH-exchanges",
    max_steps: int = 24,
):
    """
    Hierarchical CRO Orchestrator.

    Args:
        target_company: str — Prospect (pain point source)
        origin_company: str — Solution provider (value proposition source)
        output_dir: str — Where to store step-by-step JSON
        max_steps: int — Safety cap

    Returns:
        dict: final summary containing outputs + history
    """

    print("=== Hierarchical CRO Orchestrator ===")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    folder = os.path.join(
        output_dir,
        f"{target_company.replace('.', '_')}__{origin_company.replace('.', '_')}"
    )
    os.makedirs(folder, exist_ok=True)

    # ----------------------------------------------------------
    # State visible to LLM
    # ----------------------------------------------------------
    state = {
        "target_company": target_company,
        "origin_company": origin_company,
        "history": [],
        "outputs": {},
        "run_counts": {},
        "agent_registry": AGENT_SPEC,
    }

    # ----------------------------------------------------------
    # LLM-driven agent selection loop
    # ----------------------------------------------------------
    for step in range(1, max_steps + 1):

        print(f"\n=== 🧠 Step {step} — LLM deciding next agent ===")

        decision = ask_llm_for_next_agent(state)
        agent_name = decision.get("agent")

        print(f"🤖 LLM selected: {agent_name}")
        print(f"Reason: {decision.get('reason')}")

        # Stop condition
        if agent_name == "STOP":
            print("🛑 LLM decided the workflow is complete.")
            break

        # Safety: unknown agent
        if agent_name not in AGENT_SPEC:
            print(f"⚠️ LLM returned invalid agent: {agent_name}. Stopping.")
            break

        # ------------------------------------------------------
        # Build argument map for the agent
        # ------------------------------------------------------
        spec = AGENT_SPEC[agent_name]
        fn = spec["fn"]
        inputs_map = spec["inputs"]

        call_args = {}

        for arg_name, source in inputs_map.items():

            if source == "target_company":
                call_args[arg_name] = state["target_company"]

            elif source == "origin_company":
                call_args[arg_name] = state["origin_company"]

            else:  # previous agent output
                if source not in state["outputs"]:
                    raise ValueError(
                        f"Agent '{agent_name}' requires '{source}' "
                        f"but that output has not been produced."
                    )
                call_args[arg_name] = state["outputs"][source]

        # ------------------------------------------------------
        # Execute the agent
        # ------------------------------------------------------
        print(f"▶️ Calling agent: {agent_name}")

        try:
            output = fn(**call_args)
#        except Exception as e:
#           output = {"error": f"Agent '{agent_name}' failed: {e}"}
#           print(output["error"])
        except Exception as e:
            import traceback
            print("--------------- Agent ERROR ---------------")
            print(f"Agent '{agent_name}' FAILED with exception:")
            traceback.print_exc()
            print("-------------------------------------------")
            state["outputs"][agent_name] = {"error": str(e)}
            continue

        # increments run_counts
        state["run_counts"][agent_name] = state["run_counts"].get(agent_name, 0) + 1
        
        # Store output
        state["outputs"][agent_name] = output

        # Save trace
        state["history"].append({
            "step": step,
            "agent": agent_name,
            "inputs": list(call_args.keys()),
            "output_keys": list(output.keys()) if isinstance(output, dict) else "non-dict"
        })

        # Save output file
        save_json(output, f"{folder}/{step:02d}_{agent_name}.json")

    # ----------------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------------
    summary = {
        "pair": f"{target_company} -> {origin_company}",
        "timestamp": timestamp,
        "steps": state["history"],
        "final_outputs": state["outputs"],
    }

    save_json(summary, f"{folder}/00_summary_hierarchical.json")

    print("\n✅ Hierarchical CRO complete.")
    print(f"📂 All files saved to: {folder}")

    return summary
