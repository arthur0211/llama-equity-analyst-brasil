from pydantic import BaseModel, Field
from typing import Optional, List

class KeyMetric(BaseModel):
    name: str = Field(..., description="Name of the financial or operational metric.")
    value: Optional[str] = Field(None, description="Value of the metric, as a string to accommodate various formats and units initially.")
    value_numeric: Optional[float] = Field(None, description="Numeric value of the metric, if applicable and parseable.")
    unit: Optional[str] = Field(None, description="Unit of the metric (e.g., R$ milhões, MW, km).")
    period: Optional[str] = Field(None, description="Reporting period for the metric (e.g., 1T25).")
    metric_type: Optional[str] = Field(None, description="Type of metric (e.g., 'Financial', 'Operational', 'Valuation').")
    source_comment: Optional[str] = Field(None, description="Brief comment on the source or derivation, if applicable.")

class CompanyFinancialSummaryOutput(BaseModel):
    company_name: str = Field(..., description="Name of the company.")
    report_period: str = Field(..., description="The primary reporting period being summarized (e.g., 1T25).")
    key_financial_metrics: List[KeyMetric] = Field([], description="List of key extracted financial metrics (e.g., Revenue, EBITDA, Net Income).")
    revenue_growth_yoy: Optional[KeyMetric] = Field(None, description="Year-over-year revenue growth.")
    ebitda_margin: Optional[KeyMetric] = Field(None, description="EBITDA margin.")
    net_income_margin: Optional[KeyMetric] = Field(None, description="Net income margin.")
    net_debt_to_ebitda: Optional[KeyMetric] = Field(None, description="Net Debt / EBITDA ratio.")
    dividend_yield: Optional[KeyMetric] = Field(None, description="Dividend yield, if applicable.")
    key_operational_metrics: List[KeyMetric] = Field([], description="List of key extracted operational metrics.")
    management_discussion_summary: Optional[str] = Field(None, description="Concise summary of the management discussion and outlook, focusing on their narrative.")
    key_projects_summary: Optional[str] = Field(None, description="Summary of key projects, CAPEX, and investments.")
    debt_leverage_summary: Optional[str] = Field(None, description="Summary of debt profile, leverage, and financing activities.")
    investment_highlights: List[str] = Field([], description="Key positive aspects and investment highlights for the company.")
    key_concerns_company: List[str] = Field([], description="Key concerns and risks specific to the company's performance or outlook.")
    strategic_initiatives_and_impact: Optional[str] = Field(None, description="Summary of major strategic initiatives and their potential impact.")

class ComparativeAnalysisOutput(BaseModel):
    financial_comparison: List[str] = Field([], description="Direct comparison of key financial metrics (e.g., 'Engie shows higher revenue growth (X%) vs Taesa (Y%)').")
    operational_comparison: List[str] = Field([], description="Comparison of operational aspects, scale, efficiency, and project pipelines.")
    valuation_comparison: List[str] = Field([], description="Placeholder for comparing valuation metrics (e.g., P/E, EV/EBITDA). To be developed further.")
    risk_comparison: List[str] = Field([], description="Comparison of key risks faced by each company.")
    analyst_preference_rationale: Optional[str] = Field(None, description="Analyst's preference between the two companies, with clear rationale based on the comparison.")

class RiskItem(BaseModel):
    risk_description_pt: str = Field(..., description="Risk description (PT).")
    mitigation_factors_pt: Optional[str] = Field(None, description="Mitigation factors (PT).")
    potential_impact_pt: Optional[str] = Field(None, description="Potential impact (PT).")

class SWOTAnalysis(BaseModel):
    strengths_pt: List[str] = Field([], description="Strengths (PT).")
    weaknesses_pt: List[str] = Field([], description="Weaknesses (PT).")
    opportunities_pt: List[str] = Field([], description="Opportunities (PT).")
    threats_pt: List[str] = Field([], description="Threats (PT).")

class InvestmentThesisSection(BaseModel):
    overall_recommendation_taesa_pt: str = Field(..., description="Taesa recommendation (PT).")
    recommendation_rationale_taesa_pt: str = Field(..., description="Taesa rationale (PT).")
    bull_case_taesa_pt: List[str] = Field([], description="Taesa bull case (PT).")
    bear_case_taesa_pt: List[str] = Field([], description="Taesa bear case (PT).")
    overall_recommendation_engie_pt: str = Field(..., description="Engie recommendation (PT).")
    recommendation_rationale_engie_pt: str = Field(..., description="Engie rationale (PT).")
    bull_case_engie_pt: List[str] = Field([], description="Engie bull case (PT).")
    bear_case_engie_pt: List[str] = Field([], description="Engie bear case (PT).")

class ValuationSection(BaseModel):
    primary_methodology_taesa_pt: Optional[str] = Field(None, description="Taesa valuation methodology (PT).")
    key_valuation_assumptions_taesa_pt: List[str] = Field([], description="Taesa valuation assumptions (PT).")
    target_price_taesa_pt: Optional[KeyMetric] = Field(None, description="Taesa target price (PT).")
    upside_downside_taesa_pt: Optional[KeyMetric] = Field(None, description="Taesa upside/downside (PT).")
    primary_methodology_engie_pt: Optional[str] = Field(None, description="Engie valuation methodology (PT).")
    key_valuation_assumptions_engie_pt: List[str] = Field([], description="Engie valuation assumptions (PT).")
    target_price_engie_pt: Optional[KeyMetric] = Field(None, description="Engie target price (PT).")
    upside_downside_engie_pt: Optional[KeyMetric] = Field(None, description="Engie upside/downside (PT).")
    valuation_summary_notes_pt: str = Field(..., description="Valuation summary notes (PT).")

class RiskAnalysisSection(BaseModel):
    sector_risks_pt: List[RiskItem] = Field([], description="Sector risks (PT).")
    taesa_specific_risks_pt: List[RiskItem] = Field([], description="Taesa specific risks (PT).")
    engie_specific_risks_pt: List[RiskItem] = Field([], description="Engie specific risks (PT).")

class ESGSection(BaseModel):
    environmental_pt: Optional[str] = Field(None, description="Environmental factors (PT).")
    social_pt: Optional[str] = Field(None, description="Social factors (PT).")
    governance_pt: Optional[str] = Field(None, description="Governance factors (PT).")
    esg_summary_notes_pt: Optional[str] = Field(None, description="ESG summary notes (PT).")

class CompanyAnalysisSection(BaseModel):
    company_overview_pt: str = Field(..., description="Company overview (PT).")
    financial_performance_analysis_pt: str = Field(..., description="Financial performance analysis (PT).")
    operational_performance_analysis_pt: str = Field(..., description="Operational performance analysis (PT).")
    key_projects_and_pipeline_pt: str = Field(..., description="Key projects and pipeline (PT).")
    management_strategy_and_outlook_pt: str = Field(..., description="Management strategy and outlook (PT).")
    swot_analysis_pt: Optional[SWOTAnalysis] = Field(None, description="SWOT analysis (PT).")
    financial_summary_data: CompanyFinancialSummaryOutput = Field(..., description="Structured financial summary data.")

class FinalBrazilianEnergyMemoOutput(BaseModel):
    memo_title_pt: str = Field("Análise Setorial: Energia Elétrica no Brasil - Foco em Taesa e Engie", description="Memo title (PT).")
    date_generated: str = Field(..., description="Generated date (YYYY-MM-DD).")
    report_period_covered_pt: str = Field(..., description="Report period covered (PT).")
    executive_summary_pt: str = Field(..., description="Executive summary (PT).")
    
    taesa_analysis_pt: CompanyAnalysisSection = Field(..., description="Taesa detailed analysis (PT).")
    engie_analysis_pt: CompanyAnalysisSection = Field(..., description="Engie detailed analysis (PT).")
    
    comparative_analysis_pt: ComparativeAnalysisOutput = Field(..., description="Comparative analysis.")
    
    investment_thesis_pt: InvestmentThesisSection = Field(..., description="Investment thesis (PT).")
    valuation_section_pt: ValuationSection = Field(..., description="Valuation section (PT).")
    risk_analysis_pt: RiskAnalysisSection = Field(..., description="Risk analysis (PT).")
    esg_considerations_pt: Optional[ESGSection] = Field(None, description="ESG considerations (PT).")
    
    final_recommendation_summary_pt: str = Field(..., description="Final recommendation summary (PT).")
    appendix_modeling_assumptions_pt: Optional[str] = Field(None, description="Appendix: Modeling assumptions (PT).")
    disclaimer_pt: Optional[str] = Field("Este relatório foi gerado por uma inteligência artificial e destina-se apenas a fins informativos. Não constitui aconselhamento de investimento.", description="Disclaimer (PT).")

print("Output schemas defined in output_schemas.py") 