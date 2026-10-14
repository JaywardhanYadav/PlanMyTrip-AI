from .client import MCPHttpClient
from ..core.config import get_settings


class MCPRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self.flight_client = MCPHttpClient("flight_service", settings.MCP_FLIGHT_URL)
        self.weather_client = MCPHttpClient("weather_service", settings.MCP_WEATHER_URL)
        self.places_client = MCPHttpClient("places_service", settings.MCP_PLACES_URL)
