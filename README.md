# OpsAgent

A production-ready, multi-agent LangGraph system for operations automation and infrastructure management. Built with a scalable routing architecture that supports multiple specialized agents working together through a single entry point.

## Features

🚀 **Multi-Agent Routing Architecture**
- Single coordinator entry point with intelligent routing
- Easily extensible to 30+ specialized agents
- Each agent focuses on specific operational domains

🔧 **Ansible Automation Platform Integration**
- 13 production-ready tools for AAP operations
- Inventory management, job execution, and monitoring
- Event-Driven Ansible (EDA) support
- Playbook linting and syntax validation
- Red Hat documentation search

⚙️ **Configuration-Driven Design**
- YAML-based configuration for all settings
- Environment variable overrides
- Support for any LLM provider (OpenAI, Anthropic, LlamaStack, etc.)
- Hot-reloadable prompts and instructions

🧠 **Built-in Memory Management**
- User-scoped conversation memory
- Semantic search across past interactions
- Context-aware responses

## Architecture

```
┌─────────────────────────────────────┐
│   Routing Coordinator (Entry Point) │
│   - Routes requests to agents        │
│   - Manages agent lifecycle          │
└──────────────┬──────────────────────┘
               │
               ├─────────────────────────────────┐
               │                                 │
       ┌───────▼─────────┐           ┌──────────▼──────────┐
       │   ops_agent     │           │  Future Agents      │
       │   (Active)      │           │  (Playbook Dev,     │
       │                 │           │   Infrastructure,   │
       │ 14 Tools:       │           │   Security, etc.)   │
       │ - Ansible AAP   │           └─────────────────────┘
       │ - EDA           │
       │ - Linting       │
       │ - Docs Search   │
       │ - Memory        │
       └─────────────────┘
```

### Directory Structure

```
app/
├── graph.py                    # Main entry point
├── routing/
│   └── coordinator.py          # Multi-agent router
├── agents/
│   └── ops_agent/              # Operations agent
│       ├── agent.py            # Agent logic
│       └── tools/              # Agent-specific tools
│           ├── ansible_tools.py
│           └── memory.py
├── mcp/                        # MCP adapter pattern
│   ├── client.py
│   └── adapters/
└── shared/                     # Shared utilities
    ├── config.py               # Configuration management
    ├── state.py                # State schemas
    └── utils.py
```

## Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment recommended

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
# Copy environment template
cp env.example .env

# Edit .env with your settings
# At minimum, configure your LLM endpoint
```

3. **Configure agent:**

Edit `config.yaml` to customize:
- LLM provider and model
- Ansible API endpoint
- Agent prompts and instructions
- Memory settings

4. **Run the agent:**

```bash
# Start LangGraph dev server
langgraph dev

# Access at http://127.0.0.1:2024
# Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

## Configuration

### Main Configuration (`config.yaml`)

```yaml
# Agent metadata
name: "OpsAgent"
debug: false

# LLM Configuration
llm:
  base_url: "https://your-llm-endpoint.com/v1/openai/v1"
  api_key: "your-api-key"
  default_model: "llama-4-scout-17b-16e-w4a16"
  temperature: 0.1          # Low temp for reliable tool calling
  max_tokens: 1200

# Memory Store
store:
  embedding_model: "text-embedding-3-small"
  embedding_dims: 1536
  search_limit: 10

# Prompts (fully customizable)
prompts:
  system_prompt: |
    You are an expert operations assistant...
  
  agent_instructions: |
    - Always use tools for Ansible operations
    - Provide clear, actionable responses
```

### Environment Overrides (`.env`)

```bash
# LLM Configuration
LLM_BASE_URL=https://your-endpoint.com/v1
LLM_API_KEY=your-key
LLM_DEFAULT_MODEL=gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1200

# Store Configuration
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMS=1536

# Agent Configuration
AGENT_NAME=OpsAgent
DEBUG=true
```

**Priority:** Environment variables > `config.yaml` > defaults

## Ansible Automation Platform

### Available Tools

#### Core Operations
| Tool | Description |
|------|-------------|
| `list_ansible_inventories` | List all inventories |
| `get_ansible_inventory` | Get inventory details |
| `create_ansible_inventory` | Create new inventory |
| `run_ansible_job` | Execute job template |
| `get_ansible_job_status` | Check job status |
| `get_ansible_job_logs` | Retrieve job logs |
| `search_ansible_galaxy_collections` | Search Galaxy collections |

#### Event-Driven Ansible
| Tool | Description |
|------|-------------|
| `list_eda_activations` | List EDA activations |
| `get_eda_activation` | Get activation details |

#### Linting & Validation
| Tool | Description |
|------|-------------|
| `lint_ansible_playbook` | Lint playbooks for best practices |
| `validate_ansible_syntax` | Quick syntax validation |

#### Documentation
| Tool | Description |
|------|-------------|
| `search_redhat_docs` | Search Red Hat docs |
| `fetch_redhat_doc_content` | Fetch specific doc pages |

### Example Interactions

```
User: "What inventories are available?"
Agent: [Calls list_ansible_inventories]
       
       The following Ansible inventories are available:
       
       1. Demo Inventory (ID: 1)
          - Organization: Default
          - Total Hosts: 1
       
       2. ocp-virt (ID: 2)
          - Organization: Default  
          - Total Hosts: 23

User: "Show me the details of inventory 2"
Agent: [Calls get_ansible_inventory with ID 2]
       
       Inventory: ocp-virt
       Description: Inventory for VM operations jobs
       ...

User: "Lint this playbook: [paste YAML]"
Agent: [Calls lint_ansible_playbook]
       
       Found 3 issues:
       - Line 12: Use fully qualified collection names
       ...
```

### Configuration

Update the API endpoint in `app/agents/ops_agent/tools/ansible_tools.py`:

```python
def _get_api_base_url() -> str:
    return "http://your-aap-endpoint.com"
```

Or set via environment variable:

```bash
ANSIBLE_API_BASE_URL=http://your-aap-endpoint.com
```

## Multi-Agent System

### Current Agents

- **ops_agent**: Handles Ansible operations, EDA, linting, and documentation

### Adding New Agents

The architecture is designed for easy agent addition:

1. **Create agent module:**

```python
# app/agents/playbook_dev/agent.py
def create_playbook_dev_agent():
    """Create specialized playbook development agent."""
    # Define tools, prompts, and logic
    return compiled_graph
```

2. **Register in coordinator:**

```python
# app/routing/coordinator.py
from agents.playbook_dev import create_playbook_dev_agent

# Add to routing options
workflow.add_node("playbook_dev", 
                  create_agent_wrapper("playbook_dev", 
                                      create_playbook_dev_agent()))

# Update routing logic
workflow.add_conditional_edges(
    "router",
    route_to_agent,
    {
        "ops_agent": "ops_agent",
        "playbook_dev": "playbook_dev",  # New route
    }
)
```

3. **Update routing classification:**

```python
# app/routing/coordinator.py
class RouteClassification(BaseModel):
    agent: Literal["ops_agent", "playbook_dev"] = Field(...)
```

The system supports **30+ agents** without performance degradation. Each agent:
- Has its own state and tools
- Can be independently developed and tested
- Shares common infrastructure (config, state, utils)

## LLM Provider Support

### LlamaStack / vLLM (Default)

```yaml
llm:
  base_url: "https://lss.apps.prod.rhoai.rh-aiservices-bu.com/v1/openai/v1"
  api_key: "not-needed"
  default_model: "llama-4-scout-17b-16e-w4a16"
  temperature: 0.1
  max_tokens: 1200
```

**Note:** LlamaStack does not support `SystemMessage` with tool calling. The agent automatically prepends system instructions to user messages as a workaround.

### OpenAI

```yaml
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-your-key"
  default_model: "gpt-4"
  temperature: 0.1
  max_tokens: 1200
```

### Anthropic

```yaml
llm:
  base_url: "https://api.anthropic.com/v1"
  api_key: "your-anthropic-key"
  default_model: "claude-3-5-sonnet-20240620"
  temperature: 0.1
  max_tokens: 1200
```

## Development

### Run Tests

```bash
# Unit tests
make test

# Integration tests (requires running agent)
make integration-test

# All tests
make test-all
```

### Run Linter

```bash
make lint
```

### Format Code

```bash
make format
```

## MCP (Model Context Protocol) Pattern

The agent includes infrastructure for MCP integration, allowing dynamic tool loading from external servers:

```yaml
mcp:
  servers:
    aap_ansible:
      name: "AAP Ansible MCP"
      url: "http://mcp-server.com/mcp"
      transport: "streamable_http"
      timeout: 30
      enabled: false  # Currently using direct LangChain tools
```

The MCP adapter pattern is ready for when MCP servers become available.

## Production Deployment

### Container Build

The project includes a production-ready `Containerfile` using Red Hat UBI 9 with Python 3.11:

```bash
# Build container image
podman build -f Containerfile -t quay.io/rbrhssa/ops-agents:latest .

# Push to registry
podman push quay.io/rbrhssa/ops-agents:latest

# Run locally
podman run -p 2024:2024 \
  -e LLM_BASE_URL=https://your-llm.com/v1 \
  -e LLM_API_KEY=your-key \
  quay.io/rbrhssa/ops-agents:latest
```

### OpenShift Deployment

Complete OpenShift manifests are provided in the `deploy/` directory:

```bash
# Create project
oc new-project ops-agent

# Create secrets
oc create secret generic ops-agent-secrets \
  --from-literal=llm-api-key='your-key' \
  --from-literal=llm-base-url='https://your-endpoint.com/v1'

# Deploy application
oc apply -f deploy/configmap.yaml
oc apply -f deploy/deployment.yaml

# Get route URL
oc get route ops-agent -o jsonpath='{.spec.host}'
```

See [deploy/README.md](deploy/README.md) for complete deployment guide.

### LangGraph Cloud

Deploy to [LangGraph Cloud](https://langchain-ai.github.io/langgraph/cloud/):

```bash
langgraph deploy
```

### Environment Variables (Production)

```bash
# Required
LLM_BASE_URL=https://your-llm.com/v1
LLM_API_KEY=your-production-key
LLM_DEFAULT_MODEL=your-model

# Ansible
ANSIBLE_API_BASE_URL=https://your-aap.com

# Optional
DEBUG=false
AGENT_NAME=OpsAgent-Prod
```

## Troubleshooting

### Agent Not Calling Tools

**Symptom:** Agent responds with text instead of calling tools.

**Solution:**
1. Check `llm.temperature` in `config.yaml` (should be 0.1 for reliable tool calling)
2. Ensure prompts clearly instruct tool usage
3. For LlamaStack: Verify system prompt workaround is enabled

### Connection Errors

**Symptom:** HTTP errors when calling Ansible API.

**Solution:**
1. Verify `ANSIBLE_API_BASE_URL` is correct
2. Check network connectivity to AAP endpoint
3. Review timeout settings in tool definitions

### Memory Not Persisting

**Symptom:** Agent doesn't remember past conversations.

**Solution:**
1. Check store configuration in `config.yaml`
2. Ensure LangGraph store is properly initialized
3. Use same `user_id` across threads in API calls

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run linter and tests (`make lint test`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Ansible Automation Platform integration
- OpenAI-compatible LLM support