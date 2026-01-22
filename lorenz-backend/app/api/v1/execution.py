"""
LORENZ SaaS - Execution API Routes
Endpoints for local and remote command execution
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.mcp import MCPManager

router = APIRouter()
logger = logging.getLogger(__name__)


# =====================
# Request/Response Models
# =====================

class ExecuteLocalRequest(BaseModel):
    """Request to execute a local command"""
    command: str
    timeout: Optional[int] = 30


class ExecuteSSHRequest(BaseModel):
    """Request to execute an SSH command"""
    host: str
    command: str
    timeout: Optional[int] = 30


class OpenAppRequest(BaseModel):
    """Request to open an application"""
    app_name: str


class OpenURLRequest(BaseModel):
    """Request to open a URL"""
    url: str


class SayRequest(BaseModel):
    """Request for text-to-speech"""
    text: str
    voice: Optional[str] = None


class ClipboardRequest(BaseModel):
    """Request to set clipboard"""
    content: str


class AppleScriptRequest(BaseModel):
    """Request to run AppleScript"""
    script: str


class FileRequest(BaseModel):
    """Request for file operations"""
    path: str
    pattern: Optional[str] = None


class ExecutionResponse(BaseModel):
    """Response from execution request"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    execution_type: str = "local"


class CapabilitiesResponse(BaseModel):
    """Response with user's execution capabilities"""
    permission_level: str
    local_execution: bool
    ssh_execution: bool
    filesystem_access: bool
    puppeteer: bool
    ssh_hosts: List[dict]
    safe_commands: List[str]


# =====================
# Endpoints
# =====================

@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's execution capabilities.
    Returns what the user is allowed to do based on their role.
    """
    manager = MCPManager(current_user)
    caps = manager.get_capabilities()

    return CapabilitiesResponse(
        permission_level=caps["permission_level"],
        local_execution=caps["local_execution"],
        ssh_execution=caps["ssh_execution"],
        filesystem_access=caps["filesystem_access"],
        puppeteer=caps["puppeteer"],
        ssh_hosts=manager.get_ssh_hosts(),
        safe_commands=caps["safe_commands"][:20],  # Limit for response size
    )


@router.post("/local", response_model=ExecutionResponse)
async def execute_local(
    request: ExecuteLocalRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a local shell command.

    Available to: owner, admin, member (with command whitelist)
    """
    manager = MCPManager(current_user)
    result = await manager.execute_local(request.command, request.timeout)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        exit_code=result.exit_code,
        execution_type=result.execution_type
    )


@router.post("/ssh", response_model=ExecutionResponse)
async def execute_ssh(
    request: ExecuteSSHRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a command on a remote server via SSH.

    Available to: owner only (Bibop)
    """
    manager = MCPManager(current_user)
    result = await manager.execute_ssh(
        request.host,
        request.command,
        request.timeout
    )

    if not result.success and "not allowed" in (result.error or "").lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error
        )

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        exit_code=result.exit_code,
        execution_type=result.execution_type
    )


@router.get("/ssh/hosts")
async def get_ssh_hosts(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available SSH hosts for the current user.
    """
    manager = MCPManager(current_user)
    return {"hosts": manager.get_ssh_hosts()}


@router.post("/open-app", response_model=ExecutionResponse)
async def open_application(
    request: OpenAppRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Open an application on the local system.
    """
    manager = MCPManager(current_user)
    result = await manager.open_app(request.app_name)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/open-url", response_model=ExecutionResponse)
async def open_url(
    request: OpenURLRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Open a URL in the default browser.
    """
    manager = MCPManager(current_user)
    result = await manager.open_url(request.url)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/say", response_model=ExecutionResponse)
async def text_to_speech(
    request: SayRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Convert text to speech (macOS only).
    """
    manager = MCPManager(current_user)
    result = await manager.say(request.text, request.voice)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.get("/clipboard", response_model=ExecutionResponse)
async def get_clipboard(
    current_user: User = Depends(get_current_user)
):
    """
    Get clipboard contents.
    """
    manager = MCPManager(current_user)
    result = await manager.get_clipboard()

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/clipboard", response_model=ExecutionResponse)
async def set_clipboard(
    request: ClipboardRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Set clipboard contents.
    """
    manager = MCPManager(current_user)
    result = await manager.set_clipboard(request.content)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/screenshot", response_model=ExecutionResponse)
async def take_screenshot(
    path: str = "/tmp/lorenz_screenshot.png",
    current_user: User = Depends(get_current_user)
):
    """
    Take a screenshot (macOS only).
    """
    manager = MCPManager(current_user)
    result = await manager.screenshot(path)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/applescript", response_model=ExecutionResponse)
async def run_applescript(
    request: AppleScriptRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Run AppleScript (macOS only).
    """
    manager = MCPManager(current_user)
    result = await manager.applescript(request.script)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/files/list", response_model=ExecutionResponse)
async def list_files(
    request: FileRequest,
    current_user: User = Depends(get_current_user)
):
    """
    List files in a directory.
    """
    manager = MCPManager(current_user)
    result = await manager.list_files(request.path)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/files/read", response_model=ExecutionResponse)
async def read_file(
    request: FileRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Read a file's contents.
    """
    manager = MCPManager(current_user)
    result = await manager.read_file(request.path)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )


@router.post("/files/search", response_model=ExecutionResponse)
async def search_files(
    request: FileRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for files matching a pattern.
    """
    if not request.pattern:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pattern is required for search"
        )

    manager = MCPManager(current_user)
    result = await manager.search_files(request.path, request.pattern)

    return ExecutionResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_type=result.execution_type
    )
