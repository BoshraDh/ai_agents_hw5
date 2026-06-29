"""Terminal keyboard menu — all operations go through DebateSDK only."""

from __future__ import annotations

import json

from debate.sdk.sdk import DebateSDK
from debate.shared.version import VERSION


def _print_header() -> None:
    print(f"\n{'='*40}")
    print(f"  AI Debate System v{VERSION}")
    print(f"{'='*40}")


def _menu_start(sdk: DebateSDK) -> None:
    print(f"\nTopic: {sdk._config.topic}")
    print("Starting debate... (this may take a few minutes)")
    try:
        session_id = sdk.start_debate()
        print(f"\nDebate complete! Session: {session_id}")
        verdict = sdk.get_verdict(session_id)
        if verdict:
            print(f"Winner: {verdict['winner']}")
            print(f"Pro score: {verdict['pro_score']:.1f} | Con score: {verdict['con_score']:.1f}")
    except Exception as exc:
        print(f"\nError: {exc}")


def _menu_transcript(sdk: DebateSDK) -> None:
    transcript = sdk.get_transcript("")
    if not transcript:
        print("\nNo transcript available — run a debate first.")
        return
    print(f"\n--- Transcript ({len(transcript)} messages) ---")
    for msg in transcript:
        print(f"\n[Round {msg['round_number']} | {msg['from_agent']}]")
        print(msg["content"][:500])
        if msg.get("citations"):
            print(f"  Citations: {len(msg['citations'])} source(s)")


def _menu_verdict(sdk: DebateSDK) -> None:
    verdict = sdk.get_verdict("")
    if not verdict:
        print("\nNo verdict yet — run a debate first.")
        return
    print(f"\n--- Verdict ---")
    print(f"Winner:       {verdict['winner']}")
    print(f"Pro score:    {verdict['pro_score']:.1f}")
    print(f"Con score:    {verdict['con_score']:.1f}")
    print(f"Criterion:    {verdict['criterion']}")
    print(f"Justification:\n{verdict['justification']}")


def run_menu() -> None:
    """Entry point for the interactive terminal menu."""
    sdk = DebateSDK()
    while True:
        _print_header()
        print("1. Start new debate")
        print("2. View last transcript")
        print("3. View verdict")
        print("4. Change debate topic")
        print("5. Show configuration")
        print("6. Exit")
        choice = input("\nEnter choice: ").strip()
        if choice == "1":
            _menu_start(sdk)
        elif choice == "2":
            _menu_transcript(sdk)
        elif choice == "3":
            _menu_verdict(sdk)
        elif choice == "4":
            topic = input("Enter new topic: ").strip()
            if topic:
                sdk.set_topic(topic)
                print(f"Topic updated: {topic}")
        elif choice == "5":
            print(json.dumps(sdk.get_config_summary(), indent=2))
        elif choice == "6":
            print("Goodbye.")
            sdk.stop()
            break
        else:
            print("Invalid choice.")
