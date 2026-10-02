import os
import json
from pydantic import BaseModel, Field
from typing import List
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, ROUTER_MODEL
from dotenv import load_dotenv

load_dotenv()

class QAPair(BaseModel):
    question: str = Field(description="The frequently asked question.")
    answer: str = Field(description="The detailed answer to the question.")
    department: str = Field(description="The department responsible for this question.")
    audience: str = Field(description="The target audience (Internal or External).")

class QADataset(BaseModel):
    qa_pairs: List[QAPair]

def generate_dataset():
    if not GROQ_API_KEY:
        print("Please set GROQ_API_KEY in your environment.")
        return

    # Use a low temperature for factual generation
    llm = ChatGroq(api_key=GROQ_API_KEY, model=ROUTER_MODEL, temperature=0.1)
    structured_llm = llm.with_structured_output(QADataset)

    departments = [
        {"name": "HR", "audience": "Internal employees"},
        {"name": "IT Support", "audience": "Internal employees"},
        {"name": "Billing & Payments", "audience": "External customers"},
        {"name": "Shipping & Delivery", "audience": "External customers"}
    ]

    all_data = []
    
    for dept in departments:
        print(f"Generating data for {dept['name']}...")
        prompt = f"""You are generating a synthetic FAQ dataset for a retail company named ShopUNow.
Create exactly 12 Question and Answer pairs for the {dept['name']} department.
This department caters to {dept['audience']}.
Make the questions realistic and the answers helpful, detailed, and specific.
Do not use placeholders, provide concrete synthetic details.
"""
        try:
            result = structured_llm.invoke(prompt)
            # Override metadata to be perfectly clean
            for item in result.qa_pairs:
                item.department = dept['name']
                item.audience = "Internal" if "Internal" in dept['audience'] else "External"
            all_data.extend([item.model_dump() for item in result.qa_pairs])
        except Exception as e:
            print(f"Failed to generate for {dept['name']}: {e}")

    # Ensure directory exists
    os.makedirs("./data", exist_ok=True)
    
    with open("./data/shopunow_qa_dataset.json", "w") as f:
        json.dump(all_data, f, indent=4)
        
    print(f"Successfully generated {len(all_data)} QA pairs and saved to ./data/shopunow_qa_dataset.json")

if __name__ == "__main__":
    generate_dataset()
