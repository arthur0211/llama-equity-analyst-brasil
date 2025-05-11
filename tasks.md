# Project: Equity Research Analysis for Brazilian Companies (Taesa & Engie)

This document outlines the tasks and subtasks required to replicate an equity research analysis project using LlamaIndex and Gemini for the Brazilian companies Taesa and Engie, leveraging LlamaExtract for data extraction.

## 1. Project Setup & Configuration

- [x] **1.1. Initialize Project Environment:**
    - [x] Create a dedicated project directory.
    - [x] Set up a Python virtual environment.
- [x] **1.2. Install Dependencies:**
    - [x] `pip install llama-index-core`
    - [-] `pip install llama-index-readers-file` (Attempted, but local parsing issues led to pivoting to LlamaCloud services)
    - [x] `pip install llama-index-llms-gemini`
    - [x] `pip install llama-cloud-services` (For LlamaParse & LlamaExtract)
    - [x] `pip install google-generativeai`
    - [x] `pip install python-dotenv`
    - [x] `pip install pandas`
- [x] **1.3. API Key Configuration:**
    - [x] Obtain and configure `GEMINI_API_KEY` in `.env`.
    - [x] **1.3.1. Obtain and Configure LlamaCloud API Key:**
        - [x] Go to [LlamaCloud](https://cloud.llamaindex.ai/) and generate a new API key.
        - [x] Add `LLAMA_CLOUD_API_KEY='YOUR_LLAMA_CLOUD_KEY'` to your `.env` file. (User confirmed setup)
- [x] **1.4. Organize Project Structure:** (Directories `data/`, `scripts/`, etc. created)
- [x] **1.5. Data Files Organized:** (PDFs moved to `data/release-taee/` and `data/release-engie/`)

## 2. Data Extraction using LlamaExtract

- [x] **2.1. Define Extraction Schemas (Pydantic Models):**
    - [x] **2.1.1. Identify Key Financial and Operational Metrics:** Determined the specific data points to extract.
    - [x] **2.1.2. Create Pydantic Models:** Python classes using Pydantic defined and implemented in `scripts/data_extractor.py`.
- [x] **2.2. Implement Data Extraction for Taesa's Report:**
    - [x] **2.2.1. Initialize `LlamaExtract` Client:** Implemented in `scripts/data_extractor.py`.
    - [x] **2.2.2. Create/Configure `LlamaExtract` Agent:** Implemented in `scripts/data_extractor.py` (Agent: "brazilian-equity-extractor-v1").
    - [x] **2.2.3. Extract Data from Taesa PDF:** Initial extraction successful.
        - [x] Called the agent's `extract` method with `data/release-taee/TAESA-Release-1T25.pdf`.
        - [x] Inspected the `result.data` and `result.extraction_metadata`.
    - [x] **2.2.4. Refine Pydantic Schema and Re-extract (Iterative):**
        - [x] Adjusted field descriptions in `BrazilianCompanyReportData` (and sub-models) in `scripts/data_extractor.py`. CAPEX extraction improved. Some specific operational totals (km, MVA) and broad qualitative summaries (MD&A) remain `None` for Taesa, likely due to source document structure. Current extraction deemed sufficient for Taesa first pass.
        - [x] Re-ran extraction for Taesa to verify improvements.
- [x] **2.3. Implement Data Extraction for Engie's Report:**
    - [x] **2.3.1. Apply Existing Schema to Engie's Report:** Used the `BrazilianCompanyReportData` schema in `scripts/data_extractor.py` to extract data from `data/release-engie/250507-Release-de-Resultados-1T25.pdf`.
        - [x] Modified `scripts/data_extractor.py` to target Engie's PDF.
        - [x] Ran the script and inspected `result.data` and `result.extraction_metadata` for Engie.
    - [x] **2.3.2. Analyze Engie Extraction & Refine Schema (if needed):**
        - [x] Compared extracted data for Engie against the report. Iteratively refined schema.
        - [x] Final Engie extraction: `management_discussion_and_outlook` and most financials are good. Unit conversions for key financials (CAPEX, cash, dividends) are corrected. `taesa_operational_summary` is correctly `None`. However, `regulatory_environment_impacts` remains `None`. `engie_operational_summary.transmission_segment_rap` and `engie_operational_summary.transmission_segment_investment` regressed to `None` in the final run after being present in a prior run. Decided to proceed with current extraction as "good enough" for now.
- [x] **2.4. Convert Extracted Data to LlamaIndex Documents:**
    - [x] **For Engie:** Processed structured data from `LlamaExtract` (`result.data`). Converted to LlamaIndex `Document` (Pydantic model as JSON string in `text`, key fields in `metadata`). Saved to `output/extracted_documents/engie_brasil_energia_sa_1t25.json`. Some minor data value inconsistencies noted in step 2.3.2 remain but deemed acceptable for now.
    - [x] **For Taesa:** Processed structured data from `LlamaExtract` (`result.data`). Converted to LlamaIndex `Document` (Pydantic model as JSON string in `text`, key fields in `metadata`). Saved to `output/extracted_documents/taesa___transmissora_aliança_de_energia_elétrica_sa_1º_trimestre_de_2025.json`. Some fields (`management_discussion_and_outlook`, `regulatory_environment_impacts`, `ESG_highlights`, `transmission_lines_km`, `substation_capacity_mva`) are `null`, consistent with source document and previous extraction attempts.

## 3. Data Indexing and Agentic Workflow with LlamaIndex & Gemini

- [x] **3.1. Initialize LlamaIndex Components:**
    - [x] Created `scripts/index_builder.py`.
    - [x] Set up `GoogleGenAI` LLM (`models/gemini-pro`) and `GoogleGenAIEmbedding` (`models/embedding-001`) in LlamaIndex `Settings`.
- [x] **3.2. Create Index from Extracted Taesa Data:**
    - [x] Implemented logic in `scripts/index_builder.py` to load the LlamaIndex `Document` from `output/extracted_documents/taesa___transmissora_aliança_de_energia_elétrica_sa_1º_trimestre_de_2025.json`.
    - [x] Implemented logic to build and persist a `VectorStoreIndex` to `output/indexes/taesa/`.
    - [x] Ran script and verified index creation. Index persisted.
- [x] **3.3. Create Index from Extracted Engie Data:**
    - [x] Implemented logic in `scripts/index_builder.py` to load the LlamaIndex `Document` from `output/extracted_documents/engie_brasil_energia_sa_1t25.json`.
    - [x] Implemented logic to build and persist a `VectorStoreIndex` to `output/indexes/engie/`.
    - [x] Ran script and verified index creation. Index persisted.
- [x] **3.4. Define and Load Modeling Assumptions:** (This was previously 2.1, moved here as it's more relevant for the analysis phase after initial data extraction)
    - [x] **3.4.1. Research and define key modeling assumptions** for the Brazilian energy/utility sector.
    - [x] Created `data/reference/modeling_assumptions.txt` with placeholders and initial researched values.
    - [x] **3.4.2. Load modeling assumptions into the workflow/agent.** (Implemented in `scripts/equity_analyzer_agent.py` via `InputNode`)
- [ ] **3.5. Implement Asynchronous Multi-Step LlamaIndex Workflow for Financial Analysis:**
    - [x] **3.5.1. Workflow Step: Generate Taesa Financial Summary**
        - [x] Define Pydantic output schema (`CompanyFinancialSummaryOutput`).
        - [x] Create prompt template incorporating modeling assumptions.
        - [x] Implement workflow step using `Settings.llm.astructured_predict`.
    - [x] **3.5.2. Workflow Step: Generate Engie Financial Summary**
        - [x] Reuse `CompanyFinancialSummaryOutput` schema.
        - [x] Create similar prompt template for Engie.
        - [x] Implement workflow step.
    - [x] **3.5.3. Workflow Step: Generate Comparative Analysis**
        - [x] Define Pydantic output schema (`ComparativeAnalysisOutput`).
        - [x] Create prompt template that takes both company summaries as input.
        - [x] Implement workflow step. This step will depend on the completion of 3.5.1 and 3.5.2. Use `Context` to await both `CompanySummaryEvent`s.
    - [x] **3.5.4. Workflow Step: Generate Final Equity Research Memo**
        - [x] Define Pydantic output schema (`FinalBrazilianEnergyMemoOutput`).
        - [x] Create prompt template that takes Taesa summary, Engie summary, and comparative analysis as input.
        - [x] Implement workflow step. This step depends on 3.5.1, 3.5.2, and 3.5.3. Use `Context` to await `ComparativeAnalysisReadyEvent`.
    - [x] **3.5.5. Execute Workflow and Save Output:**
        - [x] Instantiate the `EquityResearchWorkflow`.
        - [x] Asynchronously run the workflow with the Taesa and Engie query engines as input to `StartEvent`.
        - [x] Retrieve the final `FinalBrazilianEnergyMemoOutput` from the `StopEvent`.
        - [x] Save the final memo to a timestamped JSON file in `output/`.
    - [ ] **3.5.6. Refactor main script for clarity and argument parsing (argparse).**
- [x] **3.6. Refactor Index Creation for Granularity:** (Completed)
    - [x] Modified `scripts/index_builder.py`.
    - [x] Successfully re-ran `scripts/index_builder.py`, creating and persisting granular indexes: 6 nodes for Taesa, 14 nodes for Engie.
- [ ] **3.7. Review and Refine Workflow:** (This task replaces the old 3.7 which was more generic)
    - [x] Verify data flow and automatic wiring of step dependencies using `Context` and custom `Event`s.
    - [ ] Test the quality of prompts for each step.
    - [ ] Analyze the generated outputs for accuracy, completeness, and insightfulness.

## 4. Reporting and Output

- [ ] **4.1. Generate Financial Summaries:**

## 5. Output Generation and Reporting

- [x] **5.1. Define Final Report/Memo Structure (Pydantic Model if outputting JSON).** (Completed in `scripts/output_schemas.py`)
- [ ] **5.2. Execute the Agentic Workflow.** (To be done by running `scripts/equity_analyzer_agent.py`)
- [ ] **5.3. Format and Present Findings.** (Currently JSON output, further presentation can be a future step)

## 6. Testing and Refinement

- [ ] **6.1. Test LlamaExtract Data Extraction Quality.**
- [ ] **6.2. Test Agentic Workflow Logic and LLM Responses.**
- [ ] **6.3. Validate Analysis and Final Memo.**

## 7. Documentation and Finalization

- [ ] **7.1. Code Documentation.**
- [ ] **7.2. Project README.**
- [ ] **7.3. Final Review.**

## 8. Refactor Index Creation for Granularity

- [x] **3.6. Refactor Index Creation for Granularity:** (Completed)
    - [x] Modified `scripts/index_builder.py`.
    - [x] Successfully re-ran `scripts/index_builder.py`, creating and persisting granular indexes: 6 nodes for Taesa, 14 nodes for Engie.
- [ ] **3.7. Review and Refine Workflow:** (This task replaces the old 3.7 which was more generic)
    - [ ] Verify data flow and automatic wiring of step dependencies.
    - [ ] Test prompts for each step for clarity, effectiveness, and to ensure they guide the LLM to produce accurate Pydantic outputs.
    - [ ] Analyze the quality and completeness of the `CompanyFinancialSummaryOutput`, `ComparativeAnalysisOutput`, and `FinalBrazilianEnergyMemoOutput`.
    - [ ] Iteratively adjust prompts, Pydantic schemas (if necessary), and LLM parameters (`temperature`, `model_name` if experimenting) based on output quality.
    - [ ] Ensure modeling assumptions are effectively utilized by the LLM in relevant steps.

## 9. Update Main Script Execution

- [x] Ensure `scripts/equity_analyzer_agent.py` can be run as a module: `python -m scripts.equity_analyzer_agent`.
- [ ] Add command-line arguments (using `argparse`) for:
    - Taesa index directory.
    - Engie index directory.
    - Modeling assumptions file path.
    - Report period string (e.g., "1Q2025").
    - Optional output directory. 