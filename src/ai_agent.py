
import os
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
