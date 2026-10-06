from agent import graph_app


ABSTENTION_MESSAGE = (
    "I don't have enough information in the ShopUNow "
    "knowledge base to answer this accurately."
)


def run_evaluation():
    print("Starting ShopUNow Evaluation Suite...\n")

    test_cases = [
        {
            "name": "HR RAG",
            "query": "How do I apply for a vacation day?",
            "expected_department": "HR",
            "expected_scope": "In-Scope",
            "expected_routing": "rag",
            "expected_abstention": False,
            "expected_escalation": False,
        },
        {
            "name": "IT RAG",
            "query": (
                "What should I do if my laptop is running "
                "slow after the latest Windows update?"
            ),
            "expected_department": "IT Support",
            "expected_scope": "In-Scope",
            "expected_routing": "rag",
            "expected_abstention": False,
            "expected_escalation": False,
        },
        {
            "name": "Negative Escalation",
            "query": (
                "I am furious! You overcharged me for my "
                "last order and I demand a refund right now!"
            ),
            "expected_department": "Billing & Payments",
            "expected_scope": "In-Scope",
            "expected_routing": "escalation",
            "expected_abstention": False,
            "expected_escalation": True,
        },
        {
            "name": "Out-of-Scope",
            "query": "What is the capital of France?",
            "expected_scope": "Out-of-Scope",
            "expected_routing": "out_of_scope",
            "expected_abstention": False,
            "expected_escalation": False,
        },
        {
            "name": "In-Scope Knowledge Gap",
            "query": (
                "Does ShopUNow offer ten years of unpaid "
                "parental leave?"
            ),
            "expected_department": "HR",
            "expected_scope": "In-Scope",
            "expected_routing": "rag",
            "expected_abstention": True,
            "expected_escalation": False,
        },
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, start=1):
        print(
            f"Test {i}: {test_case['name']}\n"
            f"  Query: {test_case['query']}"
        )

        try:
            result = graph_app.invoke(
                {"query": test_case["query"]}
            )
        except Exception as e:
            print(f"  [FAIL] Execution error: {e}\n")
            continue

        department = result.get("department")
        scope = result.get("scope")
        sentiment = result.get("sentiment")
        response = result.get("response", "")
        needs_escalation = result.get(
            "needs_escalation",
            False
        )

        response_lower = response.lower()

        test_passed = True

        # Department check
        if "expected_department" in test_case:
            if department != test_case["expected_department"]:
                print(
                    "  [FAIL] Department mismatch: "
                    f"expected '{test_case['expected_department']}', "
                    f"got '{department}'"
                )
                test_passed = False

        # Scope check
        if "expected_scope" in test_case:
            if scope != test_case["expected_scope"]:
                print(
                    "  [FAIL] Scope mismatch: "
                    f"expected '{test_case['expected_scope']}', "
                    f"got '{scope}'"
                )
                test_passed = False

        # Human escalation check
        if test_case.get("expected_escalation"):
            if not needs_escalation:
                print(
                    "  [FAIL] Expected human escalation, "
                    "but needs_escalation=False"
                )
                test_passed = False

            if "escalated to a human" not in response_lower:
                print(
                    "  [FAIL] Expected human escalation "
                    f"message, got: {response}"
                )
                test_passed = False

        # Out-of-scope check
        if test_case.get("expected_routing") == "out_of_scope":
            if needs_escalation:
                print(
                    "  [FAIL] Out-of-scope query should not "
                    "trigger human escalation."
                )
                test_passed = False

            if "shopunow ai assistant" not in response_lower:
                print(
                    "  [FAIL] Expected ShopUNow out-of-scope "
                    f"response, got: {response}"
                )
                test_passed = False

        # Abstention check
        if test_case.get("expected_abstention"):
            if ABSTENTION_MESSAGE.lower() not in response_lower:
                print(
                    "  [FAIL] Expected controlled abstention, "
                    f"got: {response}"
                )
                test_passed = False

        # Expected successful RAG response
        if (
            test_case.get("expected_routing") == "rag"
            and not test_case.get("expected_abstention")
        ):
            if not response.strip():
                print(
                    "  [FAIL] Expected a RAG response, "
                    "but response was empty."
                )
                test_passed = False

            if ABSTENTION_MESSAGE.lower() in response_lower:
                print(
                    "  [FAIL] Expected a grounded answer, "
                    "but system abstained."
                )
                test_passed = False

        # Final result
        if test_passed:
            print(
                f"  [PASS] "
                f"Sentiment={sentiment}, "
                f"Department={department}, "
                f"Scope={scope}"
            )
            passed += 1

        print()

    print("=" * 60)
    print(
        f"Evaluation Complete: {passed}/{total} tests passed."
    )
    print("=" * 60)

    if passed == total:
        print("SUCCESS: All ShopUNow evaluation tests passed.")
    else:
        print(
            "WARNING: Some evaluation tests failed. "
            "Review the results above."
        )


if __name__ == "__main__":
    run_evaluation()
