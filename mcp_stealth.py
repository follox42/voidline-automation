"""
Direct HTTP client for MCP tools.

Prefers mcphub aggregator at https://mcphub.nocode18.com/mcp when
MCPHUB_TOKEN env var is set (cloud routine mode). Falls back to direct
camoufox-stealth at http://mcp-stealth.nocode18.com/mcp for local dev.

Bypasses the Claude Code MCP registry. Uses JSON-RPC 2.0 streamable-http.

Tool names:
- mcphub mode → call with full prefix e.g. "camoufox-stealth_navigate"
  (mcphub auto-routes the prefix)
- direct mode → call with bare name "stealth_navigate"
"""
import json
import os
import sys
import time
import uuid
from typing import Any, Dict, Optional

import urllib.request
import urllib.error


MCPHUB_TOKEN = os.environ.get("MCPHUB_TOKEN")
if MCPHUB_TOKEN:
    MCP_URL = "https://mcphub.nocode18.com/mcp"
    _MCPHUB_MODE = True
else:
    MCP_URL = "http://mcp-stealth.nocode18.com/mcp"
    _MCPHUB_MODE = False

_session_id: Optional[str] = None
_req_id = 0


def _next_id() -> int:
    global _req_id
    _req_id += 1
    return _req_id


def _post(payload: dict, timeout: int = 30) -> dict:
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Mozilla/5.0 (compatible; voidline-mcp-client/1.0)",
    }
    if MCPHUB_TOKEN:
        headers["Authorization"] = f"Bearer {MCPHUB_TOKEN}"
    if _session_id:
        headers["mcp-session-id"] = _session_id
    req = urllib.request.Request(MCP_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            # SSE format: 'event: message\ndata: {...}\n\n'
            data_lines = [ln[len("data:"):].strip() for ln in raw.splitlines() if ln.startswith("data:")]
            if not data_lines:
                return {"_raw": raw}
            return json.loads(data_lines[-1])
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"_http_error": e.code, "_body": body}
    except Exception as e:
        return {"_exception": str(e)}


def initialize() -> dict:
    global _session_id
    payload = {
        "jsonrpc": "2.0",
        "id": _next_id(),
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "voidline-direct", "version": "1.0"},
        },
    }
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Mozilla/5.0 (compatible; voidline-mcp-client/1.0)",
    }
    if MCPHUB_TOKEN:
        headers["Authorization"] = f"Bearer {MCPHUB_TOKEN}"
    req = urllib.request.Request(MCP_URL, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        # Capture session id from headers
        _session_id = resp.headers.get("mcp-session-id")
        raw = resp.read().decode()
        data_lines = [ln[len("data:"):].strip() for ln in raw.splitlines() if ln.startswith("data:")]
        result = json.loads(data_lines[-1]) if data_lines else {"_raw": raw}
    # Send initialized notification
    notif_payload = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    body2 = json.dumps(notif_payload).encode()
    headers2 = dict(headers)
    if _session_id:
        headers2["mcp-session-id"] = _session_id
    req2 = urllib.request.Request(MCP_URL, data=body2, headers=headers2, method="POST")
    try:
        urllib.request.urlopen(req2, timeout=10).read()
    except Exception:
        pass
    return result


def list_tools() -> dict:
    return _post({"jsonrpc": "2.0", "id": _next_id(), "method": "tools/list", "params": {}})


def _translate_tool_name(name: str) -> str:
    """Translate bare tool names to mcphub-prefixed names when needed.

    Local mode: scripts use 'stealth_navigate'. Mcphub mode: same tool is
    exposed as 'camoufox-stealth_navigate'. This lets the same scripts run
    in both modes transparently.
    """
    if not _MCPHUB_MODE:
        return name
    # Camoufox-stealth tools
    if name.startswith("stealth_"):
        return f"camoufox-{name}"
    # If already prefixed (e.g. "camoufox-stealth_*" or "github-*"), pass through
    return name


def call(name: str, arguments: Optional[Dict[str, Any]] = None) -> dict:
    return _post(
        {
            "jsonrpc": "2.0",
            "id": _next_id(),
            "method": "tools/call",
            "params": {"name": _translate_tool_name(name), "arguments": arguments or {}},
        },
        timeout=60,
    )


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "init"
    if cmd == "init":
        print(json.dumps(initialize(), indent=2))
    elif cmd == "tools":
        initialize()
        result = list_tools()
        # Print just tool names
        tools = result.get("result", {}).get("tools", [])
        print(f"{len(tools)} tools available:")
        for t in tools[:30]:
            print(f"  - {t['name']}")
    elif cmd == "call":
        initialize()
        tool_name = sys.argv[2]
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(call(tool_name, args), indent=2)[:4000])
