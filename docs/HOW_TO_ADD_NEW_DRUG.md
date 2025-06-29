# How to Add a New Drug

This guide explains how to prepare PDFs, run the processing pipeline, and review the outputs when adding a new drug to the system.

## Step 1: Prepare PDFs
- Collect all articles related to the drug and place them in `data/new_pdfs/`.
- Name each PDF using its DOI followed by `.pdf`; for example `10.1234/article.pdf`.

## Step 2: Run the Pipeline
Run the end-to-end pipeline from the repository root:

```bash
python run_pipeline.py --pdf_dir data/new_pdfs --drug <your_drug_name>
```

This command ingests the PDFs, extracts text, gathers metadata, and generates a narrative review.

## Step 3: Check Outputs
- The review will be written to `outputs/review_<your_drug_name>.md`.
- Individual metadata files are saved in `data/meta/`.
- The aggregated metadata summary can be found at `data/master.json`.

## Troubleshooting
- **Missing data**: Inspect the JSON files in `data/meta/` to see if any PDFs failed metadata extraction.
- **Errors during execution**: Check the log files generated in `data/` for details about pipeline failures.
