import os
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
import json
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import argparse

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
    FinalBrazilianEnergyMemoOutput,
    CompanyAnalysisSection,
    InvestmentThesisSection,
    ValuationSection,
    RiskAnalysisSection,
    ESGSection,
    SWOTAnalysis,
    RiskItem
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
    template_str = """Contexto:
Nome da Empresa: {company_name}
Período do Relatório: {report_period}
Premissas de Modelagem Financeira (para o Setor de Energia Brasileiro - usar como guia geral):
{modeling_assumptions}

Dados Financeiros Chave Extraídos (JSON):
{financials_data_json_str}

Unidade Monetária dos Dados Financeiros: {currency_unit_str}

Contexto Adicional do Relatório (pode incluir dados operacionais, discussão da administração, etc.):
{report_data_context_additional}

Tarefa:
Realize uma análise detalhada dos dados fornecidos para a empresa e o período do relatório especificados.
Gere um resumo financeiro e operacional abrangente, juntamente com uma perspectiva analítica.
Concentre-se em popular todos os campos do schema Pydantic `CompanyFinancialSummaryOutput` fornecido.

Instruções Específicas para Campos (Output Requirements):
- `company_name`: {company_name}
- `report_period`: {report_period}
- `key_financial_metrics`: Use os dados do JSON em `{financials_data_json_str}`. Este objeto já possui as métricas financeiras extraídas (ex: `net_revenue`, `ebitda`, etc.).
  Sua tarefa é transformar cada par chave-valor relevante deste objeto `{financials_data_json_str}` em um item da lista `key_financial_metrics`.
  Para cada métrica no objeto `{financials_data_json_str}`:
    - `name`: Use um nome descritivo em português para a métrica (ex: `net_revenue` -> "Receita Líquida", `ebitda` -> "EBITDA", `net_debt` -> "Dívida Líquida", `adjusted_ebitda` -> "EBITDA Ajustado", `gross_debt` -> "Dívida Bruta", `cash_and_equivalents` -> "Caixa e Equivalentes", `operational_expenses` -> "Despesas Operacionais", `dividends_paid_or_proposed` -> "Dividendos Pagos/Propostos").
    - `value_numeric`: Use o valor numérico diretamente do objeto em `{financials_data_json_str}`.
    - `value`: Converta o `value_numeric` para string, se aplicável, ou use o valor original se já for uma string formatada.
    - `unit`: Use o valor de `{currency_unit_str}`.
    - `period`: Use o valor de `{report_period}`.
    - `metric_type`: Defina como "Financeira".
  Por exemplo, se `{financials_data_json_str}` contiver `"net_revenue": 3013.0` e `{currency_unit_str}` for "R$ milhões", você deve criar um KeyMetric com `name="Receita Líquida"`, `value_numeric=3013.0`, `unit="R$ milhões"`, `period="{report_period}"`, `metric_type="Financeira"`.
  Priorize a inclusão das seguintes métricas se estiverem presentes e preenchidas no objeto `{financials_data_json_str}`: Receita Líquida (net_revenue), EBITDA (ebitda), EBITDA Ajustado (adjusted_ebitda), Lucro Líquido (net_income), Dívida Líquida (net_debt), CAPEX (capex).
- `revenue_growth_yoy`, `ebitda_margin`, `net_income_margin`, `net_debt_to_ebitda`, `dividend_yield`: Calcule ou extraia estas métricas. Se não disponíveis diretamente nos dados fornecidos (`{financials_data_json_str}` ou `{report_data_context_additional}`) ou se não puderem ser calculadas a partir dos dados em `{financials_data_json_str}`, deixe como `None`. Preencha os sub-campos de `KeyMetric` para cada, similarmente às `key_financial_metrics`.
    - `metric_type`: "Financeira (Rácio)" ou "Financeira (Indicador)"
- `key_operational_metrics`: Extraia métricas operacionais chave (geração/transmissão de energia, capacidade, eficiência, etc.) do `{report_data_context_additional}`. Preencha os sub-campos de `KeyMetric`.
    - `metric_type`: "Operacional"
- `management_discussion_summary`: Resuma a discussão da administração e as perspectivas futuras, com foco em sua narrativa, usando o `{report_data_context_additional}`.
- `key_projects_summary`: Resuma os principais projetos, CAPEX associado e investimentos, usando o `{report_data_context_additional}`.
- `debt_leverage_summary`: Resuma o perfil da dívida, alavancagem e atividades de financiamento, usando o `{report_data_context_additional}` e `{financials_data_json_str}`.
- `investment_highlights`: Liste os principais aspectos positivos e destaques de investimento para a empresa, com base em todas as informações.
- `key_concerns_company`: Liste as principais preocupações e riscos específicos para o desempenho ou perspectivas da empresa, com base em todas as informações.
- `strategic_initiatives_and_impact`: Resuma as principais iniciativas estratégicas e seu impacto potencial, usando o `{report_data_context_additional}`.

Formato de Saída:
- A saída DEVE seguir estritamente o schema Pydantic `CompanyFinancialSummaryOutput`.
- Todos os campos de texto devem ser preenchidos em Português do Brasil.
- Seja conciso, mas informativo, adequado para um memorando de pesquisa de ações.
"""
    return PromptTemplate(template=template_str)

def get_comparative_analysis_prompt_template() -> PromptTemplate:
    template_str = """Contexto:
Você possui resumos financeiros e operacionais para duas empresas brasileiras de energia:
Empresa A ({company_a_name}): 
{company_a_summary_json}

Empresa B ({company_b_name}): 
{company_b_summary_json}

Tarefa:
Realize uma análise comparativa detalhada dessas duas empresas com base em seus resumos.
Concentre-se em popular todos os campos do schema Pydantic `ComparativeAnalysisOutput` fornecido.

Instruções Específicas para Campos (Output Requirements):
- `financial_comparison`: Compare diretamente as principais métricas financeiras (crescimento da receita, margens, endividamento, etc.). Forneça exemplos como "Engie apresenta maior crescimento de receita (X%) vs Taesa (Y%)".
- `operational_comparison`: Compare aspectos operacionais, escala, eficiência, pipelines de projetos e diferenciais estratégicos.
- `valuation_comparison`: (Placeholder por enquanto, mas mencione se alguma métrica de avaliação relativa pode ser inferida ou se dados adicionais seriam necessários).
- `risk_comparison`: Compare os principais riscos enfrentados por cada empresa, com base nas seções `key_concerns_company` dos resumos.
- `analyst_preference_rationale`: Indique uma preferência (ou neutralidade) entre as duas empresas, com uma justificativa clara baseada na análise comparativa.

Formato de Saída:
- A análise deve ser equilibrada, destacando aspectos de ambas as empresas.
- A saída DEVE seguir estritamente o schema Pydantic `ComparativeAnalysisOutput`.
- Todos os campos de texto devem ser preenchidos em Português do Brasil.
"""
    return PromptTemplate(template=template_str)

def get_final_memo_prompt_template() -> PromptTemplate:
    # This prompt is now much more complex, guiding the LLM to fill the new FinalBrazilianEnergyMemoOutput
    template_str = """Contexto Principal:
Data Atual: {current_date}
Período do Relatório Coberto: {report_period}
Premissas Gerais de Modelagem (Setor de Energia Brasileiro): 
{modeling_assumptions}

Dados Base Recebidos:
1.  Resumo Detalhado - {company_a_name} (Taesa): 
{company_a_summary_json}
2.  Resumo Detalhado - {company_b_name} (Engie): 
{company_b_summary_json}
3.  Análise Comparativa Preliminar: 
{comparative_analysis_json}

Tarefa Principal:
Sintetize TODAS as informações fornecidas em um memorando final de pesquisa de ações (Equity Research Memo) de nível SÊNIOR para o Setor de Energia Brasileiro, com foco em {company_a_name} e {company_b_name}.
O memorando DEVE ser totalmente escrito em Português do Brasil e seguir estritamente o schema Pydantic `FinalBrazilianEnergyMemoOutput`.

Instruções Detalhadas por Seção do Schema `FinalBrazilianEnergyMemoOutput`:

- `memo_title_pt`: Crie um título apropriado em português (ex: "Análise Setorial: Energia Elétrica no Brasil - Aprofundamento em Taesa e Engie").
- `date_generated`: Use a data atual: {current_date}.
- `report_period_covered_pt`: Use o período fornecido: {report_period}.
- `executive_summary_pt`: Escreva um resumo executivo conciso (2-3 parágrafos) dos principais achados, teses de investimento e recomendações.

- `taesa_analysis_pt` (tipo: `CompanyAnalysisSection`):
    - `company_overview_pt`: Desenvolva uma visão geral detalhada da Taesa (negócios, mercado, estratégia).
    - `financial_performance_analysis_pt`: Elabore uma análise aprofundada do desempenho financeiro da Taesa, tendências e drivers, usando dados de `company_a_summary_json`.
    - `operational_performance_analysis_pt`: Elabore uma análise aprofundada do desempenho operacional, eficiência e ativos da Taesa.
    - `key_projects_and_pipeline_pt`: Detalhe os principais projetos, planos de CAPEX e pipeline de crescimento da Taesa.
    - `management_strategy_and_outlook_pt`: Analise a estratégia da administração da Taesa, histórico de execução e perspectivas declaradas.
    - `swot_analysis_pt` (tipo: `SWOTAnalysis`): Realize uma análise SWOT para a Taesa (Forças, Fraquezas, Oportunidades, Ameaças).
    - `financial_summary_data`: Copie os dados relevantes do `company_a_summary_json` fornecido.

- `engie_analysis_pt` (tipo: `CompanyAnalysisSection`):
    - Preencha de forma análoga à `taesa_analysis_pt`, usando dados de `company_b_summary_json`.

- `comparative_analysis_pt` (tipo: `ComparativeAnalysisOutput`):
    - Utilize e expanda a `comparative_analysis_json` fornecida. Certifique-se de que todos os campos deste sub-schema (`financial_comparison`, `operational_comparison`, etc.) sejam preenchidos de forma completa e detalhada em português.

- `investment_thesis_pt` (tipo: `InvestmentThesisSection`):
    - `overall_recommendation_taesa_pt` / `engie_pt`: (Comprar, Manter, Vender).
    - `recommendation_rationale_taesa_pt` / `engie_pt`: Justificativa detalhada.
    - `bull_case_taesa_pt` / `engie_pt`: Cenários otimistas (lista de pontos).
    - `bear_case_taesa_pt` / `engie_pt`: Cenários pessimistas (lista de pontos).

- `valuation_section_pt` (tipo: `ValuationSection`):
    - Para ambas as empresas (Taesa e Engie):
        - `primary_methodology_..._pt`: (ex: DCF, Múltiplos). Se não for possível calcular, descreva a abordagem que seria usada.
        - `key_valuation_assumptions_..._pt`: Principais premissas (ex: taxa de desconto, crescimento na perpetuidade).
        - `target_price_..._pt` (tipo `KeyMetric`): Preço-alvo estimado. Se não for possível calcular, deixe como `None`.
        - `upside_downside_..._pt` (tipo `KeyMetric`): Potencial de valorização/desvalorização.
    - `valuation_summary_notes_pt`: Notas resumidas sobre a avaliação.

- `risk_analysis_pt` (tipo: `RiskAnalysisSection`):
    - `sector_risks_pt`: Riscos do setor de energia brasileiro (lista de `RiskItem`).
    - `taesa_specific_risks_pt`: Riscos específicos da Taesa (lista de `RiskItem`).
    - `engie_specific_risks_pt`: Riscos específicos da Engie (lista de `RiskItem`).
    - Para cada `RiskItem`: `risk_description_pt`, `mitigation_factors_pt`, `potential_impact_pt`.

- `esg_considerations_pt` (tipo: `ESGSection`):
    - `environmental_pt`, `social_pt`, `governance_pt`: Análise dos fatores ESG.
    - `esg_summary_notes_pt`: Resumo das considerações ESG.

- `final_recommendation_summary_pt`: Um breve parágrafo final resumindo as recomendações de investimento para ambas as empresas.
- `appendix_modeling_assumptions_pt`: Inclua as premissas de modelagem fornecidas em `modeling_assumptions`.
- `disclaimer_pt`: Mantenha o disclaimer padrão.

Requisitos Gerais de Qualidade:
- O memorando deve ser bem estruturado, profissional, perspicaz e adequado para um analista de ações sênior.
- Profundidade analítica é esperada em todas as seções.
- Todas as narrativas e textos devem ser em Português do Brasil fluente e profissional.
- Use os dados dos resumos e da análise comparativa como base, mas ELABORE e SINTETIZE para criar as seções detalhadas do memorando final. Não apenas copie e cole.
- O resultado DEVE CONFORMAR ESTRITAMENTE ao schema `FinalBrazilianEnergyMemoOutput` e seus sub-schemas.
"""
    return PromptTemplate(template=template_str)

# --- BEGIN NEW PROMPT TEMPLATES FOR ITERATIVE GENERATION ---
def get_executive_summary_prompt_template() -> PromptTemplate:
    template_str = """Contexto:
Data Atual: {current_date}
Período do Relatório Coberto: {report_period}
Resumo Taesa: {taesa_summary_json}
Resumo Engie: {engie_summary_json}
Análise Comparativa: {comparative_analysis_json}
Premissas de Modelagem: {modeling_assumptions}

Tarefa: Com base em TODAS as informações fornecidas, escreva um Resumo Executivo conciso (2-3 parágrafos) em Português do Brasil para um memorando de pesquisa de ações sobre Taesa e Engie. Destaque os principais achados, teses de investimento e recomendações gerais.
Retorne APENAS o texto do resumo executivo como uma string.
"""
    return PromptTemplate(template=template_str)

def get_company_analysis_section_prompt_template() -> PromptTemplate:
    template_str = """Contexto:
Nome da Empresa: {company_name}
Período do Relatório: {report_period}
Resumo Detalhado da Empresa (JSON): {company_summary_json}
Premissas de Modelagem (Geral): {modeling_assumptions}

Tarefa: Gere a seção de análise detalhada para a {company_name} para o período {report_period}, em Português do Brasil.
A saída DEVE seguir estritamente o schema Pydantic `CompanyAnalysisSection`.

Instruções para Campos de `CompanyAnalysisSection`:
- `company_overview_pt`: Desenvolva uma visão geral detalhada da empresa (negócios, mercado, estratégia).
- `financial_performance_analysis_pt`: Elabore uma análise aprofundada do desempenho financeiro, tendências e drivers, usando dados de `company_summary_json`.
- `operational_performance_analysis_pt`: Elabore uma análise aprofundada do desempenho operacional, eficiência e ativos.
- `key_projects_and_pipeline_pt`: Detalhe os principais projetos, planos de CAPEX e pipeline de crescimento.
- `management_strategy_and_outlook_pt`: Analise a estratégia da administração, histórico de execução e perspectivas declaradas.
- `swot_analysis_pt` (tipo: `SWOTAnalysis`): Realize uma análise SWOT (Forças, Fraquezas, Oportunidades, Ameaças).
    - `strengths_pt`, `weaknesses_pt`, `opportunities_pt`, `threats_pt`: Listas de strings.
- `financial_summary_data`: Popule este campo com o objeto JSON fornecido em `company_summary_json`.

Qualidade: Profundidade analítica e texto profissional são esperados.
"""
    return PromptTemplate(template=template_str)

def get_investment_thesis_section_prompt_template() -> PromptTemplate:
    template_str = """Contexto:
Resumo Taesa: {taesa_summary_json}
Resumo Engie: {engie_summary_json}
Análise Comparativa: {comparative_analysis_json}
Premissas de Modelagem: {modeling_assumptions}
Análise Detalhada Taesa (se disponível): {taesa_analysis_section_json}
Análise Detalhada Engie (se disponível): {engie_analysis_section_json}

Tarefa: Desenvolva a Tese de Investimento para Taesa e Engie, em Português do Brasil.
A saída DEVE seguir estritamente o schema Pydantic `InvestmentThesisSection`.

Instruções para Campos de `InvestmentThesisSection`:
- Para Taesa e Engie separadamente:
    - `overall_recommendation_..._pt`: (Comprar, Manter, Vender).
    - `recommendation_rationale_..._pt`: Justificativa detalhada para a recomendação.
    - `bull_case_..._pt`: Principais pontos para um cenário otimista (lista de strings).
    - `bear_case_..._pt`: Principais pontos para um cenário pessimista (lista de strings).
Considere todos os dados de entrada para formular a tese.
"""
    return PromptTemplate(template=template_str)

def get_valuation_section_prompt_template() -> PromptTemplate:
    template_str = """Contexto:
Resumo Taesa: {taesa_summary_json}
Resumo Engie: {engie_summary_json}
Premissas de Modelagem (Valuation): {modeling_assumptions}
Análise Detalhada Taesa (se disponível): {taesa_analysis_section_json}
Análise Detalhada Engie (se disponível): {engie_analysis_section_json}

Tarefa: Desenvolva a Seção de Valuation para Taesa e Engie, em Português do Brasil.
A saída DEVE seguir estritamente o schema Pydantic `ValuationSection`.

Instruções para Campos de `ValuationSection`:
- Para Taesa e Engie separadamente:
    - `primary_methodology_..._pt`: Metodologia principal (ex: DCF, Múltiplos). Se não for possível calcular, descreva a abordagem que seria usada.
    - `key_valuation_assumptions_..._pt`: Principais premissas de valuation (ex: taxa de desconto WACC, crescimento na perpetuidade g, múltiplos EV/EBITDA de pares).
    - `target_price_..._pt` (tipo `KeyMetric`): Preço-alvo estimado. Se não for possível calcular, deixe como `None`, mas explique o porquê na `valuation_summary_notes_pt`.
    - `upside_downside_..._pt` (tipo `KeyMetric`): Potencial de valorização/desvalorização baseado no preço-alvo. Se não aplicável, deixe `None`.
- `valuation_summary_notes_pt`: Notas resumidas sobre a avaliação, incluindo quaisquer limitações ou desafios na aplicação das metodologias com os dados disponíveis.
"""
    return PromptTemplate(template=template_str)

def get_risk_analysis_section_prompt_template() -> PromptTemplate:
    template_str = """Contexto:
Resumo Taesa (contém `key_concerns_company`): {taesa_summary_json}
Resumo Engie (contém `key_concerns_company`): {engie_summary_json}
Análise Comparativa (contém `risk_comparison`): {comparative_analysis_json}
Premissas de Modelagem (Riscos Setoriais): {modeling_assumptions}
Análise Detalhada Taesa (se disponível): {taesa_analysis_section_json}
Análise Detalhada Engie (se disponível): {engie_analysis_section_json}

Tarefa: Desenvolva a Seção de Análise de Risco, em Português do Brasil.
A saída DEVE seguir estritamente o schema Pydantic `RiskAnalysisSection`.

Instruções para Campos de `RiskAnalysisSection`:
- `sector_risks_pt` (lista de `RiskItem`): Identifique 2-3 riscos chave aplicáveis ao setor de energia brasileiro, com base nas premissas e contexto geral.
- `taesa_specific_risks_pt` (lista de `RiskItem`): Detalhe 2-3 riscos específicos para a Taesa, baseando-se em `taesa_summary_json.key_concerns_company` e outras informações.
- `engie_specific_risks_pt` (lista de `RiskItem`): Detalhe 2-3 riscos específicos para a Engie, baseando-se em `engie_summary_json.key_concerns_company` e outras informações.
- Para cada `RiskItem` (dentro das listas acima):
    - `risk_description_pt`: Descrição clara do risco.
    - `mitigation_factors_pt`: Fatores de mitigação ou abordagem da empresa (se conhecido).
    - `potential_impact_pt`: Impacto potencial estimado (ex: Alto, Médio, Baixo).
"""
    return PromptTemplate(template=template_str)

def get_esg_section_prompt_template() -> PromptTemplate:
    template_str = """Contexto:
Resumo Taesa: {taesa_summary_json}
Resumo Engie: {engie_summary_json}
Premissas de Modelagem (ESG): {modeling_assumptions} 
Análise Detalhada Taesa (se disponível): {taesa_analysis_section_json}
Análise Detalhada Engie (se disponível): {engie_analysis_section_json}

Tarefa: Desenvolva a Seção de Considerações ESG para Taesa e Engie, em Português do Brasil.
A saída DEVE seguir estritamente o schema Pydantic `ESGSection`.

Instruções para Campos de `ESGSection`:
- `environmental_pt`: Analise fatores ambientais relevantes para as empresas/setor.
- `social_pt`: Analise fatores sociais relevantes.
- `governance_pt`: Analise fatores de governança corporativa relevantes.
- `esg_summary_notes_pt`: Forneça um resumo conciso das considerações ESG e como elas podem impactar as empresas.
Se informações específicas não estiverem disponíveis nos dados, indique isso e discuta com base em conhecimento geral do setor no Brasil.
"""
    return PromptTemplate(template=template_str)
# --- END NEW PROMPT TEMPLATES FOR ITERATIVE GENERATION ---

# --- Workflow Definition (Class-based) ---

class EquityResearchWorkflow(Workflow):
    def __init__(self, 
                 modeling_assumptions_content: str,
                 report_period_str: str,
                 taesa_name_str: str,
                 engie_name_str: str,
                 taesa_json_file_path: str,
                 engie_json_file_path: str,
                 output_dir: str,
                 llm: Optional[LLM] = None, 
                 **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or Settings.llm
        self.modeling_assumptions_content = modeling_assumptions_content
        self.report_period_str = report_period_str
        self.taesa_name_str = taesa_name_str
        self.engie_name_str = engie_name_str
        self.taesa_json_file_path = taesa_json_file_path
        self.engie_json_file_path = engie_json_file_path
        self.output_dir = output_dir

    @step
    async def generate_taesa_summary_step(
        self, 
        ctx: Context,
        ev: StartEvent
    ) -> CompanySummaryEvent:
        print(f"\n----- Generating Company Financial Summary for {self.taesa_name_str} -----")
        taesa_query_engine = ev.taesa_query_engine
        
        # --- Load Full Extracted JSON Data ---
        print(f"Loading full extracted JSON for {self.taesa_name_str} from: {self.taesa_json_file_path}")
        raw_extracted_report_data_dict = {}
        financials_data = {}
        currency_unit = "N/A"
        full_report_context_for_rag_fallback = "{}"

        try:
            with open(self.taesa_json_file_path, 'r', encoding='utf-8') as f:
                llama_document_dict = json.load(f)
            # The 'text' field of the LlamaIndex Document holds the JSON string of BrazilianCompanyReportData
            brazilian_company_report_data_str = llama_document_dict.get("text", "{}")
            raw_extracted_report_data_dict = json.loads(brazilian_company_report_data_str)
            
            financials_data = raw_extracted_report_data_dict.get("financials", {})
            currency_unit = raw_extracted_report_data_dict.get("currency_unit", "N/A")
            full_report_context_for_rag_fallback = brazilian_company_report_data_str # Use the full JSON string as fallback
            print(f"Successfully loaded and parsed full JSON for {self.taesa_name_str}.")
            print(f"Financials for {self.taesa_name_str}: {json.dumps(financials_data, indent=2)}")
            print(f"Currency unit for {self.taesa_name_str}: {currency_unit}")
        except FileNotFoundError:
            print(f"ERROR: Taesa JSON file not found at {self.taesa_json_file_path}. Financials will be empty.")
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not decode JSON from Taesa file {self.taesa_json_file_path}: {e}. Financials will be empty.")
        except Exception as e:
            print(f"ERROR: Unexpected error loading Taesa JSON file {self.taesa_json_file_path}: {e}. Financials will be empty.")
        
        financials_data_json_str = json.dumps(financials_data)

        # --- Query RAG for additional qualitative context ---
        # This query now focuses on qualitative aspects, assuming financials are directly loaded.
        query_str = f"Resuma a discussão da administração, projetos chave e perspectivas para {self.taesa_name_str} para o período {self.report_period_str}, com base no relatório financeiro."
        response = await asyncio.to_thread(taesa_query_engine.query, query_str)
        
        report_data_context_additional = full_report_context_for_rag_fallback # Default to full JSON if RAG fails
        if response.source_nodes:
            report_data_context_additional = response.source_nodes[0].node.get_content()
            print(f"Retrieved RAG context for {self.taesa_name_str} (length: {len(report_data_context_additional)} chars).")
        else:
            print(f"No source nodes from RAG for {self.taesa_name_str}. Using full extracted JSON as additional context.")
        
        output: CompanyFinancialSummaryOutput = await self.llm.astructured_predict(
            output_cls=CompanyFinancialSummaryOutput,
            prompt=get_company_summary_prompt_template(),
            company_name=self.taesa_name_str,
            report_period=self.report_period_str,
            modeling_assumptions=self.modeling_assumptions_content,
            financials_data_json_str=financials_data_json_str,
            currency_unit_str=currency_unit,
            report_data_context_additional=report_data_context_additional
        )
        print(f"Raw Pydantic Output for {self.taesa_name_str} (CompanyFinancialSummaryOutput):\n{output.model_dump_json(indent=2)}")
        
        # Store in context for the comparative step
        await ctx.set(self.taesa_name_str, output) 
        return CompanySummaryEvent(summary=output, company_name=self.taesa_name_str)

    @step
    async def generate_engie_summary_step(
        self, 
        ctx: Context,
        ev: StartEvent
    ) -> CompanySummaryEvent:
        print(f"\n----- Generating Company Financial Summary for {self.engie_name_str} -----")
        engie_query_engine = ev.engie_query_engine
        
        # --- Load Full Extracted JSON Data ---
        print(f"Loading full extracted JSON for {self.engie_name_str} from: {self.engie_json_file_path}")
        raw_extracted_report_data_dict = {}
        financials_data = {}
        currency_unit = "N/A"
        full_report_context_for_rag_fallback = "{}"

        try:
            with open(self.engie_json_file_path, 'r', encoding='utf-8') as f:
                llama_document_dict = json.load(f)
            brazilian_company_report_data_str = llama_document_dict.get("text", "{}")
            raw_extracted_report_data_dict = json.loads(brazilian_company_report_data_str)

            financials_data = raw_extracted_report_data_dict.get("financials", {})
            currency_unit = raw_extracted_report_data_dict.get("currency_unit", "N/A")
            full_report_context_for_rag_fallback = brazilian_company_report_data_str
            print(f"Successfully loaded and parsed full JSON for {self.engie_name_str}.")
            print(f"Financials for {self.engie_name_str}: {json.dumps(financials_data, indent=2)}")
            print(f"Currency unit for {self.engie_name_str}: {currency_unit}")
        except FileNotFoundError:
            print(f"ERROR: Engie JSON file not found at {self.engie_json_file_path}. Financials will be empty.")
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not decode JSON from Engie file {self.engie_json_file_path}: {e}. Financials will be empty.")
        except Exception as e:
            print(f"ERROR: Unexpected error loading Engie JSON file {self.engie_json_file_path}: {e}. Financials will be empty.")

        financials_data_json_str = json.dumps(financials_data)

        # --- Query RAG for additional qualitative context ---
        query_str = f"Resuma a discussão da administração, projetos chave e perspectivas para {self.engie_name_str} para o período {self.report_period_str}, com base no relatório financeiro."
        response = await asyncio.to_thread(engie_query_engine.query, query_str)
        
        report_data_context_additional = full_report_context_for_rag_fallback
        if response.source_nodes:
            report_data_context_additional = response.source_nodes[0].node.get_content()
            print(f"Retrieved RAG context for {self.engie_name_str} (length: {len(report_data_context_additional)} chars).")
        else:
            print(f"No source nodes from RAG for {self.engie_name_str}. Using full extracted JSON as additional context.")

        output: CompanyFinancialSummaryOutput = await self.llm.astructured_predict(
            output_cls=CompanyFinancialSummaryOutput,
            prompt=get_company_summary_prompt_template(),
            company_name=self.engie_name_str,
            report_period=self.report_period_str,
            modeling_assumptions=self.modeling_assumptions_content,
            financials_data_json_str=financials_data_json_str,
            currency_unit_str=currency_unit,
            report_data_context_additional=report_data_context_additional
        )
        print(f"Raw Pydantic Output for {self.engie_name_str} (CompanyFinancialSummaryOutput):\n{output.model_dump_json(indent=2)}")
        
        # Store in context for the comparative step
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
            print("Waiting for both company detailed summaries to be available...")
            return None

        print(f"\n----- Generating Detailed Comparative Analysis for {self.taesa_name_str} and {self.engie_name_str} -----")
        comparative_output = await self.llm.astructured_predict(
            output_cls=ComparativeAnalysisOutput,
            prompt=get_comparative_analysis_prompt_template(),
            company_a_name=self.taesa_name_str,
            company_a_summary_json=taesa_summary.model_dump_json(),
            company_b_name=self.engie_name_str,
            company_b_summary_json=engie_summary.model_dump_json()
        )
        print(f"Raw Pydantic Output for Comparative Analysis (ComparativeAnalysisOutput):\n{comparative_output.model_dump_json(indent=2)}")
        await ctx.set("comparative_analysis_data", comparative_output)
        return ComparativeAnalysisReadyEvent(analysis=comparative_output)

    @step
    async def generate_final_memo_step(
        self, 
        ctx: Context,
        ev: ComparativeAnalysisReadyEvent
    ) -> StopEvent:
        print("\n----- Generating Final Senior Equity Research Memo (Iteratively) -----")

        taesa_summary: Optional[CompanyFinancialSummaryOutput] = await ctx.get(self.taesa_name_str, default=None)
        engie_summary: Optional[CompanyFinancialSummaryOutput] = await ctx.get(self.engie_name_str, default=None)
        comparative_analysis_data: ComparativeAnalysisOutput = ev.analysis
        current_date_str = datetime.now().strftime("%Y-%m-%d")

        # Variables to hold generated sections
        generated_executive_summary_pt: str = "#Pendente#"
        generated_taesa_analysis_pt: Optional[CompanyAnalysisSection] = None
        generated_engie_analysis_pt: Optional[CompanyAnalysisSection] = None
        generated_investment_thesis_pt: Optional[InvestmentThesisSection] = None
        generated_valuation_section_pt: Optional[ValuationSection] = None
        generated_risk_analysis_pt: Optional[RiskAnalysisSection] = None
        generated_esg_section_pt: Optional[ESGSection] = None
        generated_final_rec_summary_pt: str = "#Pendente#"

        if not all([taesa_summary, engie_summary, comparative_analysis_data]):
            error_msg = "ERROR: Missing data for final memo generation. Required: Taesa Summary, Engie Summary, Comparative Analysis."
            print(error_msg)
            # Construct a minimal FinalBrazilianEnergyMemoOutput with error information
            error_final_memo = FinalBrazilianEnergyMemoOutput(
                memo_title_pt="Erro na Geração do Memorando",
                date_generated=current_date_str,
                report_period_covered_pt=self.report_period_str,
                executive_summary_pt=error_msg,
                taesa_analysis_pt=CompanyAnalysisSection(company_overview_pt=error_msg, financial_performance_analysis_pt="", operational_performance_analysis_pt="", key_projects_and_pipeline_pt="", management_strategy_and_outlook_pt="", financial_summary_data=CompanyFinancialSummaryOutput(company_name=self.taesa_name_str, report_period=self.report_period_str)),
                engie_analysis_pt=CompanyAnalysisSection(company_overview_pt=error_msg, financial_performance_analysis_pt="", operational_performance_analysis_pt="", key_projects_and_pipeline_pt="", management_strategy_and_outlook_pt="", financial_summary_data=CompanyFinancialSummaryOutput(company_name=self.engie_name_str, report_period=self.report_period_str)),
                comparative_analysis_pt=comparative_analysis_data if comparative_analysis_data else ComparativeAnalysisOutput(),
                investment_thesis_pt=InvestmentThesisSection(overall_recommendation_taesa_pt=error_msg, recommendation_rationale_taesa_pt="", bull_case_taesa_pt=[], bear_case_taesa_pt=[], overall_recommendation_engie_pt=error_msg, recommendation_rationale_engie_pt="", bull_case_engie_pt=[], bear_case_engie_pt=[]),
                valuation_section_pt=ValuationSection(valuation_summary_notes_pt=error_msg),
                risk_analysis_pt=RiskAnalysisSection(sector_risks_pt=[RiskItem(risk_description_pt=error_msg)]),
                esg_considerations_pt=ESGSection(esg_summary_notes_pt=error_msg),
                final_recommendation_summary_pt="Erro na geração.",
                appendix_modeling_assumptions_pt=self.modeling_assumptions_content,
                disclaimer_pt="Relatório não pôde ser gerado completamente devido a dados ausentes."
            )
            # Save and return this error object
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = os.path.join(self.output_dir, f"final_equity_memo_pt_ERROR_{timestamp}.json")
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(error_final_memo.model_dump(), f, indent=2, ensure_ascii=False)
            print(f"\nError equity research memo (JSON) saved to: {output_filename}")
            return StopEvent(result=error_final_memo)

        # 1. Generate Executive Summary (string)
        print("--- Generating Executive Summary ---")
        try:
            generated_executive_summary_pt = await self.llm.apredict(
                prompt=get_executive_summary_prompt_template(),
                current_date=current_date_str,
                report_period=self.report_period_str,
                taesa_summary_json=taesa_summary.model_dump_json(),
                engie_summary_json=engie_summary.model_dump_json(),
                comparative_analysis_json=comparative_analysis_data.model_dump_json(),
                modeling_assumptions=self.modeling_assumptions_content
            )
            print(f"Generated Executive Summary: {generated_executive_summary_pt[:200]}...")
        except Exception as e:
            print(f"Error generating executive summary: {e}")
            generated_executive_summary_pt = f"Erro ao gerar resumo executivo: {e}"

        # 2. Generate Taesa Analysis Section
        print(f"--- Generating Company Analysis Section for {self.taesa_name_str} ---")
        try:
            generated_taesa_analysis_pt = await self.llm.astructured_predict(
                output_cls=CompanyAnalysisSection,
                prompt=get_company_analysis_section_prompt_template(),
                company_name=self.taesa_name_str,
                report_period=self.report_period_str,
                company_summary_json=taesa_summary.model_dump_json(),
                modeling_assumptions=self.modeling_assumptions_content
            )
            print(f"Generated Taesa Analysis Section. Overview: {generated_taesa_analysis_pt.company_overview_pt[:100]}...")
        except Exception as e:
            print(f"Error generating Taesa analysis section: {e}")
            generated_taesa_analysis_pt = CompanyAnalysisSection(
                company_overview_pt=f"Erro ao gerar análise da Taesa: {e}",
                financial_performance_analysis_pt="#Erro#",
                operational_performance_analysis_pt="#Erro#",
                key_projects_and_pipeline_pt="#Erro#",
                management_strategy_and_outlook_pt="#Erro#",
                swot_analysis_pt=None,
                financial_summary_data=taesa_summary
            )

        # 3. Generate Engie Analysis Section
        print(f"--- Generating Company Analysis Section for {self.engie_name_str} ---")
        try:
            generated_engie_analysis_pt = await self.llm.astructured_predict(
                output_cls=CompanyAnalysisSection,
                prompt=get_company_analysis_section_prompt_template(),
                company_name=self.engie_name_str,
                report_period=self.report_period_str,
                company_summary_json=engie_summary.model_dump_json(),
                modeling_assumptions=self.modeling_assumptions_content
            )
            print(f"Generated Engie Analysis Section. Overview: {generated_engie_analysis_pt.company_overview_pt[:100]}...")
        except Exception as e:
            print(f"Error generating Engie analysis section: {e}")
            generated_engie_analysis_pt = CompanyAnalysisSection(
                company_overview_pt=f"Erro ao gerar análise da Engie: {e}",
                financial_performance_analysis_pt="#Erro#",
                operational_performance_analysis_pt="#Erro#",
                key_projects_and_pipeline_pt="#Erro#",
                management_strategy_and_outlook_pt="#Erro#",
                swot_analysis_pt=None,
                financial_summary_data=engie_summary
            )
        
        # Ensure company analysis sections are available for subsequent prompts, even if they had errors
        taesa_analysis_json_for_prompt = generated_taesa_analysis_pt.model_dump_json() if generated_taesa_analysis_pt else "{}"
        engie_analysis_json_for_prompt = generated_engie_analysis_pt.model_dump_json() if generated_engie_analysis_pt else "{}"

        # 4. Generate Investment Thesis Section
        print("--- Generating Investment Thesis Section ---")
        try:
            generated_investment_thesis_pt = await self.llm.astructured_predict(
                output_cls=InvestmentThesisSection,
                prompt=get_investment_thesis_section_prompt_template(),
                taesa_summary_json=taesa_summary.model_dump_json(),
                engie_summary_json=engie_summary.model_dump_json(),
                comparative_analysis_json=comparative_analysis_data.model_dump_json(),
                modeling_assumptions=self.modeling_assumptions_content,
                taesa_analysis_section_json=taesa_analysis_json_for_prompt,
                engie_analysis_section_json=engie_analysis_json_for_prompt
            )
            print(f"Generated Investment Thesis. Taesa Rationale: {generated_investment_thesis_pt.recommendation_rationale_taesa_pt[:100]}...")
        except Exception as e:
            print(f"Error generating investment thesis section: {e}")
            generated_investment_thesis_pt = InvestmentThesisSection(
                overall_recommendation_taesa_pt="#Erro#",
                recommendation_rationale_taesa_pt=f"Erro: {e}",
                bull_case_taesa_pt=[],
                bear_case_taesa_pt=[],
                overall_recommendation_engie_pt="#Erro#",
                recommendation_rationale_engie_pt=f"Erro: {e}",
                bull_case_engie_pt=[],
                bear_case_engie_pt=[]
            )

        # 5. Generate Valuation Section
        print("--- Generating Valuation Section ---")
        try:
            generated_valuation_section_pt = await self.llm.astructured_predict(
                output_cls=ValuationSection,
                prompt=get_valuation_section_prompt_template(),
                taesa_summary_json=taesa_summary.model_dump_json(),
                engie_summary_json=engie_summary.model_dump_json(),
                modeling_assumptions=self.modeling_assumptions_content,
                taesa_analysis_section_json=taesa_analysis_json_for_prompt,
                engie_analysis_section_json=engie_analysis_json_for_prompt
            )
            print(f"Generated Valuation Section. Summary Notes: {generated_valuation_section_pt.valuation_summary_notes_pt[:100]}...")
        except Exception as e:
            print(f"Error generating valuation section: {e}")
            generated_valuation_section_pt = ValuationSection(valuation_summary_notes_pt=f"Erro ao gerar seção de valuation: {e}")

        # 6. Generate Risk Analysis Section
        print("--- Generating Risk Analysis Section ---")
        try:
            generated_risk_analysis_pt = await self.llm.astructured_predict(
                output_cls=RiskAnalysisSection,
                prompt=get_risk_analysis_section_prompt_template(),
                taesa_summary_json=taesa_summary.model_dump_json(),
                engie_summary_json=engie_summary.model_dump_json(),
                comparative_analysis_json=comparative_analysis_data.model_dump_json(),
                modeling_assumptions=self.modeling_assumptions_content,
                taesa_analysis_section_json=taesa_analysis_json_for_prompt,
                engie_analysis_section_json=engie_analysis_json_for_prompt
            )
            print(f"Generated Risk Analysis Section. Sector Risks Count: {len(generated_risk_analysis_pt.sector_risks_pt)}...")
        except Exception as e:
            print(f"Error generating risk analysis section: {e}")
            generated_risk_analysis_pt = RiskAnalysisSection(sector_risks_pt=[RiskItem(risk_description_pt=f"Erro: {e}")])

        # 7. Generate ESG Section
        print("--- Generating ESG Section ---")
        try:
            generated_esg_section_pt = await self.llm.astructured_predict(
                output_cls=ESGSection,
                prompt=get_esg_section_prompt_template(),
                taesa_summary_json=taesa_summary.model_dump_json(),
                engie_summary_json=engie_summary.model_dump_json(),
                modeling_assumptions=self.modeling_assumptions_content,
                taesa_analysis_section_json=taesa_analysis_json_for_prompt,
                engie_analysis_section_json=engie_analysis_json_for_prompt
            )
            print(f"Generated ESG Section. Environmental: {generated_esg_section_pt.environmental_pt[:100] if generated_esg_section_pt.environmental_pt else 'N/A'}...")
        except Exception as e:
            print(f"Error generating ESG section: {e}")
            # Fallback to a default ESGSection with error messages
            generated_esg_section_pt = ESGSection(
                environmental_pt=f"Erro ao gerar seção ambiental: {e}",
                social_pt=f"Erro ao gerar seção social: {e}",
                governance_pt=f"Erro ao gerar seção de governança: {e}",
                esg_summary_notes_pt=f"Erro ao gerar resumo ESG: {e}"
            )
        
        # 8. Generate Final Recommendation Summary (string)
        print("--- Generating Final Recommendation Summary ---")
        if generated_investment_thesis_pt and not "#Erro#" in generated_investment_thesis_pt.overall_recommendation_taesa_pt:
            generated_final_rec_summary_pt = f"Taesa: {generated_investment_thesis_pt.overall_recommendation_taesa_pt}. Engie: {generated_investment_thesis_pt.overall_recommendation_engie_pt}. Consulte a seção de Tese de Investimento para o racional detalhado."
        else:
            generated_final_rec_summary_pt = "Erro ao derivar o resumo da recomendação final devido a erros na seção de tese de investimento."
        print(f"Generated Final Recommendation Summary: {generated_final_rec_summary_pt}")

        # Assemble the final memo with all generated (or error-filled) parts
        print("--- Assembling Final Memo --- ")
        final_memo_output = FinalBrazilianEnergyMemoOutput(
            memo_title_pt="Análise Setorial Aprofundada: Energia Elétrica no Brasil - Taesa e Engie",
            date_generated=current_date_str,
            report_period_covered_pt=self.report_period_str,
            executive_summary_pt=generated_executive_summary_pt,
            taesa_analysis_pt=generated_taesa_analysis_pt if generated_taesa_analysis_pt else CompanyAnalysisSection(company_overview_pt="Seção da Taesa não gerada", financial_performance_analysis_pt="", operational_performance_analysis_pt="", key_projects_and_pipeline_pt="", management_strategy_and_outlook_pt="", financial_summary_data=taesa_summary if taesa_summary else CompanyFinancialSummaryOutput(company_name=self.taesa_name_str, report_period=self.report_period_str)),
            engie_analysis_pt=generated_engie_analysis_pt if generated_engie_analysis_pt else CompanyAnalysisSection(company_overview_pt="Seção da Engie não gerada", financial_performance_analysis_pt="", operational_performance_analysis_pt="", key_projects_and_pipeline_pt="", management_strategy_and_outlook_pt="", financial_summary_data=engie_summary if engie_summary else CompanyFinancialSummaryOutput(company_name=self.engie_name_str, report_period=self.report_period_str)),
            comparative_analysis_pt=comparative_analysis_data,
            investment_thesis_pt=generated_investment_thesis_pt if generated_investment_thesis_pt else InvestmentThesisSection(overall_recommendation_taesa_pt="#Erro#", recommendation_rationale_taesa_pt="Seção de tese de investimento não gerada", bull_case_taesa_pt=[], bear_case_taesa_pt=[], overall_recommendation_engie_pt="#Erro#", recommendation_rationale_engie_pt="", bull_case_engie_pt=[], bear_case_engie_pt=[]),
            valuation_section_pt=generated_valuation_section_pt if generated_valuation_section_pt else ValuationSection(valuation_summary_notes_pt="Seção de valuation não gerada"),
            risk_analysis_pt=generated_risk_analysis_pt if generated_risk_analysis_pt else RiskAnalysisSection(sector_risks_pt=[RiskItem(risk_description_pt="Seção de análise de risco não gerada")]),
            esg_considerations_pt=generated_esg_section_pt if generated_esg_section_pt else ESGSection(esg_summary_notes_pt="Seção ESG não gerada"),
            final_recommendation_summary_pt=generated_final_rec_summary_pt,
            appendix_modeling_assumptions_pt=self.modeling_assumptions_content,
            disclaimer_pt="Este relatório foi gerado por uma inteligência artificial e destina-se apenas a fins informativos. Não constitui aconselhamento de investimento."
        )

        print(f"Final Assembled Memo (model_dump_json) - Iterative Progress:\n{json.dumps(final_memo_output.model_dump(), indent=2, ensure_ascii=False)}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(self.output_dir, f"final_equity_memo_pt_iterative_{timestamp}.json")
        os.makedirs(os.path.dirname(output_filename), exist_ok=True) 
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(final_memo_output.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"\nFinal equity research memo (JSON, iteratively generated) saved to: {output_filename}")
        
        return StopEvent(result=final_memo_output)

async def main_async(taesa_index_dir: str, engie_index_dir: str, assumptions_file: str, report_period_arg: str, output_dir_arg: str, extracted_documents_dir_arg: str):
    print("--- Initializing Equity Analyzer Workflow (Senior Analyst Mode) ---")
    
    # Load Taesa Index
    taesa_storage_context = StorageContext.from_defaults(persist_dir=taesa_index_dir)
    taesa_index = load_index_from_storage(taesa_storage_context)
    taesa_query_engine = taesa_index.as_query_engine(similarity_top_k=3) 
    
    # Load Engie Index
    engie_storage_context = StorageContext.from_defaults(persist_dir=engie_index_dir)
    engie_index = load_index_from_storage(engie_storage_context)
    engie_query_engine = engie_index.as_query_engine(similarity_top_k=3)

    with open(assumptions_file, "r", encoding="utf-8") as f:
        modeling_assumptions_content = f.read()

    taesa_company_name = "Taesa (Transmissora Aliança de Energia Elétrica S.A.)"
    engie_company_name = "Engie Brasil Energia S.A."

    # --- Construct paths to the full extracted JSON files ---
    # Use the exact filenames as generated by data_extractor.py
    # The report_period_arg is still used for LLM prompts, but filenames are fixed here
    taesa_json_filename = "taesa___transmissora_aliança_de_energia_elétrica_sa_1º_trimestre_de_2025.json"
    engie_json_filename = "engie_brasil_energia_sa_1t25.json"

    taesa_full_json_path = os.path.join(extracted_documents_dir_arg, taesa_json_filename)
    engie_full_json_path = os.path.join(extracted_documents_dir_arg, engie_json_filename)

    print(f"Expected Taesa JSON path: {taesa_full_json_path}")
    print(f"Expected Engie JSON path: {engie_full_json_path}")

    print("\n--- Starting Workflow (Senior Analyst Mode) ---")
    
    workflow_instance = EquityResearchWorkflow(
        modeling_assumptions_content=modeling_assumptions_content,
        report_period_str=report_period_arg,
        taesa_name_str=taesa_company_name,
        engie_name_str=engie_company_name,
        taesa_json_file_path=taesa_full_json_path,
        engie_json_file_path=engie_full_json_path,
        output_dir=output_dir_arg,
        timeout=600
    )

    workflow_result = await workflow_instance.run(
        taesa_query_engine=taesa_query_engine,
        engie_query_engine=engie_query_engine
    )
    
    if isinstance(workflow_result, FinalBrazilianEnergyMemoOutput):
        print("\n--- Workflow Completed Successfully (Senior Analyst Mode) ---")
        print("Final Memo Output (from workflow run - a Pydantic object):")
        print(json.dumps(workflow_result.model_dump(), indent=2, ensure_ascii=False))
    elif isinstance(workflow_result, dict) and workflow_result.get("missing_data"):
        print("\n--- Workflow Stopped Due to Missing Data ---")
        print(f"Error: {workflow_result.get('error')}")
    else:
        print("\n--- Workflow Completed (Unexpected Result Type) ---")
        print(f"Type: {type(workflow_result)}")
        print(f"Value: {workflow_result}")

if __name__ == "__main__":
    DEFAULT_TAESA_INDEX_DIR = "output/indexes/taesa"
    DEFAULT_ENGIE_INDEX_DIR = "output/indexes/engie"
    DEFAULT_ASSUMPTIONS_FILE = "data/reference/modeling_assumptions.txt"
    DEFAULT_REPORT_PERIOD = "1Q2025"
    DEFAULT_OUTPUT_DIR = "output/senior_reports" 
    DEFAULT_EXTRACTED_DOCUMENTS_DIR = "output/extracted_documents"

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")

    parser = argparse.ArgumentParser(description="Senior Equity Research Analyzer Workflow for Brazilian Energy Sector")
    parser.add_argument("--taesa_index_dir", type=str, default=DEFAULT_TAESA_INDEX_DIR, 
                        help=f"Directory of the Taesa index (default: {DEFAULT_TAESA_INDEX_DIR})")
    parser.add_argument("--engie_index_dir", type=str, default=DEFAULT_ENGIE_INDEX_DIR, 
                        help=f"Directory of the Engie index (default: {DEFAULT_ENGIE_INDEX_DIR})")
    parser.add_argument("--assumptions_file", type=str, default=DEFAULT_ASSUMPTIONS_FILE, 
                        help=f"Path to the modeling assumptions file (default: {DEFAULT_ASSUMPTIONS_FILE})")
    parser.add_argument("--report_period", type=str, default=DEFAULT_REPORT_PERIOD, 
                        help=f"Report period string (e.g., 1T2025) (default: {DEFAULT_REPORT_PERIOD})")
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR, 
                        help=f"Directory to save the final memo and other outputs (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--extracted_documents_dir", type=str, default=DEFAULT_EXTRACTED_DOCUMENTS_DIR, 
                        help=f"Directory containing the full JSON outputs from data_extractor.py (default: {DEFAULT_EXTRACTED_DOCUMENTS_DIR})")

    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    asyncio.run(main_async(
        taesa_index_dir=args.taesa_index_dir,
        engie_index_dir=args.engie_index_dir,
        assumptions_file=args.assumptions_file,
        report_period_arg=args.report_period,
        output_dir_arg=args.output_dir,
        extracted_documents_dir_arg=args.extracted_documents_dir
    ))

