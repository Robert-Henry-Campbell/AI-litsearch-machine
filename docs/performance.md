# Pipeline Performance Report

This document summarizes execution time and memory usage when running the
pipeline on the sample PDFs located in `tests/fixtures/sample_pdfs`.

## Metrics Collection

`pipeline.py` records the duration and memory delta for each major step. It
uses the standard `resource` module on Unix-like systems and falls back to
`psutil` on Windows. After all steps complete, a summary is logged with steps
sorted by runtime.

## Sample Run

A run using fake extractors on the two sample PDFs produced the following log:

```
2025-06-29 16:04:13,956 [INFO] pipeline: Ingestion completed in 0.01s (+256 KB)
2025-06-29 16:04:13,956 [INFO] pipeline: Metadata Extraction completed in 0.00s (+0 KB)
2025-06-29 16:04:13,956 [INFO] pipeline: Aggregation completed in 0.00s (+0 KB)
2025-06-29 16:04:13,957 [INFO] pipeline: Narrative Generation completed in 0.00s (+0 KB)
2025-06-29 16:04:13,957 [INFO] pipeline: -- Performance Summary --
2025-06-29 16:04:13,957 [INFO] pipeline: Ingestion            0.01s +256 KB
2025-06-29 16:04:13,957 [INFO] pipeline: Narrative Generation 0.00s +0 KB
2025-06-29 16:04:13,957 [INFO] pipeline: Metadata Extraction  0.00s +0 KB
2025-06-29 16:04:13,957 [INFO] pipeline: Aggregation          0.00s +0 KB
```

The ingestion stage, which includes PDF text extraction, was the slowest step in
this small run.

## Observations

- **Ingestion** took noticeably longer than other steps, mostly due to PDF
  processing with `pdfminer.six`.
- Memory use remained low (under one megabyte increase for each step), and no
  significant leaks were observed.

## Optimization Ideas

1. **Parallelize PDF processing** – using multiprocessing or threading could
   speed up ingestion when many PDFs are present.
2. **Cache intermediate text files** – skipping extraction when text already
   exists would avoid redundant work.

