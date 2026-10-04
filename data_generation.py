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

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=ROUTER_MODEL,
        temperature=0.1
    )

    structured_llm = llm.with_structured_output(QADataset)

    departments = [
        {"name": "HR", "audience": "Internal employees"},
        {"name": "IT Support", "audience": "Internal employees"},
        {"name": "Billing & Payments", "audience": "External customers"},
        {"name": "Shipping & Delivery", "audience": "External customers"}
    ]

    all_data = []

    for dept in departments:
        print(f"\nGenerating data for {dept['name']}...")

        prompt = f"""
You are generating a synthetic FAQ dataset for a fictional retail company named ShopUNow.

Create EXACTLY 12 Question and Answer pairs for the {dept['name']} department.

Department audience: {dept['audience']}

Requirements:
- Return exactly 12 QA pairs.
- Each question must be realistic and different.
- Each answer must be helpful and detailed.
- Use concrete fictional ShopUNow details.
- Do not use placeholders.
- Keep each answer reasonably concise.
- Do not include markdown tables.
- Do not include unnecessary special characters.
"""

        # Retry up to 3 times if Groq returns malformed structured output
        success = False

        for attempt in range(1, 4):
            try:
                print(f"Attempt {attempt}/3...")

                result = structured_llm.invoke(prompt)

                if not result or not result.qa_pairs:
                    raise ValueError("Model returned no QA pairs.")

                if len(result.qa_pairs) != 12:
                    raise ValueError(
                        f"Expected 12 QA pairs, but received {len(result.qa_pairs)}."
                    )

                for item in result.qa_pairs:
                    item.department = dept["name"]
                    item.audience = (
                        "Internal"
                        if "Internal" in dept["audience"]
                        else "External"
                    )

                all_data.extend(
                    [item.model_dump() for item in result.qa_pairs]
                )

                print(f"Successfully generated 12 QA pairs for {dept['name']}.")
                success = True
                break

            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")

        if not success:
            print(f"ERROR: Could not generate data for {dept['name']}.")

    os.makedirs("./data", exist_ok=True)

    with open("./data/shopunow_qa_dataset.json", "w") as f:
        json.dump(all_data, f, indent=4)

    print(
        f"\nSuccessfully generated {len(all_data)} QA pairs "
        f"and saved to ./data/shopunow_qa_dataset.json"
    )


if __name__ == "__main__":
    generate_dataset()