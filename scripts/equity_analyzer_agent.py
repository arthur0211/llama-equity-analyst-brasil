import os
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
import json
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

# LlamaIndex Workflow and Pydantic Program
from llama_index.core.workflow import (
    Workflow,
    step,
    StopEvent,
    StartEvent,
    Event,
    Context,
)
from llama_index.core.prompts import PromptTemplate
from llama_index.core.llms.llm import LLM

# Output Schemas
from scripts.output_schemas import (
    KeyMetric,
    CompanyFinancialSummaryOutput,
    ComparativeAnalysisOutput,
    FinalBrazilianEnergyMemoOutput
)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY") 

# Configure LLM and Embedding Model
Settings.llm = GoogleGenAI(model="models/gemini-2.0-flash", api_key=GEMINI_API_KEY)
Settings.embed_model = GoogleGenAIEmbedding(model_name="models/embedding-001", api_key=GEMINI_API_KEY)

# --- Custom Workflow Events ---
class CompanySummaryEvent(Event):
    summary: CompanyFinancialSummaryOutput
    company_name: str

class ComparativeAnalysisReadyEvent(Event):
    analysis: ComparativeAnalysisOutput

# --- Helper Functions (Prompts) ---

def get_company_summary_prompt_template() -> PromptTemplate:
    template_str = """Context:
Company Name: {company_name}
Report Period: {report_period}
Financial Modeling Assumptions (for Brazilian Energy Sector - use as general guidance):
{modeling_assumptions}

Data from financial report:
{report_data_context}

Task:
Analyze the provided data for the company and report period.
Generate a comprehensive financial summary and outlook.
Focus on:
1.  Key Financial Metrics: Net Revenue, EBITDA, Net Income, CAPEX, Debt levels.
2.  Operational Highlights: Significant projects, capacity changes, energy generation/transmission volumes.
3.  Management's Outlook: Stated expectations for future performance, key challenges, and opportunities.
4.  Qualitative Factors: Regulatory impacts, market conditions, strategic initiatives relevant to {company_name}.

Output Requirements:
- Provide specific figures and data points where available in the documents.
- Clearly state the units for all financial figures (e.g., R$ millions, R$ billions).
- The summary should be concise yet informative, suitable for an equity research memo.
- Extract relevant KeyMetric objects for revenue, ebitda, and net_income.
- Ensure the output strictly follows the Pydantic schema for CompanyFinancialSummaryOutput.
"""
    return PromptTemplate(template=template_str)

def get_comparative_analysis_prompt_template() -> PromptTemplate:
    template_str = """Context:
You have financial summaries for two Brazilian energy companies:
Company A ({company_a_name}): 
{company_a_summary_json}

Company B ({company_b_name}): 
{company_b_summary_json}

Task:
Perform a comparative analysis of these two companies based on their summaries.
Focus on:
1.  Relative financial performance (e.g., revenue growth, profitability margins, debt levels).
2.  Key operational differences and strengths/weaknesses.
3.  Differing outlooks or strategic priorities.
4.  Identify 2-3 key differentiating factors that an investor should consider.

Output Requirements:
- The analysis should be balanced, highlighting aspects of both companies.
- Conclude with a brief statement on which company appears to have a stronger profile or better outlook, and why.
- Ensure the output strictly follows the Pydantic schema for ComparativeAnalysisOutput.
"""
    return PromptTemplate(template=template_str)

def get_final_memo_prompt_template() -> PromptTemplate:
    template_str = """Context:
Current Date: {current_date}
You have the following information:
1.  Financial Summary for {company_a_name}: 
{company_a_summary_json}
2.  Financial Summary for {company_b_name}: 
{company_b_summary_json}
3.  Comparative Analysis: 
{comparative_analysis_json}
4.  Overall Modeling Assumptions: 
{modeling_assumptions}

Task:
Synthesize all the provided information into a final equity research memo for the Brazilian Energy Sector, focusing on {company_a_name} and {company_b_name}.
The memo should include:
1.  An Executive Summary: Briefly state the key findings and overall investment thesis.
2.  Individual Company Overviews: Derived from the financial summaries.
3.  Comparative Analysis Section: Based on the provided comparative analysis.
4.  Investment Recommendation: For each company (e.g., Buy, Hold, Sell, Neutral) with a clear rationale based on the analysis. Consider the modeling assumptions in your rationale.
5.  Key Risks: Identify 2-3 major risks applicable to investing in these companies or the sector.
6.  Date Generated: Use the Current Date provided: {current_date}.

Output Requirements:
- The memo should be well-structured, professional, and insightful.
- Ensure the output strictly follows the Pydantic schema for FinalBrazilianEnergyMemoOutput, especially ensuring the 'date_generated' field uses the provided Current Date.
"""
    return PromptTemplate(template=template_str)

# --- Workflow Definition (Class-based) ---

class EquityResearchWorkflow(Workflow):
    def __init__(self, 
                 modeling_assumptions_content: str,
                 report_period_str: str,
                 taesa_name_str: str,
                 engie_name_str: str,
                 llm: Optional[LLM] = None, 
                 **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or Settings.llm
        self.modeling_assumptions_content = modeling_assumptions_content
        self.report_period_str = report_period_str
        self.taesa_name_str = taesa_name_str
        self.engie_name_str = engie_name_str

    @step
    async def generate_taesa_summary_step(
        self, 
        ctx: Context,
        ev: StartEvent
    ) -> CompanySummaryEvent:
        taesa_query_engine = ev.taesa_query_engine
        print(f"\n----- Generating Financial Summary for {self.taesa_name_str} ({self.report_period_str}) -----")
        
        context_query = f"Provide all available financial and operational data, management discussion, project details, and debt information for {self.taesa_name_str} for {self.report_period_str}."
        report_data_context = await taesa_query_engine.aquery(context_query)

        output = await self.llm.astructured_predict(
            output_cls=CompanyFinancialSummaryOutput,
            prompt=get_company_summary_prompt_template(),
            company_name=self.taesa_name_str,
            report_period=self.report_period_str,
            modeling_assumptions=self.modeling_assumptions_content,
            report_data_context=str(report_data_context)
        )
        print(f"Raw Pydantic Output for {self.taesa_name_str}:\n{output.model_dump_json(indent=2)}")
        await ctx.set(self.taesa_name_str, output)
        return CompanySummaryEvent(summary=output, company_name=self.taesa_name_str)

    @step
    async def generate_engie_summary_step(
        self, 
        ctx: Context,
        ev: StartEvent
    ) -> CompanySummaryEvent:
        engie_query_engine = ev.engie_query_engine
        print(f"\n----- Generating Financial Summary for {self.engie_name_str} ({self.report_period_str}) -----")

        context_query = f"Provide all available financial and operational data, management discussion, project details, and debt information for {self.engie_name_str} for {self.report_period_str}."
        report_data_context = await engie_query_engine.aquery(context_query)

        output = await self.llm.astructured_predict(
            output_cls=CompanyFinancialSummaryOutput,
            prompt=get_company_summary_prompt_template(),
            company_name=self.engie_name_str,
            report_period=self.report_period_str,
            modeling_assumptions=self.modeling_assumptions_content,
            report_data_context=str(report_data_context)
        )
        print(f"Raw Pydantic Output for {self.engie_name_str}:\n{output.model_dump_json(indent=2)}")
        await ctx.set(self.engie_name_str, output)
        return CompanySummaryEvent(summary=output, company_name=self.engie_name_str)

    @step
    async def generate_comparative_analysis_step(
        self, 
        ctx: Context,
        ev: CompanySummaryEvent
    ) -> Optional[ComparativeAnalysisReadyEvent]:
        print(f"\n----- generate_comparative_analysis_step triggered by {ev.company_name} ----- ")
        
        taesa_summary = await ctx.get(self.taesa_name_str, default=None)
        engie_summary = await ctx.get(self.engie_name_str, default=None)

        if taesa_summary is None or engie_summary is None:
            print("Waiting for both company summaries to be available...")
            return None

        print(f"\n----- Generating Comparative Analysis for {self.taesa_name_str} and {self.engie_name_str} -----")
        comparative_output = await self.llm.astructured_predict(
            output_cls=ComparativeAnalysisOutput,
            prompt=get_comparative_analysis_prompt_template(),
            company_a_name=self.taesa_name_str,
            company_a_summary_json=taesa_summary.model_dump_json(),
            company_b_name=self.engie_name_str,
            company_b_summary_json=engie_summary.model_dump_json()
        )
        print(f"Raw Pydantic Output for Comparative Analysis:\n{comparative_output.model_dump_json(indent=2)}")
        await ctx.set("comparative_analysis_data", comparative_output)
        return ComparativeAnalysisReadyEvent(analysis=comparative_output)

    @step
    async def generate_final_memo_step(
        self, 
        ctx: Context,
        ev: ComparativeAnalysisReadyEvent
    ) -> StopEvent:
        print("\n----- Generating Final Equity Research Memo -----")

        taesa_summary = await ctx.get(self.taesa_name_str, default=None)
        engie_summary = await ctx.get(self.engie_name_str, default=None)
        comparative_analysis = ev.analysis

        if not all([taesa_summary, engie_summary, comparative_analysis]):
            print("ERROR: Missing data for final memo generation. This shouldn't happen if workflow is correct.")
            return StopEvent(result={"error": "Missing data for final memo"})

        final_output = await self.llm.astructured_predict(
            output_cls=FinalBrazilianEnergyMemoOutput,
            prompt=get_final_memo_prompt_template(),
            current_date=datetime.now().strftime("%Y-%m-%d"),
            company_a_name=self.taesa_name_str,
            company_a_summary_json=taesa_summary.model_dump_json(),
            company_b_name=self.engie_name_str,
            company_b_summary_json=engie_summary.model_dump_json(),
            comparative_analysis_json=comparative_analysis.model_dump_json(),
            modeling_assumptions=self.modeling_assumptions_content
        )
        print(f"Raw Pydantic Output for Final Memo:\n{final_output.model_dump_json(indent=2)}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output/final_equity_memo_{timestamp}.json"
        os.makedirs(os.path.dirname(output_filename), exist_ok=True) 
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(final_output.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"\nFinal equity research memo saved to: {output_filename}")
        
        return StopEvent(result=final_output)

# Instantiate the class-based workflow
# equity_workflow = EquityResearchWorkflow(verbose=True)

async def main_async(taesa_index_dir: str, engie_index_dir: str, assumptions_file: str, report_period_arg: str):
    print("--- Initializing Equity Analyzer Workflow ---")
    
    taesa_storage_context = StorageContext.from_defaults(persist_dir=taesa_index_dir)
    taesa_index = load_index_from_storage(taesa_storage_context)
    taesa_query_engine = taesa_index.as_query_engine(similarity_top_k=5)
    
    engie_storage_context = StorageContext.from_defaults(persist_dir=engie_index_dir)
    engie_index = load_index_from_storage(engie_storage_context)
    engie_query_engine = engie_index.as_query_engine(similarity_top_k=5)

    with open(assumptions_file, "r", encoding="utf-8") as f:
        modeling_assumptions_content = f.read()

    taesa_company_name = "Taesa (Transmissora Aliança de Energia Elétrica S.A.)"
    engie_company_name = "Engie Brasil Energia S.A."

    print("\n--- Starting Workflow ---")
    
    workflow_instance = EquityResearchWorkflow(
        modeling_assumptions_content=modeling_assumptions_content,
        report_period_str=report_period_arg,
        taesa_name_str=taesa_company_name,
        engie_name_str=engie_company_name,
        llm=Settings.llm, 
        verbose=True,
        timeout=240 # Added timeout
    )

    workflow_result = await workflow_instance.run(
        taesa_query_engine=taesa_query_engine,
        engie_query_engine=engie_query_engine
    )
    
    if isinstance(workflow_result, FinalBrazilianEnergyMemoOutput):
        print("\n--- Workflow Completed Successfully ---")
        print("Final Memo Output (from workflow run):")
        print(workflow_result.model_dump_json(indent=2))
    else:
        print("\n--- Workflow Completed (Unexpected Result Type) ---")
        print(f"Type: {type(workflow_result)}")
        print(f"Value: {workflow_result}")

if __name__ == "__main__":
    TAESA_INDEX_DIR = "output/indexes/taesa"
    ENGIE_INDEX_DIR = "output/indexes/engie"
    ASSUMPTIONS_FILE = "data/reference/modeling_assumptions.txt"
    REPORT_PERIOD = "1Q2025"

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file")

    asyncio.run(main_async(TAESA_INDEX_DIR, ENGIE_INDEX_DIR, ASSUMPTIONS_FILE, REPORT_PERIOD))

