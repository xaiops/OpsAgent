"""
Example: Using MCP with OpsAgent

This is a STANDALONE example showing how to integrate MCP with LangGraph.
It demonstrates the exact pattern used in our production agent.

=== WHAT THIS EXAMPLE SHOWS ===
1. How to connect to an MCP server using MultiServerMCPClient
2. How to dynamically load tools from the MCP server
3. How to create a ReAct agent with those tools
4. How to invoke the agent with a query

=== WHY THIS PATTERN? ===
- No hardcoded tools needed - MCP servers expose tools dynamically
- Same agent code works with different MCP servers
- Tools can be versioned independently of the agent
- Following official LangGraph pattern (production-ready)

=== TRY IT YOURSELF ===
1. Make sure the MCP server is running:
   http://mcp-aap-ansible-proxy-toolhive-system.apps.virt.na-launch.com/mcp
2. Run this script: python examples/mcp_integration.py
3. Watch the agent discover tools and answer the query

References:
- LangGraph MCP Docs: https://langchain-ai.github.io/langgraph/how-tos/mcp/
- langchain-mcp-adapters: https://github.com/langchain-ai/langchain-mcp-adapters
- MCP Protocol: https://modelcontextprotocol.io/
"""
import asyncio
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    """
    Example of connecting to Ansible MCP server and creating an agent.
    
    This demonstrates the 4-step pattern for MCP integration:
    1. Connect to MCP server
    2. Discover tools
    3. Create agent
    4. Run query
    """
    
    # === STEP 1: Connect to MCP server via HTTP ===
    print("🔌 Connecting to MCP server...")
    
    # MultiServerMCPClient handles the protocol communication
    # "streamable_http" means we're connecting to a remote HTTP endpoint
    client = MultiServerMCPClient(
        connections={
            "aap_ansible": {  # Server name (can be any identifier)
                "url": "http://mcp-aap-ansible-proxy-toolhive-system.apps.virt.na-launch.com/mcp",
                "transport": "streamable_http",  # HTTP transport for remote servers
            }
        }
    )

    # === STEP 2: Discover tools from MCP server ===
    print("🔍 Discovering tools from MCP server...")
    
    # get_tools() makes HTTP request to /mcp endpoint
    # MCP server responds with list of available tools
    # langchain-mcp-adapters converts them to LangChain BaseTool format
    tools = await client.get_tools()
    
    print(f"✅ Found {len(tools)} tools:")
    print(f"   {[tool.name for tool in tools][:5]}...")  # Show first 5

    # === STEP 3: Create ReAct agent with MCP tools ===
    print("\n🤖 Creating LangGraph ReAct agent...")
    
    # LLM must support function calling (OpenAI-compatible)
    llm = ChatOpenAI(
        base_url="https://lss-lss.apps.prod.rhoai.rh-aiservices-bu.com/v1/openai/v1",
        api_key="not-needed",
        model="llama-4-scout-17b-16e-w4a16",
        temperature=0.0,  # Deterministic for tool calling
    )
    
    # create_react_agent builds a graph with tool calling built in
    # The LLM will receive all tool schemas and can call them as needed
    agent = create_react_agent(llm, tools=tools)

    # === STEP 4: Run a query ===
    print("\n💬 Running agent query: 'List all Ansible inventories'")
    print("-" * 60)
    
    # Invoke agent with tuple format message (works best with ReAct)
    result = await agent.ainvoke({
        "messages": [("user", "List all Ansible inventories")]
    })

    # === STEP 5: Show the result ===
    print("\n📋 Agent Response:")
    print("-" * 60)
    final_message = result["messages"][-1]
    print(final_message.content)
    print("-" * 60)
    
    print("\n✅ Example complete!")


if __name__ == "__main__":
    asyncio.run(main())

