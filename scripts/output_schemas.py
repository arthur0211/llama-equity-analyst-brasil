from pydantic import BaseModel, Field
from typing import Optional, List

class KeyMetric(BaseModel):
    name: str = Field(..., description="Name of the financial or operational metric.")
    value: Optional[str] = Field(None, description="Value of the metric, as a string to accommodate various formats and units initially.")
    unit: Optional[str] = Field(None, description="Unit of the metric (e.g., R$ milhões, MW, km).")
    period: Optional[str] = Field(None, description="Reporting period for the metric (e.g., 1T25).")
    source_comment: Optional[str] = Field(None, description="Brief comment on the source or derivation, if applicable.")

class CompanyFinancialSummaryOutput(BaseModel):
    company_name: str = Field(..., description="Name of the company.")
    report_period: str = Field(..., description="The primary reporting period being summarized (e.g., 1T25).")
    key_financial_metrics: List[KeyMetric] = Field([], description="List of key extracted financial metrics.")
    key_operational_metrics: List[KeyMetric] = Field([], description="List of key extracted operational metrics.")
    management_discussion_summary: Optional[str] = Field(None, description="Concise summary of the management discussion and outlook.")
    key_projects_summary: Optional[str] = Field(None, description="Summary of key projects and investments.")
    debt_leverage_summary: Optional[str] = Field(None, description="Summary of debt and leverage analysis.")
    analyst_outlook_notes: Optional[str] = Field(None, description="Analyst notes on the qualitative outlook based on the report and assumptions. Focus on factors influencing future performance.")

class ComparativeAnalysisOutput(BaseModel):
    comparison_points: List[str] = Field([], description="List of key points comparing the two companies.")
    relative_strengths_taesa: List[str] = Field([], description="Relative strengths identified for Taesa.")
    relative_strengths_engie: List[str] = Field([], description="Relative strengths identified for Engie.")
    comparative_outlook_notes: Optional[str] = Field(None, description="Overall notes on the comparative outlook.")

class FinalBrazilianEnergyMemoOutput(BaseModel):
    memo_title: str = Field("Equity Research Memo: Taesa & Engie - Brazilian Energy Sector", description="Title of the memo.")
    date_generated: str = Field(..., description="Date the memo was generated.")
    taesa_summary: CompanyFinancialSummaryOutput = Field(..., description="Financial summary for Taesa.")
    engie_summary: CompanyFinancialSummaryOutput = Field(..., description="Financial summary for Engie.")
    comparative_analysis: ComparativeAnalysisOutput = Field(..., description="Comparative analysis between Taesa and Engie.")
    overall_conclusion_and_recommendation: Optional[str] = Field(None, description="Overall conclusion and high-level investment recommendation or strategic insights.")

print("Output schemas defined in output_schemas.py") 