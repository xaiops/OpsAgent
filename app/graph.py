"""Main entry point for the OpsAgent system.

This file is referenced by langgraph.json and serves as the single entry point
for the entire multi-agent system. It delegates to the routing coordinator
which manages all specialist agents.

Architecture:
- app.routing.coordinator: Routes requests to appropriate agents
- app.agents.ops_agent: General Ansible automation operations
- Future: More specialized agents can be added
"""

import logging
import sys
import asyncio
from pathlib import Path

# Add app directory to Python path for imports
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from routing import create_ops_coordinator

logger = logging.getLogger(__name__)

# Create and export the graph
# This is what langgraph.json references
# Initialize async coordinator using asyncio.run() at module level
graph = asyncio.run(create_ops_coordinator())

logger.info("OpsAgent graph initialized successfully")
logger.info("Entry point: Routing coordinator with single ops_agent")