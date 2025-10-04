
import os
import json
import google.generativeai as genai
from typing import Dict, Any

# Configure the Gemini API client
# IMPORTANT: The API key should be set as an environment variable for security.
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  Aviso: A variável de ambiente GEMINI_API_KEY não foi definida. A geração de resumo por IA será desativada.")
        genai.configure(api_key="DUMMY_KEY_FOR_INITIALIZATION") # Avoid crashing if key is missing
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    print(f"❌ Erro ao configurar a API do Gemini: {e}")


def ask_question_to_agent(question: str, report_data_json: str) -> str:
    """
    Envia uma pergunta para a IA do Gemini com o contexto de um relatório.

    Args:
        question (str): A pergunta do usuário.
        report_data_json (str): Uma string JSON contendo os dados do relatório ('header' e 'records').

    Returns:
        str: A resposta gerada pela IA.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        return "A funcionalidade de chat com IA está desativada pois a chave de API (GEMINI_API_KEY) não foi configurada."

    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # Carrega o JSON para garantir que está bem formatado e para extrair informações
        report_data = json.loads(report_data_json)
        header = report_data.get('header', {})
        records_preview = report_data.get('records', [])[:3] # Pega uma amostra dos registros

        prompt = f"""
        Você é um analista de dados especialista em operações de TI e está respondendo a perguntas sobre um relatório de alertas.
        Seja conciso e direto ao ponto. Use os dados fornecidos como a única fonte da verdade para sua resposta.

        **Contexto do Relatório (Resumo):**
        - Total de Alertas no período: {header.get('total_alertas', 'N/A')}
        - Risco Médio dos Casos: {header.get('risco_medio', 0):.2f}
        - Ineficiência Média da Automação: {header.get('ineficiencia_media', 0):.2f}
        - Impacto Médio (volume): {header.get('impacto_medio', 0):.2f}

        **Amostra dos Dados (Primeiros 3 de {len(report_data.get('records', []))} casos):**
        ```json
        {json.dumps(records_preview, indent=2, default=str)}
        ```

        **Pergunta do Usuário:** "{question}"

        Responda à pergunta do usuário com base nos dados fornecidos. Se a pergunta não puder ser respondida com os dados, informe que não possui essa informação.
        """
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"❌ Erro ao chamar a API do Gemini na função de chat: {e}")
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
    if not os.environ.get("GEMINI_API_KEY"):
        return "A geração de resumo por IA está desativada pois a chave de API (GEMINI_API_KEY) não foi configurada."

    try:
        model = genai.GenerativeModel('gemini-pro')

        # Construir um prompt detalhado para a IA
        prompt = f"""
        Você é um analista de operações de TI sênior e sua tarefa é escrever um resumo executivo conciso e direto ao ponto para a gestão.
        Com base nos seguintes dados de análise de alertas, gere um parágrafo curto (máximo de 4 frases) que destaque os pontos mais importantes.

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

        **Instruções:**
        1. Comece com o resultado principal: o saldo de casos em aberto aumentou ou diminuiu?
        2. Mencione a taxa de resolução e o que ela significa (boa ou ruim).
        3. Destaque o número de novos casos como um indicador de novos problemas.
        4. Seja claro e evite jargões técnicos. O público é gerencial.
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"❌ Erro ao chamar a API do Gemini: {e}")
        return f"Ocorreu um erro ao gerar o resumo da IA. Detalhes: {e}"
