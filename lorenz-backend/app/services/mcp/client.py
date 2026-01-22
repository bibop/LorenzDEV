"""
LORENZ SaaS - MCP Client
Communicates with MCP servers for local system execution
"""

import asyncio
import json
import subprocess
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import os
import platform

logger = logging.getLogger(__name__)


class MCPServerType(Enum):
    """Available MCP server types"""
    FILESYSTEM = "filesystem"
    SHELL = "shell"
    PUPPETEER = "puppeteer"
    FETCH = "fetch"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    server_type: MCPServerType
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class MCPClient:
    """
    Client for communicating with MCP servers.

    MCP (Model Context Protocol) allows Claude to interact with local
    system resources through standardized servers.
    """

    # Default MCP server configurations
    DEFAULT_SERVERS = {
        MCPServerType.FILESYSTEM: MCPServerConfig(
            server_type=MCPServerType.FILESYSTEM,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        ),
        MCPServerType.SHELL: MCPServerConfig(
            server_type=MCPServerType.SHELL,
            command="npx",
            args=["-y", "@anthropic/mcp-server-shell"],
        ),
        MCPServerType.PUPPETEER: MCPServerConfig(
            server_type=MCPServerType.PUPPETEER,
            command="npx",
            args=["-y", "@anthropic/mcp-server-puppeteer"],
        ),
        MCPServerType.FETCH: MCPServerConfig(
            server_type=MCPServerType.FETCH,
            command="npx",
            args=["-y", "@anthropic/mcp-server-fetch"],
        ),
    }

    def __init__(self, allowed_paths: List[str] = None):
        self.allowed_paths = allowed_paths or ["/tmp", os.path.expanduser("~")]
        self._processes: Dict[MCPServerType, subprocess.Popen] = {}
        self._request_id = 0

    async def start_server(self, server_type: MCPServerType) -> bool:
        """Start an MCP server"""
        if server_type in self._processes:
            return True  # Already running

        config = self.DEFAULT_SERVERS.get(server_type)
        if not config:
            logger.error(f"Unknown server type: {server_type}")
            return False

        try:
            # Prepare environment
            env = os.environ.copy()
            if config.env:
                env.update(config.env)

            # Modify args for filesystem server to include allowed paths
            args = config.args.copy()
            if server_type == MCPServerType.FILESYSTEM:
                args = ["-y", "@modelcontextprotocol/server-filesystem"] + self.allowed_paths

            # Start the process
            process = subprocess.Popen(
                [config.command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            self._processes[server_type] = process
            logger.info(f"Started MCP server: {server_type.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to start MCP server {server_type.value}: {e}")
            return False

    async def stop_server(self, server_type: MCPServerType):
        """Stop an MCP server"""
        if server_type in self._processes:
            self._processes[server_type].terminate()
            del self._processes[server_type]
            logger.info(f"Stopped MCP server: {server_type.value}")

    async def stop_all(self):
        """Stop all running MCP servers"""
        for server_type in list(self._processes.keys()):
            await self.stop_server(server_type)

    def _get_request_id(self) -> int:
        """Get a unique request ID"""
        self._request_id += 1
        return self._request_id

    async def _send_request(
        self,
        server_type: MCPServerType,
        method: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send a JSON-RPC request to an MCP server"""
        if server_type not in self._processes:
            await self.start_server(server_type)

        process = self._processes.get(server_type)
        if not process:
            raise RuntimeError(f"MCP server not running: {server_type.value}")

        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": method,
            "params": params or {}
        }

        try:
            # Send request
            request_str = json.dumps(request) + "\n"
            process.stdin.write(request_str.encode())
            process.stdin.flush()

            # Read response
            response_line = process.stdout.readline()
            response = json.loads(response_line.decode())

            if "error" in response:
                raise RuntimeError(f"MCP error: {response['error']}")

            return response.get("result", {})

        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            raise

    # =====================
    # Filesystem Operations
    # =====================

    async def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """List contents of a directory"""
        result = await self._send_request(
            MCPServerType.FILESYSTEM,
            "tools/call",
            {"name": "list_directory", "arguments": {"path": path}}
        )
        return result

    async def read_file(self, path: str) -> str:
        """Read contents of a file"""
        result = await self._send_request(
            MCPServerType.FILESYSTEM,
            "tools/call",
            {"name": "read_file", "arguments": {"path": path}}
        )
        return result.get("content", "")

    async def write_file(self, path: str, content: str) -> bool:
        """Write content to a file"""
        result = await self._send_request(
            MCPServerType.FILESYSTEM,
            "tools/call",
            {"name": "write_file", "arguments": {"path": path, "content": content}}
        )
        return True

    async def search_files(self, path: str, pattern: str) -> List[str]:
        """Search for files matching a pattern"""
        result = await self._send_request(
            MCPServerType.FILESYSTEM,
            "tools/call",
            {"name": "search_files", "arguments": {"path": path, "pattern": pattern}}
        )
        return result.get("files", [])

    # =====================
    # Shell Operations
    # =====================

    async def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a shell command"""
        result = await self._send_request(
            MCPServerType.SHELL,
            "tools/call",
            {"name": "execute", "arguments": {"command": command, "timeout": timeout}}
        )
        return {
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exitCode", -1),
        }

    # =====================
    # Puppeteer Operations
    # =====================

    async def browser_navigate(self, url: str) -> Dict[str, Any]:
        """Navigate browser to a URL"""
        result = await self._send_request(
            MCPServerType.PUPPETEER,
            "tools/call",
            {"name": "puppeteer_navigate", "arguments": {"url": url}}
        )
        return result

    async def browser_screenshot(self) -> str:
        """Take a screenshot of the current page"""
        result = await self._send_request(
            MCPServerType.PUPPETEER,
            "tools/call",
            {"name": "puppeteer_screenshot", "arguments": {}}
        )
        return result.get("screenshot", "")

    async def browser_click(self, selector: str) -> bool:
        """Click an element on the page"""
        result = await self._send_request(
            MCPServerType.PUPPETEER,
            "tools/call",
            {"name": "puppeteer_click", "arguments": {"selector": selector}}
        )
        return True

    async def browser_fill(self, selector: str, value: str) -> bool:
        """Fill a form field"""
        result = await self._send_request(
            MCPServerType.PUPPETEER,
            "tools/call",
            {"name": "puppeteer_fill", "arguments": {"selector": selector, "value": value}}
        )
        return True

    async def browser_evaluate(self, script: str) -> Any:
        """Execute JavaScript in the browser"""
        result = await self._send_request(
            MCPServerType.PUPPETEER,
            "tools/call",
            {"name": "puppeteer_evaluate", "arguments": {"script": script}}
        )
        return result.get("result")

    # =====================
    # Fetch Operations
    # =====================

    async def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch content from a URL"""
        result = await self._send_request(
            MCPServerType.FETCH,
            "tools/call",
            {"name": "fetch", "arguments": {"url": url}}
        )
        return result


class LocalExecutor:
    """
    Direct local execution without MCP (for simple commands).
    Used as fallback when MCP servers are not available.
    """

    def __init__(self):
        self.system = platform.system()  # 'Darwin', 'Windows', 'Linux'

    async def execute_command(
        self,
        command: str,
        timeout: int = 30,
        shell: bool = True
    ) -> Dict[str, Any]:
        """Execute a local shell command directly"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "stdout": "",
                    "stderr": "Command timed out",
                    "exit_code": -1,
                    "error": "timeout"
                }

            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "exit_code": process.returncode,
            }

        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "error": str(e)
            }

    async def open_application(self, app_name: str) -> bool:
        """Open an application (macOS/Windows)"""
        if self.system == "Darwin":
            result = await self.execute_command(f"open -a '{app_name}'")
        elif self.system == "Windows":
            result = await self.execute_command(f"start {app_name}")
        else:
            result = await self.execute_command(app_name)

        return result["exit_code"] == 0

    async def open_url(self, url: str) -> bool:
        """Open a URL in default browser"""
        if self.system == "Darwin":
            result = await self.execute_command(f"open '{url}'")
        elif self.system == "Windows":
            result = await self.execute_command(f"start {url}")
        else:
            result = await self.execute_command(f"xdg-open '{url}'")

        return result["exit_code"] == 0

    async def say(self, text: str, voice: str = None) -> bool:
        """Text to speech (macOS only)"""
        if self.system != "Darwin":
            return False

        voice_arg = f"-v {voice}" if voice else ""
        result = await self.execute_command(f"say {voice_arg} '{text}'")
        return result["exit_code"] == 0

    async def get_clipboard(self) -> str:
        """Get clipboard contents"""
        if self.system == "Darwin":
            result = await self.execute_command("pbpaste")
        elif self.system == "Windows":
            result = await self.execute_command("powershell Get-Clipboard")
        else:
            result = await self.execute_command("xclip -selection clipboard -o")

        return result["stdout"].strip()

    async def set_clipboard(self, content: str) -> bool:
        """Set clipboard contents"""
        if self.system == "Darwin":
            result = await self.execute_command(f"echo '{content}' | pbcopy")
        elif self.system == "Windows":
            result = await self.execute_command(f"echo {content} | clip")
        else:
            result = await self.execute_command(f"echo '{content}' | xclip -selection clipboard")

        return result["exit_code"] == 0

    async def screenshot(self, output_path: str = "/tmp/screenshot.png") -> str:
        """Take a screenshot (macOS only for now)"""
        if self.system == "Darwin":
            result = await self.execute_command(f"screencapture -x {output_path}")
            if result["exit_code"] == 0:
                return output_path
        return ""

    async def run_applescript(self, script: str) -> str:
        """Run AppleScript (macOS only)"""
        if self.system != "Darwin":
            return ""

        result = await self.execute_command(f"osascript -e '{script}'")
        return result["stdout"].strip()
