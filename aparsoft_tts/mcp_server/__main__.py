# aparsoft_tts/mcp_server/__main__.py

"""Entry point for running the MCP server as a module.

Allows execution via: python -m aparsoft_tts.mcp_server

CRITICAL: This file MUST import all decorator modules BEFORE calling main()
to ensure all tools, resources, and prompts are registered with the MCP server.
"""

# Step 1: Import the MCP instance FIRST (this creates the server)
from aparsoft_tts.mcp_server.mcp_server_main import mcp, main

# Step 2: Import modules that use decorators to register components
# These imports MUST happen for decorators to execute and register tools/resources/prompts
import aparsoft_tts.mcp_server.mcp_tools  # noqa: F401
import aparsoft_tts.mcp_server.mcp_resources  # noqa: F401
import aparsoft_tts.mcp_server.mcp_prompts  # noqa: F401

if __name__ == "__main__":
    # By the time we reach here, all decorators have run and components are registered
    main()
