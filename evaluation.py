import json
from agent import graph_app

def run_evaluation():
    print("Starting Deterministic Evaluation Suite...\n")
    
    test_cases = [
        # Normal queries mapped to correct departments
        {
            "query": "How do I apply for a vacation day?",
            "expected_department": "HR",
            "expected_routing": "rag",
            "expected_abstention": False
        },
        {
            "query": "What should I do if my laptop is running slow after the latest Windows update?",
            "expected_department": "IT Support",
            "expected_routing": "rag",
            "expected_abstention": False
        },
        # Negative sentiment query
        {
            "query": "I am furious! You overcharged me for my last order and I demand a refund right now!",
            "expected_routing": "escalation",
            "expected_escalation_trigger": True
        },
        # Unknown department query
        {
            "query": "Do you sell dog food?",
            "expected_department": "Unknown",
            "expected_routing": "escalation",
            "expected_escalation_trigger": True
        },
        # Out-of-scope / insufficient context query
        {
    
    "query": "What is the exact net worth of the CEO of ShopUNow?",
    "expected_department": "Unknown",
    "expected_routing": "escalation",
    "expected_escalation_trigger": True
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, tc in enumerate(test_cases):
        print(f"Test {i+1}: {tc['query']}")
        state = {"query": tc["query"]}
        
        try:
            result = graph_app.invoke(state)
        except Exception as e:
            print(f"  [ERROR] Execution failed (Are API keys set?): {e}")
            continue
            
        dept = result.get("department")
        sentiment = result.get("sentiment")
        response = result.get("response")
        
        # Check Department if specified
        if "expected_department" in tc and tc["expected_department"] != dept:
            print(f"  [FAIL] Expected department {tc['expected_department']}, got {dept}")
            continue
                
        # Check Escalation
        if tc.get("expected_escalation_trigger"):
            if "escalated to a human" not in response.lower():
                print(f"  [FAIL] Expected human escalation, got: {response}")
                continue
                
        # Check Abstention
        if tc.get("expected_abstention"):
            if "don't have enough information" not in response.lower():
                print(f"  [FAIL] Expected abstention, got: {response}")
                continue
                
        # Check Non-Abstention (Context found)
        if not tc.get("expected_abstention") and not tc.get("expected_escalation_trigger"):
            if "don't have enough information" in response.lower():
                print(f"  [FAIL] Expected answer, but system abstained.")
                continue
                
        print(f"  [PASS] Sentiment: {sentiment}, Dept: {dept}")
        passed += 1

    print(f"\nEvaluation Complete: {passed}/{total} tests passed.")

if __name__ == "__main__":
    run_evaluation()
