# Project B4
## Overview
This is a Python-based data pipeline and database. It processes personal data exports (Kindle, YouTube, Instagram) to extract sessions, merge libraries, and run  compliance checks and alerts.

## Features
- Extract sessions and activity from Kindle, YouTube, and Instagram exports
- Merge and normalize library records across exports
- Run simple GDPR/compliance scans and emit alerts
- Provide a basic concentration/activity analysis module

## Layout
- Main entry: src/main.py
- Processing modules: src/processors/ (kindle_extract.py, youtube_extract.py, instagram_extract.py, library_merger.py, gdpr_compliance.py, alerts.py, concentration_extract.py, logging_config.py)
- Data input: data/ (place raw export folders here)
- Schema and DB helpers: schema.sql

## Requirements
See requirements.txt for required packages.
A .env file needs to be created and added to the /src to allow main.py to function.
This file needs to contain a Youtube Data API key, the credentials for the PostGres DB, and an ENVIRONMENT variable to tell it whether it is in development or production, as this affects whether raw source files are deleted after ingestion or kept.  

## Usage
1. Place exports inside the `data/` directory.
2. Run the main script:
python src/main.py

## Configuration
Adjust logging and processor options in `src/processors/logging_config.py` and the individual processor modules.

## System Design
Architecture
- Extract: individual extractor modules in `src/processors/` read raw export files from `data/` and produce normalized records.
- Process: worker processes perform parsing, enrichment and validation; `library_merger` consolidates records.
- Store: processed records live in a relational store (schema defined in `schema.sql`) while raw files remain on shared disk or an object store.
- Load: downstream consumers/querying use the merged tables and read replicas for analytics and reporting.