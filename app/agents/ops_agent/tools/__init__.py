"""Tools for the Ops Agent.

This module contains all tools available to the Ops Agent:
- Ansible Automation Platform tools (inventories, jobs, EDA, playbooks, docs)
- Memory management tools
"""

from agents.ops_agent.tools.ansible_tools import (
    list_ansible_inventories,
    get_ansible_inventory,
    create_ansible_inventory,
    run_ansible_job,
    get_ansible_job_status,
    get_ansible_job_logs,
    search_ansible_galaxy_collections,
    list_eda_activations,
    get_eda_activation,
    lint_ansible_playbook,
    validate_ansible_syntax,
    search_redhat_docs,
    fetch_redhat_doc_content,
    ANSIBLE_TOOLS,
)
from agents.ops_agent.tools.memory import upsert_memory


# All tools available to the Ops Agent
ALL_TOOLS = [upsert_memory] + ANSIBLE_TOOLS


__all__ = [
    # Individual tools
    "upsert_memory",
    "list_ansible_inventories",
    "get_ansible_inventory",
    "create_ansible_inventory",
    "run_ansible_job",
    "get_ansible_job_status",
    "get_ansible_job_logs",
    "search_ansible_galaxy_collections",
    "list_eda_activations",
    "get_eda_activation",
    "lint_ansible_playbook",
    "validate_ansible_syntax",
    "search_redhat_docs",
    "fetch_redhat_doc_content",
    # Tool collections
    "ANSIBLE_TOOLS",
    "ALL_TOOLS",
]
