import json
from collections import Counter

PATH = "../model/test_terra_few_shot_2.json"

errors = Counter()

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for paragraph in data["errors"].values():
    for span in paragraph.values():
        errors[f"{span["prediction"]} vs {span["gold_label"]}"] += 1

selected = {
    "model": data["model"],
    "errors": errors.most_common(),
}

with open("errors.json", "w", encoding="utf-8") as f:
    json.dump(
        selected,
        f,
        ensure_ascii=False,
        indent=2
    )


