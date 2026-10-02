import argparse
from agent import graph_app

def main():
    parser = argparse.ArgumentParser(description="Test the ShopUNow AI Assistant CLI")
    parser.add_argument("--query", type=str, help="The query to ask the assistant")
    args = parser.parse_args()

    if args.query:
        print(f"User Query: {args.query}\n")
        
        state = {"query": args.query}
        try:
            result = graph_app.invoke(state)
            print("--- RESULT ---")
            print(f"Department: {result.get('department')}")
            print(f"Sentiment: {result.get('sentiment')}")
            print(f"Response: {result.get('response')}")
        except Exception as e:
            print(f"An error occurred (check if API keys are set): {e}")
    else:
        print("Please provide a query using --query 'Your question here'")

if __name__ == "__main__":
    main()
