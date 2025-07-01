# AI-litsearch-machine

This project automates the extraction and synthesis of structured information from academic PDFs. It is designed to streamline literature reviews of Mendelian Randomization (MR) studies across various pharmacological agents.

## Implemented Features
- **PDF Ingestion**: Automated collection and logging of academic PDFs.
- **Text Extraction**: Conversion of PDFs to structured, page-wise text files.
- **Metadata Extraction (Agent 1)**: Uses the OpenAI API to pull key metadata fields into JSON.
- **Data Aggregation**: Collates individual metadata JSON files into a master dataset.
- **Text Retrieval Helper**: Fetches keyword-based snippets from stored PDF text files for downstream RAG tasks.
- **Text Embeddings**: Splits extracted text into chunks and generates OpenAI embeddings for semantic retrieval.
- **Embedding Indexing**: Builds a FAISS vector store from extracted text for semantic snippet retrieval.
- **Embedding-based Retrieval**: Searches the FAISS index for semantically similar text chunks.
- **Narrative Review Generation (Agent 2)**: Generates peer-review style summaries using `agent2/openai_narrative.py`.

## Script Overview
Below is a brief description of the main scripts and where their outputs are written.

- `ingest/collector.py` logs each PDF's checksum so it is only processed once.
  It appends a JSON line to `ingestion_log.jsonl` in the repository root.
- `extract/pdf_to_text.py` converts a PDF into a JSON file of page texts and
  saves it under `data/text/`.
- `agent1/openai_client.py` and `agent1/metadata_extractor.py` call the OpenAI
  API to extract structured metadata.  Each result is written to
  `data/meta/<doi>.json` (the filename falls back to a hash if no DOI is
  available).
- `aggregate.py` validates all metadata files and combines them into
  `data/master.json`. Existing masters are backed up to `data/master_history/`,
  and any invalid files are logged to `data/aggregation_errors.log`.
- `utils/json_validator.py` checks every JSON file for UTF‑8 encoding and valid
  structure. It prints results to the console without writing new files.
- `agent2/retrieval.py` loads page text from `data/text/` and returns short
  excerpts around a keyword for downstream use.
- `agent2/embeddings.py` provides helpers for chunking text and generating
  embedding vectors via OpenAI.
- `agent2/openai_narrative.py` uses the OpenAI API to turn metadata and
  snippets into a narrative review string.
- `agent2/synthesiser.py` is a command-line wrapper that filters `master.json`
  by drug, gathers snippets, and writes a Markdown review to the `outputs/`
  directory.
- `pipeline.py` and `run_pipeline.py` orchestrate the entire workflow—ingestion,
  metadata extraction, aggregation and narrative generation—when run from the
  command line. Both accept an optional `--model` argument to override the
  default OpenAI model used for metadata extraction and narrative generation.
- `run_smoke_test.py` ingests a single PDF and prints the first few hundred
  characters from each page as a quick sanity check.
- `utils/data_wipe.py` deletes generated data and logs. Pass `--with-pdfs` to
  remove files in `data/pdfs/` as well.

## Features Under Development
None at this time.

## Installation (VENV-- Not Reccomended)
Clone the repository and create a virtual environment:

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
python3 -m venv venv
source venv/bin/activate
```

Install dependencies from the provided requirements file:

```bash
pip install -r requirements.txt
```
This installs the pinned OpenAI client and all other packages needed for the pipeline.

Provide your OpenAI API key via the ``OPENAI_API_KEY`` environment variable or
as a Docker secret at ``/run/secrets/openai_api_key``. The key cannot be stored
in the repository:

```bash
export OPENAI_API_KEY=<your-key>
```

## Installation Docker (recommended)

1. Build the Codex-universal base once:

   MSYS_NO_PATHCONV=1 docker build -t codex-universal:fixed ./codex-universal

2. Build the project image:

   MSYS_NO_PATHCONV=1 docker build -t ai-litsearch-machine .

3. Create an `.env` file (not committed) with your key:

   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

4. Run the full pipeline (PDFs must already be in `data/pdfs/`):

   MSYS_NO_PATHCONV=1 docker run --rm -it \
     --env-file .env \
     -v "$(pwd)/data:/data" \
     -v "$(pwd)/outputs:/app/outputs" \
     ai-litsearch-machine \
     run_pipeline.py --pdf_dir /data/pdfs --drug <drug-name>

Results appear in `./outputs/` on the host.

## Testing
Run `pytest` to execute the test suite. Any test that requires the OpenAI API
will use your configured key and is skipped automatically if the key is absent.
Live integration tests that exercise the entire pipeline are located under
`tests/integration/` and in `tests/agent2/test_openai_narrative_live.py`.

## Usage
1. Place your academic PDFs in `data/pdfs/`.
2. Run ingestion and text extraction **for each PDF**:

```bash
python ingest/collector.py path/to/paper.pdf
python extract/pdf_to_text.py path/to/paper.pdf
```
Both commands expect a single PDF file path and should be run for every paper.

3. Execute Agent 1 to extract metadata by pointing it to a text JSON file:

```bash
python -m agent1.metadata_extractor data/text/paper.json
```

If you prefer running the script directly, set `PYTHONPATH=$(pwd)` first:

```bash
PYTHONPATH=$(pwd) python agent1/metadata_extractor.py data/text/paper.json
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
python run_pipeline.py --pdf_dir data/pdfs --drug <drug-name> --model <model-name>

```

## Output
- Individual metadata JSONs in `data/meta/`.
- Aggregated metadata in `data/master.json`.
- Generated narrative reviews in `outputs/`.
- For instructions on processing a new drug, see `docs/HOW_TO_ADD_NEW_DRUG.md`.

## Cleaning Up Generated Data

Use `utils/data_wipe.py` to delete intermediate outputs and logs:

```bash
python utils/data_wipe.py
```

Raw PDFs in `data/pdfs/` remain untouched. To remove them as well, pass `--with-pdfs`:

```bash
python utils/data_wipe.py --with-pdfs
```

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

