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
        {
            "name": "HR",
            "audience": "Internal employees"
        },
        {
            "name": "IT Support",
            "audience": "Internal employees"
        },
        {
            "name": "Billing & Payments",
            "audience": "External customers"
        },
        {
            "name": "Shipping & Delivery",
            "audience": "External customers"
        }
    ]

    records_per_department = 20
    all_data = []

    for dept in departments:
        print(f"\nGenerating data for {dept['name']}...")

        prompt = f"""
You are generating a synthetic FAQ dataset for a fictional
retail company named ShopUNow.

Create EXACTLY {records_per_department} unique Question and Answer pairs
for the {dept['name']} department.

Department audience: {dept['audience']}

Requirements:

- Return exactly {records_per_department} QA pairs.
- Every question must be different.
- Questions should represent realistic customer or employee queries.
- Include different ways users might ask the same type of question.
- Use natural conversational wording.
- Answers must be accurate, helpful, and based only on fictional
  ShopUNow policies.
- Use concrete fictional ShopUNow details.
- Do not use placeholders.
- Keep answers reasonably concise.
- Do not use markdown tables.
- Do not include unnecessary special characters.
- Do not create questions belonging to another department.
- Avoid duplicate or nearly identical questions.

Important:
The dataset will be used for semantic vector search.
Therefore, use varied wording and realistic synonyms.

For example, HR questions may use terms such as:
PTO, paid time off, vacation, leave, time off, days off.

IT Support questions may use terms such as:
password reset, login problem, credentials, access, account locked.

Billing questions may use terms such as:
refund, reimbursement, money back, charge, payment, invoice.

Shipping questions may use terms such as:
delivery, shipment, tracking, package, parcel, order arrival.

Return ONLY the structured QA dataset.
"""

        success = False

        for attempt in range(1, 4):
            try:
                print(f"Attempt {attempt}/3...")

                result = structured_llm.invoke(prompt)

                if not result or not result.qa_pairs:
                    raise ValueError("Model returned no QA pairs.")

                if len(result.qa_pairs) != records_per_department:
                    raise ValueError(
                        f"Expected {records_per_department} QA pairs, "
                        f"but received {len(result.qa_pairs)}."
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

                print(
                    f"Successfully generated "
                    f"{records_per_department} QA pairs "
                    f"for {dept['name']}."
                )

                success = True
                break

            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")

        if not success:
            print(f"ERROR: Could not generate data for {dept['name']}.")

    os.makedirs("./data", exist_ok=True)

    dataset_path = "./data/shopunow_qa_dataset.json"

    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Dataset generation complete.")
    print(f"Total records: {len(all_data)}")
    print(f"Expected records: 80")
    print(f"Saved to: {dataset_path}")
    print("=" * 60)

    # Verify department counts
    from collections import Counter

    counts = Counter(item["department"] for item in all_data)

    print("\nDepartment counts:")
    for department in departments:
        name = department["name"]
        print(f"{name}: {counts[name]}")

    if len(all_data) == 80 and all(
        counts[dept["name"]] == 20 for dept in departments
    ):
        print("\nSUCCESS: Dataset contains exactly 80 records.")
    else:
        print("\nWARNING: Dataset does not contain the expected 80 records.")


if __name__ == "__main__":
    generate_dataset()
