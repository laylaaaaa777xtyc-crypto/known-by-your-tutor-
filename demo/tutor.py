"""Minimal Claude-powered adaptive tutor demo.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python tutor.py                                    # xiaohe, no profile
    python tutor.py --tutor zhouzhou                   # switch persona
    python tutor.py --profile ../examples/learner-profile.example.json

Reads:
    - prompts/_shared_contract.md         (shared底层契约)
    - prompts/<tutor>.md                  (角色 prompt)
    - optional: <profile.json>            (跨会话承接)

Design choices worth noting:
    - Model: claude-opus-4-7 (default per the loaded claude-api skill).
    - Adaptive thinking on: the tutor's "换讲法/切换认知入口" logic benefits
      from real reasoning.
    - Prompt caching on system: the shared contract + persona is large and
      stable across turns — cache it. Verify via usage.cache_read_input_tokens.
    - Streaming: better UX; also required if max_tokens grows.
    - Type-hinted with `from __future__ import annotations` so this still
      runs on 3.10+.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
VALID_TUTORS = ("xiaohe", "zhouzhou", "zhiyuan")
MODEL = "claude-opus-4-7"


def load_system_prompt(tutor: str, profile: dict | None) -> list[dict]:
    """Build the system message as a list of text blocks with cache_control.

    Placement: shared contract + persona are frozen across turns, so we
    cache them together. The (optional) profile block goes AFTER the cache
    breakpoint because it's session-specific and would otherwise invalidate
    the shared prefix across different learners.
    """
    shared = (PROMPTS_DIR / "_shared_contract.md").read_text(encoding="utf-8")
    persona = (PROMPTS_DIR / f"{tutor}.md").read_text(encoding="utf-8")

    blocks: list[dict] = [
        {
            "type": "text",
            "text": (
                "# 底层契约（三位老师共享）\n\n"
                f"{shared}\n\n---\n\n"
                "# 你当前扮演的老师\n\n"
                f"{persona}"
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    if profile is not None:
        blocks.append(
            {
                "type": "text",
                "text": (
                    "# 本会话的学习者画像 (JSON)\n\n"
                    "把它当作跨会话承接点：读上次进度、薄弱点、到期复习、"
                    "以及`last_commitment.text`——如果存在，用它作为开场承接。"
                    "\n\n```json\n"
                    f"{json.dumps(profile, ensure_ascii=False, indent=2)}\n"
                    "```"
                ),
            }
        )

    return blocks


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Adaptive tutor demo (Claude API)")
    p.add_argument(
        "--tutor",
        choices=VALID_TUTORS,
        default="xiaohe",
        help="Which persona to load (default: xiaohe).",
    )
    p.add_argument(
        "--profile",
        type=Path,
        default=None,
        help="Path to a learner-profile JSON file (see examples/).",
    )
    p.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Response cap. Increase if you see truncation.",
    )
    return p.parse_args()


def load_profile(path: Path | None) -> dict | None:
    if path is None:
        return None
    if not path.exists():
        sys.exit(f"Profile file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"Profile is not valid JSON: {e}")


def run() -> None:
    args = parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. See .env.example.")

    profile = load_profile(args.profile)
    system_blocks = load_system_prompt(args.tutor, profile)
    client = anthropic.Anthropic()
    messages: list[dict] = []

    banner = f"[tutor={args.tutor}, profile={'yes' if profile else 'no'}, model={MODEL}]"
    print(banner)
    print("按 Ctrl-C 或输入空行退出。\n")

    while True:
        try:
            user = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            break

        messages.append({"role": "user", "content": user})

        print(f"{args.tutor} > ", end="", flush=True)
        with client.messages.stream(
            model=MODEL,
            max_tokens=args.max_tokens,
            system=system_blocks,
            thinking={"type": "adaptive"},
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            final = stream.get_final_message()
        print()

        assistant_text = "".join(
            block.text for block in final.content if block.type == "text"
        )
        messages.append({"role": "assistant", "content": assistant_text})

        u = final.usage
        cached = getattr(u, "cache_read_input_tokens", 0) or 0
        written = getattr(u, "cache_creation_input_tokens", 0) or 0
        print(
            f"  [usage: in={u.input_tokens} out={u.output_tokens} "
            f"cache_read={cached} cache_write={written}]\n"
        )


if __name__ == "__main__":
    run()
