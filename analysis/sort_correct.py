import json
from collections import Counter

PATH = "../model/test_terra_few_shot_2.json"

correct = Counter()

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for paragraph in data["correct"].values():
    for span in paragraph.values():
        correct[f"{span["prediction"]}"] += 1

selected = {
    "model": data["model"],
    "correct": correct.most_common(),
}

with open("correct.json", "w", encoding="utf-8") as f:
    json.dump(
        selected,
        f,
        ensure_ascii=False,
        indent=2
    )


