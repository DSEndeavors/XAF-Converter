"""Session management: in-memory storage, expiry, and cleanup."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from ..utils.security import safe_path, validate_uuid

logger = logging.getLogger(__name__)

# Configurable base directory for temp files
TEMP_BASE = os.environ.get("XAF_TEMP_BASE", os.path.join(os.path.dirname(__file__), "..", "..", "tmp"))

# Session lifetime in seconds (1 hour)
SESSION_LIFETIME = 3600

# Cleanup grace period: remove sessions older than 70 minutes
CLEANUP_MAX_AGE = 70 * 60

# Cleanup interval: every 5 minutes
CLEANUP_INTERVAL = 5 * 60


@dataclass
class SessionData:
    """Holds all data for a single upload session."""
    session_id: str
    created_at: float  # time.time()
    original_filename: str = ""
    file_size: int = 0
    xaf_version: str = ""
    fiscal_year: str = ""
    company_name: str = ""
    validation_checks: list[dict[str, Any]] = field(default_factory=list)
    temp_dir: str = ""
    # Parsed data stored as plain dicts for serialization
    parsed_data: dict[str, Any] = field(default_factory=dict)
    # WebSocket connections for progress updates
    ws_connections: list[Any] = field(default_factory=list)


class SessionManager:
    """Manages upload sessions with in-memory storage and timed cleanup."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._base_dir: str = ""

    def initialize(self) -> None:
        """Initialize the session manager: create temp base dir, purge old sessions."""
        self._base_dir = os.path.realpath(TEMP_BASE)
        os.makedirs(self._base_dir, exist_ok=True)
        # Set restrictive umask
        os.umask(0o077)
        # Purge all existing session directories on startup
        self._purge_all_dirs()

    def _purge_all_dirs(self) -> None:
        """Remove all subdirectories in the temp base (startup cleanup)."""
        if not os.path.isdir(self._base_dir):
            return
        for entry in os.listdir(self._base_dir):
            entry_path = os.path.join(self._base_dir, entry)
            if os.path.isdir(entry_path):
                try:
                    shutil.rmtree(entry_path, ignore_errors=False)
                    logger.info("Purged old session dir: %s", entry)
                except OSError as exc:
                    logger.warning("Failed to purge %s: %s", entry, exc)

    def create_session(self) -> SessionData:
        """Create a new session with a unique ID and temp directory."""
        session_id = str(uuid.uuid4())
        session_dir = safe_path(self._base_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)

        session = SessionData(
            session_id=session_id,
            created_at=time.time(),
            temp_dir=session_dir,
        )
        self._sessions[session_id] = session
        logger.info("Created session %s", session_id)
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve a session by ID, validating the UUID format."""
        if not validate_uuid(session_id):
            return None
        session = self._sessions.get(session_id)
        if session is None:
            return None
        # Check expiry
        if time.time() - session.created_at > SESSION_LIFETIME:
            self.destroy_session(session_id)
            return None
        return session

    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session and delete its temp directory."""
        session = self._sessions.pop(session_id, None)
        if session is None:
            return False
        if session.temp_dir and os.path.isdir(session.temp_dir):
            try:
                shutil.rmtree(session.temp_dir, ignore_errors=False)
            except OSError as exc:
                logger.warning("Failed to remove session dir %s: %s", session_id, exc)
        logger.info("Destroyed session %s", session_id)
        return True

    def cleanup_expired(self) -> int:
        """Remove all sessions older than CLEANUP_MAX_AGE. Returns count removed."""
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.created_at > CLEANUP_MAX_AGE
        ]
        for sid in expired:
            self.destroy_session(sid)
        if expired:
            logger.info("Cleaned up %d expired sessions", len(expired))
        return len(expired)

    async def start_cleanup_loop(self) -> None:
        """Start the background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_loop(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        """Periodically clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL)
                self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in session cleanup loop")

    @property
    def base_dir(self) -> str:
        return self._base_dir

    @property
    def active_sessions(self) -> int:
        return len(self._sessions)


# Global singleton
session_manager = SessionManager()
