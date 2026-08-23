import json
import argparse

PATH_TRAIN = "annotations/X_train.json"
PATH_TEST = "annotations/X_test.json"


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("from_type")
    parser.add_argument("relation_type")
    parser.add_argument("to_type")
    parser.add_argument("output_file")

    args = parser.parse_args()

    with open(PATH_TRAIN, "r", encoding="utf-8") as f:
        data_train = json.load(f)

    with open(PATH_TEST, "r", encoding="utf-8") as f:
        data_test = json.load(f)

    data = data_train + data_test

    selected = []

    for item in data:

        if not item.get("annotations"):
            continue

        paragraph_id = item.get("id")
        paragraph_text = item.get("data", {}).get("text", "")

        results = item["annotations"][0].get("result", [])

        # Store claims and premises by their region IDs

        spans = {}

        for result in results:

            if result.get("from_name") == "arg_label":

                region_id = result["id"]
                value = result["value"]

                spans[region_id] = {
                    "text": value.get("text", ""),
                    "argument_type": value.get("labels", [None])[0],
                    "semantic_type": None
                }

        # Add semantic types

        for result in results:

            if result.get("from_name") in {"claim_type", "premise_type"}:

                region_id = result["id"]

                if region_id in spans:

                    choices = result["value"].get("choices", [])

                    if choices:
                        spans[region_id]["semantic_type"] = choices[0]

        # Find relations

        matching_relations = []

        for result in results:

            if result.get("type") != "relation":
                continue

            from_id = result.get("from_id")
            to_id = result.get("to_id")

            if from_id not in spans or to_id not in spans:
                continue

            relation_labels = result.get("labels", [])

            if not relation_labels:
                continue

            relation = relation_labels[0]

            from_unit = spans[from_id]
            to_unit = spans[to_id]

            if (
                from_unit["argument_type"] == args.from_type
                and relation == args.relation_type
                and to_unit["argument_type"] == args.to_type
            ):

                matching_relations.append({
                    "from": from_unit,
                    "relation": relation,
                    "to": to_unit
                })

        # Save paragraph if it contains at least one matching relation

        if matching_relations:

            selected.append({
                "paragraph_id": paragraph_id,
                "paragraph_text": paragraph_text,
                "matching_relations": matching_relations
            })

    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(
            selected,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Found {len(selected)} paragraphs.")
    print(f"Saved to: {args.output_file}")


if __name__ == "__main__":
    main()