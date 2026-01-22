"""
LORENZ SaaS - Cloud Storage Discovery Service
==============================================

Automatic discovery of files from cloud storage providers:
- Google Drive
- Microsoft OneDrive
- Dropbox

Uses OAuth tokens from connected accounts.
"""

import logging
import aiohttp
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, AsyncIterator
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class CloudProvider(str, Enum):
    """Supported cloud storage providers"""
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"
    ICLOUD = "icloud"  # Future


@dataclass
class CloudFile:
    """A file discovered in cloud storage"""
    id: str
    name: str
    path: str
    provider: CloudProvider
    mime_type: Optional[str]
    size_bytes: int
    modified_at: datetime
    created_at: Optional[datetime]
    web_url: Optional[str]
    download_url: Optional[str]
    is_folder: bool = False
    parent_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "provider": self.provider.value,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "web_url": self.web_url,
            "download_url": self.download_url,
            "is_folder": self.is_folder,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }


@dataclass
class CloudDiscoveryResult:
    """Result of cloud storage discovery"""
    scan_id: str
    provider: CloudProvider
    started_at: datetime
    completed_at: Optional[datetime]
    files_found: int
    folders_found: int
    total_size_bytes: int
    files: List[CloudFile]
    root_folder_id: Optional[str]
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "scan_id": self.scan_id,
            "provider": self.provider.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "files_found": self.files_found,
            "folders_found": self.folders_found,
            "total_size_bytes": self.total_size_bytes,
            "files": [f.to_dict() for f in self.files],
            "root_folder_id": self.root_folder_id,
            "errors": self.errors,
        }


# MIME types we care about for documents
RELEVANT_MIME_TYPES = {
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "text/plain",
    "text/markdown",

    # Spreadsheets
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.spreadsheet",
    "text/csv",

    # Presentations
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    # Google Workspace
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.presentation",

    # Notes
    "text/html",
}


class CloudStorageDiscovery:
    """
    Discovers files from cloud storage providers.

    Features:
    - Multi-provider support (Google Drive, OneDrive, Dropbox)
    - Folder traversal with depth limits
    - MIME type filtering
    - Progress callbacks
    - Rate limiting
    """

    def __init__(
        self,
        access_token: str,
        provider: CloudProvider,
        max_results: int = 1000,
        include_folders: bool = True,
        mime_type_filter: Optional[set] = None
    ):
        """
        Initialize cloud discovery.

        Args:
            access_token: OAuth access token
            provider: Cloud provider
            max_results: Maximum files to discover
            include_folders: Include folders in results
            mime_type_filter: Only include these MIME types (default: documents)
        """
        self.access_token = access_token
        self.provider = provider
        self.max_results = max_results
        self.include_folders = include_folders
        self.mime_type_filter = mime_type_filter or RELEVANT_MIME_TYPES

        self._session: Optional[aiohttp.ClientSession] = None
        self._cancelled = False

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    def cancel(self):
        """Cancel ongoing discovery"""
        self._cancelled = True

    async def discover_all(self) -> CloudDiscoveryResult:
        """
        Discover all relevant files from the cloud storage.

        Returns:
            CloudDiscoveryResult with discovered files
        """
        scan_id = str(uuid4())
        started_at = datetime.now()
        all_files: List[CloudFile] = []
        errors: List[str] = []

        logger.info(f"Starting cloud discovery for {self.provider.value}")

        try:
            if self.provider == CloudProvider.GOOGLE_DRIVE:
                async for file in self._discover_google_drive():
                    all_files.append(file)
                    if len(all_files) >= self.max_results:
                        break

            elif self.provider == CloudProvider.ONEDRIVE:
                async for file in self._discover_onedrive():
                    all_files.append(file)
                    if len(all_files) >= self.max_results:
                        break

            elif self.provider == CloudProvider.DROPBOX:
                async for file in self._discover_dropbox():
                    all_files.append(file)
                    if len(all_files) >= self.max_results:
                        break

        except Exception as e:
            error_msg = f"Discovery error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Calculate stats
        files_count = sum(1 for f in all_files if not f.is_folder)
        folders_count = sum(1 for f in all_files if f.is_folder)
        total_size = sum(f.size_bytes for f in all_files if not f.is_folder)

        return CloudDiscoveryResult(
            scan_id=scan_id,
            provider=self.provider,
            started_at=started_at,
            completed_at=datetime.now(),
            files_found=files_count,
            folders_found=folders_count,
            total_size_bytes=total_size,
            files=all_files,
            root_folder_id=None,
            errors=errors,
        )

    # ==========================================================================
    # Google Drive
    # ==========================================================================

    async def _discover_google_drive(self) -> AsyncIterator[CloudFile]:
        """Discover files from Google Drive"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        page_token = None
        base_url = "https://www.googleapis.com/drive/v3/files"

        # Build MIME type query
        mime_queries = [f"mimeType='{mt}'" for mt in self.mime_type_filter]
        # Also get folders
        if self.include_folders:
            mime_queries.append("mimeType='application/vnd.google-apps.folder'")

        while not self._cancelled:
            params = {
                "pageSize": 100,
                "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,createdTime,webViewLink,parents)",
                "q": f"({' or '.join(mime_queries)}) and trashed=false",
            }

            if page_token:
                params["pageToken"] = page_token

            try:
                async with self._session.get(
                    base_url,
                    params=params,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                ) as resp:
                    if resp.status == 401:
                        logger.error("Google Drive: Unauthorized - token may be expired")
                        return

                    if resp.status != 200:
                        logger.error(f"Google Drive API error: {resp.status}")
                        return

                    data = await resp.json()

                    for item in data.get("files", []):
                        is_folder = item.get("mimeType") == "application/vnd.google-apps.folder"

                        # Parse dates
                        modified_at = None
                        created_at = None
                        if item.get("modifiedTime"):
                            modified_at = datetime.fromisoformat(
                                item["modifiedTime"].replace("Z", "+00:00")
                            )
                        if item.get("createdTime"):
                            created_at = datetime.fromisoformat(
                                item["createdTime"].replace("Z", "+00:00")
                            )

                        yield CloudFile(
                            id=item["id"],
                            name=item["name"],
                            path=f"/Google Drive/{item['name']}",  # Simplified path
                            provider=CloudProvider.GOOGLE_DRIVE,
                            mime_type=item.get("mimeType"),
                            size_bytes=int(item.get("size", 0)),
                            modified_at=modified_at,
                            created_at=created_at,
                            web_url=item.get("webViewLink"),
                            download_url=None,  # Requires separate API call
                            is_folder=is_folder,
                            parent_id=item.get("parents", [None])[0],
                            metadata={
                                "google_mime_type": item.get("mimeType"),
                            }
                        )

                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break

            except aiohttp.ClientError as e:
                logger.error(f"Google Drive request error: {e}")
                break

            # Rate limiting
            await asyncio.sleep(0.1)

    # ==========================================================================
    # Microsoft OneDrive
    # ==========================================================================

    async def _discover_onedrive(self) -> AsyncIterator[CloudFile]:
        """Discover files from OneDrive"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        # Start from root
        url = "https://graph.microsoft.com/v1.0/me/drive/root/children"

        while url and not self._cancelled:
            try:
                async with self._session.get(
                    url,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                ) as resp:
                    if resp.status == 401:
                        logger.error("OneDrive: Unauthorized - token may be expired")
                        return

                    if resp.status != 200:
                        logger.error(f"OneDrive API error: {resp.status}")
                        return

                    data = await resp.json()

                    for item in data.get("value", []):
                        is_folder = "folder" in item

                        # Check MIME type for files
                        if not is_folder:
                            file_mime = item.get("file", {}).get("mimeType", "")
                            if file_mime not in self.mime_type_filter:
                                # Check by extension
                                name = item.get("name", "")
                                ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                                if ext not in {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "md", "csv"}:
                                    continue

                        # Parse dates
                        modified_at = None
                        created_at = None
                        if item.get("lastModifiedDateTime"):
                            modified_at = datetime.fromisoformat(
                                item["lastModifiedDateTime"].replace("Z", "+00:00")
                            )
                        if item.get("createdDateTime"):
                            created_at = datetime.fromisoformat(
                                item["createdDateTime"].replace("Z", "+00:00")
                            )

                        yield CloudFile(
                            id=item["id"],
                            name=item["name"],
                            path=item.get("parentReference", {}).get("path", "") + "/" + item["name"],
                            provider=CloudProvider.ONEDRIVE,
                            mime_type=item.get("file", {}).get("mimeType"),
                            size_bytes=item.get("size", 0),
                            modified_at=modified_at,
                            created_at=created_at,
                            web_url=item.get("webUrl"),
                            download_url=item.get("@microsoft.graph.downloadUrl"),
                            is_folder=is_folder,
                            parent_id=item.get("parentReference", {}).get("id"),
                            metadata={}
                        )

                        # Recursively discover folder contents
                        if is_folder and self.include_folders:
                            folder_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item['id']}/children"
                            async for sub_item in self._discover_onedrive_folder(folder_url):
                                yield sub_item

                    # Pagination
                    url = data.get("@odata.nextLink")

            except aiohttp.ClientError as e:
                logger.error(f"OneDrive request error: {e}")
                break

            await asyncio.sleep(0.1)

    async def _discover_onedrive_folder(self, url: str, depth: int = 0) -> AsyncIterator[CloudFile]:
        """Recursively discover OneDrive folder contents"""
        if depth > 5 or self._cancelled:  # Max depth
            return

        try:
            async with self._session.get(
                url,
                headers={"Authorization": f"Bearer {self.access_token}"}
            ) as resp:
                if resp.status != 200:
                    return

                data = await resp.json()

                for item in data.get("value", []):
                    is_folder = "folder" in item

                    if not is_folder:
                        file_mime = item.get("file", {}).get("mimeType", "")
                        name = item.get("name", "")
                        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                        if file_mime not in self.mime_type_filter and ext not in {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "md", "csv"}:
                            continue

                    modified_at = None
                    if item.get("lastModifiedDateTime"):
                        modified_at = datetime.fromisoformat(
                            item["lastModifiedDateTime"].replace("Z", "+00:00")
                        )

                    yield CloudFile(
                        id=item["id"],
                        name=item["name"],
                        path=item.get("parentReference", {}).get("path", "") + "/" + item["name"],
                        provider=CloudProvider.ONEDRIVE,
                        mime_type=item.get("file", {}).get("mimeType"),
                        size_bytes=item.get("size", 0),
                        modified_at=modified_at,
                        created_at=None,
                        web_url=item.get("webUrl"),
                        download_url=item.get("@microsoft.graph.downloadUrl"),
                        is_folder=is_folder,
                        parent_id=item.get("parentReference", {}).get("id"),
                    )

                    if is_folder:
                        folder_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item['id']}/children"
                        async for sub in self._discover_onedrive_folder(folder_url, depth + 1):
                            yield sub

        except Exception as e:
            logger.error(f"OneDrive folder discovery error: {e}")

    # ==========================================================================
    # Dropbox
    # ==========================================================================

    async def _discover_dropbox(self) -> AsyncIterator[CloudFile]:
        """Discover files from Dropbox"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        url = "https://api.dropboxapi.com/2/files/list_folder"
        cursor = None

        # Initial request
        body = {
            "path": "",
            "recursive": True,
            "include_non_downloadable_files": False,
            "limit": 100,
        }

        while not self._cancelled:
            try:
                if cursor:
                    url = "https://api.dropboxapi.com/2/files/list_folder/continue"
                    body = {"cursor": cursor}

                async with self._session.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    if resp.status == 401:
                        logger.error("Dropbox: Unauthorized - token may be expired")
                        return

                    if resp.status != 200:
                        logger.error(f"Dropbox API error: {resp.status}")
                        return

                    data = await resp.json()

                    for entry in data.get("entries", []):
                        is_folder = entry.get(".tag") == "folder"

                        if not is_folder:
                            # Check extension
                            name = entry.get("name", "")
                            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                            if ext not in {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "md", "csv"}:
                                continue

                        modified_at = None
                        if entry.get("server_modified"):
                            modified_at = datetime.fromisoformat(
                                entry["server_modified"].replace("Z", "+00:00")
                            )

                        yield CloudFile(
                            id=entry.get("id", ""),
                            name=entry.get("name", ""),
                            path=entry.get("path_display", ""),
                            provider=CloudProvider.DROPBOX,
                            mime_type=None,  # Dropbox doesn't return MIME types directly
                            size_bytes=entry.get("size", 0),
                            modified_at=modified_at,
                            created_at=None,
                            web_url=None,  # Requires separate API call
                            download_url=None,
                            is_folder=is_folder,
                            parent_id=entry.get("parent_shared_folder_id"),
                            metadata={
                                "content_hash": entry.get("content_hash"),
                            }
                        )

                    if not data.get("has_more"):
                        break

                    cursor = data.get("cursor")

            except aiohttp.ClientError as e:
                logger.error(f"Dropbox request error: {e}")
                break

            await asyncio.sleep(0.1)


# Factory function
async def discover_cloud_storage(
    access_token: str,
    provider: str,
    max_results: int = 1000
) -> CloudDiscoveryResult:
    """
    Factory function to discover files from cloud storage.

    Args:
        access_token: OAuth access token
        provider: Provider name (google_drive, onedrive, dropbox)
        max_results: Maximum files to discover

    Returns:
        CloudDiscoveryResult
    """
    provider_enum = CloudProvider(provider)

    async with CloudStorageDiscovery(
        access_token=access_token,
        provider=provider_enum,
        max_results=max_results
    ) as discovery:
        return await discovery.discover_all()
