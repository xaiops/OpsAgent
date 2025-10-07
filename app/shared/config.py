"""Configuration management for the agent using Pydantic models."""

import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)


class LLMConfig(BaseModel):
    """LLM configuration for the agent."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    base_url: str = Field(
        default="https://lss-lss.apps.prod.rhoai.rh-aiservices-bu.com/v1/openai/v1",
        description="Base URL for the LLM endpoint"
    )
    api_key: str = Field(
        default="not-needed",
        description="API key for LLM authentication"
    )
    default_model: str = Field(
        default="llama-4-scout-17b-16e-w4a16",
        description="Default model to use for inference"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for model generation"
    )
    max_tokens: int = Field(
        default=2000,
        gt=0,
        description="Maximum tokens for model response"
    )


class StoreConfig(BaseModel):
    """Memory store configuration."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model for semantic search"
    )
    embedding_dims: int = Field(
        default=1536,
        description="Dimensions for embedding vectors"
    )
    search_limit: int = Field(
        default=10,
        description="Default number of memories to retrieve"
    )


class PromptsConfig(BaseModel):
    """Prompts and instructions configuration."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    system_prompt: str = Field(
        default="""You are a helpful and friendly chatbot. Get to know the user! \
Ask questions! Be spontaneous! 
{user_info}

System Time: {time}""",
        description="System prompt template for the agent"
    )
    agent_instructions: str = Field(
        default="",
        description="Additional agent-specific instructions"
    )


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(
        description="Human-readable name for the MCP server"
    )
    url: str = Field(
        description="MCP server URL endpoint"
    )
    transport: str = Field(
        default="streamable_http",
        description="Transport type: streamable_http or stdio"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts on failure"
    )
    enabled: bool = Field(
        default=True,
        description="Whether this server is enabled"
    )
    description: str = Field(
        default="",
        description="Description of what this server provides"
    )


class MCPConfig(BaseModel):
    """Model Context Protocol configuration."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    enabled: bool = Field(
        default=False,
        description="Whether MCP integration is enabled"
    )
    servers: dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="Dictionary of MCP server configurations"
    )


class AgentConfig(BaseModel):
    """Main agent configuration."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(
        default="OpsAgent",
        description="Name of the agent"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM configuration"
    )
    store: StoreConfig = Field(
        default_factory=StoreConfig,
        description="Memory store configuration"
    )
    prompts: PromptsConfig = Field(
        default_factory=PromptsConfig,
        description="Prompts and instructions"
    )
    mcp: MCPConfig = Field(
        default_factory=MCPConfig,
        description="Model Context Protocol configuration"
    )

    @staticmethod
    def _env_override(cfg: "AgentConfig") -> "AgentConfig":
        """Override config values with environment variables if present."""
        # LLM overrides
        cfg.llm.base_url = os.getenv("LLM_BASE_URL", cfg.llm.base_url).rstrip("/")
        cfg.llm.api_key = os.getenv("LLM_API_KEY", cfg.llm.api_key)
        cfg.llm.default_model = os.getenv("LLM_DEFAULT_MODEL", cfg.llm.default_model)
        cfg.llm.temperature = float(os.getenv("LLM_TEMPERATURE", str(cfg.llm.temperature)))
        cfg.llm.max_tokens = int(os.getenv("LLM_MAX_TOKENS", str(cfg.llm.max_tokens)))
        
        # Store overrides
        cfg.store.embedding_model = os.getenv("EMBEDDING_MODEL", cfg.store.embedding_model)
        cfg.store.embedding_dims = int(os.getenv("EMBEDDING_DIMS", str(cfg.store.embedding_dims)))
        
        # Prompts overrides
        cfg.prompts.system_prompt = os.getenv("SYSTEM_PROMPT", cfg.prompts.system_prompt)
        cfg.prompts.agent_instructions = os.getenv("AGENT_INSTRUCTIONS", cfg.prompts.agent_instructions)
        
        # Agent overrides
        cfg.debug = os.getenv("DEBUG", "false").lower() == "true"
        cfg.name = os.getenv("AGENT_NAME", cfg.name)
        
        return cfg

    @classmethod
    def load(cls, path: Optional[str] = None) -> "AgentConfig":
        """Load configuration from YAML file, then apply environment variable overrides.
        
        Args:
            path: Optional path to config file. If not provided, searches in default locations.
            
        Returns:
            AgentConfig instance with values from YAML and environment overrides.
            
        Raises:
            RuntimeError: If config file is not found or invalid.
        """
        if path is None:
            # Search in common locations
            possible_paths = [
                os.getenv("CONFIG_PATH"),
                os.path.join(os.path.dirname(__file__), "../../config.yaml"),
                os.path.join(os.getcwd(), "config.yaml"),
                "config.yaml"
            ]
            
            path = None
            for p in possible_paths:
                if p and os.path.exists(p):
                    path = p
                    break
        
        # If no config file found, use defaults
        if not path or not os.path.exists(path):
            cfg = cls()
            return cls._env_override(cfg)
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            cfg = cls()
            return cls._env_override(cfg)
        
        try:
            cfg = cls(**data)
        except ValidationError as e:
            raise RuntimeError(f"Invalid config at {path}: {e}")
        
        return cls._env_override(cfg)


# Global config instance (loaded once at module level)
_config_instance: Optional[AgentConfig] = None


def get_agent_config() -> AgentConfig:
    """Get the global agent configuration.
    
    Loads configuration once and caches it to avoid blocking I/O in async contexts.
    
    Returns:
        AgentConfig: Loaded configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AgentConfig.load()
    return _config_instance


def get_llm(temperature: Optional[float] = None, max_tokens: Optional[int] = None):
    """Get properly configured LLM instance using configuration.
    
    Args:
        temperature: Optional temperature override (uses config default if not provided)
        max_tokens: Optional max_tokens override (uses config default if not provided)
    
    Returns:
        ChatOpenAI: Configured LLM instance
    """
    from langchain_openai import ChatOpenAI
    
    config = get_agent_config()
    
    return ChatOpenAI(
        base_url=config.llm.base_url,
        api_key=config.llm.api_key,
        model=config.llm.default_model,
        temperature=temperature if temperature is not None else config.llm.temperature,
        max_tokens=max_tokens if max_tokens is not None else config.llm.max_tokens
    )


__all__ = [
    "AgentConfig",
    "LLMConfig",
    "StoreConfig",
    "PromptsConfig",
    "MCPConfig",
    "MCPServerConfig",
    "get_agent_config",
    "get_llm",
]
