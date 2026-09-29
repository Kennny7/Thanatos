#!/usr/bin/env python3
# Thanatos/thanatos_cli.py
"""
Thanatos Terminal CLI Client Entry Point.
Run with: python thanatos_cli.py
"""

import asyncio
import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.cli.terminal_client import ThanatosCLI


def main() -> None:
    try:
        cli = ThanatosCLI()
        asyncio.run(cli.start())
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
