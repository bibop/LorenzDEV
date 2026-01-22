"""
LORENZ SaaS - MCP Manager
Unified interface for local and remote execution with permission checks
"""

import asyncio
import asyncssh
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.models import User
from .permissions import ExecutionPermissions, PermissionLevel
from .client import MCPClient, LocalExecutor

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of an execution request"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    execution_type: str = "local"
    metadata: Optional[Dict[str, Any]] = None


class SSHExecutor:
    """
    SSH executor for remote server commands.
    Only available to owner (Bibop) and admin users.
    """

    # SSH configuration for Bibop's servers
    SSH_CONFIGS = {
        "80.240.31.197": {
            "username": "linuxuser",
            "key_path": "~/.ssh/id_rsa",
            "name": "Vultr Server",
        }
    }

    # Safe commands that can be executed without explicit approval
    SAFE_SSH_COMMANDS = [
        "uptime", "free -h", "df -h", "date",
        "systemctl status", "systemctl is-active",
        "journalctl -u", "journalctl --since",
        "ps aux | grep", "top -b -n 1",
        "netstat -tlnp", "ss -tlnp",
        "docker ps", "docker logs",
        "cat /etc/hostname", "hostname",
        "uname -a", "lsb_release -a",
        "who", "w", "last",
    ]

    async def execute(
        self,
        host: str,
        command: str,
        timeout: int = 30
    ) -> ExecutionResult:
        """Execute a command on a remote server via SSH"""
        config = self.SSH_CONFIGS.get(host)
        if not config:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unknown host: {host}",
                exit_code=-1,
                execution_type="ssh"
            )

        try:
            # Expand key path
            import os
            key_path = os.path.expanduser(config["key_path"])

            async with asyncssh.connect(
                host,
                username=config["username"],
                client_keys=[key_path],
                known_hosts=None,  # Skip host key verification for simplicity
                connect_timeout=10,
            ) as conn:
                result = await asyncio.wait_for(
                    conn.run(command),
                    timeout=timeout
                )

                return ExecutionResult(
                    success=result.exit_status == 0,
                    output=result.stdout or "",
                    error=result.stderr if result.exit_status != 0 else None,
                    exit_code=result.exit_status,
                    execution_type="ssh",
                    metadata={"host": host, "server_name": config["name"]}
                )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output="",
                error="SSH command timed out",
                exit_code=-1,
                execution_type="ssh"
            )
        except Exception as e:
            logger.error(f"SSH execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_type="ssh"
            )

    def is_safe_command(self, command: str) -> bool:
        """Check if command is in the safe list"""
        command_lower = command.lower().strip()
        for safe in self.SAFE_SSH_COMMANDS:
            if command_lower.startswith(safe.lower()):
                return True
        return False


class MCPManager:
    """
    Unified manager for all execution capabilities.

    Routes requests to appropriate executor based on user permissions:
    - Bibop (owner): Full SSH + MCP access
    - Admins: Tenant-configured SSH + MCP
    - Members: Local MCP only
    - Guests: No execution
    """

    def __init__(self, user: User):
        self.user = user
        # Get tenant settings safely (might not be eagerly loaded)
        try:
            tenant_settings = user.tenant.settings if user.tenant else {}
        except Exception:
            tenant_settings = {}

        self.permissions = ExecutionPermissions(
            user_role=user.role,
            user_email=user.email,
            tenant_settings=tenant_settings
        )
        self.local_executor = LocalExecutor()
        self.ssh_executor = SSHExecutor()
        self._mcp_client: Optional[MCPClient] = None

    @property
    def mcp_client(self) -> MCPClient:
        """Lazy initialization of MCP client"""
        if self._mcp_client is None:
            allowed_paths = self.permissions.get_allowed_paths()
            self._mcp_client = MCPClient(allowed_paths=allowed_paths)
        return self._mcp_client

    def get_capabilities(self) -> Dict[str, Any]:
        """Get user's execution capabilities"""
        return self.permissions.get_capabilities()

    # =====================
    # Local Execution
    # =====================

    async def execute_local(self, command: str, timeout: int = 30) -> ExecutionResult:
        """Execute a local shell command"""
        allowed, reason = self.permissions.validate_execution_request(
            "local", command=command
        )

        if not allowed:
            return ExecutionResult(
                success=False,
                output="",
                error=reason,
                exit_code=-1,
                execution_type="local"
            )

        result = await self.local_executor.execute_command(command, timeout)

        return ExecutionResult(
            success=result["exit_code"] == 0,
            output=result["stdout"],
            error=result["stderr"] if result["exit_code"] != 0 else None,
            exit_code=result["exit_code"],
            execution_type="local"
        )

    async def open_app(self, app_name: str) -> ExecutionResult:
        """Open an application"""
        allowed, reason = self.permissions.validate_execution_request("local")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        success = await self.local_executor.open_application(app_name)
        return ExecutionResult(
            success=success,
            output=f"Opened {app_name}" if success else "",
            error=f"Failed to open {app_name}" if not success else None,
            execution_type="local"
        )

    async def open_url(self, url: str) -> ExecutionResult:
        """Open a URL in browser"""
        allowed, reason = self.permissions.validate_execution_request("local")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        success = await self.local_executor.open_url(url)
        return ExecutionResult(
            success=success,
            output=f"Opened {url}" if success else "",
            error=f"Failed to open {url}" if not success else None,
            execution_type="local"
        )

    async def say(self, text: str, voice: str = None) -> ExecutionResult:
        """Text to speech (macOS)"""
        allowed, reason = self.permissions.validate_execution_request("local")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        success = await self.local_executor.say(text, voice)
        return ExecutionResult(
            success=success,
            output="Speech completed" if success else "",
            error="Text-to-speech failed" if not success else None,
            execution_type="local"
        )

    async def get_clipboard(self) -> ExecutionResult:
        """Get clipboard contents"""
        allowed, reason = self.permissions.validate_execution_request("local")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        content = await self.local_executor.get_clipboard()
        return ExecutionResult(
            success=True,
            output=content,
            execution_type="local"
        )

    async def set_clipboard(self, content: str) -> ExecutionResult:
        """Set clipboard contents"""
        allowed, reason = self.permissions.validate_execution_request("local")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        success = await self.local_executor.set_clipboard(content)
        return ExecutionResult(
            success=success,
            output="Clipboard set" if success else "",
            error="Failed to set clipboard" if not success else None,
            execution_type="local"
        )

    async def screenshot(self, path: str = "/tmp/screenshot.png") -> ExecutionResult:
        """Take a screenshot"""
        allowed, reason = self.permissions.validate_execution_request("local")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        result_path = await self.local_executor.screenshot(path)
        return ExecutionResult(
            success=bool(result_path),
            output=result_path,
            error="Screenshot failed" if not result_path else None,
            execution_type="local"
        )

    async def applescript(self, script: str) -> ExecutionResult:
        """Run AppleScript (macOS)"""
        allowed, reason = self.permissions.validate_execution_request("local")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        output = await self.local_executor.run_applescript(script)
        return ExecutionResult(
            success=True,
            output=output,
            execution_type="local"
        )

    # =====================
    # SSH Execution (Owner only)
    # =====================

    async def execute_ssh(
        self,
        host: str,
        command: str,
        timeout: int = 30
    ) -> ExecutionResult:
        """Execute a command on a remote server via SSH"""
        allowed, reason = self.permissions.validate_execution_request(
            "ssh", command=command, host=host
        )

        if not allowed:
            return ExecutionResult(
                success=False,
                output="",
                error=reason,
                exit_code=-1,
                execution_type="ssh"
            )

        return await self.ssh_executor.execute(host, command, timeout)

    def get_ssh_hosts(self) -> List[Dict[str, str]]:
        """Get list of available SSH hosts for user"""
        hosts = self.permissions.get_allowed_ssh_hosts()
        return [
            {
                "host": host,
                "name": self.ssh_executor.SSH_CONFIGS.get(host, {}).get("name", host)
            }
            for host in hosts
            if host in self.ssh_executor.SSH_CONFIGS
        ]

    # =====================
    # Filesystem Operations
    # =====================

    async def list_files(self, path: str) -> ExecutionResult:
        """List files in a directory"""
        allowed, reason = self.permissions.validate_execution_request(
            "filesystem", path=path
        )
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        # Use local executor for simplicity
        result = await self.local_executor.execute_command(f"ls -la '{path}'")
        return ExecutionResult(
            success=result["exit_code"] == 0,
            output=result["stdout"],
            error=result["stderr"] if result["exit_code"] != 0 else None,
            execution_type="filesystem"
        )

    async def read_file(self, path: str) -> ExecutionResult:
        """Read a file"""
        allowed, reason = self.permissions.validate_execution_request(
            "filesystem", path=path
        )
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        result = await self.local_executor.execute_command(f"cat '{path}'")
        return ExecutionResult(
            success=result["exit_code"] == 0,
            output=result["stdout"],
            error=result["stderr"] if result["exit_code"] != 0 else None,
            execution_type="filesystem"
        )

    async def search_files(self, path: str, pattern: str) -> ExecutionResult:
        """Search for files"""
        allowed, reason = self.permissions.validate_execution_request(
            "filesystem", path=path
        )
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        result = await self.local_executor.execute_command(
            f"find '{path}' -name '{pattern}'"
        )
        return ExecutionResult(
            success=result["exit_code"] == 0,
            output=result["stdout"],
            error=result["stderr"] if result["exit_code"] != 0 else None,
            execution_type="filesystem"
        )

    # =====================
    # Browser Automation
    # =====================

    async def browser_open(self, url: str) -> ExecutionResult:
        """Open URL in browser (simple version)"""
        allowed, reason = self.permissions.validate_execution_request("puppeteer")
        if not allowed:
            return ExecutionResult(success=False, output="", error=reason)

        success = await self.local_executor.open_url(url)
        return ExecutionResult(
            success=success,
            output=f"Opened {url}" if success else "",
            error="Failed to open URL" if not success else None,
            execution_type="puppeteer"
        )

    # =====================
    # Cleanup
    # =====================

    async def cleanup(self):
        """Cleanup resources"""
        if self._mcp_client:
            await self._mcp_client.stop_all()
