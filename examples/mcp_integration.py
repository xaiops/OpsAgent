"""
Example: Using MCP with OpsAgent

This example demonstrates how to use the Model Context Protocol (MCP)
integration with OpsAgent following the official LangGraph pattern.

References:
- LangGraph MCP Docs: https://langchain-ai.github.io/langgraph/how-tos/mcp/
- langchain-mcp-adapters: https://github.com/langchain-ai/langchain-mcp-adapters
"""
import asyncio
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    """Example of connecting to Ansible MCP server and creating an agent."""
    
    # 1. Create MCP client with HTTP connection to AAP Ansible server
    print("Connecting to MCP server...")
    
    client = MultiServerMCPClient(
        connections={
            "aap_ansible": {
                "url": "http://mcp-aap-ansible-proxy-toolhive-system.apps.virt.na-launch.com/mcp",
                "transport": "streamable_http",
            }
        }
    )

    # 2. Load tools from the MCP server
    print("Loading tools from MCP server...")
    tools = await client.get_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")

    # 3. Create a LangGraph agent that can use MCP tools
    print("Creating LangGraph agent...")
    llm = ChatOpenAI(
        base_url="https://lss-lss.apps.prod.rhoai.rh-aiservices-bu.com/v1/openai/v1",
        api_key="not-needed",
        model="llama-4-scout-17b-16e-w4a16"
    )
    agent = create_react_agent(llm, tools=tools)

    # 4. Run a query
    print("\n--- Running agent query ---")
    result = await agent.ainvoke({
        "messages": [("user", "List all Ansible inventories")]
    })

    print("\n--- Agent Response ---")
    final_message = result["messages"][-1]
    print(final_message.content)


if __name__ == "__main__":
    asyncio.run(main())

