"""Stylized workflow preview for the converse plugin.

Drives a deterministic terminal animation that mirrors what a real
/converse session looks like. Used to generate assets/converse-demo.gif
via:

    asciinema rec assets/demo.cast --command "python3 assets/demo.py" --overwrite
    agg assets/demo.cast assets/converse-demo.gif --speed 1.0

This is a workflow preview, not a real recording of an LLM session.
"""
from __future__ import annotations

import random
import sys
import time

random.seed(7)

# ANSI
RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
ORANGE = "\033[38;5;214m"
GREY = "\033[38;5;245m"


def out(s: str = "") -> None:
    sys.stdout.write(s)
    sys.stdout.flush()


def line(s: str = "") -> None:
    out(s + "\n")


def type_user(text: str, base: float = 0.045, jitter: float = 0.05) -> None:
    for ch in text:
        out(ch)
        time.sleep(base + random.random() * jitter)


def stream_model(text: str, base: float = 0.010, jitter: float = 0.012) -> None:
    for ch in text:
        out(ch)
        time.sleep(base + random.random() * jitter)


def pause(s: float) -> None:
    time.sleep(s)


def prompt() -> None:
    out(f"\n{ORANGE}• {RESET}")


def slash_echo(cmd: str) -> None:
    out(f"\n{GREY}⚙ /{cmd}{RESET}\n")


def banner() -> None:
    line(f"{YELLOW}Welcome to Hermes Agent.{RESET}")
    line(f"{DIM}Type your message or /help for commands.{RESET}")


def main() -> None:
    banner()
    pause(0.6)

    # Turn 1: enable converse
    prompt()
    type_user("/converse")
    pause(0.25)
    line()
    slash_echo("converse")
    line(f"{GREEN}converse: ON.{RESET} i'll discuss only, no tools.")
    line(f"{DIM}talk through what you want; type /go when ready to execute.{RESET}")
    pause(0.6)

    # Turn 2: vague request
    prompt()
    type_user("i want to build a tip-splitting cli for groups of friends")
    pause(0.3)
    line()
    pause(0.5)
    stream_model(
        "A few things to pin down before any code:\n\n"
        "  1. even split across all people, or weighted by what each person ordered?\n"
        "  2. include tax in the split, or tip-only?\n"
        "  3. terminal output only, or save a receipt file too?\n\n"
        f"{BOLD}Plan so far:{RESET}\n"
        f"{DIM}  GOAL{RESET}            cli that splits a bill across a group\n"
        f"{DIM}  IN SCOPE{RESET}        bill + tip split, terminal output\n"
        f"{DIM}  OPEN QUESTIONS{RESET}  even vs weighted; tax handling; receipt file\n"
        f"{DIM}  NEXT STEPS{RESET}      confirm scope, then /go\n"
    )
    pause(0.9)

    # Turn 3: user clarifies
    prompt()
    type_user("even split, no tax, terminal only")
    pause(0.25)
    line()
    pause(0.4)
    stream_model(
        "Locked in.\n\n"
        f"{BOLD}Plan so far:{RESET}\n"
        f"{DIM}  GOAL{RESET}         cli that splits a bill evenly across a group\n"
        f"{DIM}  IN SCOPE{RESET}     even bill+tip split, terminal output\n"
        f"{DIM}  OUT OF SCOPE{RESET} weighted splits, tax, file output\n"
        f"{DIM}  NEXT STEPS{RESET}   scaffold, run, edge cases (1 person, 0 tip)\n"
    )
    pause(0.8)

    # Turn 4: /go
    prompt()
    type_user("/go")
    pause(0.25)
    line()
    slash_echo("go")
    line(f"{GREEN}converse: off, executing.{RESET}")
    pause(0.5)
    stream_model(
        "Scaffolding the project now...\n\n"
    )
    pause(0.3)
    stream_model(
        f"{CYAN}➜{RESET} write_file  tip_split.py\n",
        base=0.005, jitter=0.005,
    )
    pause(0.2)
    stream_model(
        f"{CYAN}➜{RESET} write_file  README.md\n",
        base=0.005, jitter=0.005,
    )
    pause(0.2)
    stream_model(
        f"{CYAN}➜{RESET} terminal    python3 tip_split.py 124.50 4 18\n",
        base=0.005, jitter=0.005,
    )
    pause(0.4)
    stream_model(
        f"{DIM}each pays $36.73 (bill $31.13 + tip $5.60){RESET}\n"
    )
    pause(1.2)


if __name__ == "__main__":
    main()
