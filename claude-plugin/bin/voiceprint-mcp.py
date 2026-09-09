#!/usr/bin/env python3
"""Launch the voiceprint MCP server, or explain how to install it."""
import importlib.util
import subprocess
import sys

if importlib.util.find_spec("voiceprint") is None:
    sys.stderr.write(
        "voiceprint is not installed in this Python environment.\n"
        "Run: pip install voiceprint\n"
    )
    sys.exit(1)

sys.exit(subprocess.call([sys.executable, "-m", "voiceprint.mcp"]))
