"""Terraform Agent - Specialized agent for Terraform Cloud operations.

This module provides an intelligent agent for managing Terraform Cloud operations.
The agent understands complex workflows and can execute multi-step deployments
like RHEL 9 VM provisioning on OpenShift Virtualization.

Key Capabilities:
- Workspace management (create, list, configure)
- Variable management (environment and terraform variables)
- Run management (plan, apply, monitor)
- Complex multi-step workflows (RHEL 9 VM deployment, infrastructure provisioning)
- Organization and project management
"""

from .agent import create_terraform_agent

__all__ = [
    "create_terraform_agent",
]

