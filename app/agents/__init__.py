"""All specialized agents.

Currently contains:
- OpsAgent: General purpose Ansible automation agent

Future agents can be added here:
- PlaybookDevAgent: Playbook development and code generation
- InfrastructureAgent: Infrastructure provisioning
- SecurityAgent: Security baseline and compliance
- etc.
"""

from agents.ops_agent import create_ops_agent, ALL_TOOLS as OPS_AGENT_TOOLS

__all__ = [
    "create_ops_agent",
    "OPS_AGENT_TOOLS",
]
