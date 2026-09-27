import json
from pathlib import Path
import httpx

BASE_URL = "http://localhost:8080"

DATASET_DIR = Path(__file__).parent / "dataset" / "expanded"


def load_json_files(folder_name):
    folder = DATASET_DIR / folder_name

    for file in folder.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            yield file.stem, json.load(f)


def push_context(client, scope, context_id, payload, version=1):
    response = client.post(
        f"{BASE_URL}/v1/context",
        json={
            "scope": scope,
            "context_id": context_id,
            "version": version,
            "payload": payload,
            "delivered_at": "2026-09-27T00:00:00Z"
        }
    )

    if response.status_code != 200:
        print(
            f"ERROR {scope} {context_id}: "
            f"{response.status_code} {response.text}"
        )



def main():

    scope_map = {
        "categories": "category",
        "merchants": "merchant",
        "customers": "customer",
        "triggers": "trigger",
    }

    total = 0

    with httpx.Client(
        timeout=10.0,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=20
        )
    ) as client:

        for folder_name, scope_name in scope_map.items():

            folder = DATASET_DIR / folder_name

            if not folder.exists():
                print(f"Skipping {folder_name}: folder not found")
                continue

            files = list(folder.glob("*.json"))

            print(
                f"Loading {scope_name}: "
                f"{len(files)} contexts..."
            )

            for file in files:

                with open(file, "r", encoding="utf-8") as f:
                    payload = json.load(f)

                push_context(
                    client,
                    scope_name,
                    file.stem,
                    payload
                )

                total += 1

            print(f"{scope_name}: done")

    print(f"\nDataset loading complete: {total} contexts")


if __name__ == "__main__":
    main()