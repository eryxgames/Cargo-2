#!/usr/bin/env python3
"""Cargo 2: a text-based space trading saga, the second part of the Cargo trilogy.

    python3 cargo2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.start import main  # noqa: E402
import game.world  # noqa: E402,F401  (loads every module of the game)

if __name__ == "__main__":
    main()
