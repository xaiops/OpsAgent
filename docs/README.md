# OpsAgent Documentation

This directory contains architecture diagrams and documentation for OpsAgent use cases.

## 📊 Architecture Diagrams

### 1. [VM Migration using AI Assistant, AAP, and MTV](./vm-migration-mtv-diagram.md)
**Use Case:** Migrate virtual machines from VMware vSphere to OpenShift Virtualization using Ansible Automation Platform and Migration Toolkit for Virtualization (MTV).

**Key Components:**
- OpsAgent Router → Ansible Agent
- Ansible MCP Server (71 tools)
- Ansible Automation Platform (AAP)
- MTV/Forklift Operator
- VMware vSphere → OpenShift Virtualization

**Diagrams Included:**
- Architecture diagram (component relationships)
- Sequence flow diagram (step-by-step execution)
- Complete workflow explanation
- Sample interactions and error handling

**Example Query:**
```
Migrate VM 'web-server' from VMware to OpenShift using MTV
```

---

### 2. [RHEL VM Provisioning using AI Assistant and Terraform Cloud](./rhel-vm-terraform-diagram.md)
**Use Case:** Deploy new RHEL 9 virtual machines on OpenShift Virtualization using Terraform Cloud with infrastructure-as-code.

**Key Components:**
- OpsAgent Router → Terraform Agent
- Terraform MCP Server (71 tools)
- Terraform Cloud (workspace, variables, runs)
- Git repository (Terraform code)
- OpenShift Virtualization (VirtualMachine CRDs)

**Diagrams Included:**
- Architecture diagram (TFC integration flow)
- Sequence flow diagram (complete run lifecycle)
- Terraform code examples (main.tf, variables.tf, cloud-init)
- Variable management workflow
- Sample interactions and error handling

**Example Query:**
```
Deploy a RHEL 9 VM named "rhel9-demo-vm" in namespace "rhel9-vms" using Terraform Cloud.
Organization: ocp-virt-tfe-demo
Workspace: openshift-cluster-management
All credentials are already configured.
```

---

## 🔍 Viewing Diagrams

### In GitHub/GitLab
Both platforms render mermaid diagrams natively. Simply view the markdown files.

### In VS Code
Install the **Markdown Preview Mermaid Support** extension:
```bash
code --install-extension bierner.markdown-mermaid
```

### In Browser
Use the [Mermaid Live Editor](https://mermaid.live/) to paste and render the diagrams.

### Generate Images
Use the mermaid CLI to generate PNG/SVG images:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i vm-migration-mtv-diagram.md -o vm-migration-mtv.png
mmdc -i rhel-vm-terraform-diagram.md -o rhel-vm-terraform.png
```

---

## 🏗️ Architecture Overview

### OpsAgent System Components

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                       │
│              (Natural Language Queries)                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Router/Coordinator                         │
│         (LLM-powered query analysis)                    │
│  • Keyword detection                                    │
│  • Context maintenance                                  │
│  • Agent selection                                      │
└────────┬────────────┬────────────┬─────────────────────┘
         │            │            │
    ┌────▼───┐   ┌───▼────┐  ┌───▼────────┐
    │Ansible │   │OpenShift│  │ Terraform  │
    │ Agent  │   │ Agent   │  │  Agent     │
    └────┬───┘   └───┬─────┘  └───┬────────┘
         │            │            │
┌────────▼────────────▼────────────▼────────────────────┐
│           MCP Integration Layer                       │
│  • Ansible MCP (71 tools)                            │
│  • OpenShift MCP (45 tools)                          │
│  • Terraform MCP (71 tools)                          │
└────────┬────────────┬────────────┬────────────────────┘
         │            │            │
    ┌────▼───┐   ┌───▼────┐  ┌───▼────────┐
    │  AAP   │   │OpenShift│  │  Terraform │
    │Controller│  │   API   │  │   Cloud    │
    └────────┘   └────────┘  └────────────┘
```

### Agent Capabilities

| Agent | MCP Tools | Primary Use Cases |
|-------|-----------|-------------------|
| **Ansible Agent** | 71 | Job templates, workflows, MTV migrations, EDA |
| **OpenShift Agent** | 45 | Pods, namespaces, VMs, deployments, projects |
| **Terraform Agent** | 71 | Workspaces, runs, variables, IaC deployments |

### Routing Logic

The Router uses LLM-powered keyword analysis to route queries:

1. **"migrate", "VMware", "MTV"** → Ansible Agent
2. **"OpenShift", "pod", "namespace"** → OpenShift Agent  
3. **"Terraform", "deploy VM using Terraform"** → Terraform Agent
4. **General/ambiguous** → OpsAgent (fallback)

**Context Awareness:** Router maintains workflow context to prevent incorrect agent switching mid-execution.

---

## 🔐 Security Considerations

### Credentials Management

**Ansible Agent:**
- AAP API token stored in environment: `AAP_API_TOKEN`
- MCP server configuration

**OpenShift Agent:**
- Service account token: `KUBE_TOKEN`
- Or kubeconfig file: `KUBECONFIG`

**Terraform Agent:**
- Terraform Cloud API token: `TF_API_TOKEN`
- OpenShift credentials stored as workspace variables:
  - `KUBE_HOST` (environment variable)
  - `KUBE_TOKEN` (sensitive environment variable)
  - `KUBE_CLUSTER_CA_CERT_DATA` (environment variable, optional)

### Best Practices

1. **Never commit credentials to Git**
   - `config.yaml` is in `.gitignore`
   - Use environment variables or secret managers
   
2. **Use least-privilege service accounts**
   - AAP: User with job execution permissions
   - OpenShift: Service account with VM management RBAC
   - Terraform: Token with workspace management permissions

3. **Rotate credentials regularly**
   - Service account tokens
   - API keys
   - SSH keys

---

## 🚀 Quick Start

### Run OpsAgent

```bash
cd /Users/raghurambanda/playground/OpsAgent-1
source venv/bin/activate
langgraph dev
```

### Access UI

```
Open browser: http://localhost:8123
```

### Example Queries

**VM Migration:**
```
Migrate VM 'database-server' from VMware to OpenShift using MTV
```

**VM Provisioning:**
```
Deploy a RHEL 9 VM named "app-server" using Terraform Cloud in organization ocp-virt-tfe-demo
```

**Check Status:**
```
What's the status of migration job 156?
```

```
Check status of Terraform run run-T8yKe3taG7tymoco
```

---

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Ansible Automation Platform](https://www.ansible.com/products/automation-platform)
- [OpenShift Virtualization](https://docs.openshift.com/container-platform/latest/virt/about_virt/about-virt.html)
- [Migration Toolkit for Virtualization](https://docs.openshift.com/container-platform/latest/migration_toolkit_for_virtualization/about-mtv.html)
- [Terraform Cloud](https://www.terraform.io/cloud)
- [KubeVirt](https://kubevirt.io/)

---

## 🐛 Troubleshooting

### Issue: Agent not routing correctly

**Solution:** Check router keywords in `config.yaml`, ensure query contains relevant keywords.

### Issue: MCP server connection failed

**Solution:** Check MCP server configuration in `config.yaml`, verify API endpoints and tokens.

### Issue: Terraform run stuck in "planned" state

**Solution:** Workspace has `auto_apply: false` - requires manual approval in Terraform Cloud UI.

### Issue: VM migration failed

**Solution:** Check MTV/Forklift logs in OpenShift, verify network/storage mappings are configured.

---

## 📝 Contributing

To add new diagrams or documentation:

1. Create a new markdown file in `docs/`
2. Use mermaid syntax for diagrams
3. Include:
   - Architecture diagram
   - Sequence diagram
   - Component details
   - Sample interactions
   - Error handling
4. Update this README with a link to your diagram

---

**Last Updated:** November 6, 2024  
**Version:** 1.0.0

