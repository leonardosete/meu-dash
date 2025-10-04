
import os
import json
import functools
from groq import Groq
from collections import Counter
from typing import Dict, Any, List, Callable, Optional, Union

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

@functools.lru_cache(maxsize=2) # Aumenta o cache para acomodar o histórico
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

# =============================================================================
# MODELOS E CONFIGURAÇÕES DA IA (APÓS APLICAÇÃO DA SUGESTÃO ANTERIOR)
# =============================================================================

# Modelo principal para raciocínio e análise
MODEL_NAME = 'llama-3.3-70b-versatile' 
# Modelo mais rápido para tarefas de classificação/roteamento
ROUTER_MODEL_NAME = 'llama-3.1-8b-instant'

def gerar_resumo_ia(kpis_tendencia: Dict[str, Any], header_atual: Dict[str, Any]) -> str: # Esta função permanece inalterada
    """
    Gera um resumo executivo em linguagem natural usando a API do Gemini.

    Args:
        kpis_tendencia (Dict[str, Any]): Dicionário com os KPIs da análise de tendência. # ... (código inalterado)
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

def gerar_resumo_analise_unica_ia(report_data: Dict[str, Any]) -> str:
    """
    Gera um resumo executivo para uma única análise, focando nos pontos mais críticos.
    """
    if not client:
        return "A geração de resumo por IA está desativada."

    try:
        header = report_data.get('header', {})
        records = report_data.get('records', [])
        
        # Extrai os top 5 problemas mais críticos para dar contexto à IA
        top_5_problemas = sorted(records, key=lambda x: x.get('score_ponderado_final', 0), reverse=True)[:5]
        
        problemas_contexto = "\n".join(
            f"- Problema: \"{p.get('short_description')}\", Time: {p.get('assignment_group')}, Score: {p.get('score_ponderado_final', 0):.1f}"
            for p in top_5_problemas
        )

        system_prompt = """Você é um analista de operações de TI sênior. Sua tarefa é escrever um resumo executivo conciso (máximo de 3 frases) para a gestão.
1. Comece a resposta com "No período (DD/MM/YYYY a DD/MM/YYYY) analisado...", usando exatamente o valor do campo 'Período da Análise'.
2. Mencione os KPIs gerais, como o total de alertas e o número de casos únicos.
3. Analise a lista dos "Top 5 Problemas Mais Críticos" e, em vez de focar em apenas um, identifique os **temas centrais** de criticidade (ex: 'indisponibilidade de processos', 'saturação de CPU', 'falhas de aplicação').
4. Destaque os times mais afetados por esses problemas críticos. Seja direto e foque no que é acionável."""
        
        user_content = f"""
        **Dados do Período Atual:**
        - Período da Análise: {report_data.get('date_range', 'Não informado')}
        - Total de alertas analisados: {header.get('total_alertas', 'N/A')}
        - Total de casos únicos (problemas): {len(records)}
        - Risco médio dos casos: {header.get('risco_medio', 0):.2f}

        **Top 5 Problemas Mais Críticos por Score:**
        {problemas_contexto}

        Gere o resumo executivo.
        """

        chat_completion = client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}], model=MODEL_NAME)
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Erro ao gerar resumo de análise única com IA: {e}")
        return f"Ocorreu um erro ao gerar o resumo da IA para esta análise. Detalhes: {e}"

# =============================================================================
# ARQUITETURA DO AGENTE (BASEADA EM FERRAMENTAS)
# =============================================================================

def project_docs_tool(question: str, chat_history: List[Dict[str, str]]) -> str:
    """Ferramenta para responder perguntas sobre o funcionamento e arquitetura do projeto."""
    project_docs = get_docs_content()
    system_prompt = """Você é um especialista sênior no projeto 'meu-dash'. Sua única fonte de conhecimento é a documentação fornecida. Responda às perguntas do usuário de forma clara e concisa, baseando-se estritamente neste contexto e no histórico da conversa. Se a resposta não estiver na documentação, informe que não possui essa informação."""
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": f"**Documentação do Projeto (Contexto):**\n{project_docs}\n\n**Nova Pergunta do Usuário:** \"{question}\""})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=MODEL_NAME,
    )
    return chat_completion.choices[0].message.content

def data_analysis_tool(question: str, report_id: Optional[int] = None, chat_history: List[Dict[str, str]] = []) -> str:
    """Ferramenta para responder perguntas sobre os dados de um relatório de análise."""
    from .app import Report # Importação local para evitar dependência circular

    # Lógica para selecionar o relatório mais recente se nenhum ID for fornecido
    if report_id:
        report = Report.query.get(report_id)
    else:
        print("ℹ️ Nenhum report_id fornecido. Buscando o relatório mais recente.")
        report = Report.query.order_by(Report.timestamp.desc()).first()

    if not report or not report.json_summary_path or not os.path.exists(report.json_summary_path):
        return "Não foi possível encontrar um relatório de análise para responder à sua pergunta. Por favor, processe um arquivo primeiro."

    with open(report.json_summary_path, 'r', encoding='utf-8') as f:
        report_data_json = f.read()

    system_prompt = """Você é um analista de dados sênior especialista em operações de TI. Sua tarefa é responder perguntas sobre um relatório de análise de alertas, considerando o histórico da conversa.
- Use apenas os dados do JSON fornecido como sua única fonte da verdade.
- Responda de forma concisa e direta.
- Se a pergunta não puder ser respondida com os dados, informe que não possui a informação no relatório.
- Os dados estão em um JSON com duas chaves principais: 'header' (com KPIs gerais) e 'records' (uma lista de todos os 'casos' analisados).
- Preste atenção aos campos de cada registro, como 'assignment_group' (time), 'score_ponderado_final' (criticidade), 'alert_count' (volume), e 'acao_sugerida'.
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": f"**Dados do Relatório (Contexto JSON):**\n```json\n{report_data_json}\n```\n\n**Nova Pergunta do Usuário:** \"{question}\""})
    
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=MODEL_NAME,
    )
    return chat_completion.choices[0].message.content

def get_tools() -> List[Dict[str, Any]]:
    """Define a lista de ferramentas que o agente pode usar."""
    return [
        {
            "name": "project_documentation_expert",
            "description": "Use esta ferramenta para perguntas sobre o funcionamento do projeto, arquitetura, código, Flask, Kubernetes, Docker, ou como usar a aplicação.",
            "function": project_docs_tool,
        },
        {
            "name": "data_analysis_expert",
            "description": "Use esta ferramenta para perguntas sobre dados, relatórios, KPIs, números, tendências, 'casos', 'alertas', 'times' ou 'squads'.",
            "function": data_analysis_tool,
        },
    ]

def route_to_tool(question: str, tools: List[Dict[str, Any]]) -> Optional[Union[Dict[str, Any], str]]:
    """
    Usa o LLM para decidir qual ferramenta é a mais apropriada para a pergunta.
    """
    if not client:
        return None

    tool_descriptions = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tools])
    
    system_prompt = f"""Sua tarefa é rotear a pergunta do usuário para a ferramenta correta.
Responda apenas com o nome da ferramenta escolhida. As ferramentas disponíveis são:
{tool_descriptions}

Se a pergunta for uma saudação ou conversa informal (oi, olá, tudo bem?), responda com 'greeting'.
Se nenhuma ferramenta parecer adequada, responda com 'fallback'.
"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            model=ROUTER_MODEL_NAME,
            temperature=0.0,
        )
        chosen_tool_name = chat_completion.choices[0].message.content.strip()
        
        for tool in tools:
            if tool['name'] == chosen_tool_name:
                return tool
        
        # Retorna uma string para casos especiais
        if chosen_tool_name in ['greeting', 'fallback']:
            return chosen_tool_name
        
        return "fallback" # Segurança

    except Exception as e:
        print(f"⚠️ Erro ao rotear pergunta, usando fallback. Erro: {e}")
        return "fallback"

def ask_unified_agent(question: str, report_id: Optional[int] = None, chat_history: List[Dict[str, str]] = []) -> str:
    """
    Ponto de entrada unificado que roteia a pergunta para a ferramenta correta e a executa.
    """
    if not client:
        return "A funcionalidade de chat com IA está desativada pois a chave de API (GROQ_API_KEY) não foi configurada."

    tools = get_tools()
    chosen_tool = route_to_tool(question, tools)

    if not chosen_tool:
        # Fallback caso o roteador falhe
        return "Desculpe, não consegui decidir como processar sua pergunta. Tente reformulá-la."

    tool_name = chosen_tool if isinstance(chosen_tool, str) else chosen_tool.get("name")
    print(f"🤖 Pergunta roteada para a ferramenta: {tool_name}")

    try:
        if tool_name == "greeting":
            return ("Olá! Sou seu agente de IA. Estou pronto para ajudar. Você pode me fazer perguntas sobre os dados do relatório "
                    "(ex: 'Qual time teve mais casos?') ou sobre o funcionamento do projeto (ex: 'Como o Kubernetes é usado aqui?'). "
                    "Como posso te ajudar agora?")

        elif isinstance(chosen_tool, dict) and tool_name == "project_documentation_expert":
            return chosen_tool["function"](question, chat_history=chat_history)

        elif isinstance(chosen_tool, dict) and tool_name == "data_analysis_expert":
            # Passa o report_id para a ferramenta de análise de dados
            return chosen_tool["function"](question, report_id=report_id, chat_history=chat_history)

        else: # Fallback
            return "Não tenho certeza de como responder a essa pergunta. Você pode perguntar sobre os dados do relatório ou sobre o funcionamento do projeto."

    except Exception as e:
        print(f"❌ Erro ao executar a ferramenta '{tool_name}': {e}")
        return f"Ocorreu um erro ao processar sua pergunta. Detalhes: {e}"
