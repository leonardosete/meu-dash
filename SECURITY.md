# Security Policy

## Versões Suportadas

Atualmente, apenas a última versão do projeto recebe recenteizações de segurança.

| Versão | Suportada          |
| ------ | ------------------ |
| latest | :white_check_mark: |
| < latest | :x:              |

## Práticas de Segurança

Este projeto utiliza o [GitHub CodeQL](https://docs.github.com/pt/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql) para realizar Análise Estática de Segurança de Aplicação (SAST) de forma automatizada. As varreduras são executadas:

- **Em cada push e pull request**: Para as branches `main` e `develop`, garantindo que novas alterações sejam analisadas continuamente.
- **Semanalmente**: Para detectar proativamente quaisquer vulnerabilidades que possam ter surgido.

Essa abordagem nos ajuda a identificar e corrigir possíveis falhas de segurança de forma precoce no ciclo de desenvolvimento.

## Reportando uma Vulnerabilidade

A segurança do projeto é levada a sério. Se você descobrir uma vulnerabilidade de segurança, por favor reporte-a de forma responsável.

### Como Reportar

1. **Reporte Privado (Recomendado)**: Utilize o recurso de Private Vulnerability Reporting do GitHub:
   - Acesse a aba Security do repositório
   - Clique em "Report a vulnerability" ou "Advisories"
   - Preencha o formulário com detalhes da vulnerabilidade

2. **Email Direto**: Se preferir, envie um email para o mantenedor do repositório com:
   - Descrição detalhada da vulnerabilidade
   - Passos para reproduzir o problema
   - Possível impacto de segurança
   - Sugestões de correção (se houver)

### O que Esperar

- **Confirmação**: Você receberá uma confirmação do recebimento em até 48 horas
- **Análise**: A vulnerabilidade será analisada e validada
- **Atualização**: Você receberá recenteizações sobre o progresso da correção
- **Divulgação**: Após a correção, a vulnerabilidade será divulgada publicamente com os devidos créditos

### Política de Divulgação

- Pedimos que NÃO divulgue publicamente a vulnerabilidade antes da correção
- Trabalharemos para corrigir vulnerabilidades críticas o mais rápido possível
- Daremos o crédito apropriado aos pesquisadores que reportarem vulnerabilidades de forma responsável

Obrigado por ajudar a manter este projeto seguro!
