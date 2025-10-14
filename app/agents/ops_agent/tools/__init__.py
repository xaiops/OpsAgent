"""Tools for the Ops Agent.

This module contains agent-side tools:
- Memory management tools (user preferences, context)

Ansible Automation Platform tools are loaded dynamically from MCP servers.
See: app/mcp_integration/client.py for MCP tool loading.

Architecture:
- MCP enabled: 46 tools from MCP + 1 memory tool = 47 tools total
- MCP disabled: 1 memory tool only

Note: Hardcoded Ansible tools were archived to archive/tools/ansible_tools.py
      They can be restored if MCP integration becomes unavailable.
"""

from agents.ops_agent.tools.memory import upsert_memory


# All agent-side tools (non-MCP)
# MCP tools are loaded dynamically at runtime
ALL_TOOLS = [upsert_memory]


__all__ = [
    "upsert_memory",
    "ALL_TOOLS",
]
