"""Shared dependency injection helpers."""
from .core.dispatcher import dispatch_tool_call

# For future use: could yield a dispatcher instance or a tool registry.
async def get_dispatcher():
    return dispatch_tool_call