"""
Session management utilities.
Handles in-memory session storage and cleanup.
"""
from datetime import datetime, timedelta
from uuid import uuid4


class TokenInfo:
    """Information about a selected token."""

    def __init__(
        self,
        token_id: int,
        token_text: str,
        probability: float,
        category: str,
        sampled_from_other: bool = False,
    ):
        self.token_id = token_id
        self.token_text = token_text
        self.probability = probability
        self.category = category
        self.sampled_from_other = sampled_from_other
        self.selected_at = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = {
            "token_id": self.token_id,
            "token_text": self.token_text,
            "probability": self.probability,
            "category": self.category,
            "selected_at": self.selected_at.isoformat() + "Z",
        }
        if self.sampled_from_other:
            result["sampled_from_other"] = True
        return result


class Session:
    """Session class for managing user state."""

    def __init__(self, model_name: str = "gpt2"):
        self.session_id = str(uuid4())
        self.model_name = model_name
        self.initial_prompt = ""
        self.token_history: list[TokenInfo] = []
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()

    @property
    def current_text(self) -> str:
        """Get current text (prompt + generated tokens)."""
        text = self.initial_prompt
        for token in self.token_history:
            text += token.token_text
        return text

    @property
    def generation_count(self) -> int:
        """Number of generated tokens."""
        return len(self.token_history)

    def set_prompt(self, prompt: str):
        """Set the initial prompt and reset history."""
        self.initial_prompt = prompt
        self.token_history = []
        self.last_accessed = datetime.utcnow()

    def append_token(self, token_info: TokenInfo):
        """Append a token to the history."""
        self.token_history.append(token_info)
        self.last_accessed = datetime.utcnow()

    def undo_last_token(self) -> TokenInfo | None:
        """Remove the last token from history."""
        if not self.token_history:
            return None
        self.last_accessed = datetime.utcnow()
        return self.token_history.pop()

    def is_expired(self, ttl_hours: int = 1) -> bool:
        """Check if session has expired."""
        expiry = self.last_accessed + timedelta(hours=ttl_hours)
        return datetime.utcnow() > expiry

    def to_dict(self):
        """Convert session to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "model_name": self.model_name,
            "initial_prompt": self.initial_prompt,
            "current_text": self.current_text,
            "token_history": [token.to_dict() for token in self.token_history],
            "generation_count": self.generation_count,
            "created_at": self.created_at.isoformat() + "Z",
            "last_accessed": self.last_accessed.isoformat() + "Z",
        }


class SessionManager:
    """Manager for all sessions."""

    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def create_session(self, model_name: str = "gpt2") -> Session:
        """Create a new session."""
        session = Session(model_name=model_name)
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if session:
            session.last_accessed = datetime.utcnow()
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def cleanup_expired_sessions(self, ttl_hours: int = 1):
        """Remove expired sessions."""
        expired_sessions = [
            sid
            for sid, session in self.sessions.items()
            if session.is_expired(ttl_hours)
        ]
        for sid in expired_sessions:
            del self.sessions[sid]
        return len(expired_sessions)

    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self.sessions)


# Global session manager instance
session_manager = SessionManager()
