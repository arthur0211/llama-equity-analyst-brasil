# Equity Research Analysis for Brazilian Energy Companies (Taesa & Engie) using LlamaIndex & Gemini

This project demonstrates an automated equity research analysis workflow for Brazilian energy sector companies, specifically Taesa and Engie. It leverages LlamaIndex for building a retrieval augmented generation (RAG) pipeline, Google's Gemini Pro as the Large Language Model (LLM) for analysis and summarization, and LlamaExtract (via LlamaCloud) for structured data extraction from PDF financial reports.

The workflow ingests quarterly financial reports (PDFs), extracts key financial and operational data, creates granular vector indexes, and then uses a multi-step LlamaIndex Workflow to:
1.  Generate individual financial summaries for Taesa and Engie.
2.  Perform a comparative analysis.
3.  Produce a final equity research memo in a structured Pydantic format.

## Features

*   **Automated Data Extraction:** Uses `LlamaExtract` with Pydantic schemas to pull structured data from PDF reports.
*   **Granular Indexing:** Creates fine-grained nodes in LlamaIndex `VectorStoreIndex` for precise data retrieval.
*   **Multi-Step Analysis Workflow:** Employs LlamaIndex `Workflow` to orchestrate asynchronous analysis steps.
    *   Individual company summaries.
    *   Comparative analysis.
    *   Final memo generation.
*   **Structured Output:** Uses Pydantic models for all LLM outputs, ensuring consistent and parsable results.
*   **LLM Integration:** Leverages Google Gemini Pro for text generation and structured data prediction.
*   **Customizable:** Prompts, Pydantic schemas, and modeling assumptions can be adapted for different companies or sectors.

## Project Structure

```
Equity-Research-llama/
├── .env                        # Environment variables (API keys) - !! GITIGNORE !!
├── .venv/                      # Python virtual environment - !! GITIGNORE !!
├── data/
│   ├── reference/
│   │   └── modeling_assumptions.txt # Key assumptions for financial modeling
│   ├── release-engie/
│   │   └── ENGIE_REPORT.pdf    # Engie's PDF financial report
│   └── release-taese/
│       └── TAESA_REPORT.pdf    # Taesa's PDF financial report
├── notebooks/                  # Jupyter notebooks for experimentation (if any)
├── output/
│   ├── extracted_documents/    # JSON outputs from LlamaExtract
│   ├── final_equity_memo_YYYYMMDD_HHMMSS.json # Final generated memo
│   └── indexes/                # Persisted LlamaIndex vector stores
│       ├── engie/
│       └── taesa/
├── reference/                  # Reference materials, original notebooks
├── scripts/
│   ├── data_extractor.py       # Script for LlamaExtract data extraction
│   ├── index_builder.py        # Script for creating granular LlamaIndex indexes
│   ├── equity_analyzer_agent.py # Main script for running the analysis workflow
│   └── output_schemas.py       # Pydantic models for structured LLM outputs
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── tasks.md                    # Project task tracking
```

## Setup

1.  **Clone the repository (or initialize if you have the files):**
    ```bash
    # If cloning an existing repo:
    # git clone https://github.com/arthur0211/llama-equity-analyst-brasil.git
    # cd llama-equity-analyst-brasil
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` will be generated in a later step. For now, ensure you have installed the packages mentioned in `tasks.md`)*

4.  **Set up API Keys:**
    Create a `.env` file in the project root with your API keys:
    ```env
    GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
    LLAMA_CLOUD_API_KEY="YOUR_LLAMA_CLOUD_API_KEY"
    ```
    Replace `YOUR_GOOGLE_GEMINI_API_KEY` and `YOUR_LLAMA_CLOUD_API_KEY` with your actual keys.

5.  **Place Data Files:**
    *   Put Taesa's PDF report in `data/release-taese/` (e.g., `TAESA-Release-1T25.pdf`).
    *   Put Engie's PDF report in `data/release-engie/` (e.g., `250507-Release-de-Resultados-1T25.pdf`).
    *   Update `data/reference/modeling_assumptions.txt` if needed.

## Running the Analysis

The workflow consists of three main script executions:

1.  **Extract Data (LlamaExtract):**
    This script uses LlamaExtract to parse the PDF reports and save the structured data as JSON.
    You'll need to run this for each company, typically by modifying the script to point to the correct PDF and output path.
    ```bash
    python -m scripts.data_extractor
    ```
    *(Review `scripts/data_extractor.py` to ensure it's configured for the desired company and PDF before each run if not yet parameterized).*

2.  **Build Indexes:**
    This script takes the extracted JSON data and builds granular LlamaIndex vector stores.
    ```bash
    python -m scripts.index_builder
    ```

3.  **Run Equity Analyzer Workflow:**
    This script loads the built indexes and runs the multi-step analysis to generate the final equity memo.
    ```bash
    python -m scripts.equity_analyzer_agent
    ```
    The output memo will be saved in the `output/` directory.

## Next Steps & Potential Improvements

*   Parameterize scripts (`data_extractor.py`, `index_builder.py`, `equity_analyzer_agent.py`) using `argparse` for easier execution with different files/settings.
*   Refine prompts for LLM steps to improve the quality and detail of generated summaries and analyses.
*   Expand Pydantic schemas to capture more detailed financial or operational metrics.
*   Implement more sophisticated error handling and logging.
*   Add unit and integration tests.
*   Explore different LLM models or LlamaIndex components.

## Contributing

Contributions, issues, and feature requests are welcome.

*(This is a placeholder for a more detailed contributing guide if the project becomes more collaborative).* 