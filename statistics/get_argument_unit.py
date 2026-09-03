import json
import argparse

PATH_TRAIN = "annotations/X_train.json"
PATH_TEST = "annotations/X_test.json"

def main():

    parser = argparse.ArgumentParser(
         description="Type obligatory semantic type (speaker:policy, opponent:actions, etc.) and get all spans with this type." \
         "You can restrict your search: add optional argument type (e.g. claim) and get only claim + speaker:policy (excluding premise + speaker:policy)"
         "Use example: python3 get_argument_unit.py speaker:policy my.json"
         "Use example: python3 get_argument_unit.py -argument_type claim speaker:policy my.json"
    )

    parser.add_argument("-argument_type")
    parser.add_argument("semantic_type")
    parser.add_argument("output_file")

    args = parser.parse_args()

    with open(PATH_TRAIN, "r", encoding="utf-8") as f:
        data_train = json.load(f)

    with open(PATH_TEST, "r", encoding="utf-8") as f:
        data_test = json.load(f)

    # Combine train and test data

    data = data_train + data_test

    # Extract all annotated claims/premises together with their semantic types

    units = []

    for item in data:
        paragraph_id = item.get("id")
        paragraph_text = item.get("data", {}).get("text", "")

        if not item.get("annotations"):
            continue

        results = item["annotations"][0].get("result", [])

        # Store span information by Label Studio region ID
        spans = {}

        for result in results:
            if result.get("from_name") == "arg_label":
                region_id = result["id"]
                value = result["value"]

                spans[region_id] = {
                    "paragraph_id": paragraph_id,
                    "paragraph_text": paragraph_text,
                    "text": value.get("text", ""),
                    "argument_type": value.get("labels", [None])[0],
                    "semantic_type": None
                }

        # Add semantic type (speaker:mind, opponent:policy, etc.)
        for result in results:
            if result.get("from_name") in {"claim_type", "premise_type"}:
                region_id = result["id"]

                if region_id in spans:
                    choices = result["value"].get("choices", [])

                    if choices:
                        spans[region_id]["semantic_type"] = choices[0]

        units.extend(spans.values())
    #import ipdb; ipdb.set_trace()
    #select required units

    if args.argument_type:

        selected = [
            unit for unit in units
            if (unit["argument_type"] == args.argument_type and unit["semantic_type"] == args.semantic_type)
    ]

    else:
         selected = [
              unit for unit in units
              if unit["semantic_type"] == args.semantic_type
         ]

    #save the file

    with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(
                selected,
                f,
                ensure_ascii=False,
                indent=2
            )

if __name__ == "__main__":
	main()