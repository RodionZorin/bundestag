import json
from collections import Counter

PATH_TRAIN = "annotations/X_train.json"
PATH_TEST = "annotations/X_test.json"

with open(PATH_TRAIN, "r", encoding="utf-8") as f:
    data_train = json.load(f)

with open(PATH_TEST, "r", encoding="utf-8") as f:
    data_test = json.load(f)

# Combine train and test data

data = data_train + data_test

labels = Counter()
categories = Counter()
relations = Counter()
unlabeled_relations = 0

for task in data:
    for annotation in task["annotations"]:
        for result in annotation["result"]:

            # claim / premise / other
            if result["type"] == "labels":
                label = result["value"]["labels"][0]
                labels[label] += 1

            # semantic categories
            elif result["type"] == "choices":
                if result["from_name"] in ["claim_type", "premise_type"]:
                    category = result["value"]["choices"][0]
                    categories[category] += 1

            # relations
            elif result["type"] == "relation":
                if "labels" in result:
                    relation = result["labels"][0]
                    relations[relation] += 1
                else:
                    unlabeled_relations += 1

print("Number of paragraphs:", len(data))
print("Number of spans:", sum(labels.values()))

print("\nLabels:")
for label, count in labels.items():
    print(label, count)

print("\nSemantic categories:")
for category, count in categories.items():
    print(category, count)

print("\nNumber of relations:", sum(relations.values()) + unlabeled_relations)

print("\nRelations:")
for relation, count in relations.items():
    print(relation, count)

print("unlabeled:", unlabeled_relations)