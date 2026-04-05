# Web-Scraping-Job-Aggregator-with-AI-Filtering
This project reflects how I think about data systems end-to-end—from extraction and cleaning to automation and AI-driven insights—while also understanding trade-offs between custom engineering and scalable tools.


Problem Statement
“Finding relevant job openings across multiple company websites is time-consuming and inefficient.”

Approach:
Scrape job listings
Store and process them
Use AI to filter relevant roles based on your preferences

🏗️ System Architecture (Big Picture)

Source → Extraction → Storage → Processing → AI Filtering → Output

Extraction → Web scraping (Apify / custom scripts)
Transformation → Data cleaning + structuring
Loading → CSV / local storage
AI Layer → Claude + prompt engineering
Automation → Scheduling pipeline runs


🔹 Way 1: Manual Pipeline (Baseline Approach)
📌 Overview

This approach focuses on building a basic end-to-end pipeline, but with manual intervention at multiple steps.
##
⚙️ Steps
Created an account on Apify
Searched and selected the most suitable scraper (actor)
Configured and ran the actor
Extracted job data
Downloaded results as a .csv file
Stored the file locally
Uploaded the dataset to Claude
Used prompt engineering to filter relevant job roles
##
🧠 Key Characteristics
Fully functional ETL pipeline (manual)
Simple and easy to implement
No automation
##
⚠️ Limitations
Time-consuming
Not scalable
Requires repeated manual effort


🔹 Way 2: Automated Pipeline (Production-Oriented Approach ⭐)
📌 Overview

This approach improves Way 1 by introducing automation and scheduling, making the pipeline more scalable and efficient.

⚙️ Steps
Created an account on Apify
Selected and configured the scraper (actor)
Ran the actor to extract job data
Connected Claude with Apify
Automated the workflow using Apify’s scheduler
Pipeline runs at regular intervals (no manual trigger needed)
Data is processed and sent to Claude
Used prompt engineering to filter and rank relevant jobs

🧠 Key Characteristics
Automated ETL pipeline
Reduced manual intervention
Scalable and repeatable workflow

🚀 Why This Is the Best Version
Demonstrates data engineering mindset
Shows ability to build real-world pipelines
Combines automation + AI integration


🔹 Way 3: Custom Scraper (Code-Driven Approach ⚠️)
📌 Overview

This approach attempts to build the entire pipeline from scratch using custom scraping logic.

⚙️ Steps
Wrote custom web scraping scripts (e.g., Python-based)
Extracted job data directly from websites
Stored results in .csv format
Uploaded dataset to Claude
Used prompt engineering to filter relevant roles

🧠 Key Characteristics
Full control over scraping logic
No dependency on external scraping platforms

⚠️ Challenges Faced
Difficulty handling dynamic websites (JavaScript-heavy)
Encountered anti-scraping mechanisms (blocking, captchas)
Higher maintenance effort
