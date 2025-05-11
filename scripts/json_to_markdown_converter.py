import json
import argparse
import os
from typing import Optional, List, Dict, Any
from scripts.output_schemas import (
    FinalBrazilianEnergyMemoOutput,
    CompanyAnalysisSection,
    SWOTAnalysis,
    KeyMetric,
    ComparativeAnalysisOutput,
    InvestmentThesisSection,
    ValuationSection,
    RiskAnalysisSection,
    RiskItem,
    ESGSection,
    CompanyFinancialSummaryOutput
)

# --- Markdown Formatting Helper Functions ---

def format_optional_str(value: Optional[Any], default: str = "N/A") -> str:
    if value is None:
        return default
    str_value = str(value) # Ensure value is a string for strip() and startswith()
    return str_value if str_value.strip() and str_value != "#Pendente#" and not str_value.startswith("Erro ao gerar") else default

def format_list_to_markdown(items: Optional[List[str]], prefix: str = "- ") -> str:
    if not items:
        return format_optional_str(None)
    return "\n".join([f"{prefix}{item}" for item in items if item])

def format_key_metrics_table(metrics: Optional[List[KeyMetric]]) -> str:
    if not metrics:
        return format_optional_str(None)
    
    headers = ["Métrica", "Valor", "Unidade", "Período", "Tipo", "Comentário"]
    table = f"| {' | '.join(headers)} |\n"
    table += f"| {' | '.join(['---'] * len(headers))} |\n"
    for m in metrics:
        row = [
            format_optional_str(m.name),
            format_optional_str(m.value_numeric if m.value_numeric is not None else m.value),
            format_optional_str(m.unit),
            format_optional_str(m.period),
            format_optional_str(m.metric_type),
            format_optional_str(m.source_comment)
        ]
        table += f"| {' | '.join(row)} |\n"
    return table

def format_financial_summary_data(summary: Optional[CompanyFinancialSummaryOutput]) -> str:
    if not summary:
        return "\n**Dados de Resumo Financeiro:** N/A\n"
    
    md = "\n**Dados Estruturados do Resumo Financeiro:**\n"
    md += f"- **Crescimento da Receita (YoY):** {format_optional_str(str(summary.revenue_growth_yoy))}\n"
    md += f"- **Margem EBITDA:** {format_optional_str(str(summary.ebitda_margin))}\n"
    md += f"- **Margem Líquida:** {format_optional_str(str(summary.net_income_margin))}\n"
    md += f"- **Dívida Líquida / EBITDA:** {format_optional_str(str(summary.net_debt_to_ebitda))}\n"
    md += f"- **Dividend Yield:** {format_optional_str(str(summary.dividend_yield))}\n"
    
    md += "\n**Métricas Financeiras Chave:**\n"
    md += format_key_metrics_table(summary.key_financial_metrics)
    
    md += "\n**Métricas Operacionais Chave:**\n"
    md += format_key_metrics_table(summary.key_operational_metrics)
    
    md += f"\n- **Sumário da Discussão da Administração:** {format_optional_str(summary.management_discussion_summary)}\n"
    md += f"- **Sumário de Projetos Chave:** {format_optional_str(summary.key_projects_summary)}\n"
    md += f"- **Sumário de Alavancagem e Dívida:** {format_optional_str(summary.debt_leverage_summary)}\n"
    
    md += "\n**Destaques do Investimento:**\n"
    md += format_list_to_markdown(summary.investment_highlights)
    
    md += "\n**Principais Preocupações (Empresa):**\n"
    md += format_list_to_markdown(summary.key_concerns_company)
    
    md += f"\n- **Iniciativas Estratégicas e Impacto:** {format_optional_str(summary.strategic_initiatives_and_impact)}\n"
    return md

def format_swot_analysis(swot: Optional[SWOTAnalysis]) -> str:
    if not swot:
        return "**Análise SWOT:** N/A\n"
    md = "**Análise SWOT:**\n"
    md += "- **Forças (Strengths):**\n"
    md += format_list_to_markdown(swot.strengths_pt, prefix="  - ")
    md += "\n- **Fraquezas (Weaknesses):**\n"
    md += format_list_to_markdown(swot.weaknesses_pt, prefix="  - ")
    md += "\n- **Oportunidades (Opportunities):**\n"
    md += format_list_to_markdown(swot.opportunities_pt, prefix="  - ")
    md += "\n- **Ameaças (Threats):**\n"
    md += format_list_to_markdown(swot.threats_pt, prefix="  - ")
    return md

def format_company_analysis_section(section: Optional[CompanyAnalysisSection], company_name: str) -> str:
    if not section:
        return f"## Análise Detalhada: {company_name}\n\nN/A\n"
    
    md = f"## Análise Detalhada: {company_name}\n\n"
    md += f"### Visão Geral da Companhia\n{format_optional_str(section.company_overview_pt)}\n\n"
    md += f"### Análise de Desempenho Financeiro\n{format_optional_str(section.financial_performance_analysis_pt)}\n\n"
    md += f"### Análise de Desempenho Operacional\n{format_optional_str(section.operational_performance_analysis_pt)}\n\n"
    md += f"### Principais Projetos e Pipeline de Crescimento\n{format_optional_str(section.key_projects_and_pipeline_pt)}\n\n"
    md += f"### Estratégia da Administração e Perspectivas\n{format_optional_str(section.management_strategy_and_outlook_pt)}\n\n"
    if section.swot_analysis_pt:
        md += format_swot_analysis(section.swot_analysis_pt) + "\n\n"
    if section.financial_summary_data:
        md += format_financial_summary_data(section.financial_summary_data) + "\n\n"
    return md

def format_comparative_analysis(analysis: Optional[ComparativeAnalysisOutput]) -> str:
    if not analysis:
        return "## Análise Comparativa Consolidada\n\nN/A\n"
    md = "## Análise Comparativa Consolidada\n\n"
    md += "### Comparação Financeira Direta\n"
    md += format_list_to_markdown(analysis.financial_comparison) + "\n\n"
    md += "### Comparação Operacional (Escala, Eficiência, Projetos)\n"
    md += format_list_to_markdown(analysis.operational_comparison) + "\n\n"
    md += "### Comparação de Valuation (Múltiplos, etc.)\n"
    md += format_list_to_markdown(analysis.valuation_comparison) + "\n\n"
    md += "### Comparação de Riscos Chave\n"
    md += format_list_to_markdown(analysis.risk_comparison) + "\n\n"
    md += f"### Preferência do Analista e Racional\n{format_optional_str(analysis.analyst_preference_rationale)}\n\n"
    return md

def format_investment_thesis(thesis: Optional[InvestmentThesisSection]) -> str:
    if not thesis:
        return "## Tese de Investimento Detalhada\n\nN/A\n"
    md = "## Tese de Investimento Detalhada\n\n"
    md += f"### Taesa (TAEE11) - Recomendação Geral: {format_optional_str(thesis.overall_recommendation_taesa_pt)}\n"
    md += f"**Racional da Recomendação:**\n{format_optional_str(thesis.recommendation_rationale_taesa_pt)}\n"
    md += "**Cenário Otimista (Bull Case):**\n"
    md += format_list_to_markdown(thesis.bull_case_taesa_pt)
    md += "\n**Cenário Pessimista (Bear Case):**\n"
    md += format_list_to_markdown(thesis.bear_case_taesa_pt)
    md += "\n\n"
    md += f"### Engie Brasil (EGIE3) - Recomendação Geral: {format_optional_str(thesis.overall_recommendation_engie_pt)}\n"
    md += f"**Racional da Recomendação:**\n{format_optional_str(thesis.recommendation_rationale_engie_pt)}\n"
    md += "**Cenário Otimista (Bull Case):**\n"
    md += format_list_to_markdown(thesis.bull_case_engie_pt)
    md += "\n**Cenário Pessimista (Bear Case):**\n"
    md += format_list_to_markdown(thesis.bear_case_engie_pt)
    return md

def format_valuation_section(valuation: Optional[ValuationSection]) -> str:
    if not valuation:
        return "## Detalhamento da Avaliação (Valuation)\n\nN/A\n"
    md = "## Detalhamento da Avaliação (Valuation)\n\n"
    md += f"### Metodologia Primária e Premissas Chave - Taesa\n"
    md += f"**Metodologia Principal:** {format_optional_str(valuation.primary_methodology_taesa_pt)}\n"
    md += "**Principais Premissas de Valuation:**\n"
    md += format_list_to_markdown(valuation.key_valuation_assumptions_taesa_pt)
    md += f"\n**Preço-Alvo:** {format_optional_str(valuation.target_price_taesa_pt)}\n"
    md += f"**Potencial de Upside/Downside:** {format_optional_str(valuation.upside_downside_taesa_pt)}\n\n"
    
    md += f"### Metodologia Primária e Premissas Chave - Engie\n"
    md += f"**Metodologia Principal:** {format_optional_str(valuation.primary_methodology_engie_pt)}\n"
    md += "**Principais Premissas de Valuation:**\n"
    md += format_list_to_markdown(valuation.key_valuation_assumptions_engie_pt)
    md += f"\n**Preço-Alvo:** {format_optional_str(valuation.target_price_engie_pt)}\n"
    md += f"**Potencial de Upside/Downside:** {format_optional_str(valuation.upside_downside_engie_pt)}\n\n"
    
    md += f"### Notas de Sumário da Avaliação\n{format_optional_str(valuation.valuation_summary_notes_pt)}\n"
    return md

def format_risk_item(item: RiskItem) -> str:
    md = f"- **Risco:** {format_optional_str(item.risk_description_pt)}\n"
    if item.mitigation_factors_pt:
        md += f"  - **Fatores de Mitigação:** {format_optional_str(item.mitigation_factors_pt)}\n"
    if item.potential_impact_pt:
        md += f"  - **Impacto Potencial:** {format_optional_str(item.potential_impact_pt)}\n"
    return md

def format_risk_analysis(analysis: Optional[RiskAnalysisSection]) -> str:
    if not analysis:
        return "## Análise de Riscos Detalhada\n\nN/A\n"
    md = "## Análise de Riscos Detalhada\n\n"
    md += "### Riscos Setoriais Críticos (Brasil - Energia)\n"
    if analysis.sector_risks_pt:
        for risk in analysis.sector_risks_pt:
            md += format_risk_item(risk)
    else:
        md += format_optional_str(None) + "\n"
    md += "\n### Riscos Específicos - Taesa\n"
    if analysis.taesa_specific_risks_pt:
        for risk in analysis.taesa_specific_risks_pt:
            md += format_risk_item(risk)
    else:
        md += format_optional_str(None) + "\n"
    md += "\n### Riscos Específicos - Engie\n"
    if analysis.engie_specific_risks_pt:
        for risk in analysis.engie_specific_risks_pt:
            md += format_risk_item(risk)
    else:
        md += format_optional_str(None) + "\n"
    return md

def format_esg_section(esg: Optional[ESGSection]) -> str:
    if not esg:
        return "## Considerações ESG (Ambiental, Social e Governança)\n\nN/A\n"
    md = "## Considerações ESG (Ambiental, Social e Governança)\n\n"
    md += f"### Fatores Ambientais\n{format_optional_str(esg.environmental_pt)}\n\n"
    md += f"### Fatores Sociais\n{format_optional_str(esg.social_pt)}\n\n"
    md += f"### Fatores de Governança\n{format_optional_str(esg.governance_pt)}\n\n"
    md += f"### Sumário das Notas ESG\n{format_optional_str(esg.esg_summary_notes_pt)}\n"
    return md

# --- Main Conversion Logic ---

def convert_json_to_markdown(json_data: Dict[str, Any]) -> str:
    memo = FinalBrazilianEnergyMemoOutput(**json_data)
    
    markdown_parts = []
    
    # Header
    markdown_parts.append(f"# {format_optional_str(memo.memo_title_pt, 'Relatório de Análise Setorial')}")
    markdown_parts.append(f"**Data de Geração:** {format_optional_str(memo.date_generated)}")
    markdown_parts.append(f"**Período Coberto pelo Relatório:** {format_optional_str(memo.report_period_covered_pt)}")
    markdown_parts.append("---_Rascunho Confidencial - Apenas Para Uso Interno_---")
    markdown_parts.append("\n")
    
    # Executive Summary
    markdown_parts.append("## Sumário Executivo (Opinião do Analista)\n")
    markdown_parts.append(format_optional_str(memo.executive_summary_pt) + "\n")
    
    # Final Recommendation Summary (early for emphasis)
    markdown_parts.append("## Sumário da Recomendação Final\n")
    markdown_parts.append(format_optional_str(memo.final_recommendation_summary_pt) + "\n")

    # Company Analysis Sections
    if memo.taesa_analysis_pt:
        markdown_parts.append(format_company_analysis_section(memo.taesa_analysis_pt, "Taesa (Transmissora Aliança de Energia Elétrica S.A. - TAEE11)"))
    if memo.engie_analysis_pt:
        markdown_parts.append(format_company_analysis_section(memo.engie_analysis_pt, "Engie Brasil Energia S.A. - EGIE3"))
        
    # Comparative Analysis
    if memo.comparative_analysis_pt:
        markdown_parts.append(format_comparative_analysis(memo.comparative_analysis_pt))
        
    # Investment Thesis
    if memo.investment_thesis_pt:
        markdown_parts.append(format_investment_thesis(memo.investment_thesis_pt))
        
    # Valuation
    if memo.valuation_section_pt:
        markdown_parts.append(format_valuation_section(memo.valuation_section_pt))
        
    # Risk Analysis
    if memo.risk_analysis_pt:
        markdown_parts.append(format_risk_analysis(memo.risk_analysis_pt))
        
    # ESG
    if memo.esg_considerations_pt:
        markdown_parts.append(format_esg_section(memo.esg_considerations_pt))
        
    # Appendix
    markdown_parts.append("## Apêndice: Premissas de Modelagem Adotadas\n")
    markdown_parts.append(format_optional_str(memo.appendix_modeling_assumptions_pt) + "\n")
    
    # Disclaimer
    markdown_parts.append("---_Disclaimer_---")
    markdown_parts.append(format_optional_str(memo.disclaimer_pt))
    
    return "\n".join(markdown_parts)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converte o JSON do memorando de análise de ações para Markdown.")
    parser.add_argument("--input_json", type=str, required=True, help="Caminho para o arquivo JSON de entrada.")
    parser.add_argument("--output_markdown", type=str, required=True, help="Caminho para o arquivo Markdown de saída.")
    
    args = parser.parse_args()
    
    print(f"Lendo JSON de: {args.input_json}")
    try:
        with open(args.input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo JSON de entrada não encontrado em {args.input_json}")
        exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar o arquivo JSON em {args.input_json}")
        exit(1)
        
    print("Convertendo JSON para Markdown...")
    markdown_content = convert_json_to_markdown(data)
    
    output_dir = os.path.dirname(args.output_markdown)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    print(f"Salvando Markdown em: {args.output_markdown}")
    with open(args.output_markdown, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
        
    print("Conversão para Markdown concluída com sucesso!") 