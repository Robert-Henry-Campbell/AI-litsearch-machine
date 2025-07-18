# How to Add a New Drug

This guide explains how to prepare PDFs, run the processing pipeline, and review the outputs when adding a new drug to the system.

## Step 1: Prepare PDFs
- Collect all articles related to the drug and place them in `data/new_pdfs/`.
- Name each PDF using its DOI followed by `.pdf`; for example `10.1234/article.pdf`.

## Step 2: Run the Pipeline
Run the end-to-end pipeline from the repository root:

```bash
python run_pipeline.py --pdf_dir data/new_pdfs --drug <your_drug_name> \
    --base_dir data/<your_drug_name> [--batch]
```

Ensure the OpenAI API key is available via ``OPENAI_API_KEY`` or the secret file ``/run/secrets/openai_api_key`` and that you've installed the dependencies from ``requirements.txt``.

This command ingests the PDFs, extracts text, gathers metadata, and generates a narrative review. With `--batch`, the pipeline writes batch files named `<your_drug_name>_batch_<n>.jsonl` (each under 40,000 tokens) and exits before contacting the API.

## Step 3: Check Outputs
- The review will be written to `outputs/review_<your_drug_name>.md`.
- Individual metadata files are saved in `data/meta/`.
- The aggregated metadata summary can be found at `data/master.json`.

## Troubleshooting
- **Missing data**: Inspect the JSON files in `data/meta/` to see if any PDFs failed metadata extraction.
- **Errors during execution**: Check the log files generated in `data/` for details about pipeline failures.
