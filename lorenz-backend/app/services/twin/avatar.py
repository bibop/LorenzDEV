"""
LORENZ SaaS - Avatar Session Service
=====================================

WebRTC signaling and session management for 3D avatar interactions.
Handles real-time communication between client and avatar rendering.
"""

import os
import logging
import json
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    PENDING = "pending"
    CONNECTING = "connecting"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


@dataclass
class AvatarSession:
    """Represents an active avatar session"""
    session_id: str
    user_id: str
    tenant_id: str
    state: SessionState
    created_at: datetime
    voice_id: Optional[str] = None
    avatar_model: str = "default"
    ice_candidates: List[Dict[str, Any]] = field(default_factory=list)
    sdp_offer: Optional[str] = None
    sdp_answer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "voice_id": self.voice_id,
            "avatar_model": self.avatar_model,
            "ice_candidates_count": len(self.ice_candidates),
            "has_sdp_offer": self.sdp_offer is not None,
            "has_sdp_answer": self.sdp_answer is not None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AvatarSession":
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            state=SessionState(data["state"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            voice_id=data.get("voice_id"),
            avatar_model=data.get("avatar_model", "default"),
            ice_candidates=data.get("ice_candidates", []),
            sdp_offer=data.get("sdp_offer"),
            sdp_answer=data.get("sdp_answer"),
            metadata=data.get("metadata", {})
        )


class AvatarSessionManager:
    """
    Manages WebRTC sessions for 3D avatar interactions.
    Uses Redis for session state and signaling.
    """

    SESSION_TTL = 3600  # 1 hour
    SESSION_PREFIX = "lorenz:avatar:session:"
    SIGNALING_PREFIX = "lorenz:avatar:signal:"

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or getattr(settings, "REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()

    async def create_session(
        self,
        user_id: str,
        tenant_id: str,
        voice_id: Optional[str] = None,
        avatar_model: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AvatarSession:
        """Create a new avatar session"""
        session = AvatarSession(
            session_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            state=SessionState.PENDING,
            created_at=datetime.utcnow(),
            voice_id=voice_id,
            avatar_model=avatar_model,
            metadata=metadata or {}
        )

        r = await self._get_redis()
        key = f"{self.SESSION_PREFIX}{session.session_id}"

        await r.setex(
            key,
            self.SESSION_TTL,
            json.dumps(session.to_dict())
        )

        logger.info(f"Created avatar session: {session.session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[AvatarSession]:
        """Get session by ID"""
        r = await self._get_redis()
        key = f"{self.SESSION_PREFIX}{session_id}"

        data = await r.get(key)
        if not data:
            return None

        return AvatarSession.from_dict(json.loads(data))

    async def update_session(self, session: AvatarSession) -> bool:
        """Update session state"""
        r = await self._get_redis()
        key = f"{self.SESSION_PREFIX}{session.session_id}"

        # Check if session exists
        if not await r.exists(key):
            return False

        await r.setex(
            key,
            self.SESSION_TTL,
            json.dumps(session.to_dict())
        )
        return True

    async def end_session(self, session_id: str) -> bool:
        """End and remove a session"""
        r = await self._get_redis()
        key = f"{self.SESSION_PREFIX}{session_id}"

        session = await self.get_session(session_id)
        if session:
            session.state = SessionState.ENDED
            await r.setex(key, 60, json.dumps(session.to_dict()))  # Keep for 1 minute
            logger.info(f"Ended avatar session: {session_id}")
            return True
        return False

    async def set_sdp_offer(self, session_id: str, sdp: str) -> bool:
        """Set SDP offer from client"""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.sdp_offer = sdp
        session.state = SessionState.CONNECTING
        return await self.update_session(session)

    async def set_sdp_answer(self, session_id: str, sdp: str) -> bool:
        """Set SDP answer from server"""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.sdp_answer = sdp
        session.state = SessionState.ACTIVE
        return await self.update_session(session)

    async def add_ice_candidate(
        self,
        session_id: str,
        candidate: Dict[str, Any],
        from_client: bool = True
    ) -> bool:
        """Add ICE candidate to session"""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.ice_candidates.append({
            "candidate": candidate,
            "from_client": from_client,
            "timestamp": datetime.utcnow().isoformat()
        })
        return await self.update_session(session)

    async def get_user_sessions(self, user_id: str) -> List[AvatarSession]:
        """Get all sessions for a user"""
        r = await self._get_redis()
        sessions = []

        # Scan for user's sessions
        async for key in r.scan_iter(f"{self.SESSION_PREFIX}*"):
            data = await r.get(key)
            if data:
                session = AvatarSession.from_dict(json.loads(data))
                if session.user_id == user_id and session.state != SessionState.ENDED:
                    sessions.append(session)

        return sessions

    async def publish_signaling_message(
        self,
        session_id: str,
        message_type: str,
        data: Dict[str, Any]
    ):
        """Publish signaling message via Redis pub/sub"""
        r = await self._get_redis()
        channel = f"{self.SIGNALING_PREFIX}{session_id}"

        await r.publish(channel, json.dumps({
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }))

    async def subscribe_signaling(self, session_id: str):
        """Subscribe to signaling messages for a session"""
        r = await self._get_redis()
        pubsub = r.pubsub()
        channel = f"{self.SIGNALING_PREFIX}{session_id}"

        await pubsub.subscribe(channel)
        return pubsub


# Singleton
_session_manager: Optional[AvatarSessionManager] = None


def get_avatar_session_manager() -> AvatarSessionManager:
    """Get or create avatar session manager singleton"""
    global _session_manager
    if _session_manager is None:
        _session_manager = AvatarSessionManager()
    return _session_manager
