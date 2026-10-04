import httpx
from ..resilience.breaker import CircuitBreaker
from ..resilience.retry import with_retry


class MCPHttpClient:
    def __init__(self, service_name: str, base_url: str, timeout: float = 15.0) -> None:
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.breaker = CircuitBreaker(service_name=service_name)

    async def list_tools(self) -> list[dict[str, object]]:
        self.breaker.check_state()

        async def _request() -> list[dict[str, object]]:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base_url}/tools")
                resp.raise_for_status()
                data = resp.json()
                return data.get("tools", [])  # type: ignore[no-any-return]

        try:
            tools = await with_retry(_request, max_retries=2)
            self.breaker.record_success()
            return tools
        except Exception:
            self.breaker.record_failure()
            raise

    async def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        self.breaker.check_state()

        async def _request() -> dict[str, object]:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/call",
                    json={"name": name, "arguments": arguments},
                )
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]

        try:
            result = await with_retry(_request, max_retries=2)
            self.breaker.record_success()
            return result
        except Exception:
            self.breaker.record_failure()
            raise
