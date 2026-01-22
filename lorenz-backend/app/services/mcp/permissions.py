"""
LORENZ SaaS - Execution Permissions System
Defines what each user role can execute
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for execution capabilities"""
    NONE = "none"           # No execution allowed
    LOCAL_ONLY = "local"    # Only local MCP (filesystem, shell, puppeteer)
    REMOTE_SSH = "ssh"      # Can execute SSH on configured servers
    FULL = "full"           # Full access (owner only)


@dataclass
class ExecutionCapability:
    """Defines a specific execution capability"""
    name: str
    description: str
    permission_level: PermissionLevel
    allowed_commands: Optional[List[str]] = None  # Whitelist for shell commands
    allowed_paths: Optional[List[str]] = None     # Whitelist for filesystem paths
    ssh_hosts: Optional[List[str]] = None         # Allowed SSH hosts


class ExecutionPermissions:
    """
    Manages execution permissions based on user role.

    Permission Matrix:
    - owner (Bibop): FULL access - SSH to servers + all MCP
    - admin: REMOTE_SSH - Can SSH to tenant-configured servers + MCP
    - member: LOCAL_ONLY - Only local MCP (filesystem, shell, puppeteer)
    - guest: NONE - No execution capabilities
    """

    # Default safe commands for local shell execution
    SAFE_LOCAL_COMMANDS = [
        # System info
        "date", "whoami", "hostname", "uname",
        "uptime", "sw_vers",  # macOS
        "ver",  # Windows

        # File operations (read-only)
        "ls", "dir", "pwd", "cat", "head", "tail",
        "find", "grep", "wc", "file", "stat",

        # Process info
        "ps", "top -l 1", "Activity Monitor",

        # Network info
        "ifconfig", "ipconfig", "ping", "nslookup",
        "curl", "wget",

        # Disk info
        "df", "du",

        # Development tools
        "git status", "git log", "git diff",
        "npm list", "pip list", "python --version",
        "node --version", "ruby --version",

        # macOS specific
        "osascript",  # AppleScript
        "open",       # Open files/apps
        "pbcopy", "pbpaste",  # Clipboard
        "say",        # Text to speech
        "screencapture",

        # Safe system commands
        "echo", "printf", "which", "where",
    ]

    # Dangerous commands that are NEVER allowed for non-owners
    BLOCKED_COMMANDS = [
        "rm -rf", "rmdir", "del /f",
        "format", "mkfs",
        "sudo", "su", "chmod 777",
        "shutdown", "reboot", "halt",
        "> /dev/", "dd if=",
        "curl | bash", "wget | bash",
        "eval", "exec",
    ]

    # Bibop's SSH hosts (configured separately)
    OWNER_SSH_HOSTS = [
        "80.240.31.197",  # Vultr server
    ]

    def __init__(self, user_role: str, user_email: str, tenant_settings: Dict[str, Any] = None):
        self.user_role = user_role
        self.user_email = user_email
        self.tenant_settings = tenant_settings or {}
        self._permission_level = self._calculate_permission_level()

    def _calculate_permission_level(self) -> PermissionLevel:
        """Calculate permission level based on role and email"""
        # Bibop gets FULL access
        if self.user_email == "bibop@hyperloopitalia.com":
            return PermissionLevel.FULL

        # Role-based permissions
        if self.user_role == "owner":
            return PermissionLevel.REMOTE_SSH
        elif self.user_role == "admin":
            return PermissionLevel.REMOTE_SSH
        elif self.user_role == "member":
            return PermissionLevel.LOCAL_ONLY
        else:
            return PermissionLevel.NONE

    @property
    def permission_level(self) -> PermissionLevel:
        return self._permission_level

    def can_execute_local(self) -> bool:
        """Check if user can execute local commands via MCP"""
        return self._permission_level in [
            PermissionLevel.LOCAL_ONLY,
            PermissionLevel.REMOTE_SSH,
            PermissionLevel.FULL
        ]

    def can_execute_ssh(self) -> bool:
        """Check if user can execute SSH commands"""
        return self._permission_level in [
            PermissionLevel.REMOTE_SSH,
            PermissionLevel.FULL
        ]

    def can_access_filesystem(self) -> bool:
        """Check if user can access local filesystem"""
        return self.can_execute_local()

    def can_use_puppeteer(self) -> bool:
        """Check if user can use Puppeteer for browser automation"""
        return self.can_execute_local()

    def is_command_allowed(self, command: str) -> bool:
        """Check if a specific command is allowed"""
        command_lower = command.lower().strip()

        # Check blocked commands first
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command_lower:
                # Only FULL permission can use blocked commands
                if self._permission_level != PermissionLevel.FULL:
                    logger.warning(f"Blocked command attempt: {command}")
                    return False

        # For LOCAL_ONLY, check whitelist
        if self._permission_level == PermissionLevel.LOCAL_ONLY:
            for safe in self.SAFE_LOCAL_COMMANDS:
                if command_lower.startswith(safe.lower()):
                    return True
            logger.warning(f"Command not in whitelist: {command}")
            return False

        # REMOTE_SSH and FULL can use any non-blocked command
        return True

    def get_allowed_ssh_hosts(self) -> List[str]:
        """Get list of SSH hosts user can connect to"""
        if self._permission_level == PermissionLevel.FULL:
            # Bibop can access all his servers
            return self.OWNER_SSH_HOSTS

        if self._permission_level == PermissionLevel.REMOTE_SSH:
            # Other owners/admins can access tenant-configured hosts
            return self.tenant_settings.get("ssh_hosts", [])

        return []

    def get_allowed_paths(self) -> List[str]:
        """Get list of filesystem paths user can access"""
        if self._permission_level == PermissionLevel.FULL:
            return ["*"]  # Full access

        if self.can_access_filesystem():
            # Default safe paths
            return [
                "~/Documents",
                "~/Desktop",
                "~/Downloads",
                "/tmp",
            ]

        return []

    def get_capabilities(self) -> Dict[str, Any]:
        """Get all capabilities for current user"""
        return {
            "permission_level": self._permission_level.value,
            "local_execution": self.can_execute_local(),
            "ssh_execution": self.can_execute_ssh(),
            "filesystem_access": self.can_access_filesystem(),
            "puppeteer": self.can_use_puppeteer(),
            "ssh_hosts": self.get_allowed_ssh_hosts(),
            "allowed_paths": self.get_allowed_paths(),
            "safe_commands": self.SAFE_LOCAL_COMMANDS if self.can_execute_local() else [],
        }

    def validate_execution_request(
        self,
        execution_type: str,  # "local", "ssh", "filesystem", "puppeteer"
        command: Optional[str] = None,
        host: Optional[str] = None,
        path: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Validate an execution request.
        Returns (allowed, reason)
        """
        if execution_type == "local":
            if not self.can_execute_local():
                return False, "Local execution not allowed for your role"
            if command and not self.is_command_allowed(command):
                return False, f"Command '{command}' is not allowed"
            return True, "OK"

        elif execution_type == "ssh":
            if not self.can_execute_ssh():
                return False, "SSH execution not allowed for your role"
            if host and host not in self.get_allowed_ssh_hosts():
                return False, f"SSH to host '{host}' is not allowed"
            return True, "OK"

        elif execution_type == "filesystem":
            if not self.can_access_filesystem():
                return False, "Filesystem access not allowed for your role"
            # Path validation could be added here
            return True, "OK"

        elif execution_type == "puppeteer":
            if not self.can_use_puppeteer():
                return False, "Puppeteer not allowed for your role"
            return True, "OK"

        return False, f"Unknown execution type: {execution_type}"
