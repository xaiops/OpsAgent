"""LangChain tools for Red Hat Ansible Automation Platform REST API."""

import logging
from typing import Optional
import httpx
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

# API base URL will be loaded from config
def _get_api_base_url() -> str:
    """Get the Ansible API base URL from configuration."""
    # For now, hardcoded. Could be moved to config.yaml
    return "http://mcp-aap-ansible-proxy-toolhive-system.apps.virt.na-launch.com"


# =============================================================================
# Ansible Automation Platform Tools
# =============================================================================

async def _list_ansible_inventories() -> str:
    """List all Ansible inventories.
    
    Call this tool when the user asks about:
    - "show inventories"
    - "list inventories" 
    - "what inventories do I have"
    - "available inventories"
    
    Returns:
        str: JSON string containing list of inventories with details
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/ansible/inventories")
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to list inventories: {e}")
        return f"Error: Failed to list inventories - {str(e)}"

list_ansible_inventories = StructuredTool.from_function(
    coroutine=_list_ansible_inventories,
    name="list_ansible_inventories",
    description="""List all Ansible inventories.

Call this tool when the user asks about:
- "show inventories"
- "list inventories" 
- "what inventories do I have"
- "available inventories"

Returns: JSON string containing list of inventories with details"""
)


async def _get_ansible_inventory(inventory_id: str) -> str:
    """Get details of a specific Ansible inventory.
    
    Args:
        inventory_id: The ID of the inventory to retrieve
        
    Returns:
        str: JSON string containing inventory details
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/ansible/inventories/{inventory_id}")
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to get inventory {inventory_id}: {e}")
        return f"Error: Failed to get inventory - {str(e)}"


async def _create_ansible_inventory(name: str, description: str = "") -> str:
    """Create a new Ansible inventory.
    
    Args:
        name: Name of the inventory
        description: Optional description of the inventory
        
    Returns:
        str: JSON string with created inventory details
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/ansible/inventories",
                json={"name": name, "description": description}
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to create inventory: {e}")
        return f"Error: Failed to create inventory - {str(e)}"


async def _run_ansible_job(template_id: str, inventory: Optional[str] = None, extra_vars: Optional[str] = None) -> str:
    """Run an Ansible job template.
    
    Use this to execute Ansible playbooks and automation.
    
    Args:
        template_id: The ID of the job template to run
        inventory: Optional inventory to use for the job
        extra_vars: Optional extra variables as JSON string
        
    Returns:
        str: JSON string with job execution details including job ID
    """
    base_url = _get_api_base_url()
    try:
        payload = {}
        if inventory:
            payload["inventory"] = inventory
        if extra_vars:
            payload["extra_vars"] = extra_vars
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/ansible/jobs/{template_id}/run",
                json=payload
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to run job template {template_id}: {e}")
        return f"Error: Failed to run job - {str(e)}"


async def _get_ansible_job_status(job_id: str) -> str:
    """Get the status of an Ansible job.
    
    Use this to check if a job is running, completed, or failed.
    
    Args:
        job_id: The ID of the job to check
        
    Returns:
        str: JSON string with job status details
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/ansible/jobs/{job_id}")
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to get job status {job_id}: {e}")
        return f"Error: Failed to get job status - {str(e)}"


async def _get_ansible_job_logs(job_id: str) -> str:
    """Get the logs of an Ansible job.
    
    Use this to see the output and results of a completed or running job.
    
    Args:
        job_id: The ID of the job whose logs to retrieve
        
    Returns:
        str: Job logs as text
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/ansible/jobs/{job_id}/logs")
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to get job logs {job_id}: {e}")
        return f"Error: Failed to get job logs - {str(e)}"


async def _search_ansible_galaxy_collections(search_term: str) -> str:
    """Search for Ansible collections in Galaxy.
    
    Use this to find reusable Ansible content and modules.
    
    Args:
        search_term: The term to search for (e.g., "aws", "kubernetes")
        
    Returns:
        str: JSON string with search results
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/ansible/galaxy/collections/search",
                params={"q": search_term}
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to search Galaxy collections: {e}")
        return f"Error: Failed to search Galaxy - {str(e)}"


# =============================================================================
# Event-Driven Ansible (EDA) Tools
# =============================================================================

async def _list_eda_activations() -> str:
    """List all Event-Driven Ansible activations.
    
    Use this to see what automation is currently responding to events.
    
    Returns:
        str: JSON string containing list of EDA activations
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/eda/activations")
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to list EDA activations: {e}")
        return f"Error: Failed to list EDA activations - {str(e)}"


async def _get_eda_activation(activation_id: str) -> str:
    """Get details of a specific Event-Driven Ansible activation.
    
    Args:
        activation_id: The ID of the activation to retrieve
        
    Returns:
        str: JSON string containing activation details
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/eda/activations/{activation_id}")
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to get EDA activation {activation_id}: {e}")
        return f"Error: Failed to get EDA activation - {str(e)}"


# =============================================================================
# Ansible Lint Tools
# =============================================================================

async def _lint_ansible_playbook(playbook_content: str) -> str:
    """Lint an Ansible playbook to check for errors and best practices.
    
    Use this to validate Ansible YAML before running it.
    
    Args:
        playbook_content: The YAML content of the playbook to lint
        
    Returns:
        str: JSON string with linting results and suggestions
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/ansible-lint/lint/playbook",
                json={"playbook": playbook_content}
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to lint playbook: {e}")
        return f"Error: Failed to lint playbook - {str(e)}"


async def _validate_ansible_syntax(playbook_content: str) -> str:
    """Validate the syntax of an Ansible playbook.
    
    Use this for quick syntax checking before linting.
    
    Args:
        playbook_content: The YAML content to validate
        
    Returns:
        str: JSON string with validation results
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/ansible-lint/validate/syntax",
                json={"content": playbook_content}
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to validate syntax: {e}")
        return f"Error: Failed to validate syntax - {str(e)}"


# =============================================================================
# Red Hat Documentation Tools
# =============================================================================

async def _search_redhat_docs(query: str) -> str:
    """Search Red Hat documentation.
    
    Use this to find official Red Hat documentation on Ansible and automation topics.
    
    Args:
        query: The search query (e.g., "how to use ansible vault")
        
    Returns:
        str: JSON string with search results
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/redhat-docs/search/content",
                params={"q": query}
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to search Red Hat docs: {e}")
        return f"Error: Failed to search documentation - {str(e)}"


async def _fetch_redhat_doc_content(doc_url: str) -> str:
    """Fetch the content of a specific Red Hat documentation page.
    
    Args:
        doc_url: The URL or ID of the documentation to fetch
        
    Returns:
        str: Documentation content
    """
    base_url = _get_api_base_url()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/redhat-docs/fetch/content",
                params={"url": doc_url}
            )
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to fetch Red Hat doc content: {e}")
        return f"Error: Failed to fetch documentation - {str(e)}"


# =============================================================================
# Create Async-Compatible StructuredTools
# =============================================================================

# Inventory Tools
get_ansible_inventory = StructuredTool.from_function(
    coroutine=_get_ansible_inventory,
    name="get_ansible_inventory",
    description="Get details of a specific Ansible inventory by ID"
)

create_ansible_inventory = StructuredTool.from_function(
    coroutine=_create_ansible_inventory,
    name="create_ansible_inventory",
    description="Create a new Ansible inventory with name and optional description"
)

# Job Tools
run_ansible_job = StructuredTool.from_function(
    coroutine=_run_ansible_job,
    name="run_ansible_job",
    description="Run an Ansible job template with optional inventory and extra variables"
)

get_ansible_job_status = StructuredTool.from_function(
    coroutine=_get_ansible_job_status,
    name="get_ansible_job_status",
    description="Get the status of an Ansible job by job ID"
)

get_ansible_job_logs = StructuredTool.from_function(
    coroutine=_get_ansible_job_logs,
    name="get_ansible_job_logs",
    description="Get the logs/output of an Ansible job by job ID"
)

search_ansible_galaxy_collections = StructuredTool.from_function(
    coroutine=_search_ansible_galaxy_collections,
    name="search_ansible_galaxy_collections",
    description="Search for Ansible Galaxy collections by keyword"
)

# EDA Tools
list_eda_activations = StructuredTool.from_function(
    coroutine=_list_eda_activations,
    name="list_eda_activations",
    description="List all Event-Driven Ansible (EDA) activations"
)

get_eda_activation = StructuredTool.from_function(
    coroutine=_get_eda_activation,
    name="get_eda_activation",
    description="Get details of a specific EDA activation by ID"
)

# Playbook Tools
lint_ansible_playbook = StructuredTool.from_function(
    coroutine=_lint_ansible_playbook,
    name="lint_ansible_playbook",
    description="Lint an Ansible playbook for best practices and potential issues"
)

validate_ansible_syntax = StructuredTool.from_function(
    coroutine=_validate_ansible_syntax,
    name="validate_ansible_syntax",
    description="Validate the syntax of an Ansible playbook"
)

# Documentation Tools
search_redhat_docs = StructuredTool.from_function(
    coroutine=_search_redhat_docs,
    name="search_redhat_docs",
    description="Search Red Hat documentation for Ansible-related topics"
)

fetch_redhat_doc_content = StructuredTool.from_function(
    coroutine=_fetch_redhat_doc_content,
    name="fetch_redhat_doc_content",
    description="Fetch the full content of a specific Red Hat documentation article by ID"
)


# All Ansible tools collection
ANSIBLE_TOOLS = [
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
]
