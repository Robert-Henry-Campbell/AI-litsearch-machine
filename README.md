# AI-litsearch-machine

This project automates the extraction and synthesis of structured information from academic PDFs. It is designed to streamline literature reviews of Mendelian Randomization (MR) studies across various pharmacological agents.

## Implemented Features
- **PDF Ingestion**: Automated collection and logging of academic PDFs.
- **Text Extraction**: Conversion of PDFs to structured, page-wise text files.
- **Metadata Extraction (Agent 1)**: Uses the OpenAI API to pull key metadata fields into JSON.
- **Data Aggregation**: Collates individual metadata JSON files into a master dataset.
- **Text Retrieval Helper**: Fetches keyword-based snippets from stored PDF text files for downstream RAG tasks.
- **Narrative Review Generation (Agent 2)**: Generates peer-review style summaries using `agent2/openai_narrative.py`.

## Features Under Development
None at this time.

## Installation
Clone the repository and create a virtual environment:

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
# The pipeline relies on the pre-1.0 OpenAI client
pip install "openai<1.0"
```

Set your OpenAI API key in the ``OPENAI_API_KEY`` environment variable before running any pipeline steps:

```bash
export OPENAI_API_KEY=<your-key>
```

## Usage
1. Place your academic PDFs in `data/pdfs/`.
2. Run ingestion and text extraction **for each PDF**:

```bash
python ingest/collector.py path/to/paper.pdf
python extract/pdf_to_text.py path/to/paper.pdf
```
Both commands expect a single PDF file path and should be run for every paper.

3. Execute Agent 1 to extract metadata:

```bash
python -m agent1.metadata_extractor
```

If you prefer running the script directly, set `PYTHONPATH=$(pwd)` first:

```bash
PYTHONPATH=$(pwd) python agent1/metadata_extractor.py
```

4. Aggregate metadata:

```bash
python aggregate.py
```
This command reports how many files were aggregated and any that were skipped due
to validation errors.

5. Validate JSON integrity:

```bash
python utils/json_validator.py
```
This checks all files in `data/meta/` and `data/master.json` for UTF-8 encoding
and valid JSON structure.

6. Generate narrative reviews with Agent 2 programmatically:

```python
from agent2.openai_narrative import OpenAINarrative

generator = OpenAINarrative()
metadata = ...  # load master.json
snippets = ...  # collect text snippets
narrative = generator.generate(metadata, snippets)
```
The system prompt for this agent lives in `prompts/agent2_system.txt`.

Once `master.json` exists you can also generate a review from the command line:

```bash
python agent2/synthesiser.py --drug <drug-name>
```


6. Run the entire pipeline in one step using the CLI script:

```bash
python run_pipeline.py --pdf_dir data/pdfs --drug <drug-name>

```

## Output
- Individual metadata JSONs in `data/meta/`.
- Aggregated metadata in `data/master.json`.
- Generated narrative reviews in `outputs/`.
- For instructions on processing a new drug, see `docs/HOW_TO_ADD_NEW_DRUG.md`.

## Telemetry & Logging
Most modules emit standardized logs using Python's ``logging`` module. The
pipeline and OpenAI helpers record timestamps, log levels and token usage.
These logs include API timing information to help estimate costs and detect
rate-limit issues. The pipeline also reports the duration and memory delta of
each major step so you can identify slow stages. The ingestion and PDF
extraction scripts simply produce output files and do not currently log.

## Contributing
Contributions are welcome! Fork the repository and submit a pull request with improvements or new features.

## Continuous Integration
A GitHub Actions workflow automatically lints Markdown files in the `outputs/` directory on pull requests to the `main` branch.
Another workflow runs a schema drift unit test to ensure that `PaperMetadata` does not change unexpectedly.

## API Cost Estimation

The pipeline uses the OpenAI API (for example, GPT-4-Turbo), which is billed per
1,000 tokens. Costs may change, so always check the
[OpenAI Pricing](https://openai.com/pricing) page for the latest numbers. At the
time of writing, GPT-4-Turbo is roughly **$0.01 per 1,000 tokens**.

Estimating cost for a run is easiest when you know roughly how many tokens each
step consumes:

- **Metadata extraction**: A typical academic paper requires around 2,000 tokens
  from the API, or about **$0.02 per paper**.
- **Narrative synthesis**: Producing a narrative review for a single drug usually
  takes 4,000–6,000 tokens (**$0.04–$0.06 per review**).

For example, processing metadata for 100 papers would cost approximately:

- `100 × $0.02 = $2.00` for metadata extraction
- Narrative review costs then scale with the number of drugs you review (roughly
  `$0.05` each).

Use these numbers as a starting point to budget larger runs.

## API Rate-limit Handling

OpenAI imposes rate limits to ensure fair use of the API. If you exceed these
limits, the API will return a **429 Too Many Requests** error. When this occurs,
implement an exponential back-off strategy before retrying:

1. First retry after waiting **1 second**.
2. Second retry after waiting **4 seconds**.
3. Third retry after waiting **16 seconds**.

Additionally, limit the number of concurrent API calls to reduce the likelihood
of hitting rate limits. See the
[OpenAI rate limit documentation](https://platform.openai.com/docs/guides/rate-limits)
for more details.

