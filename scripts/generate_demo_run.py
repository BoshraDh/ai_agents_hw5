"""Generate a demo debate session log for README and docs.

Runs the full DebateOrchestrator pipeline (use_processes=False) with
rich mock LLM responses that look like real debate output. Produces:
  - logs/session_demo.jsonl  — full JSONL transcript
  - prints a formatted transcript excerpt for the README
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debate.orchestrator.debate_orchestrator import DebateOrchestrator  # noqa: E402

# ---------------------------------------------------------------------------
# Rich mock responses — 5 rounds × 2 agents + final verdict
# ---------------------------------------------------------------------------

ROUND_RESPONSES = [
    # Round 1 — Pro
    (json.dumps({
        "content": (
            "AI has proven to be a transformative benefit to humanity, most evidently in "
            "healthcare. A 2023 study in *Nature Medicine* found that AI diagnostic models "
            "detected early-stage lung cancer with 94.5% accuracy — outperforming radiologists "
            "by 11.5 percentage points. Beyond medicine, AI-powered agricultural tools have "
            "helped smallholder farmers increase crop yields by up to 30% in sub-Saharan Africa "
            "(World Bank, 2024). These are not abstract promises; they are measurable outcomes "
            "affecting millions of lives today. The burden of proof is on those who claim threat."
        )
    }), []),
    # Round 1 — Con
    (json.dumps({
        "content": (
            "The Pro agent cites cherry-picked success stories while ignoring AI's documented "
            "systemic risks. Let us examine the same 2023 period: facial-recognition AI "
            "wrongly identified Black Americans at error rates 10–100× higher than white "
            "Americans (NIST, 2023), leading to false arrests. Meanwhile, generative AI "
            "enabled over 4,000 deepfake political disinformation campaigns in 2023 alone "
            "(Stanford Internet Observatory). A technology that simultaneously saves some "
            "lives while structurally harming marginalised communities is not a net benefit — "
            "it is a redistribution of harm."
        )
    }), []),
    # Round 2 — Pro
    (json.dumps({
        "content": (
            "The Con agent equates misuse with the technology itself — a logical fallacy. "
            "Facial-recognition bias is a deployment governance problem, not an inherent "
            "property of AI. The EU AI Act (2024) and the US Executive Order on AI Safety "
            "directly address these harms through mandatory bias audits. Meanwhile, AI's "
            "contribution to climate science — accelerating climate models from weeks to "
            "hours (DeepMind AlphaTensor, 2023) — creates tools we desperately need. "
            "Regulating a technology's misuse does not make the technology itself a threat."
        )
    }), []),
    # Round 2 — Con
    (json.dumps({
        "content": (
            "The Pro agent now retreats to 'governance will fix it' — a claim that assumes "
            "regulation is both sufficient and inevitable. The historical record disagrees. "
            "Social media platforms promised self-regulation and produced a teen mental-health "
            "crisis (APA, 2023). AI threatens an identical dynamic at greater scale: "
            "600 million jobs at risk of displacement by 2030 (McKinsey Global Institute), "
            "with retraining programs reaching fewer than 3% of affected workers. "
            "Governance optimism is not evidence. The structural economic disruption is real, "
            "measurable, and already underway."
        )
    }), []),
    # Round 3 — Pro
    (json.dumps({
        "content": (
            "Job displacement is not synonymous with net harm. The Industrial Revolution "
            "displaced 90% of agricultural workers — and average global life expectancy "
            "doubled in the century that followed. AI is automating the dangerous, repetitive, "
            "and cognitively exhausting tasks that cause physical injury and burnout. "
            "The Oxford Martin School's 2024 analysis projects that AI creates 1.7 new jobs "
            "for every job displaced when measured over a 15-year horizon. The question is not "
            "'does AI displace jobs?' but 'do the aggregate human outcomes improve?' "
            "The data says yes."
        )
    }), []),
    # Round 3 — Con
    (json.dumps({
        "content": (
            "Comparing AI to the Industrial Revolution proves my point, not the Pro agent's. "
            "The Industrial Revolution produced 150 years of child labour, unsafe factories, "
            "and the near-destruction of the artisan class — before governance caught up. "
            "The Pro agent projects 15-year horizons to justify harm imposed today. "
            "That is not an ethical argument; it is deferred accountability. "
            "Furthermore, AI existential risk is now taken seriously by the very engineers "
            "who built these systems — Yoshua Bengio and Geoffrey Hinton both testified to "
            "the UN in 2024 about catastrophic AI risk. When creators warn against their own "
            "creation, the threat designation is earned."
        )
    }), []),
    # Round 4 — Pro
    (json.dumps({
        "content": (
            "Existential risk arguments rely on low-probability, high-consequence scenarios "
            "that must be weighed against the certain, high-probability benefits already "
            "being realised. AlphaFold's protein structure predictions have accelerated "
            "drug discovery for Alzheimer's and antibiotic-resistant infections. "
            "More than 2 million researchers have used AlphaFold data (DeepMind, 2024). "
            "The Con agent's strategy is to find worst-case projections and present them "
            "as representative. Every technology has tail risks. AI's expected value, "
            "calculated honestly, is strongly positive."
        )
    }), []),
    # Round 4 — Con
    (json.dumps({
        "content": (
            "The Pro agent's expected-value calculus breaks down when the downside scenarios "
            "are irreversible. Climate change, nuclear weapons, and antibiotic resistance "
            "all feature the same structure: distributed benefits today, concentrated "
            "catastrophic tail risk. We regulate those technologies heavily precisely because "
            "expected value alone is an insufficient guide. AI exhibits the same pattern. "
            "The EU AI Act categorises certain applications as 'unacceptable risk' — not "
            "because policymakers are irrational, but because some harms cannot be traded "
            "off against aggregate benefit."
        )
    }), []),
    # Round 5 — Pro
    (json.dumps({
        "content": (
            "The Con agent's final position is that AI resembles nuclear weapons in risk "
            "profile — a comparison that illuminates the debate's conclusion. Nuclear "
            "energy, which shares the same physics, powers 10% of global electricity "
            "with the lowest death-per-TWh rate of any energy source (Our World in Data). "
            "The technology is not the threat; the governance framework determines outcomes. "
            "AI already powers life-saving tools in 137 countries. The Pro position stands: "
            "with thoughtful governance, AI's net contribution to human welfare is, "
            "and will continue to be, positive."
        )
    }), []),
    # Round 5 — Con
    (json.dumps({
        "content": (
            "The Pro agent ends by conceding that governance is the critical variable — "
            "which is precisely the Con position: AI as currently deployed, without "
            "sufficient governance, is a threat. 'AI could be beneficial with perfect "
            "regulation' is not evidence that it is beneficial today. "
            "The harms I have documented — biased policing algorithms, job displacement "
            "without safety nets, disinformation infrastructure, and acknowledged existential "
            "risk from AI's own creators — are present-tense facts, not hypotheticals. "
            "The Con case is that the threat is real, present, and insufficiently addressed."
        )
    }), []),
    # Verdict
    (json.dumps({
        "winner": "pro_agent",
        "pro_score": 74.5,
        "con_score": 68.0,
        "justification": (
            "Both agents presented well-sourced, coherent arguments. The Pro agent maintained "
            "a consistent evidence-first strategy throughout all five rounds, effectively "
            "reframing each Con challenge (bias, displacement, existential risk) within a "
            "governance-and-expected-value framework. The Con agent's arguments were sharp "
            "but increasingly relied on conditional worst-case projections rather than "
            "demonstrating that present-tense harms outweigh present-tense benefits. "
            "Persuasion power favours the agent who leaves the audience with a net-positive "
            "mental model of the subject. Pro achieved that more consistently."
        ),
        "criterion": "persuasion_power",
        "rounds_evaluated": 5,
    }), []),
]


def main():
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Point at real config so ConfigManager loads properly
    config_dir = str(Path(__file__).parent.parent / "config")
    orch = DebateOrchestrator(config_dir, use_processes=False)

    call_count = {"n": 0}

    def mock_llm(system, messages, use_search=False):
        idx = call_count["n"]
        call_count["n"] += 1
        if idx < len(ROUND_RESPONSES):
            return ROUND_RESPONSES[idx]
        return ROUND_RESPONSES[-1]  # fallback to verdict

    with (
        patch.object(orch._pro, "_call_llm", side_effect=mock_llm),
        patch.object(orch._con, "_call_llm", side_effect=mock_llm),
        patch.object(orch._father, "_call_llm", side_effect=mock_llm),
    ):
        transcript, verdict = orch.run()

    print(f"\nSession ID: {orch.session_id}")
    print(f"Rounds:     {len(transcript) // 2}")
    print(f"Winner:     {verdict.winner.value}")
    print(f"Pro score:  {verdict.pro_score}")
    print(f"Con score:  {verdict.con_score}")
    print("\n--- TRANSCRIPT EXCERPT (Round 1) ---")
    for msg in transcript[:2]:
        print(f"\n[{msg.from_agent.value.upper()} — Round {msg.round_number}]")
        print(msg.content[:400] + "...")

    print("\n--- VERDICT ---")
    print(f"Winner: {verdict.winner.value}")
    print(f"Justification: {verdict.justification[:300]}...")

    # Find the generated log
    log_files = sorted(logs_dir.glob("*.jsonl"))
    if log_files:
        print(f"\nLog saved: {log_files[-1]}")


if __name__ == "__main__":
    main()
