"""Adaptive tutor demo with a zero-setup local mode and optional Claude mode.

Usage:
    python tutor.py                                    # works without an API key
    export ANTHROPIC_API_KEY=sk-ant-...                # optional: use Claude
    python tutor.py --tutor zhouzhou                   # switch persona
    python tutor.py --profile ../examples/learner-profile.example.json

Reads:
    - prompts/<tutor>.md                  (self-contained system prompt)
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

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
VALID_TUTORS = ("xiaohe", "zhouzhou", "zhiyuan")
MODEL = "claude-opus-4-7"


def load_system_prompt(tutor: str, profile: dict | None) -> list[dict]:
    """Build the system message as a list of text blocks with cache_control.

    Placement: the persona prompt is frozen across turns, so we mark it
    with cache_control. The (optional) profile block goes AFTER the cache
    breakpoint because it's session-specific and would otherwise invalidate
    the shared prefix across different learners.
    """
    persona = (PROMPTS_DIR / f"{tutor}.md").read_text(encoding="utf-8")

    blocks: list[dict] = [
        {
            "type": "text",
            "text": persona,
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
    p = argparse.ArgumentParser(description="Adaptive tutor demo")
    p.add_argument(
        "--mode",
        choices=("auto", "local", "anthropic"),
        default="auto",
        help="Backend: auto uses Claude when a key exists, otherwise local.",
    )
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


def local_reply(tutor: str, user: str, turn: int) -> str:
    """Return a useful, deterministic coaching prompt without external services.

    This intentionally does not pretend to be a language model. It provides a
    small guided learning loop so a fresh clone is immediately runnable.
    """
    text = user.strip()
    if turn == 1:
        openings = {
            "xiaohe": "好，我们慢慢来。先不求一次学完。",
            "zhouzhou": "收到。先把目标和验收标准钉死，再开始。",
            "zhiyuan": "有意思。我们先找出你真正想弄明白的那个问题。",
        }
        return (
            f"{openings[tutor]}\n\n"
            f"你提到：‘{text}’。请再告诉我两件事：\n"
            "1. 你希望学完后能独立完成什么？\n"
            "2. 你现在最卡的一点是什么？"
        )

    if any(word in text for word in ("不会", "不懂", "卡", "太难", "没明白")):
        switches = {
            "xiaohe": "没关系，这说明刚才的入口不合适。我们把任务缩小：请贴出一个最具体的例子，或只说第一个看不懂的词。",
            "zhouzhou": "先停止往后赶。请指出第一个断点，并写出你已经确定的事实；我们从断点重做，做到能复述为止。",
            "zhiyuan": "先不听更多解释。请给出一个反例，或告诉我：哪条前提一变，你原来的理解就会失效？",
        }
        return switches[tutor]

    if any(word in text for word in ("学会", "懂了", "明白了", "完成了")):
        checks = {
            "xiaohe": "很好。我们做一个轻量验收：不用看资料，用自己的话讲一遍核心思路，再举一个新例子。",
            "zhouzhou": "开始验收：关掉资料，独立完成一道同类型新题，并解释每一步为什么成立。答错就订正后重做。",
            "zhiyuan": "先别下结论。请说出这个结论的适用边界，再构造一个它不成立的情境。",
        }
        return checks[tutor]

    prompts = {
        "xiaohe": "我记下了。把下一步压缩成十分钟内能完成的小动作：请先写一个例子，然后说说哪一步最费劲。",
        "zhouzhou": "继续。请给出一个可检查的答案或产物，不只描述感受；我会按你最初的目标验收。",
        "zhiyuan": "先提出你的猜想：如果这个判断是错的，最可能被哪个例子推翻？请从那个例子开始验证。",
    }
    return prompts[tutor]


def run_local(tutor: str, profile: dict | None) -> None:
    print(f"[tutor={tutor}, profile={'yes' if profile else 'no'}, mode=local]")
    print("无需 API Key。本地模式使用内置教学流程，不具备大模型的自由问答能力。")
    print("按 Ctrl-C 或输入空行退出。\n")
    turn = 0
    while True:
        try:
            user = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            break
        turn += 1
        print(f"{tutor} > {local_reply(tutor, user, turn)}\n")


def load_profile(path: Path | None) -> dict | None:
    if path is None:
        return None
    if not path.exists():
        sys.exit(f"Profile file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"Profile is not valid JSON: {e}")


def run_anthropic(args: argparse.Namespace, profile: dict | None) -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Anthropic mode requires ANTHROPIC_API_KEY. Use --mode local instead.")
    try:
        import anthropic
    except ImportError:
        sys.exit(
            "Anthropic SDK is not installed. Run: "
            "python -m pip install -r demo/requirements.txt"
        )

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


def run() -> None:
    args = parse_args()
    profile = load_profile(args.profile)
    mode = args.mode
    if mode == "auto":
        mode = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "local"

    if mode == "local":
        run_local(args.tutor, profile)
    else:
        run_anthropic(args, profile)


if __name__ == "__main__":
    run()
