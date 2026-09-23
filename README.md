# Identifying Claims and Premises in AfD Speeches

An argument-mining project on German political discourse, focused on climate-related speeches by AfD politicians. The repository contains the annotated dataset, sampling and statistics code, prompt templates, LLM evaluation scripts, and final experiment results.

## Project Overview

The project develops an annotation scheme that combines:

- argumentative roles: `claim`, `premise`, `other`;
- argument relations, including `supports`, `adds`, `attacks`, and `undercut`;
- 15 semantic categories representing the Speaker, Opponent, World, evidential sources, and rhetoric.

The final annotated dataset contains **160 paragraphs** and **1,094 annotated spans**. The data are split into **120 training paragraphs** and **40 test paragraphs**.

## Repository Structure

```text
├── annotations/            # Label Studio exports for train/test data
├── data_and_sample/        # Source data, train/test CSVs, sampling notebook
├── model/                  # LLM evaluation script and prompt templates
├── results/                # Luna, Sol, Terra, and Terra few-shot results
├── statistics/             # Annotation and relation statistics scripts
├── analysis/               # Grouped prediction/error analysis
└── README.md
```

## Setup

Install the main dependencies:

```bash
pip install openai pyyaml jinja2 pandas scikit-learn matplotlib seaborn jupyter
```

For LLM experiments, set an OpenAI API key:

```bash
export OPENAI_API_KEY="your_api_key"
```

## Running the LLM Experiment

The evaluation script classifies the predefined semantic spans in the 40-paragraph test set and reports accuracy, macro precision, macro recall, and macro F1.

```bash
cd model
python call.py ../results/my_run.json
```

`call.py` is currently configured for GPT-5.6 Terra with the zero-shot template. Use `template_few_shot.yaml` for the few-shot setting and change the model in `call_ai()` when evaluating another model.

## Results

| Model / Prompting | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---:|---:|---:|---:|
| GPT-5.6 Luna, zero-shot | 0.471 | 0.437 | 0.484 | 0.420 |
| GPT-5.6 Sol, zero-shot | 0.471 | 0.407 | 0.505 | 0.401 |
| GPT-5.6 Terra, zero-shot | 0.488 | 0.453 | 0.521 | 0.434 |
| GPT-5.6 Terra, few-shot | **0.500** | **0.494** | **0.558** | **0.466** |

The majority-class accuracy baseline is **0.213**; all tested configurations outperform it.

## Annotation Statistics

To reproduce the main annotation counts:

```bash
cd statistics
python get_annotation_statistics.py
```

Additional scripts in `statistics/` extract selected semantic categories and argument-relation patterns from the annotated data.

## Data Sources

The project uses AfD parliamentary speech data derived from **OpenDiscourse** and **ParlLawSpeech**, with climate-related material selected from topic-clustered paragraphs. The repository is intended for research and coursework on argument mining and political discourse analysis.
