# Project: Equity Research Analysis for Brazilian Companies (Taesa & Engie)

This document outlines the tasks and subtasks required to replicate an equity research analysis project using LlamaIndex and Gemini for the Brazilian companies Taesa and Engie, leveraging LlamaExtract for data extraction. The final goal is a senior equity analyst quality report in Markdown and/or PDF format.

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

## 3. Data Indexing and Initial Workflow

- [x] **3.1. Initialize LlamaIndex Components:**
    - [x] Created `scripts/index_builder.py`.
    - [x] Set up `GoogleGenAI` LLM (`models/gemini-pro`) and `GoogleGenAIEmbedding` (`models/embedding-001`) in LlamaIndex `Settings`.
- [x] **3.2. Create Granular Index from Extracted Taesa Data:**
    - [x] Implemented logic in `scripts/index_builder.py` to load the LlamaIndex `Document` from `output/extracted_documents/taesa___transmissora_aliança_de_energia_elétrica_sa_1º_trimestre_de_2025.json`.
    - [x] Implemented logic to build and persist a `VectorStoreIndex` to `output/indexes/taesa/`.
    - [x] Ran script and verified index creation. Index persisted.
- [x] **3.3. Create Granular Index from Extracted Engie Data:**
    - [x] Implemented logic in `scripts/index_builder.py` to load the LlamaIndex `Document` from `output/extracted_documents/engie_brasil_energia_sa_1t25.json`.
    - [x] Implemented logic to build and persist a `VectorStoreIndex` to `output/indexes/engie/`.
    - [x] Ran script and verified index creation. Index persisted.
- [x] **3.4. Define and Load Modeling Assumptions:** (This was previously 2.1, moved here as it's more relevant for the analysis phase after initial data extraction)
    - [x] **3.4.1. Research and define key modeling assumptions** for the Brazilian energy/utility sector.
    - [x] Created `data/reference/modeling_assumptions.txt` with placeholders and initial researched values.
    - [x] **3.4.2. Load modeling assumptions into the workflow/agent.** (Implemented in `scripts/equity_analyzer_agent.py` via `InputNode`)
- [x] **3.5. Implement Asynchronous Multi-Step LlamaIndex Workflow (JSON Output):**
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
    - [x] **3.5.5. Execute Workflow and Save JSON Output:**
        - [x] Instantiate the `EquityResearchWorkflow`.
        - [x] Asynchronously run the workflow with the Taesa and Engie query engines as input to `StartEvent`.
        - [x] Retrieve the final `FinalBrazilianEnergyMemoOutput` from the `StopEvent`.
        - [x] Save the final memo to a timestamped JSON file in `output/`.
    - [x] **3.5.6. Verify data flow and event handling (`Context`, custom `Event`s):**
        - [x] Verify data flow and automatic wiring of step dependencies using `Context` and custom `Event`s.

## 4. Script Parameterization (argparse)

- [ ] **4.1. Add Command-Line Arguments to `equity_analyzer_agent.py`:** (Consolidates 3.5.6 and section 9)
    - [ ] Taesa index directory.
    - [ ] Engie index directory.
    - [ ] Modeling assumptions file path.
    - [ ] Report period string (e.g., "1Q2025").
    - [ ] Output directory for reports (JSON, MD, PDF).
    - [ ] Company name overrides (optional).
- [ ] **4.2. (Optional) Add Command-Line Arguments to `data_extractor.py`:**
    - [ ] Input PDF file path.
    - [ ] Output JSON file path.
    - [ ] Company name (for metadata or schema selection if it becomes more dynamic).
- [ ] **4.3. (Optional) Add Command-Line Arguments to `index_builder.py`:**
    - [ ] Input extracted JSON file path.
    - [ ] Output index directory path.

## 5. Report Generation & Senior Analyst Quality Enhancement

- [ ] **5.1. Refine Pydantic Output Schemas (`output_schemas.py`) for Senior Analyst Report:**
    - [ ] Evaluate `FinalBrazilianEnergyMemoOutput` and sub-models for completeness.
    - [ ] Consider adding/enhancing fields for:
        - [ ] Detailed SWOT analysis (Strengths, Weaknesses, Opportunities, Threats).
        - [ ] Explicit Valuation section (methodologies, key drivers, sensitivity).
        - [ ] Dedicated Investment Thesis.
        - [ ] Key Catalysts and expanded Key Risks.
        - [ ] Management Assessment/Credibility.
        - [ ] Industry Overview & Competitive Positioning.
    - [ ] Update prompts and workflow steps if schemas change.
- [ ] **5.2. Enhance Prompts for "Senior Analyst" Tone, Depth, and Critical Insight:**
    - [ ] Review and iteratively refine prompts for `CompanyFinancialSummaryOutput`.
    - [ ] Review and iteratively refine prompt for `ComparativeAnalysisOutput`.
    - [ ] Review and iteratively refine prompt for `FinalBrazilianEnergyMemoOutput`.
    - [ ] Ensure prompts explicitly ask for critical thinking, nuanced arguments, and justification for recommendations.
- [ ] **5.3. Implement Markdown Report Generation:**
    - [ ] Create a function/script to convert `FinalBrazilianEnergyMemoOutput` (Pydantic object or JSON) to a well-formatted Markdown string.
        - [ ] Use appropriate Markdown elements (headers, lists, tables for key metrics, blockquotes for summaries).
        - [ ] Ensure the structure mirrors a professional analyst report.
    - [ ] Save the generated Markdown to a `.md` file (e.g., `output/report_YYYYMMDD_HHMMSS.md`).
    - [ ] Integrate this step into the `equity_analyzer_agent.py` main execution flow or as a separate callable script.
- [ ] **5.4. (Optional) Implement PDF Report Generation from Markdown:**
    - [ ] Research and select a Python library for Markdown to PDF conversion (e.g., `pypandoc`, `WeasyPrint`).
    - [ ] Add chosen library to `requirements.txt`.
    - [ ] Implement a function to convert the generated Markdown file to a PDF file.
    - [ ] Save the PDF to `output/report_YYYYMMDD_HHMMSS.pdf`.
- [ ] **5.5. Quality Assurance and Iteration:**
    - [ ] Analyze the quality and completeness of the generated Markdown/PDF reports.
    - [ ] Iteratively adjust prompts, Pydantic schemas, Markdown generation logic, and LLM parameters (`temperature`, `model_name`) based on output quality.
    - [ ] Ensure modeling assumptions are effectively and explicitly utilized in the final report.

## 6. Git & Project Management

- [x] **6.1. Initial Project Setup on GitHub.** (README, .gitignore, initial commit)
- [ ] **6.2. Manage `output/indexes/` in `.gitignore**:
    - [ ] Confirm and apply decision to untrack/ignore these directories (recommended).
    - [ ] If untracked, ensure `.gitignore` correctly excludes them and commit the change.
- [ ] **6.3. Update `README.md**:
    - [ ] Reflect new Markdown/PDF output capabilities.
    - [ ] Update instructions for running parameterized scripts.
    - [ ] Add a section on report structure/example output.

## 7. Testing and Finalization (Future Tasks)

- [ ] **7.1. Test LlamaExtract Data Extraction Quality (Ongoing as reports change).**
- [ ] **7.2. Test Agentic Workflow Logic and LLM Responses (Ongoing with prompt/schema changes).**
- [ ] **7.3. Validate Analysis and Final Memo (Critical Review).**
- [ ] **7.4. Code Documentation (Docstrings, comments for complex logic).**
- [ ] **7.5. Final Project Review and Cleanup.**

## 8. Review, Refinement, and Final Output

- [ ] **Review generated Markdown report for quality, completeness, and formatting.** (USER TASK)
- [ ] **(Optional) Implement Markdown to PDF conversion.**
    - [ ] Research and select a suitable Python library or command-line tool for MD to PDF (e.g., Pandoc, WeasyPrint, mdpdf).
    - [ ] Add a new script or function to handle the MD to PDF conversion.
    - [ ] Update workflow/documentation.
- [ ] **Iteratively refine prompts, Pydantic output schemas, and Markdown formatting based on review.**
- [ ] **Ensure all Python code adheres to specified development standards (PEP 8, type hints, error handling, etc.).**
- [ ] **Finalize `README.md` with comprehensive instructions and project summary.**
- [ ] **Update `tasks.md` to reflect all completed and pending tasks accurately.**
- [ ] **Commit and push all final changes to the GitHub repository.**

## 9. Retry script execution after quota adjustment and model switch for `equity_analyzer_agent.py`

- [X] **Retry script execution after quota adjustment and model switch for `equity_analyzer_agent.py`** (Attempted, but hit `400 INVALID_ARGUMENT` due to schema complexity, then `503 UNAVAILABLE` which is transient, then `TypeError` for `ensure_ascii`, then `TypeError` in final print, all fixed.)

## 10. Refactor `generate_final_memo_step` to be iterative for schema complexity and token limits, with robust error handling for each sub-section.

- [X] **Refactor `generate_final_memo_step` to be iterative for schema complexity and token limits, with robust error handling for each sub-section.** (Implemented)

## 11. Run `equity_analyzer_agent.py` successfully to generate final JSON output with new schemas and iterative logic.

- [X] **Run `equity_analyzer_agent.py` successfully to generate final JSON output with new schemas and iterative logic.** (Completed, with some sections gracefully showing API errors as N/A)

## 12. Create `scripts/json_to_markdown_converter.py` to convert the final JSON memo into a well-formatted Markdown report.

- [X] **Create `scripts/json_to_markdown_converter.py` to convert the final JSON memo into a well-formatted Markdown report.**

## 13. Run the Markdown converter to produce the `.md` report.

- [X] **Run the Markdown converter to produce the `.md` report.** 