
import os
import json
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

# Modelo recomendado para velocidade e custo-benefício no Groq
MODEL_NAME = 'llama-3.3-70b-versatile'
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
