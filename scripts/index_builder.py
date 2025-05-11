import os
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex, Document # SimpleDirectoryReader, SimpleNodeParser removed as not used directly now
# from llama_index.core.node_parser import SimpleNodeParser # Not used currently
from llama_index.llms.google_genai import GoogleGenAI # Changed from gemini
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding # Corrected import path
import json
from typing import List, Optional
from pydantic import BaseModel, Field # Added pydantic imports

# --- Pydantic Schemas (Duplicated from data_extractor.py for now) ---
class FinancialMetrics(BaseModel):
    net_revenue: Optional[float] = Field(None, description="Receita Operacional Líquida (ROL) consolidada do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    ebitda: Optional[float] = Field(None, description="EBITDA (LAJIDA) consolidado do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    adjusted_ebitda: Optional[float] = Field(None, description="EBITDA Ajustado (LAJIDA Ajustado) consolidado do trimestre/período do relatório, se explicitamente reportado. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    net_income: Optional[float] = Field(None, description="Lucro Líquido consolidado atribuível aos acionistas da empresa no trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    gross_debt: Optional[float] = Field(None, description="Dívida Bruta consolidada ao final do período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ bilhões ou milhões).")
    net_debt: Optional[float] = Field(None, description="Dívida Líquida consolidada ao final do período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ bilhões ou milhões).")
    cash_and_equivalents: Optional[float] = Field(None, description="Caixa e Equivalentes de Caixa consolidados ao final do período do relatório. Reportar na unidade monetária principal (e.g., R$ milhões).")
    capex: Optional[float] = Field(None, description="CAPEX (Investimentos) consolidado do trimestre/período do relatório. Extrair o valor referente apenas ao período do relatório (e.g., 1T25), não o acumulado do ano se diferente. Reportar na unidade monetária principal (e.g., R$ milhões).")
    dividends_paid: Optional[float] = Field(None, description="Dividendos e JCP (Juros Sobre Capital Próprio) pagos ou declarados no trimestre/período do relatório. Reportar na unidade monetária principal (e.g., R$ milhões).")

class TaesaOperationalMetrics(BaseModel):
    annual_permitted_revenue_rap: Optional[float] = Field(None, description="Receita Anual Permitida (RAP) total consolidada para o ciclo tarifário atual (e.g., 2024-2025), conforme mencionado no relatório.")
    transmission_lines_km: Optional[float] = Field(None, description="Extensão total em quilômetros (km) das linhas de transmissão em operação da companhia ao final do período do relatório.")
    substation_capacity_mva: Optional[float] = Field(None, description="Capacidade total de transformação em MVA (Mega Volt-Ampere) das subestações em operação ao final do período.")

class EngieOperationalMetrics(BaseModel):
    total_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Total (MW) da Engie Brasil ao final do período.")
    hydro_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Hidrelétrica (MW) da Engie Brasil ao final do período.")
    complementary_sources_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada de Fontes Complementares (e.g., eólica, solar, biomassa) (MW) da Engie Brasil ao final do período.")
    solar_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Solar (MW) da Engie Brasil ao final do período.")
    wind_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Eólica (MW) da Engie Brasil ao final do período.")
    thermal_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Termelétrica (MW) da Engie Brasil ao final do período, se aplicável.")
    energy_sold_gwh: Optional[float] = Field(None, description="Energia vendida (GWh) no período do relatório.")
    average_contracted_price_ppa: Optional[float] = Field(None, description="Preço médio de venda de energia nos contratos de longo prazo (PPA) em R$/MWh, se disponível.")
    transmission_segment_rap: Optional[float] = Field(None, description="Receita Anual Permitida (RAP) do segmento de Transmissão da Engie Brasil, se detalhado.")
    transmission_segment_investment: Optional[float] = Field(None, description="Investimento (CAPEX) no segmento de Transmissão da Engie Brasil, se detalhado.")

class BrazilianCompanyReportData(BaseModel):
    company_name: Optional[str] = Field(None, description="Nome completo da empresa (e.g., TAESA - Transmissora Aliança de Energia Elétrica S.A., ENGIE Brasil Energia S.A.).")
    report_period: Optional[str] = Field(None, description="Período ao qual o relatório se refere (e.g., 1º trimestre de 2025, Resultados de 2024).")
    report_publication_date: Optional[str] = Field(None, description="Data de publicação do relatório de resultados.")
    currency_unit: Optional[str] = Field(None, description="Unidade monetária principal dos valores financeiros (e.g., R$ milhões, R$ bilhões, US$ milhões). Preferir R$ milhões se não especificado explicitamente como bilhões.")
    
    financial_summary: Optional[FinancialMetrics] = Field(None, description="Resumo dos principais indicadores financeiros consolidados da empresa para o período do relatório.")
    
    # Conditional Operational Summaries - LlamaExtract should pick the correct one based on company context
    taesa_operational_summary: Optional[TaesaOperationalMetrics] = Field(None, description="Preencher APENAS se o relatório for da TAESA. Resumo das métricas operacionais específicas da TAESA (segmento de Transmissão) para o período do relatório.")
    engie_operational_summary: Optional[EngieOperationalMetrics] = Field(None, description="Preencher APENAS se o relatório for da ENGIE Brasil. Resumo das métricas operacionais específicas da ENGIE Brasil (segmentos de Geração, Transmissão, Trading, etc.) para o período do relatório.")
    
    management_discussion_and_outlook: Optional[str] = Field(None, description="SUMARIZE o texto da seção 'Mensagem da Administração' ou similar que discuta os resultados, o cenário e as perspectivas da empresa. Capture os principais pontos sobre desempenho, estratégia, investimentos e visão de futuro. SE NÃO ENCONTRAR UMA SEÇÃO COM ESTE NOME EXATO, procure por seções como 'Destaques do Período', 'Comentários do Diretor Presidente', ou introduções que forneçam uma visão geral e perspectivas.")
    key_projects_and_investments_highlights: Optional[str] = Field(None, description="SUMARIZE as informações sobre os principais projetos em andamento, investimentos realizados ou planejados, e seus impactos esperados. Procure por seções de 'Investimentos', 'Projetos', 'CAPEX'.")
    debt_and_leverage_analysis: Optional[str] = Field(None, description="SUMARIZE a análise da dívida da empresa, perfil de endividamento, alavancagem financeira (Dívida Líquida/EBITDA), custo da dívida e estratégias de gerenciamento de passivos. Procure por seções como 'Endividamento', 'Gerenciamento de Riscos'.")
    dividend_information: Optional[str] = Field(None, description="SUMARIZE as informações sobre dividendos pagos, política de dividendos, JCP (Juros sobre Capital Próprio) e perspectivas de remuneração aos acionistas.")
    regulatory_environment_impacts: Optional[str] = Field(None, description="SUMARIZE os impactos relevantes do ambiente regulatório (e.g., revisões tarifárias, resoluções da ANEEL, mudanças na legislação) sobre a empresa. SE NÃO HOUVER UMA SEÇÃO ESPECÍFICA, mas houver menções relevantes sobre regulação nos comentários da administração ou análise de resultados, extraia e sumarize essas menções.")
    ESG_highlights: Optional[str] = Field(None, description="SUMARIZE as principais iniciativas e destaques de ESG (Ambiental, Social e Governança) mencionadas no relatório.")
    other_relevant_information: Optional[str] = Field(None, description="SUMARIZE qualquer outra informação qualitativa relevante para a análise da empresa que não se encaixe nos campos anteriores.")

# --- 1. Load Environment Variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

print("--- 1. Environment variables loaded ---")

# --- 2. Initialize LLM and Embedding Model ---
try:
    llm = GoogleGenAI(model_name="models/gemini-pro", api_key=GEMINI_API_KEY)
    embed_model = GoogleGenAIEmbedding(
        model_name="models/embedding-001", 
        api_key=GEMINI_API_KEY
    )
    print("--- 2. GoogleGenAI LLM and GoogleGenAIEmbedding Model initialized successfully ---")
except Exception as e:
    print(f"Error initializing Google GenAI LLM or Embedding Model: {e}")
    raise

# --- 3. Configure LlamaIndex Settings ---
Settings.llm = llm
Settings.embed_model = embed_model
# Settings.chunk_size = 512 # Optional: Adjust as needed
# Settings.chunk_overlap = 20 # Optional: Adjust as needed
# Settings.node_parser = SimpleNodeParser.from_defaults(chunk_size=Settings.chunk_size, chunk_overlap=Settings.chunk_overlap) # If customizing chunking

print("--- 3. LlamaIndex Settings configured ---")

# --- 4. Functions for Loading Documents and Building Index ---

def load_and_parse_extracted_json(file_path: str) -> BrazilianCompanyReportData | None:
    """Loads the outer LlamaIndex Document JSON, then parses its 'text' field (inner JSON string) into our Pydantic model."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            outer_doc_dict = json.load(f)
        
        inner_json_string = outer_doc_dict.get("text")
        if not inner_json_string:
            print(f"Error: 'text' field containing inner JSON not found in {file_path}")
            return None
            
        # Attempt to repair potentially dirty JSON before parsing
        # Sometimes LlamaExtract might produce slightly non-standard JSON like unquoted keys or trailing commas
        # For robust parsing, one might consider a library like `dirtyjson` if issues persist
        # For now, we assume the JSON from LlamaIndex Document.text is clean enough for Pydantic
        parsed_data = BrazilianCompanyReportData.model_validate_json(inner_json_string)
        print(f"Successfully loaded and parsed inner JSON into Pydantic model from: {file_path}")
        return parsed_data
    except json.JSONDecodeError as e:
        # Try to provide more context on JSONDecodeError
        error_pos = e.pos
        context_window = 50 # characters before and after the error position
        start_context = max(0, error_pos - context_window)
        end_context = min(len(inner_json_string), error_pos + context_window)
        error_context = inner_json_string[start_context:end_context]
        print(f"JSONDecodeError parsing inner JSON from {file_path} at position {error_pos}: {e}. Context: '...{error_context}...\'")
        return None
    except Exception as e:
        print(f"Error loading/parsing LlamaIndex Document or inner JSON from {file_path}: {e}")
        return None

def create_granular_nodes_from_pydantic(report_data: BrazilianCompanyReportData, company_name_arg: str) -> list[Document]:
    """Creates a list of granular LlamaIndex Documents from the Pydantic model."""
    nodes = []
    if not report_data:
        return nodes

    base_metadata = {
        "company_name": company_name_arg, # Use the passed argument
        "report_period": report_data.report_period or "Unknown Period",
        "report_publication_date": report_data.report_publication_date or "Unknown Date",
        "currency_unit": report_data.currency_unit or "Unknown Currency"
    }

    # Top-level string fields from BrazilianCompanyReportData
    top_level_text_fields = [
        "company_name", # Though this is in base_metadata, can be a node too if desired
        "report_period", 
        "report_publication_date",
        "currency_unit",
        "management_discussion_and_outlook",
        "key_projects_and_investments_highlights",
        "debt_and_leverage_analysis",
        "dividend_information",
        "regulatory_environment_impacts",
        "ESG_highlights",
        "other_relevant_information"
    ]

    for field_name in top_level_text_fields:
        value = getattr(report_data, field_name, None)
        if value and isinstance(value, str) and value.strip(): # Ensure it's a non-empty string
            metadata = base_metadata.copy()
            metadata.update({
                "section_name": field_name,
                "value_type": "qualitative_summary" if "summary" in field_name or "discussion" in field_name or "outlook" in field_name or "information" in field_name or "highlights" in field_name else "report_attribute"
            })
            nodes.append(Document(text=value, metadata=metadata))
    
    # FinancialMetrics
    if report_data.financial_summary:
        for metric_name, field_obj in FinancialMetrics.model_fields.items():
            value = getattr(report_data.financial_summary, metric_name, None)
            if value is not None: # Allow 0 or other falsy numbers
                metadata = base_metadata.copy()
                metadata.update({
                    "metric_name": metric_name,
                    "value_type": "financial_metric",
                    "source_model": "FinancialMetrics",
                    "description": field_obj.description or ""
                })
                # Convert numeric value to string for Document text
                nodes.append(Document(text=str(value), metadata=metadata))

    # TaesaOperationalMetrics
    if report_data.taesa_operational_summary and company_name_arg.upper() == "TAESA":
        for metric_name, field_obj in TaesaOperationalMetrics.model_fields.items():
            value = getattr(report_data.taesa_operational_summary, metric_name, None)
            if value is not None:
                metadata = base_metadata.copy()
                metadata.update({
                    "metric_name": metric_name,
                    "value_type": "operational_metric",
                    "source_model": "TaesaOperationalMetrics",
                    "description": field_obj.description or ""
                })
                nodes.append(Document(text=str(value), metadata=metadata))
    
    # EngieOperationalMetrics
    if report_data.engie_operational_summary and company_name_arg.upper() == "ENGIE":
        for metric_name, field_obj in EngieOperationalMetrics.model_fields.items():
            value = getattr(report_data.engie_operational_summary, metric_name, None)
            if value is not None:
                metadata = base_metadata.copy()
                metadata.update({
                    "metric_name": metric_name,
                    "value_type": "operational_metric",
                    "source_model": "EngieOperationalMetrics",
                    "description": field_obj.description or ""
                })
                nodes.append(Document(text=str(value), metadata=metadata))
    
    print(f"Created {len(nodes)} granular nodes for {company_name_arg}.")
    return nodes

def build_and_persist_index(documents: list[Document], index_persist_path: str):
    """Builds a VectorStoreIndex from documents and persists it."""
    if not documents:
        print("No documents provided to build index. Skipping.")
        return None
    try:
        print(f"Building index from {len(documents)} document(s)...")
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=index_persist_path)
        print(f"Index built and persisted to: {index_persist_path}")
        return index
    except Exception as e:
        print(f"Error building/persisting index to {index_persist_path}: {e}")
        return None

if __name__ == "__main__":
    print("--- Running index_builder.py --- ")
    
    taesa_doc_path = "output/extracted_documents/taesa___transmissora_aliança_de_energia_elétrica_sa_1º_trimestre_de_2025.json"
    engie_doc_path = "output/extracted_documents/engie_brasil_energia_sa_1t25.json"
    
    taesa_index_persist_dir = "output/indexes/taesa"
    engie_index_persist_dir = "output/indexes/engie"

    os.makedirs(taesa_index_persist_dir, exist_ok=True)
    os.makedirs(engie_index_persist_dir, exist_ok=True)
    print("--- Index persistence directories ensured --- ")

    # --- Processing Taesa ---
    print("\n--- Processing Taesa --- ")
    if os.path.exists(taesa_doc_path):
        taesa_report_data = load_and_parse_extracted_json(taesa_doc_path)
        if taesa_report_data:
            taesa_granular_nodes = create_granular_nodes_from_pydantic(taesa_report_data, "TAESA") # Pass company name
            if taesa_granular_nodes:
                build_and_persist_index(taesa_granular_nodes, taesa_index_persist_dir)
            else:
                print("No granular nodes created for Taesa. Index not built.")
    else:
        print(f"Taesa document not found at: {taesa_doc_path}")

    # --- Processing Engie ---
    print("\n--- Processing Engie --- ")
    if os.path.exists(engie_doc_path):
        engie_report_data = load_and_parse_extracted_json(engie_doc_path)
        if engie_report_data:
            engie_granular_nodes = create_granular_nodes_from_pydantic(engie_report_data, "ENGIE") # Pass company name
            if engie_granular_nodes:
                build_and_persist_index(engie_granular_nodes, engie_index_persist_dir)
            else:
                print("No granular nodes created for Engie. Index not built.")
    else:
        print(f"Engie document not found at: {engie_doc_path}")
        
    print("\n--- index_builder.py finished --- ") 