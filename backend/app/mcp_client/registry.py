from collections.abc import Callable, Coroutine
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

from .client import MCPHttpClient
from ..core.config import get_settings


def create_langchain_tool(
    client: MCPHttpClient,
    tool_def: dict[str, object],
) -> StructuredTool:
    name = str(tool_def.get("name", "unnamed_tool"))
    description = str(tool_def.get("description", ""))
    input_schema = tool_def.get("input_schema", {})

    fields: dict[str, tuple[type, object]] = {}
    if isinstance(input_schema, dict):
        properties = input_schema.get("properties", {})
        required = set(input_schema.get("required", []))
        if isinstance(properties, dict):
            for prop_name, prop_data in properties.items():
                is_req = prop_name in required
                default_val = ... if is_req else None
                fields[prop_name] = (str, default_val)

    args_schema = create_model(f"{name}_schema", **fields)  # type: ignore[call-overload]

    async def _tool_func(**kwargs: object) -> dict[str, object]:
        return await client.call_tool(name=name, arguments=kwargs)

    return StructuredTool.from_function(
        coroutine=_tool_func,
        name=name,
        description=description,
        args_schema=args_schema,
    )


class MCPRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self.flight_client = MCPHttpClient("flight_service", settings.MCP_FLIGHT_URL)
        self.weather_client = MCPHttpClient("weather_service", settings.MCP_WEATHER_URL)
        self.places_client = MCPHttpClient("places_service", settings.MCP_PLACES_URL)

    async def get_flight_tools(self) -> list[StructuredTool]:
        tools = await self.flight_client.list_tools()
        return [create_langchain_tool(self.flight_client, t) for t in tools]

    async def get_weather_tools(self) -> list[StructuredTool]:
        tools = await self.weather_client.list_tools()
        return [create_langchain_tool(self.weather_client, t) for t in tools]

    async def get_places_tools(self) -> list[StructuredTool]:
        tools = await self.places_client.list_tools()
        return [create_langchain_tool(self.places_client, t) for t in tools]
