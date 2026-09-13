import json
import yaml
from jinja2 import Template
import argparse
import datetime as dt

PATH = "../annotations/X_test.json"
TEMPLATE = "./template.yaml"

parser = argparse.ArgumentParser(
    description="Add your output file;" \
    "Use example: python3 call.py my_test.json"
)

parser.add_argument("output_file")

args = parser.parse_args()

with open (TEMPLATE, "r", encoding="utf-8") as f:
    template = yaml.safe_load(f)

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

#add essential collections
gold_labels = {} 
predictions = {} 
paragraphs = [] 
spans = {}  
failed_paragpraphs = 0 

def get_paragraph_spans_and_labels(annotation):
    """
    Collect spans and their gold labels
    """
    paragraph_spans = []
    paragraph_gold_labels = []
    for span in annotation[0]["result"]:
        from_name = span.get('from_name')
        if from_name in ["premise_type", "claim_type", "other_type"]:
            span_text = span.get("value").get("text")
            paragraph_spans.append(span_text)
            span_gold = span.get("value").get("choices")[0]
            paragraph_gold_labels.append(span_gold)
    return paragraph_spans, paragraph_gold_labels

#take each paragraph
for paragraph in data:
    paragraph_id = paragraph["id"]
    paragraphs.append(paragraph_id)
    annotation = paragraph["annotations"]
    paragraph_text = paragraph["data"]["text"]

    #collect spans of the paragraph and gold labels of the each span
    paragraph_spans, paragraph_gold_labels = get_paragraph_spans_and_labels(annotation)
    spans[paragraph_id] = paragraph_spans

    #create context to fill in the gaps of the template
    context = {}
    context["text"] = paragraph_text
    context["spans"] = spans[paragraph_id]

    #fill in the gaps in the template
    my_prompt = Template(template["prompt"]).render(**context)

    from openai import OpenAI
    client = OpenAI()
    response = client.responses.create(
       model="gpt-5.6-terra",
       input=my_prompt,
    )
    model_response = response.output_text

    print("paragraph id: ", paragraph_id)

    #make necessary checks of the correctness of the model answer
    if type(model_response) == str:
        model_response = json.loads(model_response)

    if len(model_response) != len(paragraph_spans):
        print("Oops! The model failed to generate correct number of predictions")
        failed_paragpraphs += 1
        continue

    if type(model_response) != type(paragraph_spans):
        print("Oops! The model failed to produce a list of predictions")
        failed_paragpraphs += 1
        continue

    print("The model generated the correct number of predictions in the correct format")

    predictions[paragraph_id] = model_response
    

#calculate accuracy
attempts = 0
count = 0
errors = {}
for paragraph_index in paragraphs:
    if paragraph_index in list(predictions.keys()):
        zipped = list(enumerate (zip (predictions[paragraph_index], gold_labels[paragraph_index]) ) )
        paragraph_errors = {}
        for pair_index, pair in zipped:
            attempts += 1
            if pair[0] == pair[1]: #if prediction == gold_label
                count += 1
            else:
                paragraph_errors[spans[paragraph_index][pair_index]] = f"prediction: {pair[0]}; gold_label: {pair[1]}"
        errors[f"paragraph {paragraph_index}"] = paragraph_errors

try:
    accuracy = count*100/attempts
    print("Accuracy: ", accuracy)
except ZeroDivisionError:
    print("No correct answers by the model")
    accuracy = 0.0

print("Baseline Accuracy: 21.61")

#output format to write down in json
date = str(dt.datetime.now())
output = {
    "datetime": date,
    "paragraphs": paragraphs,
    "accuracy": accuracy,
    "number of failed paragraphs": failed_paragpraphs,
    "number of spans": attempts,
    "number of errors": attempts - count,
    "number of successes": count,
    "errors": errors
}

# create the output file of the experiment
with open(args.output_file, "w", encoding="utf-8") as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Saved to: {args.output_file}")
import ipdb; ipdb.set_trace()