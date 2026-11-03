"""Vercel entry point for ask-your-pdf.

Vercel serves the function in api/index.py, while the Flask app lives in
app.py at the project root. This module just re-exports that app so
Vercel can run it, with no change to the local Flask behaviour.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402,F401  (Vercel looks for `app`)
