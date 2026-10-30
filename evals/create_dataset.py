from dotenv import load_dotenv
from langsmith import Client

from evals.dataset import CASES
from evals.dataset_hard import HARD_CASES

load_dotenv()
client = Client()

splits = {
    "dev": [c for i, c in enumerate(CASES) if i % 4 != 3],
    "test":[ c for i,c in enumerate(CASES) if i % 4 == 3],
    "hard": HARD_CASES,
}


for split, cases in splits.items():
    name = f"incident-triage-{split}"
    if client.has_dataset(dataset_name=name):
        print(f"{name} already exists, skipping (delete it in LangSmith to recreate)")
        continue

    dataset = client.create_dataset(
        dataset_name=name,
        description=f"IncidentPilot {split} set: invented incidents with expected outcomes",
    )
    examples = [
        {
            "inputs":{"text":text},
            "outputs":{
                "intent":intent,
                "category": category,
                "acceptable_actions":actions,
            },
        }
        for text, intent, category, actions in cases
    ]
    # client.create_example(dataset_id=dataset.id, examples=examples)
    for example in examples:
     client.create_example(
        dataset_id=dataset.id,
        inputs=example["inputs"],
        outputs=example["outputs"],
    )
    print(f" Created {name} with {len(examples)} examples")

