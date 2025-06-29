# AI-litsearch-machine

This project automates the extraction and synthesis of structured information from academic PDFs. It is designed to streamline literature reviews of Mendelian Randomization (MR) studies across various pharmacological agents.

## Implemented Features
- **PDF Ingestion**: Automated collection and logging of academic PDFs.
- **Text Extraction**: Conversion of PDFs to structured, page-wise text files.
- **Metadata Extraction (Agent 1)**: Uses the OpenAI API to pull key metadata fields into JSON.
- **Data Aggregation**: Collates individual metadata JSON files into a master dataset.
- **Text Retrieval Helper**: Fetches keyword-based snippets from stored PDF text files for downstream RAG tasks.

## Features Under Development
- **Narrative Review Generation (Agent 2)**: Prompt template available in `prompts/agent2_system.txt`; full automation is still under development.

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
```

## Usage
1. Place your academic PDFs in `data/pdfs/`.
2. Run the ingestion and text extraction pipeline:

```bash
python ingest/collector.py
python extract/pdf_to_text.py
```

3. Execute Agent 1 to extract metadata:

```bash
python agent1/metadata_extractor.py
```

4. Aggregate metadata:

```bash
python aggregate.py
```
This command reports how many files were aggregated and any that were skipped due
to validation errors.

5. Generate narrative reviews with Agent 2:

```bash
python agent2/synthesiser.py
```
The system prompt for this agent lives in `prompts/agent2_system.txt`.

## Output
- Individual metadata JSONs in `data/meta/`.
- Aggregated metadata in `data/master.json`.
- Generated narrative reviews in `outputs/`.

## Contributing
Contributions are welcome! Fork the repository and submit a pull request with improvements or new features.

