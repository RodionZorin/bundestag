import json
import yaml
from jinja2 import Template
import argparse
import datetime as dt
from openai import OpenAI
from collections import Counter

PATH = "../annotations/X_test.json"
TEMPLATE = "./template.yaml"
CATEGORIES = ["speaker:mind", "speaker:policy", "speaker:actions",
              "speaker:experience", "opponent:policy", "opponent:actions",
              "world:state", "speaker:view -> opponent:mind", "speaker:view -> opponent:policy",
              "speaker:view -> opponent:actions", "speaker:view -> opponent:motives",
              "speaker:view -> world:state", "expert", "study", "speaker:rhetoric"]

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
gold_labels = {} #gold label of the each span of the each paragraph; used in the end to count accuracy
predictions = {} #predicted label of the each span of the each paragraph; used in the end to count accuracy
paragraphs = [] #ids of the analyzed paragraphs; used as info in the output file
spans = {} #contains each paragraph with all its spans 
failed_paragpraphs = 0 #counts the cases when the model fails to generate the correct number of predictions/generate the answer in the correct format

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

def create_context(paragraph_text, paragraph_spans):
    """
    Create a context to fill in the gaps of the template
    """
    context = {}
    context["text"] = paragraph_text
    context["spans"] = paragraph_spans
    return context

def create_prompt(context):
    """
    Fill in the gaps of the template.yaml with the info from the context
    """
    prompt = Template(template["prompt"]).render(**context)
    return prompt

def call_ai(prompt):
    """
    Call ai with the prompt
    """
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=my_prompt,
    )
    return response

def check_model_response(model_response):
    """
    Check if the model response has the correct form
    """
    try:
        if type(model_response) == str:
            model_response = json.loads(model_response)
    except (json.JSONDecodeError, TypeError):
        print("Oops! Invalid JSON")
        return False

    if len(model_response) != len(paragraph_spans):
        print("Oops! The model failed to generate correct number of predictions")
        return False

    if type(model_response) != type(paragraph_spans):
        print("Oops! The model failed to produce a list of predictions")
        return False

    if not all(label in CATEGORIES for label in model_response):
        print("Oops! The model generated an unknown label")
        return False

    print("The model generated the correct number of predictions in the correct format")
    return model_response

def get_counts(paragraphs, predictions, gold_labels):
    """
    Collect counts to furhter calculate metrics"
    """
    tp = Counter()
    fp = Counter()
    fn = Counter()
    successes = 0
    failures = 0
    correct = {}
    errors = {}

    for paragraph_index in paragraphs:
            if paragraph_index in list(predictions.keys()):
                zipped = list(enumerate (zip (predictions[paragraph_index], gold_labels[paragraph_index]) ) )
                paragraph_correct = {}
                paragraph_errors = {}
                for pair_index, pair in zipped:
                    pair_pred_gold = {}
                    pair_pred_gold["prediction"] = pair[0]
                    pair_pred_gold["gold_label"] = pair[1]
                    if pair[0] == pair[1]: #if prediction == gold_label
                        successes += 1
                        tp[pair[0]] += 1
                        paragraph_correct[spans[paragraph_index][pair_index]] = pair_pred_gold
                    else:
                        failures += 1
                        fp[pair[0]] += 1
                        fn[pair[1]] += 1
                        paragraph_errors[spans[paragraph_index][pair_index]] = pair_pred_gold
                correct[f"paragraph {paragraph_index}"] = paragraph_correct
                errors[f"paragraph {paragraph_index}"] = paragraph_errors

    return tp, fp, fn, successes, failures, correct, errors          

def calculate_metrics(successes, failures, tp, fp, fn):
    """
    Calculate accuracy, collect attempts and successes, and collect errors
    """
    
    try:
        attempts = successes + failures
        accuracy = successes / attempts
        print("Accuracy: ", accuracy)
    except ZeroDivisionError:
        print("No correct answers by the model")
        accuracy = 0.0
        macroavg_precision = 0.0
        macroavg_recall = 0.0
        macroavg_f1 = 0.0

    if accuracy > 0.0:
        precisions = []
        recalls = []
        f1 = []
        for category in CATEGORIES:
            if tp[category] + fn[category] == 0: #category absent from the gold data
                continue
            if tp[category] + fp[category] == 0:
                cat_precision = 0.0
            else:
                cat_precision = tp[category] / (tp[category] + fp[category])

            cat_recall = tp[category] / (tp[category] + fn[category])

            if cat_precision + cat_recall == 0:
                cat_f1 = 0.0
            else:
                cat_f1 = 2*cat_precision*cat_recall / (cat_precision + cat_recall)

            precisions.append(cat_precision)
            recalls.append(cat_recall)
            f1.append(cat_f1)

        macroavg_precision = sum(precisions)/len(precisions)
        macroavg_recall = sum(recalls)/len(recalls)
        macroavg_f1 = sum(f1)/len(f1)

    return accuracy, macroavg_precision, macroavg_recall, macroavg_f1

#take each paragraph
for paragraph in data:
    paragraph_id = paragraph["id"]
    paragraphs.append(paragraph_id)
    annotation = paragraph["annotations"]
    paragraph_text = paragraph["data"]["text"]

    #collect spans of the paragraph and gold labels of the each span
    paragraph_spans, paragraph_gold_labels = get_paragraph_spans_and_labels(annotation)
    spans[paragraph_id] = paragraph_spans
    gold_labels[paragraph_id] = paragraph_gold_labels

    #create a context to fill in the gaps of the template
    context = create_context(paragraph_text, paragraph_spans)

    #fill in the gaps in the template
    my_prompt = create_prompt(context)

    #call an OpenAI model
    client = OpenAI()

    #give 3 attempts for the model to generate a correct answer for the paragrpaph
    tries = 3
    model_response = False
    while tries > 0 and model_response == False:
        tries -= 1
        response = call_ai(my_prompt)
        model = response.model
        model_response = response.output_text

        print("paragraph id: ", paragraph_id)

        #make necessary checks of the correctness of the model response
        model_response = check_model_response(model_response)
        if model_response:
            predictions[paragraph_id] = model_response #if the response passes the checks, add it to the model predictions
        else:
            my_prompt = "You made a mistake." \
            "You either failed to produce correct number of predictions/or the output format was incorrect." \
            "Try again. Follow the instructions strictly" + my_prompt

    #if the model fails after 3 attempts, just write it down and move to the next paragraph
    if model_response == False:
        failed_paragpraphs += 1
        del gold_labels[paragraph_id] #if not, do not add predictions and delete also the corresponding gold labels added before
        #this action is needed to correctly zip predictions and gold labels later, see below
        #this also means that failed paragraphs do not influence accuracy, but they are yet introduced in the final report of the experiment

#get counts to further calculate metrics
tp, fp, fn, successes, failures, correct, errors = get_counts(paragraphs, predictions, gold_labels)

#calculate accuracy
accuracy, precision, recall, f1 = calculate_metrics(successes, failures, tp, fp, fn)

print("Baseline Accuracy: 0.21") #the percentage of the most frequent label in the analyzed dataset

#output format to write down in json
date = str(dt.datetime.now())
output = {
    "datetime": date,
    "model": model,
    "paragraphs": paragraphs,
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1,
    "number of failed paragraphs": failed_paragpraphs,
    "number of spans": successes+failures,
    "number of successes": successes,
    "number of errors": failures,
    "tp": tp,
    "fp": fp,
    "fn": fn,
    "correct": correct,
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