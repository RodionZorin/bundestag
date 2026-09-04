import json
import yaml
from jinja2 import Template

PATH = "../annotations/X_test.json"
TEMPLATE = "./template.yaml"

with open (TEMPLATE, "r", encoding="utf-8") as f:
    template = yaml.safe_load(f)

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

golden_labels = []
predictions = []

#take each paragraph and form a prompt
for paragraph in data:
    paragraph_id = paragraph["id"]
    #if paragraph_id != 124:
        #continue
    annotation = paragraph["annotations"]
    paragraph_text = paragraph["data"]["text"]

    #collect spans of the text in a list
    spans = []
    golden_labels_paragraph = []
    for span in annotation[0]["result"]:
        from_name = span.get('from_name')
        if from_name in ["premise_type", "claim_type", "other_type"]:
            span_text = span.get("value").get("text")
            spans.append(span_text)
            span_golden = span.get("value").get("choices")[0]
            golden_labels_paragraph.append(span_golden)

    #create context to fill in the gaps of the template
    context = {}
    context["text"] = paragraph_text
    context["spans"] = spans

    #fill in the gaps in the template
    my_prompt = Template(template["prompt"]).render(**context)
    #import ipdb; ipdb.set_trace()

    from openai import OpenAI
    client = OpenAI()
    response = client.responses.create(
       model="gpt-5.6-luna",
       input=my_prompt,
    )
    model_response = response.output_text

    if type(model_response) == str:
        model_response = json.loads(model_response)

    #import ipdb; ipdb.set_trace()
    if len(model_response) != len(spans):
        print("Oops! The model failed to generate correct number of predictions")
        continue

    if type(model_response) != type(spans):
        print("Oops! The model failed to produce a list of predictions")
        continue

    predictions.extend(model_response)
    golden_labels.extend(golden_labels_paragraph)
    print(len(predictions))
    print(len(golden_labels))
    import ipdb; ipdb.set_trace()
    if paragraph_id == 130:
        break
    

#after the foor loop
zipped = list(zip(predictions, golden_labels))
count = 0
for prediction, golden_label in zipped:
    if prediction == golden_label:
        count += 1
try:
    accuracy = count*100/len(zipped)
    print("Accuracy: ", accuracy)
except ZeroDivisionError:
    print("No correct answers by the model")

print("Baseline Accuracy: 21.61")
import ipdb; ipdb.set_trace()