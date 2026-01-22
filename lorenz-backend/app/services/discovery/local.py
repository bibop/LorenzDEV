"""
LORENZ SaaS - Local Discovery Service
=====================================

Automatic discovery of local files on user's computer.
Scans standard directories for documents, emails, calendars.

Note: This runs on the user's LOCAL machine (desktop app / CLI agent)
      and reports back to the backend.
"""

import os
import asyncio
import logging
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Callable, AsyncIterator
from enum import Enum
import platform
import json

logger = logging.getLogger(__name__)


class FileCategory(str, Enum):
    """Categories of discoverable files"""
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    PDF = "pdf"
    IMAGE = "image"
    EMAIL_ARCHIVE = "email_archive"  # .mbox, .pst, .eml
    CALENDAR = "calendar"  # .ics, .ical
    NOTE = "note"  # .md, .txt, Apple Notes, etc.
    CODE = "code"
    OTHER = "other"


# File extensions by category
EXTENSION_CATEGORIES = {
    # Documents
    ".doc": FileCategory.DOCUMENT,
    ".docx": FileCategory.DOCUMENT,
    ".odt": FileCategory.DOCUMENT,
    ".rtf": FileCategory.DOCUMENT,
    ".pages": FileCategory.DOCUMENT,

    # Spreadsheets
    ".xls": FileCategory.SPREADSHEET,
    ".xlsx": FileCategory.SPREADSHEET,
    ".ods": FileCategory.SPREADSHEET,
    ".csv": FileCategory.SPREADSHEET,
    ".numbers": FileCategory.SPREADSHEET,

    # Presentations
    ".ppt": FileCategory.PRESENTATION,
    ".pptx": FileCategory.PRESENTATION,
    ".odp": FileCategory.PRESENTATION,
    ".key": FileCategory.PRESENTATION,

    # PDFs
    ".pdf": FileCategory.PDF,

    # Notes/Text
    ".txt": FileCategory.NOTE,
    ".md": FileCategory.NOTE,
    ".markdown": FileCategory.NOTE,
    ".rst": FileCategory.NOTE,

    # Email archives
    ".mbox": FileCategory.EMAIL_ARCHIVE,
    ".pst": FileCategory.EMAIL_ARCHIVE,
    ".ost": FileCategory.EMAIL_ARCHIVE,
    ".eml": FileCategory.EMAIL_ARCHIVE,
    ".emlx": FileCategory.EMAIL_ARCHIVE,

    # Calendars
    ".ics": FileCategory.CALENDAR,
    ".ical": FileCategory.CALENDAR,
    ".vcs": FileCategory.CALENDAR,

    # Images (for OCR)
    ".png": FileCategory.IMAGE,
    ".jpg": FileCategory.IMAGE,
    ".jpeg": FileCategory.IMAGE,
    ".tiff": FileCategory.IMAGE,
    ".tif": FileCategory.IMAGE,
    ".webp": FileCategory.IMAGE,
}


@dataclass
class DiscoveredFile:
    """A discovered file on the local system"""
    path: str
    filename: str
    category: FileCategory
    size_bytes: int
    modified_at: datetime
    created_at: Optional[datetime]
    mime_type: Optional[str]
    content_hash: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "filename": self.filename,
            "category": self.category.value,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "mime_type": self.mime_type,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DiscoveredFile":
        return cls(
            path=data["path"],
            filename=data["filename"],
            category=FileCategory(data["category"]),
            size_bytes=data["size_bytes"],
            modified_at=datetime.fromisoformat(data["modified_at"]) if data.get("modified_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            mime_type=data.get("mime_type"),
            content_hash=data.get("content_hash"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DiscoveryResult:
    """Result of local discovery scan"""
    scan_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    directories_scanned: List[str]
    files_found: int
    files_by_category: Dict[str, int]
    total_size_bytes: int
    files: List[DiscoveredFile]
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "scan_id": self.scan_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "directories_scanned": self.directories_scanned,
            "files_found": self.files_found,
            "files_by_category": self.files_by_category,
            "total_size_bytes": self.total_size_bytes,
            "files": [f.to_dict() for f in self.files],
            "errors": self.errors,
        }


class LocalDiscoveryService:
    """
    Discovers local files for initial user setup.

    This service is designed to run on the user's LOCAL machine
    (via a desktop app or CLI agent) and report findings back to the backend.

    Features:
    - Scans standard user directories
    - Categorizes files by type
    - Detects email archives (Outlook PST, Apple Mail, Thunderbird)
    - Finds calendar files (ICS)
    - Respects privacy (only indexes metadata by default)
    """

    def __init__(
        self,
        max_file_size_mb: int = 100,
        include_hidden: bool = False,
        compute_hashes: bool = False,
        categories_filter: Optional[Set[FileCategory]] = None
    ):
        """
        Initialize local discovery service.

        Args:
            max_file_size_mb: Maximum file size to index
            include_hidden: Include hidden files/directories
            compute_hashes: Compute content hashes (slower)
            categories_filter: Only include these categories
        """
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.include_hidden = include_hidden
        self.compute_hashes = compute_hashes
        self.categories_filter = categories_filter

        self._progress_callback: Optional[Callable] = None
        self._cancelled = False

    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """Set callback for progress: callback(current_dir, files_found, dirs_scanned)"""
        self._progress_callback = callback

    def cancel(self):
        """Cancel ongoing scan"""
        self._cancelled = True

    def get_standard_directories(self) -> List[Path]:
        """Get standard directories to scan based on OS"""
        home = Path.home()
        system = platform.system()

        directories = []

        # Common directories
        common = [
            home / "Documents",
            home / "Desktop",
            home / "Downloads",
        ]
        directories.extend([d for d in common if d.exists()])

        if system == "Darwin":  # macOS
            mac_dirs = [
                home / "Library" / "Mail",  # Apple Mail
                home / "Library" / "Calendars",  # Apple Calendar
                home / "Library" / "Mobile Documents" / "com~apple~CloudDocs",  # iCloud Drive
                home / "Library" / "Group Containers" / "group.com.apple.notes",  # Apple Notes
            ]
            directories.extend([d for d in mac_dirs if d.exists()])

        elif system == "Windows":
            win_dirs = [
                Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Outlook",  # Outlook
                Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Outlook",
                home / "OneDrive",  # OneDrive local folder
            ]
            directories.extend([d for d in win_dirs if d.exists()])

        elif system == "Linux":
            linux_dirs = [
                home / ".thunderbird",  # Thunderbird
                home / ".local" / "share" / "evolution",  # Evolution
                home / ".config" / "google-chrome",  # Chrome data
            ]
            directories.extend([d for d in linux_dirs if d.exists()])

        return directories

    def get_email_client_locations(self) -> Dict[str, Path]:
        """Get locations of known email clients"""
        home = Path.home()
        system = platform.system()

        locations = {}

        if system == "Darwin":
            mail_v2 = home / "Library" / "Mail" / "V2"
            mail_v9 = home / "Library" / "Mail" / "V9"  # Newer macOS
            mail_v10 = home / "Library" / "Mail" / "V10"

            for mail_dir in [mail_v10, mail_v9, mail_v2]:
                if mail_dir.exists():
                    locations["apple_mail"] = mail_dir
                    break

            thunderbird = home / "Library" / "Thunderbird" / "Profiles"
            if thunderbird.exists():
                locations["thunderbird"] = thunderbird

        elif system == "Windows":
            outlook_data = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Outlook"
            if outlook_data.exists():
                locations["outlook"] = outlook_data

            thunderbird = Path(os.environ.get("APPDATA", "")) / "Thunderbird" / "Profiles"
            if thunderbird.exists():
                locations["thunderbird"] = thunderbird

        elif system == "Linux":
            thunderbird = home / ".thunderbird"
            if thunderbird.exists():
                locations["thunderbird"] = thunderbird

            evolution = home / ".local" / "share" / "evolution" / "mail"
            if evolution.exists():
                locations["evolution"] = evolution

        return locations

    def get_calendar_locations(self) -> Dict[str, Path]:
        """Get locations of calendar data"""
        home = Path.home()
        system = platform.system()

        locations = {}

        if system == "Darwin":
            calendars = home / "Library" / "Calendars"
            if calendars.exists():
                locations["apple_calendar"] = calendars

        elif system == "Windows":
            # Windows Calendar data is typically synced via outlook.com
            # Local ICS files can be in Documents
            pass

        return locations

    async def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        max_depth: int = 5
    ) -> AsyncIterator[DiscoveredFile]:
        """
        Scan a directory for files.

        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            max_depth: Maximum recursion depth

        Yields:
            DiscoveredFile objects
        """
        if self._cancelled:
            return

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return

        try:
            for entry in directory.iterdir():
                if self._cancelled:
                    return

                # Skip hidden files/dirs if configured
                if not self.include_hidden and entry.name.startswith('.'):
                    continue

                if entry.is_file():
                    discovered = await self._process_file(entry)
                    if discovered:
                        yield discovered

                elif entry.is_dir() and recursive and max_depth > 0:
                    # Skip system directories
                    if entry.name in {'node_modules', '__pycache__', '.git', '.svn', 'venv', '.venv'}:
                        continue

                    async for sub_file in self.scan_directory(entry, recursive, max_depth - 1):
                        yield sub_file

        except PermissionError:
            logger.debug(f"Permission denied: {directory}")
        except Exception as e:
            logger.error(f"Error scanning {directory}: {e}")

    async def _process_file(self, file_path: Path) -> Optional[DiscoveredFile]:
        """Process a single file and return DiscoveredFile if relevant"""
        try:
            # Get extension and category
            ext = file_path.suffix.lower()
            category = EXTENSION_CATEGORIES.get(ext)

            if not category:
                return None

            # Apply category filter if set
            if self.categories_filter and category not in self.categories_filter:
                return None

            # Get file stats
            stat = file_path.stat()

            # Skip files that are too large
            if stat.st_size > self.max_file_size:
                logger.debug(f"Skipping large file: {file_path} ({stat.st_size} bytes)")
                return None

            # Get mime type
            mime_type, _ = mimetypes.guess_type(str(file_path))

            # Compute hash if enabled
            content_hash = None
            if self.compute_hashes and stat.st_size < 50 * 1024 * 1024:  # Only for files < 50MB
                content_hash = await self._compute_file_hash(file_path)

            # Get created time (platform-specific)
            created_at = None
            try:
                if platform.system() == "Darwin":
                    created_at = datetime.fromtimestamp(stat.st_birthtime)
                elif platform.system() == "Windows":
                    created_at = datetime.fromtimestamp(stat.st_ctime)
            except (AttributeError, OSError):
                pass

            return DiscoveredFile(
                path=str(file_path),
                filename=file_path.name,
                category=category,
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                created_at=created_at,
                mime_type=mime_type,
                content_hash=content_hash,
                metadata={
                    "extension": ext,
                    "parent_dir": str(file_path.parent.name),
                }
            )

        except Exception as e:
            logger.debug(f"Error processing file {file_path}: {e}")
            return None

    async def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content"""
        def _hash_file():
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _hash_file)

    async def run_full_discovery(
        self,
        additional_directories: Optional[List[Path]] = None
    ) -> DiscoveryResult:
        """
        Run a full discovery scan.

        Args:
            additional_directories: Extra directories to scan

        Returns:
            DiscoveryResult with all discovered files
        """
        import uuid

        scan_id = str(uuid.uuid4())
        started_at = datetime.now()

        # Get directories to scan
        directories = self.get_standard_directories()
        if additional_directories:
            directories.extend(additional_directories)

        all_files: List[DiscoveredFile] = []
        errors: List[str] = []
        dirs_scanned = 0

        logger.info(f"Starting local discovery scan {scan_id}")
        logger.info(f"Scanning {len(directories)} directories")

        for directory in directories:
            if self._cancelled:
                break

            logger.info(f"Scanning: {directory}")
            dirs_scanned += 1

            try:
                async for discovered_file in self.scan_directory(directory):
                    all_files.append(discovered_file)

                    # Update progress
                    if self._progress_callback:
                        self._progress_callback(str(directory), len(all_files), dirs_scanned)

            except Exception as e:
                error_msg = f"Error scanning {directory}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Calculate statistics
        files_by_category = {}
        total_size = 0

        for f in all_files:
            cat = f.category.value
            files_by_category[cat] = files_by_category.get(cat, 0) + 1
            total_size += f.size_bytes

        result = DiscoveryResult(
            scan_id=scan_id,
            started_at=started_at,
            completed_at=datetime.now(),
            directories_scanned=[str(d) for d in directories],
            files_found=len(all_files),
            files_by_category=files_by_category,
            total_size_bytes=total_size,
            files=all_files,
            errors=errors,
        )

        logger.info(f"Discovery complete: {len(all_files)} files found")
        logger.info(f"By category: {files_by_category}")

        return result

    async def quick_scan(self) -> Dict:
        """
        Quick scan to estimate what's available.
        Returns summary without full file list.
        """
        directories = self.get_standard_directories()
        email_locations = self.get_email_client_locations()
        calendar_locations = self.get_calendar_locations()

        summary = {
            "directories_available": [str(d) for d in directories],
            "email_clients_detected": list(email_locations.keys()),
            "calendar_sources_detected": list(calendar_locations.keys()),
            "estimated_scan_dirs": len(directories),
            "platform": platform.system(),
            "home_dir": str(Path.home()),
        }

        # Quick count of files in standard dirs
        file_counts = {}
        for directory in directories[:3]:  # Just first 3 for quick scan
            try:
                count = sum(1 for _ in directory.iterdir() if _.is_file())
                file_counts[str(directory)] = count
            except Exception:
                pass

        summary["file_counts_sample"] = file_counts

        return summary


# CLI helper for running on user's machine
async def run_discovery_cli():
    """CLI entrypoint for local discovery agent"""
    import argparse

    parser = argparse.ArgumentParser(description="LORENZ Local Discovery Agent")
    parser.add_argument("--output", "-o", default="discovery_result.json", help="Output file")
    parser.add_argument("--categories", "-c", nargs="+", help="Filter categories")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files")
    parser.add_argument("--compute-hashes", action="store_true", help="Compute file hashes")
    parser.add_argument("--quick", action="store_true", help="Quick scan only")

    args = parser.parse_args()

    categories = None
    if args.categories:
        categories = {FileCategory(c) for c in args.categories}

    service = LocalDiscoveryService(
        include_hidden=args.include_hidden,
        compute_hashes=args.compute_hashes,
        categories_filter=categories
    )

    def progress(directory, files, dirs):
        print(f"\r  Scanning... {files} files found in {dirs} directories", end="", flush=True)

    service.set_progress_callback(progress)

    if args.quick:
        print("Running quick scan...")
        result = await service.quick_scan()
    else:
        print("Running full discovery scan...")
        result = await service.run_full_discovery()
        result = result.to_dict()

    print(f"\n\nSaving results to {args.output}")

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print("Done!")
    return result


if __name__ == "__main__":
    asyncio.run(run_discovery_cli())
