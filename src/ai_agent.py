
import os
import json
import functools
from groq import Groq
from collections import Counter
from typing import Dict, Any
 
# Configure the Groq API client
# A chave de API deve ser definida como uma variável de ambiente.
try:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("⚠️  Aviso: A variável de ambiente GROQ_API_KEY não foi definida. A funcionalidade de IA será desativada.")
        client = None
    else:
        client = Groq(api_key=api_key)
except Exception as e:
    print(f"❌ Erro ao configurar a API do Groq: {e}")
    client = None

@functools.lru_cache(maxsize=1)
def get_docs_content() -> str:
    """Carrega e concatena o conteúdo dos arquivos de documentação, com cache."""
    docs_content = ""
    doc_files = ['README.md', 'GEMINI.md', 'docs/doc_gerencial.html']
    base_path = os.path.join(os.path.dirname(__file__), '..')
    
    for doc_file in doc_files:
        try:
            with open(os.path.join(base_path, doc_file), 'r', encoding='utf-8') as f:
                docs_content += f"\n\n--- CONTEÚDO DE {doc_file} ---\n\n{f.read()}"
        except FileNotFoundError:
            print(f"⚠️  Arquivo de documentação não encontrado: {doc_file}")
    return docs_content

# Modelo recomendado para velocidade e custo-benefício no Groq
MODEL_NAME = 'llama-3.3-70b-versatile'
# Modelo mais rápido para a tarefa simples de roteamento
ROUTER_MODEL_NAME = 'llama-3.1-8b-instant'

def route_question(question: str) -> str:
    """
    Classifica a pergunta do usuário para direcioná-la ao agente correto.
    Retorna 'data_analysis' ou 'project_documentation'.
    """
    if not client:
        # Se o cliente não estiver configurado, assume o padrão de análise de dados
        return "data_analysis"

    try:
        system_prompt = """Sua tarefa é classificar a pergunta do usuário em uma de duas categorias: 'data_analysis' ou 'project_documentation'.
- Use 'data_analysis' para perguntas sobre dados, relatórios, KPIs, números, tendências, 'casos', 'alertas', 'times' ou 'squads'.
- Use 'project_documentation' para perguntas sobre o funcionamento do projeto, arquitetura, código, 'Flask', 'Kubernetes', 'Docker', ou como usar a aplicação.
Responda apenas com a categoria.
"""
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            model=ROUTER_MODEL_NAME,
        )
        category = chat_completion.choices[0].message.content.strip().lower()
        if category in ["data_analysis", "project_documentation"]:
            return category
        return "data_analysis" # Padrão de segurança
    except Exception as e:
        print(f"⚠️ Erro ao rotear pergunta, usando padrão 'data_analysis'. Erro: {e}")
        return "data_analysis"


def ask_question_to_agent(question: str, report_data_json: str) -> str:
    """
    Envia uma pergunta para a IA do Gemini com o contexto de um relatório.

    Args:
        question (str): A pergunta do usuário.
        report_data_json (str): Uma string JSON contendo os dados do relatório ('header' e 'records').

    Returns:
        str: A resposta gerada pela IA.
    """
    if not client:
        return "A funcionalidade de chat com IA está desativada pois a chave de API (GROQ_API_KEY) não foi configurada."

    try:
        # Carrega o JSON para garantir que está bem formatado e para extrair informações
        report_data = json.loads(report_data_json)
        records = report_data.get('records', [])
        header = report_data.get('header', {})
        records_preview = records[:3] # Mantém uma pequena amostra para exemplos

        # ANÁLISE APROFUNDADA: Cria um resumo da distribuição de casos E alertas por time.
        if records:
            squad_summary_data = {}
            for record in records:
                squad = record.get('assignment_group', 'DESCONHECIDO')
                if squad not in squad_summary_data:
                    squad_summary_data[squad] = {'casos': 0, 'alertas': 0}
                squad_summary_data[squad]['casos'] += 1
                squad_summary_data[squad]['alertas'] += record.get('alert_count', 0)
            
            # Ordena os times pelo número de casos e pega o Top 10
            top_10_squads = sorted(squad_summary_data.items(), key=lambda item: item[1]['casos'], reverse=True)[:10]

            # Formata o resumo para o prompt, tornando-o inequívoco
            squad_summary = "\n".join([f"- {squad}: {data['casos']} casos (gerando {data['alertas']} alertas)" for squad, data in top_10_squads])
        else:
            squad_summary = "Nenhum caso encontrado para resumir."

        system_prompt = """Você é um analista de dados especialista em operações de TI. Responda perguntas sobre um relatório de alertas de forma concisa e direta, usando apenas os dados fornecidos como fonte da verdade. Se a pergunta não puder ser respondida com os dados, informe que não possui essa informação."""

        user_content = f"""
        **Contexto do Relatório:**
        - Distribuição por Time (Top 10 por número de casos):
{squad_summary}
        - Resumo: Total de Alertas={header.get('total_alertas', 'N/A')}, Risco Médio={header.get('risco_medio', 0):.2f}, Ineficiência Média={header.get('ineficiencia_media', 0):.2f}, Impacto Médio={header.get('impacto_medio', 0):.2f}
        - Amostra de Dados (Primeiros 3 de {len(report_data.get('records', []))} casos):
          ```json
          {json.dumps(records_preview, indent=2, default=str)}
          ```

        **Pergunta:** "{question}"
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model=MODEL_NAME,
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"❌ Erro ao chamar a API do Groq na função de chat: {e}")
        return f"Ocorreu um erro ao processar sua pergunta com a IA. Detalhes: {e}"


def gerar_resumo_ia(kpis_tendencia: Dict[str, Any], header_atual: Dict[str, Any]) -> str:
    """
    Gera um resumo executivo em linguagem natural usando a API do Gemini.

    Args:
        kpis_tendencia (Dict[str, Any]): Dicionário com os KPIs da análise de tendência.
        header_atual (Dict[str, Any]): Dicionário com os dados do cabeçalho da análise atual.

    Returns:
        str: O resumo em texto gerado pela IA, ou uma mensagem de erro/aviso.
    """
    if not client:
        return "A geração de resumo por IA está desativada pois a chave de API (GROQ_API_KEY) não foi configurada."

    try:
        system_prompt = """Você é um analista de operações de TI sênior. Sua tarefa é escrever um resumo executivo conciso (máximo de 4 frases) para a gestão, baseado nos dados fornecidos. Comece com o resultado principal (saldo de casos), mencione a taxa de resolução e destaque o número de novos casos. Evite jargões."""
        
        user_content = f"""

        **Contexto:**
        - "Casos" são problemas únicos que precisam de ação.
        - "Taxa de Resolução" é a porcentagem de casos do período anterior que foram resolvidos.
        - O objetivo é reduzir o número de casos em aberto e aumentar a taxa de resolução.

        **Dados da Análise de Tendência (Comparativo com o período anterior):**
        - Casos em aberto no período anterior: {kpis_tendencia.get('total_p1', 'N/A')}
        - Casos resolvidos neste período: {kpis_tendencia.get('resolved', 'N/A')}
        - Novos casos que surgiram neste período: {kpis_tendencia.get('new', 'N/A')}
        - Casos que persistiram do período anterior: {kpis_tendencia.get('persistent', 'N/A')}
        - Saldo final de casos em aberto: {kpis_tendencia.get('total_p2', 'N/A')}
        - Taxa de Resolução: {kpis_tendencia.get('improvement_rate', 0):.1f}%

        **Dados do Período Atual:**
        - Total de alertas analisados: {header_atual.get('total_alertas', 'N/A')}
        - Risco médio dos casos: {header_atual.get('risco_medio', 0):.2f} (de 0 a 20)
        - Ineficiência média da automação: {header_atual.get('ineficiencia_media', 0):.2f} (quanto maior, pior)

        Gere o resumo executivo.
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model=MODEL_NAME,
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"❌ Erro ao chamar a API do Groq: {e}")
        return f"Ocorreu um erro ao gerar o resumo da IA. Detalhes: {e}"

def ask_project_expert(question: str) -> str:
    """
    Responde a perguntas sobre o projeto com base na documentação.
    """
    if not client:
        return "A funcionalidade de chat com IA está desativada pois a chave de API (GROQ_API_KEY) não foi configurada."

    try:
        project_docs = get_docs_content()
        
        system_prompt = """Você é um especialista sênior no projeto 'meu-dash'. Sua única fonte de conhecimento é a documentação fornecida. Responda às perguntas do usuário de forma clara e concisa, baseando-se estritamente neste contexto. Se a resposta não estiver na documentação, informe que não possui essa informação."""

        user_content = f"""
        **Documentação do Projeto:**
        {project_docs}

        **Pergunta do Usuário:** "{question}"
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model=MODEL_NAME,
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"❌ Erro ao chamar a API do Groq no agente especialista do projeto: {e}")
        return f"Ocorreu um erro ao processar sua pergunta com o especialista do projeto. Detalhes: {e}"

def ask_unified_agent(question: str, report_id: int = None) -> str:
    """
    Ponto de entrada unificado que primeiro roteia a pergunta e depois chama o agente especialista apropriado.
    """
    category = route_question(question)
    print(f"🤖 Pergunta roteada para a categoria: {category}")

    if category == 'project_documentation':
        return ask_project_expert(question)
    
    # Se for 'data_analysis', precisamos dos dados do relatório
    if report_id:
        from .app import Report # Importação local para evitar dependência circular
        report = Report.query.get(report_id)
        if report and report.json_summary_path and os.path.exists(report.json_summary_path):
            with open(report.json_summary_path, 'r', encoding='utf-8') as f:
                report_data_json = f.read()
            return ask_question_to_agent(question, report_data_json)
    
    return "Para responder a perguntas sobre dados, por favor, certifique-se de que um relatório esteja carregado e selecionado. Se sua pergunta é sobre o projeto, tente reformulá-la."
