"""Adapter factory for creating adapters based on config."""
from app.adapters.openai_adapter import OpenAIAdapter
from app.adapters.search_adapter import SearchAdapter
from app.adapters.factiai_adapter import StubFactiAIAdapter
from app.core.config import get_settings

settings = get_settings()

def get_openai_adapter():
    """Get OpenAI adapter with API key."""
    return OpenAIAdapter(
        api_key=settings.openai_api_key,
        enable_real=settings.enable_real_adapters
    )

def get_search_adapter():
    """Get search adapter with API key."""
    return SearchAdapter(
        api_key=settings.brave_search_api_key,
        enable_real=settings.enable_real_adapters
    )

def get_factiai_adapter():
    """Get Facti.ai adapter (stub for now)."""
    return StubFactiAIAdapter()
