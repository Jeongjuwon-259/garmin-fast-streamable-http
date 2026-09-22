"""Garmin Running MCP Server."""

import os
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from garmin_mcp.auth import create_client
from garmin_mcp.client import GarminClient

mcp = FastMCP("garmin-mcp")

_client: GarminClient | None = None


def get_client() -> GarminClient:
    """Get the authenticated Garmin client (lazy initialization)."""
    global _client
    if _client is None:
        garmin = create_client()
        _client = GarminClient(garmin)
    return _client


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Liveness/readiness probe for streamable-http deployments.

    Deliberately does NOT touch Garmin (no login, no API call) — this is a
    fast "is the process up and serving requests" check, not a check that
    Garmin auth is valid. It also does not require auth itself, so it's
    safe to leave open even behind an auth-gated deployment.
    """
    from starlette.responses import JSONResponse

    from garmin_mcp.auth import _has_saved_tokens

    return JSONResponse({
        "status": "ok",
        "server": "garmin-mcp",
        "time": datetime.now(timezone.utc).isoformat(),
        "garmin_tokens_present": _has_saved_tokens(),
    })


# Register all tools
from garmin_mcp.tools import register_tools  # noqa: E402

register_tools(mcp)


def main():
    """Run the MCP server.

    Transport defaults to stdio (local, spawned by Claude Desktop as a
    subprocess) so existing local setups keep working unchanged.

    Set MCP_TRANSPORT=streamable-http to run as a standalone HTTP server
    instead (needed for remote/cloud hosting so it can be reached from
    other devices). MCP_HOST/MCP_PORT configure the listen address
    (defaults 0.0.0.0:8000).

    SECURITY: streamable-http mode has no authentication in front of it.
    Anyone who can reach the port can call every tool, including ones that
    read your Garmin account. Do not expose this port on the public
    internet without adding an auth layer (reverse proxy with a bearer
    token, mcp's built-in AuthSettings, etc.) first.
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "streamable-http":
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.settings.host = host
        mcp.settings.port = port

        if host not in ("127.0.0.1", "localhost", "::1"):
            # FastMCP auto-enables DNS-rebinding protection scoped to
            # localhost only when constructed with a localhost host. Since
            # we're changing the host after construction for a non-local
            # bind, relax that check too (still no auth — see docstring).
            from mcp.server.fastmcp.server import TransportSecuritySettings

            mcp.settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=False
            )

        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
