# Thanatos/shared/models/tool_definition.py

from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class ToolDefinition(BaseModel):
    """
    Schema for a tool (function) that the agent can call.

    This model defines the contract for a single tool that the agent
    (via the LLM brain) can invoke. It is used by:
      - The **LLM brain** to describe available functions to the language model.
      - **Plugins** that register tools with the system.
      - The **dispatcher** that routes tool call requests to the appropriate handler.

    The field ``parameters`` must be a JSON Schema object describing the
    tool's input arguments, following the OpenAI function‑calling format.
    The optional ``required`` list may contain the names of mandatory parameters;
    it can be omitted or set to ``None`` if all parameters are optional.
    """

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for the function parameters
    required: Optional[list] = None

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    def to_openai_schema(self) -> Dict[str, Any]:
        """
        Export the tool definition in OpenAI function‑calling format.

        Returns:
            dict: A dictionary with keys ``type`` and ``function``, where
            ``function`` is a sub‑dictionary containing ``name``, ``description``,
            and ``parameters``. If the optional ``required`` list is set, it is
            merged into the ``parameters`` JSON Schema.
        """
        params = self.parameters.copy()
        if self.required is not None:
            params["required"] = self.required

        function_dict = {
            "name": self.name,
            "description": self.description,
            "parameters": params,
        }
        return {"type": "function", "function": function_dict}

    @classmethod
    def from_openai_schema(cls, data: Dict[str, Any]) -> "ToolDefinition":
        """
        Create a ToolDefinition instance from an OpenAI function‑calling
        description dictionary.

        Args:
            data: A dict with the structure
                ``{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}``.
                The ``parameters`` value may optionally include a ``"required"``
                array, which will be extracted and stored separately.

        Returns:
            ToolDefinition: A new instance populated with the parsed values.
        """
        func = data["function"]
        params = func["parameters"].copy()
        required = params.pop("required", None)
        return cls(
            name=func["name"],
            description=func["description"],
            parameters=params,
            required=required,
        )