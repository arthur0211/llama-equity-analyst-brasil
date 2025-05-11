import os
from dotenv import load_dotenv
from llama_cloud_services import LlamaExtract
from llama_cloud.core.api_error import ApiError
from llama_cloud.types import ExtractConfig, ExtractMode
from pydantic import BaseModel, Field
from typing import Optional, List
import json
from llama_index.core.schema import Document

# Load environment variables from .env file
load_dotenv()

# --- 1. Define Pydantic Schemas (Corrected and Cleaned) ---
class FinancialMetrics(BaseModel):
    net_revenue: Optional[float] = Field(None, description="Receita Operacional Líquida (ROL) consolidada do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    ebitda: Optional[float] = Field(None, description="EBITDA (LAJIDA) consolidado do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    adjusted_ebitda: Optional[float] = Field(None, description="EBITDA Ajustado (LAJIDA Ajustado) consolidado do trimestre/período do relatório, se explicitamente reportado. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    net_income: Optional[float] = Field(None, description="Lucro Líquido consolidado atribuível aos acionistas da empresa no trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    gross_debt: Optional[float] = Field(None, description="Dívida Bruta consolidada ao final do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    cash_and_equivalents: Optional[float] = Field(None, description="Caixa e Equivalentes de Caixa consolidados ao final do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões). Se o valor estiver em milhares (e.g., R$ X.XXX.XXX mil) e a unidade principal for milhões, converta para milhões (e.g., R$ XXXX.X milhões).")
    net_debt: Optional[float] = Field(None, description="Dívida Líquida consolidada ao final do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    capex: Optional[float] = Field(None, description="CAPEX (Investimentos) realizado e consolidado no trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões). Se o valor for declarado como 'X bilhões' (e.g., 'R$ 1,1 bilhão'), converta para milhões (e.g., 1100.0).")
    operational_expenses: Optional[float] = Field(None, description="Despesas Operacionais consolidadas ou PMSO (Pessoal, Material, Serviços e Outros) do trimestre/período do relatório. Reportar na unidade monetária principal do relatório (e.g., R$ milhões).")
    dividends_paid_or_proposed: Optional[float] = Field(None, description="Dividendos e/ou JCP pagos ou propostos referentes aos resultados do trimestre/período do relatório ou do exercício fiscal recente. Reportar na unidade monetária principal do relatório (e.g., R$ milhões). Se o valor estiver em milhares (e.g., R$ X.XXX.XXX mil) e a unidade principal for milhões, converta para milhões (e.g., R$ XXXX.X milhões).")

class TaesaOperationalMetrics(BaseModel):
    annual_permitted_revenue_rap: Optional[float] = Field(None, description="Receita Anual Permitida (RAP) total consolidada para o ciclo tarifário atual (e.g., 2024-2025), conforme mencionado no relatório.")
    transmission_lines_km: Optional[float] = Field(None, description="Extensão total em quilômetros (km) das linhas de transmissão em operação da companhia ao final do período do relatório.")
    substation_capacity_mva: Optional[float] = Field(None, description="Capacidade total de transformação em Megavolt-ampère (MVA) das subestações em operação da companhia ao final do período do relatório.")
    availability_index_percent: Optional[float] = Field(None, description="Índice de disponibilidade percentual (%) das linhas de transmissão da companhia no trimestre/período do relatório.")
    new_projects_rap_details: Optional[str] = Field(None, description="Detalhes sobre RAP de novos projetos em construção ou recém-concluídos, CAPEX associado e prazos (e.g., Tangará, Ananaí), conforme descrito no relatório.")

class EngieOperationalMetrics(BaseModel):
    total_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Total de geração (MW) da Engie Brasil ao final do período.")
    renewable_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Renovável de geração (MW) da Engie Brasil (e.g., hidrelétrica, eólica, solar) ao final do período.")
    hydro_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Hidrelétrica (MW) da Engie Brasil ao final do período.")
    solar_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Solar (MW) da Engie Brasil ao final do período.")
    wind_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Eólica (MW) da Engie Brasil ao final do período.")
    thermal_installed_capacity_mw: Optional[float] = Field(None, description="Capacidade Instalada Termelétrica (MW) da Engie Brasil ao final do período, se aplicável.")
    energy_sold_gwh: Optional[float] = Field(None, description="Volume total de energia vendida (GWh) pela Engie Brasil no período do relatório.")
    transmission_segment_rap: Optional[float] = Field(None, description="Receita Anual Permitida (RAP) do segmento de TRANSMISSÃO específico da Engie Brasil. Procure por valores de RAP associados às atividades de transmissão da Engie. Verifique se o valor de R$186 milhões encontrado na página 24 do relatório da Engie 1T25 se refere à RAP do segmento de transmissão da Engie.")
    transmission_segment_investment: Optional[str] = Field(None, description="Investimentos ou CAPEX realizados no segmento de transmissão pela Engie Brasil no período (e.g., Novo Lote arrematado em leilão).")
    new_projects_investment_details: Optional[str] = Field(None, description="Detalhes de investimento em novos projetos de geração, transmissão ou outros segmentos pela Engie Brasil, incluindo valores e cronogramas, conforme o relatório.")

class BrazilianCompanyReportData(BaseModel):
    company_name: str = Field(..., description="Nome completo da empresa (e.g., TAESA - Transmissora Aliança de Energia Elétrica S.A., ENGIE Brasil Energia S.A.)")
    report_period: str = Field(..., description="Período ao qual o relatório de resultados se refere (e.g., '1T25', 'Resultados do Primeiro Trimestre de 2025', 'Ano de 2024')")
    report_publication_date: str = Field(..., description="Data de publicação ou divulgação do relatório de resultados (e.g., '07 de maio de 2025')")
    currency_unit: str = Field(..., description="Unidade monetária dos valores financeiros reportados (e.g., 'R$ milhões', 'BRL thousands', 'Milhares de Reais')")
    
    financials: FinancialMetrics = Field(..., description="Principais métricas financeiras consolidadas da companhia para o período do relatório.")
    
    taesa_operational_summary: Optional[TaesaOperationalMetrics] = Field(None, description="CRITICAL: ESTE CAMPO DEVE SER PREENCHIDO (COM DADOS) SOMENTE E EXCLUSIVAMENTE SE o campo 'company_name' for IDENTICO a 'TAESA - Transmissora Aliança de Energia Elétrica S.A.'. CASO CONTRÁRIO, este campo DEVE SER None e NENHUM de seus subcampos deve ser preenchido.")
    engie_operational_summary: Optional[EngieOperationalMetrics] = Field(None, description="CRITICAL: ESTE CAMPO DEVE SER PREENCHIDO (COM DADOS) SOMENTE E EXCLUSIVAMENTE SE o campo 'company_name' for IDENTICO a 'ENGIE Brasil Energia S.A.'. CASO CONTRÁRIO, este campo DEVE SER None e NENHUM de seus subcampos deve ser preenchido.")
    
    management_discussion_and_outlook: Optional[str] = Field(None, description="Se o relatório for da ENGIE Brasil Energia S.A., procure a seção intitulada 'Mensagem da Administração' (ou um título muito similar como 'Palavra da Administração' ou 'Destaques da Administração'). Extraia e sumarize o conteúdo completo desta seção. Se o relatório for da TAESA, procure por uma seção equivalente e faça o mesmo. O resumo deve focar nos comentários da liderança sobre os resultados financeiros e operacionais do período, a estratégia da empresa, os principais projetos, os desafios e as perspectivas futuras.")
    key_projects_and_investments_highlights: Optional[str] = Field(None, description="Sumarize os destaques sobre o andamento de principais projetos em construção, resultados de leilões recentes, e planos de investimento futuros mencionados no relatório.")
    regulatory_environment_impacts: Optional[str] = Field(None, description="REVISE O DOCUMENTO INTEIRO, incluindo a Mensagem da Administração, seções de desempenho, riscos, e notas explicativas. Localize e sumarize qualquer texto que discuta explicitamente o impacto do ambiente regulatório nos negócios da companhia (ENGIE Brasil Energia S.A. ou TAESA, conforme o caso). Isso inclui menções a ANEEL, políticas energéticas, mudanças em tarifas, regras de concessão, resultados de leilões, legislação específica do setor elétrico, ou fatores macroeconômicos com impacto regulatório direto. Se nenhuma discussão explícita sobre estes tópicos for encontrada em todo o documento, este campo pode ser None.")
    dividend_policy_and_distribution_notes: Optional[str] = Field(None, description="Sumarize as informações sobre a política de dividendos, e os dividendos e/ou JCP (Juros sobre Capital Próprio) declarados, pagos ou propostos no período ou referentes ao exercício fiscal recente.")
    ESG_highlights: Optional[str] = Field(None, description="Sumarize os destaques de iniciativas ESG (Ambiental, Social e Governança) mencionadas no relatório, se houver.")

# --- 2. Initialize LlamaExtract Client ---
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
if not LLAMA_CLOUD_API_KEY:
    raise ValueError("LLAMA_CLOUD_API_KEY not found in environment variables. Please set it in your .env file.")

PROJECT_ID = "740cd9c3-c8e2-4f76-9cc1-1a91f556b3a2"
ORGANIZATION_ID = "a31886fa-2327-4f38-adf7-3334024e2dc7"
AGENT_NAME = "brazilian-equity-extractor-v1"

print(f"--- Initializing LlamaExtract client for Agent: {AGENT_NAME} ---")
extractor = LlamaExtract(
    api_key=LLAMA_CLOUD_API_KEY,
    project_id=PROJECT_ID,
    organization_id=ORGANIZATION_ID,
)
print("--- LlamaExtract client initialized ---")

# --- 3. Create or Get Extraction Agent ---
def get_or_create_or_update_agent(extractor_client: LlamaExtract, agent_name: str, schema: BaseModel, config: ExtractConfig) -> 'LlamaExtractAgent':
    try:
        print(f"Attempting to get agent: {agent_name}...")
        agent = extractor_client.get_agent(name=agent_name)
        print(f"Found existing agent: {agent_name} (ID: {agent.id})")
        
        agent_schema_dict = agent.data_schema
        input_schema_dict = schema.model_json_schema()

        if agent_schema_dict != input_schema_dict or agent.config != config:
            print(f"Updating agent {agent_name} with new schema/config...")
            agent.data_schema = schema 
            agent.config = config
            agent.save()
            print(f"Agent {agent_name} updated successfully.")
        else:
            print(f"Agent {agent_name} schema and config are up to date.")
            
    except ApiError as e:
        if e.status_code == 404: 
            print(f"Agent {agent_name} not found. Creating new agent...")
            agent = extractor_client.create_agent(
                name=agent_name,
                data_schema=schema, 
                config=config,
            )
            print(f"Created new agent: {agent_name} (ID: {agent.id})")
        else:
            print(f"API Error while trying to get/create agent {agent_name}: {e}")
            raise
    except Exception as e:
        print(f"An unexpected error occurred in get_or_create_or_update_agent for {agent_name}: {e}")
        raise
    return agent

extract_config = ExtractConfig(
    use_reasoning=True,
    cite_sources=True,
    extraction_mode=ExtractMode.MULTIMODAL
)

print("--- Configuring and fetching/creating agent ---")
extraction_agent = get_or_create_or_update_agent(extractor, AGENT_NAME, BrazilianCompanyReportData, extract_config)
print("--- Agent ready ---")

# --- 4. Define Extraction Function ---
async def extract_data_from_pdf(agent: 'LlamaExtractAgent', file_path: str, company_context: str):
    if not agent:
        print(f"Error: Extraction agent is None. Cannot proceed for {company_context}.")
        return None # Return None for the whole result object
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path} for {company_context}")
        return None # Return None for the whole result object

    print(f"\n--- Starting extraction for: {file_path} ({company_context}) using agent ID: {agent.id} ---")
    raw_extraction_result = None
    parsed_pydantic_data = None

    try:
        # Run extraction
        raw_extraction_result = agent.extract(file_path) 
        
        if raw_extraction_result and raw_extraction_result.data:
            if isinstance(raw_extraction_result.data, BrazilianCompanyReportData):
                parsed_pydantic_data = raw_extraction_result.data
                print(f"\n**Extracted Data for {company_context} (Pydantic model):**")
                print(parsed_pydantic_data.model_dump_json(indent=2))
            elif isinstance(raw_extraction_result.data, dict):
                print(f"\n**Extracted Data for {company_context} (raw dict from agent):**")
                print(json.dumps(raw_extraction_result.data, indent=2))
                # Attempt to parse the dictionary into our Pydantic model
                try:
                    parsed_pydantic_data = BrazilianCompanyReportData(**raw_extraction_result.data)
                    print(f"\n**Successfully parsed raw dict into Pydantic model for {company_context}:**")
                    print(parsed_pydantic_data.model_dump_json(indent=2))
                except Exception as pydantic_parse_e:
                    print(f"\n**Error parsing raw dict into Pydantic model for {company_context}: {pydantic_parse_e}**")
                    # Keep parsed_pydantic_data as None
            else:
                print(f"\n**Extracted Data for {company_context} (unknown type):**")
                print(raw_extraction_result.data)
                # Keep parsed_pydantic_data as None
        else:
            print(f"No data field in extraction result or result is None for {company_context}.")

        if raw_extraction_result and hasattr(raw_extraction_result, 'extraction_metadata') and raw_extraction_result.extraction_metadata:
            print(f"\n**Extraction Metadata for {company_context} (result.extraction_metadata):**")
            if hasattr(raw_extraction_result.extraction_metadata, 'to_dict'):
                 print(json.dumps(raw_extraction_result.extraction_metadata.to_dict(), indent=2))
            else:
                print(raw_extraction_result.extraction_metadata)
        else:
            print(f"No extraction metadata available for {company_context}.")
        
        # Return a consistent structure, ensuring data is the Pydantic model if successful
        if parsed_pydantic_data:
            # Reconstruct a simple result object with the Pydantic data
            # This ensures the main block receives the Pydantic model in the .data attribute
            class ExtractionResultWrapper:
                def __init__(self, data, metadata):
                    self.data = data
                    self.extraction_metadata = metadata
            return ExtractionResultWrapper(data=parsed_pydantic_data, metadata=raw_extraction_result.extraction_metadata if raw_extraction_result else None)
        else:
            return None # Indicate failure to get a valid Pydantic model

    except Exception as e:
        print(f"An error occurred during extraction for {file_path} ({company_context}): {e}")
        return None # Indicate failure

# --- 5. Main Execution Block ---
if __name__ == "__main__":
    import asyncio
    print("--- Starting main execution block --- ")

    # Determine which company to process
    COMPANY_TO_PROCESS = "TAESA" # Uncomment to process Taesa

    if COMPANY_TO_PROCESS == "ENGIE":
        REPORT_PATH = os.path.join("data", "release-engie", "250507-Release-de-Resultados-1T25.pdf")
    elif COMPANY_TO_PROCESS == "TAESA":
        REPORT_PATH = os.path.join("data", "release-taee", "TAESA-Release-1T25.pdf")
    else:
        raise ValueError(f"Unknown company: {COMPANY_TO_PROCESS}")

    print(f"--- Preparing to process: {COMPANY_TO_PROCESS} --- ")
    if not os.path.exists(REPORT_PATH):
        print(f"CRITICAL ERROR: Report for {COMPANY_TO_PROCESS} not found at {REPORT_PATH}. Please ensure the file exists.")
    else:
        print(f"Found report for {COMPANY_TO_PROCESS} at: {REPORT_PATH}")
        
        # Run extraction (synchronous call within the async main function)
        extraction_result = asyncio.run(extract_data_from_pdf(extraction_agent, REPORT_PATH, COMPANY_TO_PROCESS))
        
        if extraction_result and extraction_result.data and isinstance(extraction_result.data, BrazilianCompanyReportData):
            print(f"\n--- Converting extracted {COMPANY_TO_PROCESS} data to LlamaIndex Document ---")
            
            extracted_pydantic_data = extraction_result.data
            
            # Create output directory if it doesn't exist
            output_dir = os.path.join("output", "extracted_documents")
            os.makedirs(output_dir, exist_ok=True)
            
            # Prepare Document fields
            doc_id_company_name = extracted_pydantic_data.company_name.lower().replace(" ", "_").replace(".", "").replace("-", "_")
            doc_id_report_period = extracted_pydantic_data.report_period.lower().replace(" ", "_")
            doc_id = f"{doc_id_company_name}_{doc_id_report_period}"
            
            doc_text = extracted_pydantic_data.model_dump_json(indent=2)
            
            doc_metadata = {
                "company_name": extracted_pydantic_data.company_name,
                "report_period": extracted_pydantic_data.report_period,
                "report_publication_date": extracted_pydantic_data.report_publication_date,
                "currency_unit": extracted_pydantic_data.currency_unit,
                "source_file_path": REPORT_PATH,
                "extraction_agent_id": extraction_agent.id if extraction_agent else None,
                # Optionally, include a summary of LlamaExtract metadata if desired
                # "llama_extract_reasoning_summary": {k: v.reasoning for k, v in extraction_result.extraction_metadata.field_metadata.items() if hasattr(v, 'reasoning')}
            }
            
            # Create LlamaIndex Document
            llama_document = Document(
                id_=doc_id,
                text=doc_text,
                metadata=doc_metadata
            )
            
            # Save Document to JSON
            output_file_path = os.path.join(output_dir, f"{doc_id}.json")
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(llama_document.to_dict(), f, ensure_ascii=False, indent=4)
            
            print(f"--- LlamaIndex Document for {COMPANY_TO_PROCESS} saved to: {output_file_path} ---")
        else:
            print(f"--- Skipping Document conversion for {COMPANY_TO_PROCESS} due to no extracted data. ---")

    print("\n--- Script Finished ---") 