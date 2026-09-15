"""Provider adapters package.

Exposes a provider-keyed registry used by the gateway to pick the
adapter matching a model's provider (see gateway._adapter_for).
"""

from ..adapter_base import BaseAdapter
from .llamacpp import LlamaCppAdapter
from .ollama import OllamaAdapter
from .vllm import VllmAdapter

ADAPTERS: dict[str, BaseAdapter] = {}

__all__ = [
    "ADAPTERS",
    "BaseAdapter",
    "LlamaCppAdapter",
    "OllamaAdapter",
    "VllmAdapter",
]
