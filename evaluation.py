from agent import graph_app, route_query
from retrieval import (
    ABSTENTION_MESSAGE,
    expand_query_with_synonyms,
)


# ============================================================
# DETERMINISTIC ROUTING TESTS
# ============================================================

def run_routing_unit_tests():
    test_cases = [
        (
            "Known IT department",
            {
                "scope": "In-Scope",
                "department": "IT Support",
                "sentiment": "Neutral",
            },
            "rag",
        ),
        (
            "Known HR department",
            {
                "scope": "In-Scope",
                "department": "HR",
                "sentiment": "Positive",
            },
            "rag",
        ),
        (
            "Unknown department requests clarification",
            {
                "scope": "In-Scope",
                "department": "Unknown",
                "sentiment": "Neutral",
            },
            "clarify",
        ),
        (
            "Negative billing query escalates",
            {
                "scope": "In-Scope",
                "department": "Billing & Payments",
                "sentiment": "Negative",
            },
            "escalate",
        ),
        (
            "Out-of-scope query is not escalated",
            {
                "scope": "Out-of-Scope",
                "department": "Unknown",
                "sentiment": "Neutral",
            },
            "out_of_scope",
        ),
        (
            "Negative in-scope unknown query escalates",
            {
                "scope": "In-Scope",
                "department": "Unknown",
                "sentiment": "Negative",
            },
            "escalate",
        ),
    ]

    failures = []

    for name, state, expected in test_cases:
        actual = route_query(state)
        if actual != expected:
            failures.append(
                f"{name}: expected {expected!r}, got {actual!r}"
            )

    if failures:
        raise AssertionError(
            "Routing unit tests failed:\n" + "\n".join(failures)
        )

    print(
        f"Routing unit tests: "
        f"{len(test_cases)}/{len(test_cases)} passed."
    )


# ============================================================
# QUERY EXPANSION TESTS
# ============================================================

def run_query_expansion_tests():
    test_cases = [
        (
            "my computer is slow",
            ["laptop", "poor performance"],
        ),
        (
            "I was charged twice",
            ["duplicate charge"],
        ),
        (
            "my package has not arrived",
            ["parcel", "delayed shipment"],
        ),
        (
            "I need time off",
            ["vacation", "leave request"],
        ),
    ]

    failures = []

    for query, expected_terms in test_cases:
        expanded = expand_query_with_synonyms(query).lower()
        missing = [
            term
            for term in expected_terms
            if term.lower() not in expanded
        ]

        if missing:
            failures.append(
                f"{query!r}: expected terms not found: {missing}"
            )

    if failures:
        raise AssertionError(
            "Query expansion tests failed:\n" + "\n".join(failures)
        )

    print(
        f"Query expansion tests: "
        f"{len(test_cases)}/{len(test_cases)} passed."
    )


# ============================================================
# END-TO-END AGENT EVALUATION
# ============================================================

def run_evaluation():
    print("\nStarting ShopUNow end-to-end evaluation...\n")

    test_cases = [
        {
            "name": "HR vacation question",
            "query": "How do I apply for a vacation day?",
            "expected_department": "HR",
            "expected_scope": "In-Scope",
            "expected_escalation": False,
        },
        {
            "name": "Informal IT performance question",
            "query": "My computer is slow.",
            "expected_department": "IT Support",
            "expected_scope": "In-Scope",
            "expected_escalation": False,
        },
        {
            "name": "Informal IT account-access question",
            "query": "I can't get into my account.",
            "expected_department": "IT Support",
            "expected_scope": "In-Scope",
            "expected_escalation": False,
        },
        {
            "name": "Billing duplicate charge",
            "query": "I was charged twice.",
            "expected_department": "Billing & Payments",
            "expected_scope": "In-Scope",
            "expected_escalation": False,
        },
        {
            "name": "Informal shipping delay",
            "query": "I've been waiting a week and my package isn't here.",
            "expected_department": "Shipping & Delivery",
            "expected_scope": "In-Scope",
            "expected_escalation": False,
        },
        {
            "name": "Informal HR time-off question",
            "query": "I need some time off next month.",
            "expected_department": "HR",
            "expected_scope": "In-Scope",
            "expected_escalation": False,
        },
        {
            "name": "Negative billing complaint",
            "query": (
                "I'm furious! You overcharged me for my last order "
                "and I demand a refund right now!"
            ),
            "expected_department": "Billing & Payments",
            "expected_scope": "In-Scope",
            "expected_escalation": True,
        },
        {
            "name": "Out-of-scope question",
            "query": "What is the capital of France?",
            "expected_scope": "Out-of-Scope",
            "expected_escalation": False,
            "expected_out_of_scope_response": True,
        },
        {
            "name": "In-scope knowledge gap",
            "query": (
                "Does ShopUNow offer ten years of unpaid "
                "parental leave?"
            ),
            "expected_department": "HR",
            "expected_scope": "In-Scope",
            "expected_abstention": True,
            "expected_escalation": False,
        },
        {
            "name": "Ambiguous question requests clarification",
            "query": "Can you help me with something?",
            "expected_escalation": False,
            "expected_clarification": True,
        },
    ]

    passed = 0
    total = len(test_cases)

    for index, test_case in enumerate(test_cases, start=1):
        print(f"Test {index}: {test_case['name']}")
        print(f"  Query: {test_case['query']}")

        try:
            result = graph_app.invoke({
                "query": test_case["query"],
                "conversation_history": [],
            })
        except Exception as exc:
            print(f"  [FAIL] Agent execution error: {exc}\n")
            continue

        department = result.get("department")
        scope = result.get("scope")
        sentiment = result.get("sentiment")
        response = str(result.get("response", ""))
        response_lower = response.lower()
        needs_escalation = result.get("needs_escalation", False)

        test_passed = True

        # Check expected department.
        if "expected_department" in test_case:
            expected = test_case["expected_department"]
            if department != expected:
                print(
                    f"  [FAIL] Department: expected {expected!r}, "
                    f"got {department!r}"
                )
                test_passed = False

        # Check expected scope.
        if "expected_scope" in test_case:
            expected = test_case["expected_scope"]
            if scope != expected:
                print(
                    f"  [FAIL] Scope: expected {expected!r}, "
                    f"got {scope!r}"
                )
                test_passed = False

        # Check whether escalation was requested.
        expected_escalation = test_case.get(
            "expected_escalation", False
        )
        if needs_escalation != expected_escalation:
            print(
                f"  [FAIL] Escalation: expected {expected_escalation}, "
                f"got {needs_escalation}"
            )
            test_passed = False

        # Check the escalation response wording.
        if expected_escalation:
            escalation_phrases = (
                "support representative",
                "support form",
                "follow up",
            )
            if not any(
                phrase in response_lower
                for phrase in escalation_phrases
            ):
                print(
                    "  [FAIL] Response does not appear to explain "
                    f"the support escalation: {response}"
                )
                test_passed = False

        # Out-of-scope questions should not trigger escalation.
        if test_case.get("expected_out_of_scope_response"):
            if "shopunow ai assistant" not in response_lower:
                print(
                    "  [FAIL] Expected the ShopUNow out-of-scope "
                    f"response, got: {response}"
                )
                test_passed = False

        # Knowledge-gap questions should produce controlled abstention.
        if test_case.get("expected_abstention"):
            if ABSTENTION_MESSAGE.lower() not in response_lower:
                print(
                    "  [FAIL] Expected controlled abstention, "
                    f"got: {response}"
                )
                test_passed = False

        # Ambiguous in-scope questions should request clarification.
        if test_case.get("expected_clarification"):
            clarification_phrases = (
                "share a little more detail",
                "direct you to the right information",
            )
            if not all(
                phrase in response_lower
                for phrase in clarification_phrases
            ):
                print(
                    "  [FAIL] Expected a clarification response, "
                    f"got: {response}"
                )
                test_passed = False

        # Classification tests do not require the KB to answer every
        # informal query. The knowledge base may legitimately abstain.
        if test_passed:
            print(
                f"  [PASS] Sentiment={sentiment}, "
                f"Department={department}, Scope={scope}"
            )
            passed += 1

        print()

    print("=" * 60)
    print(f"End-to-end evaluation: {passed}/{total} tests passed.")
    print("=" * 60)

    if passed == total:
        print("SUCCESS: All end-to-end tests passed.")
    else:
        print(
            "WARNING: Some tests failed. Review the details above. "
            "A classification failure may indicate a routing issue; "
            "an abstention may indicate missing FAQ coverage or "
            "retrieval settings that need investigation."
        )


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":
    run_routing_unit_tests()
    run_query_expansion_tests()
    run_evaluation()
