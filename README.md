# OpsAgent

A production-ready LangGraph agent for Ansible Automation Platform operations with dynamic MCP (Model Context Protocol) integration. Built for scalability, clean architecture, and enterprise deployment.

## 🎯 Overview

OpsAgent is a conversational AI agent that connects to Ansible Automation Platform through MCP servers, providing natural language access to 46+ operational tools without hardcoded integrations.

**Key Features:**
-  **Pure MCP Integration**: Dynamically loads 46 tools from MCP servers
-  **Production-Grade**: Clean architecture, no hardcoded tool definitions
-  **Enterprise Ready**: OpenShift/Kubernetes deployment with proper security
-  **Scalable Design**: Multi-agent routing architecture for future expansion
-  **LLM Agnostic**: Works with OpenAI, Anthropic, Llama, or any OpenAI-compatible API

## 🏗️ Architecture

### High-Level Flow

```
User Query
    ↓
LangGraph ReAct Agent (47 tools)
    ├── 46 tools via MCP Client (dynamic discovery)
    └── 1 memory tool (agent-side)
        ↓
    MCP Client (langchain-mcp-adapters)
        ↓
    MCP Server (Ansible AAP)
        ↓
    Ansible Automation Platform API
```

### Component Architecture

```
┌─────────────────────────────────────┐
│   Routing Coordinator (Entry Point) │
│   Routes to appropriate agent        │
└──────────────┬──────────────────────┘
               │
       ┌───────▼─────────┐
       │   ops_agent     │
       │   (Active)      │
       │                 │
       │ 47 Tools:       │
       │ - 46 MCP tools  │ ← Dynamically loaded from MCP server
       │ - 1 Memory tool │ ← Agent-side functionality
       └─────────────────┘
```

**Why MCP?**
- **Dynamic Tool Discovery**: No hardcoded tool definitions
- **Single Source of Truth**: MCP server defines all Ansible tools
- **Scalable**: Add new tools without code changes
- **Maintainable**: Tool updates happen at the MCP server level

### Directory Structure

```
app/
├── graph.py                    # Main entry point (creates coordinator)
├── routing/
│   └── coordinator.py          # Routes queries to agents
├── agents/
│   └── ops_agent/              # Ansible operations agent
│       ├── agent.py            # ReAct agent with MCP tools
│       └── tools/
│           ├── __init__.py     # Agent-side tools only
│           └── memory.py       # Memory management (agent-side)
├── mcp_integration/            # MCP client infrastructure
│   ├── client.py               # MultiServerMCPClient wrapper
│   └── adapters/
│       └── aap_adapter.py      # Future: AAP-specific MCP adapter
└── shared/                     # Shared utilities
    ├── config.py               # Configuration management
    ├── state.py                # State schemas
    └── utils.py                # Helper functions
```

**Note**: No `ansible_tools.py` - all Ansible tools come from MCP server!

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Access to an MCP server (or disable MCP for testing)
- LLM endpoint (OpenAI, Anthropic, LlamaStack, etc.)

### Installation

1. **Clone and setup:**

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

2. **Configure environment:**

```bash
# Copy environment template (optional)
cp env.example .env

# Edit config.yaml with your settings
```

3. **Configure MCP and LLM in `config.yaml`:**

```yaml
# LLM Configuration
llm:
  base_url: "https://your-llm-endpoint.com/v1"
  api_key: "your-api-key"
  default_model: "llama-4-scout-17b-16e-w4a16"
  temperature: 0.0  # Zero for deterministic tool calling
  max_tokens: 1200

# MCP Configuration
mcp:
  enabled: true
  servers:
    aap_ansible:
      name: "Red Hat AAP Ansible"
      url: "http://your-mcp-server.com/mcp"
      transport: "streamable_http"
      enabled: true
```

4. **Run the agent:**

```bash
# Start LangGraph dev server
langgraph dev

# Access at:
# - API: http://127.0.0.1:2024
# - Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

## 🔧 Configuration

### Main Configuration (`config.yaml`)

```yaml
# Agent metadata
name: "OpsAgent"
debug: false

# LLM Configuration
llm:
  base_url: "https://lss-lss.apps.prod.rhoai.rh-aiservices-bu.com/v1/openai/v1"
  api_key: "not-needed"
  default_model: "llama-4-scout-17b-16e-w4a16"
  temperature: 0.0  # Critical: 0.0 for reliable tool calling
  max_tokens: 1200

# Memory Store
store:
  embedding_model: "text-embedding-3-small"
  embedding_dims: 1536
  search_limit: 10

# System Prompt (Production-grade, tool-agnostic)
prompts:
  system_prompt: |
    You are an Ansible automation assistant with access to tools 
    for Ansible Automation Platform operations.
    
    ## CRITICAL RULES:
    1. When users ask operational questions, ALWAYS call a tool first
    2. NEVER respond with "No data" - you have tools to get real data
    3. Look at available tool descriptions to find the right one
    4. Format results clearly for the user
    5. Call tools ONCE per query
    
    Examples:
    - User: "List all inventories" → Call list_inventories
    - User: "Show job status" → Call job_status
    
    USE THE TOOLS!

# MCP (Model Context Protocol) Configuration
mcp:
  enabled: true  # Set to false to disable MCP
  servers:
    aap_ansible:
      name: "Red Hat AAP Ansible"
      url: "http://mcp-aap-ansible-proxy-toolhive-system.apps.virt.na-launch.com/mcp"
      transport: "streamable_http"
      timeout: 30
      enabled: true
```

### Environment Overrides (`.env` or env vars)

```bash
# LLM Configuration (overrides config.yaml)
LLM_BASE_URL=https://your-endpoint.com/v1
LLM_API_KEY=your-key
LLM_DEFAULT_MODEL=gpt-4
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=1200

# Agent Configuration
AGENT_NAME=OpsAgent
DEBUG=false
```

**Priority:** Environment variables > `config.yaml` > defaults

## 🤖 MCP Integration

### How MCP Works

The agent uses [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) following the [official LangGraph MCP pattern](https://langchain-ai.github.io/langgraph/how-tos/mcp/).

**At startup:**

1. Agent connects to configured MCP servers using `MultiServerMCPClient`
2. MCP client discovers available tools from the server (46 tools)
3. Tools are converted to LangChain format automatically
4. Agent loads tools into ReAct agent
5. **Result: 47 tools total** (46 from MCP + 1 memory tool)

**Implementation:**

```python
# app/mcp_integration/client.py
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "aap_ansible": {
        "url": "http://mcp-server.com/mcp",
        "transport": "streamable_http",
    }
})

# Dynamically discover tools
tools = await client.get_tools()  # Returns 46 LangChain tools

# Agent uses these tools automatically
```

### Available Tools (from MCP Server)

**46 tools dynamically loaded from MCP:**

| Category | Tools | Examples |
|----------|-------|----------|
| **Inventories** | 13 tools | list_inventories, get_inventory, create_inventory, delete_inventory, list_inventory_sources, create_inventory_source, update_inventory_source, sync_inventory_source, etc. |
| **Jobs** | 4 tools | run_job, job_status, job_logs, list_job_templates |
| **Projects** | 6 tools | list_projects, get_project, create_project, update_project, list_project_updates, get_project_update_logs |
| **Hosts** | 7 tools | list_hosts, get_host_details, get_host_facts, add_host_to_inventory, update_host, delete_host, get_failed_hosts |
| **Groups** | 6 tools | list_groups, get_group_details, create_group, add_host_to_group, remove_host_from_group, get_host_groups |
| **Ad-hoc Commands** | 3 tools | run_adhoc_command, get_adhoc_command_status, get_adhoc_command_output |
| **Galaxy** | 5 tools | search_galaxy_collections, search_galaxy_roles, get_collection_details, get_role_details, suggest_ansible_content |
| **Other** | 2 tools | list_jobs, list_recent_jobs |

**1 agent-side tool:**
- `upsert_memory` - User preference and context management

### Enable/Disable MCP

**Enable MCP** (recommended for production):
```yaml
# config.yaml
mcp:
  enabled: true
  servers:
    aap_ansible:
      url: "http://your-mcp-server.com/mcp"
      enabled: true
```

**Disable MCP** (fallback mode):
```yaml
# config.yaml
mcp:
  enabled: false
```

When MCP is disabled, only the memory tool is available (1 tool total).

## 💬 Example Interactions

```
User: "List all Ansible inventories"

Agent: [Calls list_inventories tool via MCP]

Response:
The following Ansible inventories are available:

1. Demo Inventory (ID: 1)
   - Organization: Default
   - Description: Localhost inventory for VM operations jobs
   - Total Hosts: 1

2. ocp-virt (ID: 2)
   - Organization: Default
   - Description: Inventory for VM operations jobs
   - Total Hosts: 35

3. stress-vm (ID: 3)
   - Total Hosts: 1

4. test-host-in-virt (ID: 4)
   - Organization: SNOW
   - Total Hosts: 1
```

```
User: "Show me recent jobs from the last 24 hours"

Agent: [Calls list_recent_jobs tool via MCP]

Response:
Here are the recent jobs from the last 24 hours:
...
```

```
User: "Run job template 5 with extra vars"

Agent: [Calls run_job tool via MCP]

Response:
Job started successfully!
- Job ID: 123
- Status: Running
...
```

## 🚢 Production Deployment

### Quick Deploy

```bash
# 1. Build container image
./build-and-push.sh v1.0.0

# 2. Deploy to OpenShift
./deploy-to-openshift.sh ops-agent v1.0.0
```

### Container Build

Build and push to Quay.io:

```bash
# Build (includes langchain-mcp-adapters)
podman build -f Containerfile -t quay.io/rbrhssa/ops-agents:v1.0.0 .

# Push to registry
podman push quay.io/rbrhssa/ops-agents:v1.0.0

# Run locally
podman run -p 2024:2024 \
  -e LLM_BASE_URL=https://your-llm.com/v1 \
  -e LLM_API_KEY=your-key \
  quay.io/rbrhssa/ops-agents:v1.0.0
```

**Base Image:** Red Hat UBI 9 with Python 3.11  
**Dependencies:** Includes `langchain-mcp-adapters` for MCP support

### OpenShift Deployment

Complete deployment manifests in `deploy/`:

```bash
# 1. Create namespace
oc new-project ops-agent

# 2. Create secrets
oc create secret generic ops-agent-secrets \
  --from-literal=llm-api-key='your-key' \
  --from-literal=llm-base-url='https://your-endpoint.com/v1'

# 3. Apply manifests
oc apply -f deploy/configmap.yaml
oc apply -f deploy/deployment.yaml

# 4. Verify
oc get pods -n ops-agent
oc logs -f deployment/ops-agent -n ops-agent

# Look for in logs:
# " Using MCP tools exclusively"
# "Total tools available: 47"

# 5. Get route URL
oc get route ops-agent -o jsonpath='{.spec.host}'
```

**Deployment includes:**
- ConfigMap with config.yaml
- Deployment with 1 replica
- Service (ClusterIP)
- Route (HTTPS with edge termination)
- ServiceAccount
- Health checks (liveness, readiness, startup)

See [DEPLOYMENT_READY.md](DEPLOYMENT_READY.md) for detailed guide.

## 🧪 Testing

### Test MCP Connection

```bash
# Test MCP server connectivity
python test_mcp.py

# Expected output:
#  Successfully loaded 46 tools from MCP server
# 🎉 MCP integration test successful!
```

### Test Agent Locally

```bash
# Start dev server
langgraph dev

# Test query in Studio:
"List all inventories"

# Expected:
# - Agent calls list_inventories tool
# - Returns formatted inventory list
```

### Verify Tool Loading

```bash
# Check startup logs
langgraph dev 2>&1 | grep -E "MCP|tools"

# Expected output:
# MCP is enabled - loading tools from MCP servers...
# Successfully loaded 46 tools from MCP servers
#  Using MCP tools exclusively (not loading hardcoded tools)
# Added 1 agent-side tool(s)
# Total tools available: 47
```

## 🔍 Troubleshooting

### Agent Not Calling Tools

**Symptom:** Agent responds with text instead of calling tools.

**Solutions:**
1.  Check `temperature: 0.0` in config (not 0.1 or higher)
2.  Verify system prompt has aggressive tool-calling instructions
3.  Test with GPT-4 to rule out model capability issues
4.  Check logs for tool binding errors

**Revert to aggressive prompt if needed:**
See production backup strategy in deployment guide.

### MCP Connection Errors

**Symptom:** "Failed to load MCP tools" in logs.

**Solutions:**
1.  Verify MCP server URL is accessible
2.  Check network connectivity (firewall, DNS)
3.  Confirm MCP server is running and healthy
4.  Set `mcp.enabled: false` to test without MCP

### Missing Tools

**Symptom:** Only 1 tool available instead of 47.

**Solutions:**
1.  Check `mcp.enabled: true` in config
2.  Verify MCP server configuration is correct
3.  Review startup logs for MCP initialization errors
4.  Test MCP server independently with `test_mcp.py`

## 🏗️ Architecture Details

### Multi-Agent Design

The system uses a **routing coordinator pattern** for scalability:

```python
# app/routing/coordinator.py
workflow = StateGraph(RoutingState)

# Add router
workflow.add_node("router", routing_classifier)

# Add agents
workflow.add_node("ops_agent", create_agent_wrapper("ops_agent", ops_agent))

# Future: Add more agents
# workflow.add_node("playbook_dev", create_agent_wrapper("playbook_dev", playbook_agent))

# Route based on query
workflow.add_conditional_edges("router", route_to_agent, {
    "ops_agent": "ops_agent",
    # Future routing options
})
```

**Benefits:**
- Single entry point for all queries
- Easy to add new specialized agents
- Each agent has its own tools and state
- Supports 30+ agents without performance issues

### Adding New Agents

1. Create agent module: `app/agents/my_agent/agent.py`
2. Register in coordinator: `workflow.add_node("my_agent", ...)`
3. Update routing logic in `RouteClassification`

**That's it!** The infrastructure handles everything else.

## 📊 Monitoring

### Health Checks

```bash
# Check if agent is healthy
curl http://localhost:2024/ok

# Check via OpenShift
oc get pods -n ops-agent
oc describe pod <pod-name> -n ops-agent
```

### Logs

```bash
# Local development
langgraph dev

# OpenShift
oc logs -f deployment/ops-agent -n ops-agent

# Filter for important events
oc logs -f deployment/ops-agent -n ops-agent | grep -E "MCP|tools|ERROR"
```

### Key Log Messages

```
 Successfully loaded 46 tools from MCP servers
 Using MCP tools exclusively (not loading hardcoded tools)
Total tools available: 47
OpsAgent (ReAct) created successfully
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run linter and tests (`make lint test`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- MCP integration via [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- Follows [official LangGraph MCP pattern](https://langchain-ai.github.io/langgraph/how-tos/mcp/)
- Red Hat Ansible Automation Platform integration

---

**Ready for production deployment!** 🚀

For detailed deployment guide, see [DEPLOYMENT_READY.md](DEPLOYMENT_READY.md).
