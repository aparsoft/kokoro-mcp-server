# aparsoft_tts/run_http_server.py

#!/usr/bin/env python3
"""Run Aparsoft TTS MCP Server with HTTP transport for OpenAI integration.

This server is specifically for use with OpenAI's Responses API.
For Claude Desktop/Cursor, continue using the standard mcp_server.py with stdio.

Usage:
    python run_http_server.py

    # Or with custom port
    python run_http_server.py --port 8200

    # With debug logging
    LOG_LEVEL=DEBUG python run_http_server.py
"""

import sys
import argparse
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

from aparsoft_tts.mcp_server import mcp
from aparsoft_tts.utils.logging import get_logger

log = get_logger(__name__)


def main():
    """Run MCP server with HTTP transport."""
    parser = argparse.ArgumentParser(description="Run Aparsoft TTS MCP Server with HTTP transport")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8200, help="Port to listen on (default: 8200)")
    parser.add_argument("--path", default="/mcp", help="URL path for MCP endpoint (default: /mcp)")

    args = parser.parse_args()

    print(
        f"""
╔══════════════════════════════════════════════════════════════╗
║     Aparsoft TTS MCP Server - HTTP Transport Mode          ║
╚══════════════════════════════════════════════════════════════╝

🌐 Server Configuration:
   Host: {args.host}
   Port: {args.port}
   Path: {args.path}
   
📍 MCP Endpoint: http://localhost:{args.port}{args.path}/

🔧 For OpenAI Responses API:
   server_url: "http://localhost:{args.port}{args.path}/"
   
⚠️  Note: This server uses HTTP transport for OpenAI integration.
    For Claude Desktop/Cursor, use: python -m aparsoft_tts.mcp_server
    
🚀 Starting server...
"""
    )

    try:
        # Run with HTTP transport
        mcp.run(transport="http", host=args.host, port=args.port, path=args.path)
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
