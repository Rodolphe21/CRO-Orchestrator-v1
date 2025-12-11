"""
Agent Registry for the Hierarchical CRO System

Each agent:
- has a function reference
- declares exactly which inputs it requires
- uses target_company / origin_company convention
"""

from cro.agents.pain_point_detective import pain_point_detective
from cro.agents.value_prop_engineer import value_prop_engineer
from cro.agents.match_scorer import match_scorer
from cro.agents.selling_argumentation_builder import selling_argumentation_builder
from cro.agents.outreach_email_builder import outreach_email_builder
from cro.agents.offer_note_builder import offer_note_builder
from cro.agents.meta_reasoner import meta_reasoner_agent
from cro.agents.summarizer import summarizer_agent

AGENT_SPEC = {
    # 1. Pain Points ----------------------------------------------------------
    "pain_point_detective": {
        "fn": pain_point_detective,
        "inputs": {
            "target_company": "target_company",
        }
    },

    # 2. Value Proposition -----------------------------------------------------
    "value_prop_engineer": {
        "fn": value_prop_engineer,
        "inputs": {
            "origin_company": "origin_company"
        }
    },

    # 3. Matching --------------------------------------------------------------
    "match_scorer": {
        "fn": match_scorer,
        "inputs": {
            "target_company": "target_company",
            "origin_company": "origin_company",
            "pain_json": "pain_point_detective",
            "value_json": "value_prop_engineer"
        }
    },

    # 4. Selling Argumentation -------------------------------------------------
    "selling_argumentation_builder": {
        "fn": selling_argumentation_builder,
        "inputs": {
            "target_company": "target_company",
            "pain_json": "pain_point_detective",
            "value_json": "value_prop_engineer",
            "match_json": "match_scorer"
        }
    },

    # 5. Outreach Email --------------------------------------------------------
    "outreach_email_builder": {
        "fn": outreach_email_builder,
        "inputs": {
            "target_company": "target_company",
            "pain_json": "pain_point_detective",
            "value_json": "value_prop_engineer",
            "match_json": "match_scorer",
            "sell_json": "selling_argumentation_builder"
        }
    },

    # 6. Offer Note ------------------------------------------------------------
    "offer_note_builder": {
        "fn": offer_note_builder,
        "inputs": {
            "target_company": "target_company",
            "pain_json": "pain_point_detective",
            "value_json": "value_prop_engineer",
            "match_json": "match_scorer",
            "sell_json": "selling_argumentation_builder",
            "email_json": "outreach_email_builder"
        }
    },

    # 7. Summarizer ------------------------------------------------------------
    "summarizer_agent": {
        "fn": summarizer_agent,
        "inputs": {
            "target_company": "target_company",
            "origin_company": "origin_company",
            "match_json": "match_scorer",
            "sell_json": "selling_argumentation_builder",
            "email_json": "outreach_email_builder"
        }
    },

    # 8. Meta Reasoner ---------------------------------------------------------
    "meta_reasoner": {
        "fn": meta_reasoner_agent,
        "inputs": {
            "target_company": "target_company",
            "origin_company": "origin_company",
            "pain_json": "pain_point_detective",
            "value_json": "value_prop_engineer",
            "match_json": "match_scorer",
            "sell_json": "selling_argumentation_builder",
            "email_json": "outreach_email_builder",
            "offer_json": "offer_note_builder"
        }
    },
}

AVAILABLE_AGENTS = list(AGENT_SPEC.keys())
