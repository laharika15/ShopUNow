from agent import run_agent
from memory import conversation_memory


def test_conversation_memory():
    session_id = "memory-test-user"

    # Start with a clean session
    conversation_memory.clear(session_id)

    print("\n--- Conversation Memory Test ---")

    # First conversation turn
    first_query = "How do I apply for a vacation day?"

    result1 = run_agent(
        query=first_query,
        session_id=session_id,
    )

    print("\nQ1:", first_query)
    print("A1:", result1.get("response", ""))

    # Follow-up question that depends on conversation context
    second_query = "What about sick leave?"

    result2 = run_agent(
        query=second_query,
        session_id=session_id,
    )

    print("\nQ2:", second_query)
    print("A2:", result2.get("response", ""))

    # Verify that both turns were stored
    history = conversation_memory.get_history(session_id)

    assert len(history) == 2

    assert history[0]["user"] == first_query
    assert history[1]["user"] == second_query

    print("\nConversation memory test passed.")


def test_multi_user_isolation():
    user_a = "user-A"
    user_b = "user-B"

    # Start with clean sessions
    conversation_memory.clear(user_a)
    conversation_memory.clear(user_b)

    # User A
    run_agent(
        query="How do I apply for vacation?",
        session_id=user_a,
    )

    # User B
    run_agent(
        query="How do I reset my password?",
        session_id=user_b,
    )

    history_a = conversation_memory.get_history(user_a)
    history_b = conversation_memory.get_history(user_b)

    # Each user should have only their own conversation
    assert len(history_a) == 1
    assert len(history_b) == 1

    assert "vacation" in history_a[0]["user"].lower()
    assert "password" in history_b[0]["user"].lower()

    print("Multi-user isolation test passed.")


if __name__ == "__main__":
    test_conversation_memory()
    test_multi_user_isolation()

    print("\nAll memory tests passed successfully.")
