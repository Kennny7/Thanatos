#!/usr/bin/env python3
# Thanatos/thanatos_cli.py
"""
Thanatos Terminal CLI Client Entry Point.
Run with:
    thanatos
    thanatos -c "/status"
    thanatos -c "find AI engineer jobs in Pune"
"""

import argparse
import asyncio
import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.cli.terminal_client import ThanatosCLI


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thanatos Autonomous Multi-Agent Terminal Client & AI Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c", "--command",
        type=str,
        default=None,
        help="Execute a single command or query non-interactively and exit (e.g. -c '/status')",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="Thanatos AI 1.0.0",
    )

    args = parser.parse_args()

    try:
        cli = ThanatosCLI()
        if args.command:
            asyncio.run(cli.execute_single_command(args.command))
        else:
            asyncio.run(cli.start())
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
