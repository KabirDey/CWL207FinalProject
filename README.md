# PakMag & IMDb Film Data Scraper

A robust Python-based automation tool designed to aggregate historical film records from the PakMag database and cross-reference them with unique identifiers from the IMDb autocomplete API.

## Overview

This project facilitates the collection of cinematic data from two distinct historical eras:
* Pre-Partition: Historical film records prior to 1947.
* Post-Partition: Cinematic data from 1947 to the present day.

The script utilizes a non-invasive method to fetch IMDb IDs (ttIDs) by querying the hidden autocomplete API, bypassing standard web-scraping blocks and ensuring a high success rate for data matching.

## Technical Features

* Dual-Source Scraping: Automated iteration through PakMag's Pre- and Post-Partition database endpoints.
* IMDb API Integration: Real-time title matching via the IMDb suggestion engine.
* Resilient Parsing: Uses label-based extraction (BeautifulSoup) to handle variations in source HTML structure.
* Fault Tolerance: Includes consecutive failure logic to detect database boundaries and a graceful interruption handler (KeyboardInterrupt) to prevent data loss.
* Rate Limiting: Integrated delays to ensure ethical scraping practices and prevent IP throttling.

## Installation & Environment

IMPORTANT: Compatibility Requirement
This script is developed and tested specifically for Python 3.12. Later versions (e.g., Python 3.13+) are not supported and may result in library incompatibilities or script failure.

Ensure you have Python 3.12 installed. You will need to install the following dependencies:

pip install requests beautifulsoup4 pandas

## Data Schema

The script generates a comprehensive CSV file (pakmag_FULL_dataset.csv) containing the following fields:

- pageid: The internal ID from the source URL.
- era: Classification (Pre-Partition or Post-Partition).
- film_name: The primary title of the movie.
- imdb_id: The matched IMDb identifier (ttXXXXXXX).
- directors: Primary directorial credits.
- actors: Main cast members and ensemble.
- metadata: Compiled release year and language information.
- credits: Specific columns for Producers, Writers, Musicians, and Crew.

## Usage

1. Clone the repository or download the script.
2. Verify your Python version:
   python --version  # Should output Python 3.12.x
3. Run the scraper via your terminal:
   python scraper_script.py
4. The script will log progress in the terminal, showing IMDb matches and current page status.
5. Upon completion or manual stop (Ctrl+C), the script will export all gathered data to a CSV file.
