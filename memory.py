from collections import defaultdict
from threading import Lock


MAX_TURNS = 10


class ConversationMemory:
    """
    Lightweight in-process conversation memory.

    Each session_id gets its own conversation history.
    This provides multi-user isolation while keeping the
    implementation simple for the capstone application.
    """

    def __init__(self, max_turns: int = MAX_TURNS):
        self._store = defaultdict(list)
        self._lock = Lock()
        self.max_turns = max_turns

    def get_history(self, session_id: str) -> list[dict]:
        with self._lock:
            return list(self._store.get(session_id, []))

    def add_turn(
        self,
        session_id: str,
        user_query: str,
        assistant_response: str,
    ) -> None:

        with self._lock:
            self._store[session_id].append(
                {
                    "user": user_query,
                    "assistant": assistant_response,
                }
            )

            # Keep only the most recent turns.
            self._store[session_id] = self._store[
                session_id
            ][-self.max_turns:]

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

conversation_memory = ConversationMemory()
