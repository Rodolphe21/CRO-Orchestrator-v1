from cro.orchestrator.hierarchical_cro import CRO_hierarchical_orchestrator

if __name__ == "__main__":
    CRO_hierarchical_orchestrator(
        target_company="swissre.com",
        origin_company="outsystems.com",
        max_steps=12
    )
