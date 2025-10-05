### **Prompt Estruturado para Gemini Code Assist**

**Instrução Inicial:**

Por favor, leia e analise o conteúdo do arquivo `GEMINI.md` que descreve o meu projeto. Use o contexto fornecido nesse arquivo como base para responder a todas as perguntas e solicitações a seguir.

---

**Objetivo:**

Com base no `GEMINI.md` e nas minhas anotações abaixo, preciso de ajuda para refinar a lógica de negócio, tomar decisões de arquitetura, melhorar a experiência do usuário e planejar os próximos passos do desenvolvimento.

---

#### **Parte 1: Lógica de Negócio e Validação de Dados**

Tenho uma questão crítica sobre a lógica de comparação de períodos. Atualmente, o sistema permite que o usuário defina qual arquivo CSV representa o "Período Atual" e qual representa o "Período Anterior", sem uma validação cronológica estrita das datas contidas nos arquivos.

**Cenário de Dúvida:**
* **Período Anterior:** `csv-dummy-2.csv` (contém dados de 20/10/2025 a 22/10/2025)
* **Período Atual:** `csv-dummy-1.csv` (contém dados de 20/09/2025 a 21/09/2025)

Neste cenário, o "Período Atual" tem datas cronologicamente mais antigas que o "Período Anterior", o que parece conceitualmente incorreto.

**Perguntas:**

1.  **Validação de Datas:**
    * Considerando a proposta do projeto, devo implementar uma regra de negócio que obriga o "Período Atual" a ter sempre datas posteriores ao "Período Anterior"?
    * Quais são os prós e contras de permitir essa flexibilidade versus impor uma ordem cronológica estrita? Existe algum caso de uso, dentro do escopo do meu projeto, em que um "período atual" com datas mais antigas faria sentido?
    * Poderia me fornecer um exemplo de código em Python (usando Pandas, por exemplo) para extrair as datas mínimas e máximas de dois DataFrames e validar se o intervalo de datas do "Período Atual" é de fato posterior ao do "Período Anterior"?

---

#### **Parte 2: Arquitetura e Tecnologia**

Estou avaliando o uso de Redis no meu projeto e preciso de ajuda para decidir se é a escolha correta.

**Perguntas:**

1.  **Uso do Redis:**
    * Analisando a arquitetura e o fluxo de dados descritos no `GEMINI.md`, faz sentido usar o Redis? Quais seriam os principais casos de uso para o *meu projeto*? (Ex: cache de resultados de análises, gerenciamento de sessões, fila de processamento de uploads).
    * Quais as vantagens e desvantagens de usar Redis em comparação com outras soluções (como cache em memória ou banco de dados relacional) no contexto específico da minha aplicação?

---

#### **Parte 3: Funcionalidades e Experiência do Usuário (UX)**

Preciso de orientação sobre o desenvolvimento e aprimoramento da interface do usuário e do gerenciamento das análises.

**Perguntas:**

1.  **Melhorias na Página "Home":**
    * Com base na descrição do projeto, que informações e componentes visuais seriam mais úteis para exibir na página inicial para o meu usuário? (Ex: um dashboard com o resumo da última análise, um histórico de análises recentes, um formulário de upload proeminente, gráficos de tendência).

2.  **Gerenciamento de Análises:**
    * Estou considerando implementar uma funcionalidade para deletar análises antigas. Qual seria a melhor abordagem para isso: exclusão manual pelo usuário ou um sistema automático de rotação?
    * Se eu optar por um sistema de rotação automático, que número de análises armazenadas você sugeriria como um ponto de partida razoável (ex: 5, 10, 20)? Como posso implementar a lógica para limitar o número de análises, mantendo apenas as N mais recentes?

---

#### **Parte 4: Implantação e DevOps (Kubernetes)**

Minha aplicação será implantada no Kubernetes. Tenho algumas configurações comentadas no meu arquivo `kubernetes.yaml`.

**Contexto:**
Meu arquivo `kubernetes.yaml` possui seções comentadas para `namespace` e `ingress` para evitar ter que recriar certificados TLS/SSL e entradas de DNS a cada deploy em ambiente de desenvolvimento.

**Perguntas:**

1.  **Estratégia de Deploy:**
    * Qual é a melhor prática (Kustomize, Helm, etc.) para gerenciar as configurações do meu `kubernetes.yaml` entre diferentes ambientes (desenvolvimento e produção)?
    * Poderia me fornecer um exemplo de como estruturar meu `ingress.yaml` para que seja facilmente configurável para diferentes domínios e certificados, pensando na transição de desenvolvimento para produção?

---

#### **Parte 5: Planejamento e Documentação**

Preciso organizar os próximos passos e garantir que a documentação do projeto esteja atualizada.

**Perguntas:**

1.  **Próximos Passos:**
    * Com base em todas as questões levantadas, qual seria uma sequência lógica de tarefas para eu abordar a seguir? Por favor, me ajude a criar um plano de ação ou um checklist priorizado.

2.  **Documentação:**
    * Revise a estrutura do `GEMINI.md`. Há alguma seção essencial faltando? O que mais eu deveria adicionar para tornar a documentação mais completa e útil para o futuro?