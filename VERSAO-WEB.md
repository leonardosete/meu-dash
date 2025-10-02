1.  **O Prompt Mestre (O Escopo):** Este é o documento estratégico que você apresentará ao candidato. Ele define a visão completa do projeto, os objetivos, a arquitetura recomendada e as fases de desenvolvimento. É o seu "plano de ataque".
2.  **Os Prompts de Execução por Fase:** São os prompts detalhados, um para cada fase do projeto. Você entregará esses prompts ao desenvolvedor contratado à medida que cada fase começar. Eles contêm as tarefas específicas, os requisitos técnicos e os critérios de aceitação para cada etapa.

---

### Prompt Mestre: O Blueprint Estratégico para o Desenvolvedor

Este é o documento que você usará para contratar e alinhar as expectativas com o especialista.

***

#### **Título do Projeto: Evolução do `meu-dash` para uma Aplicação Web Containerizada com Frontend Interativo**

**Resumo da Oportunidade:**
Buscamos um Desenvolvedor Sênior Full-Stack com sólida experiência em DevOps para liderar a evolução de uma ferramenta interna de análise de dados (`meu-dash`) em uma aplicação web robusta, escalável e de fácil utilização. O candidato ideal será responsável por projetar e implementar uma interface de frontend para upload de arquivos, refatorar a lógica de backend para um serviço web, e containerizar toda a solução com Docker, preparando-a para implantação em um ambiente orquestrado com Kubernetes.

**Contexto do Projeto:**
O `meu-dash` é atualmente um conjunto de scripts Python que automatiza a análise de alertas de monitoramento a partir de arquivos `.csv`. Ele calcula um "Score de Prioridade" e gera dashboards HTML estáticos. Embora funcional, o processo atual é manual (requer execução de scripts via linha de comando) e não centralizado, dificultando o acesso a relatórios históricos e a colaboração entre equipes.

**Objetivo Principal:**
Transformar o `meu-dash` em uma aplicação web self-service que permita aos usuários fazer upload de seus próprios arquivos `.csv` e acessar um histórico de relatórios gerados, tudo através de uma interface web intuitiva e segura.

**Arquitetura Alvo e Stack Tecnológico:**
*   **Backend:** Python com o micro-framework **Flask**. A escolha se dá pela sua leveza e flexibilidade, ideal para "envolver" a lógica de negócio já existente sem a complexidade de um framework mais opinativo.[3, 4]
*   **Frontend:** HTML5, CSS3 e JavaScript vanilla. Não há necessidade de um framework complexo de frontend nesta fase.
*   **Banco de Dados:** SQLite para a fase inicial (armazenamento de metadados de relatórios), com a arquitetura permitindo a evolução para um banco de dados mais robusto como PostgreSQL.
*   **Containerização:** **Docker** e **Docker Compose** para criar um ambiente de desenvolvimento consistente e portátil.[5, 6]
*   **Orquestração:** A aplicação deve ser projetada para ser "cloud-native", com a entrega final incluindo manifestos básicos para **Kubernetes** (`Deployment` e `Service`).[7, 8]

**Fases do Projeto:**
O desenvolvimento será dividido em quatro fases claras e iterativas:

1.  **Fase 1: Prova de Conceito (PoC) - A Aplicação Web Mínima:** Estabelecer a base da aplicação web e o ambiente de containerização.
2.  **Fase 2: Integração do Core Logic e Frontend de Upload:** Implementar a funcionalidade principal de upload e processamento de arquivos.
3.  **Fase 3: Persistência e Histórico de Relatórios:** Adicionar um banco de dados para rastrear os relatórios e uma interface para visualizá-los.
4.  **Fase 4: Preparação para Produção e Kubernetes:** Otimizar a aplicação para um ambiente de produção e criar os artefatos de implantação para Kubernetes.

**O que Buscamos em um Candidato:**
*   Experiência comprovada no desenvolvimento de aplicações web com Python (Flask é um diferencial).
*   Proficiência na criação de `Dockerfiles` otimizados para produção e no uso de Docker Compose.[9, 10]
*   Compreensão sólida dos princípios de arquitetura de microsserviços e design de APIs.
*   Experiência prática com Kubernetes, incluindo a criação de manifestos de `Deployment` e `Service`.[11, 8]
*   Capacidade de trabalhar de forma autônoma, tomar decisões arquitetônicas sólidas e comunicar o progresso de forma eficaz.

***

### Prompts de Execução por Fase

Aqui estão os prompts detalhados para cada fase. Entregue-os sequencialmente ao desenvolvedor.

---

#### **Prompt para a Fase 1: Prova de Conceito (PoC) - A Aplicação Web Mínima**

**Objetivo da Fase:**
Criar a estrutura inicial da aplicação Flask, containerizá-la com Docker e garantir que o ambiente de desenvolvimento possa ser iniciado de forma consistente com Docker Compose.

**Requisitos Técnicos / Tarefas:**
1.  Inicialize uma nova aplicação Flask (`app.py`).
2.  Crie um endpoint raiz (`/`) que retorne uma simples mensagem "Olá, Mundo!" ou renderize um HTML básico.
3.  Crie um `Dockerfile` que:
    *   Utilize uma imagem base oficial e leve do Python (ex: `python:3.11-slim`).[9]
    *   Copie o código da aplicação para dentro do container.
    *   Instale as dependências listadas em um arquivo `requirements.txt`.
    *   Exponha a porta necessária para a aplicação.
4.  Crie um arquivo `docker-compose.yml` que defina um serviço para a aplicação web, construindo a imagem a partir do `Dockerfile` e mapeando a porta do container para a máquina host.
5.  Estruture o projeto de forma organizada, separando o código da aplicação (`src/`) de outros arquivos.

**Entregáveis Esperados:**
*   Arquivo `app.py` com a aplicação Flask inicial.
*   Arquivo `Dockerfile`.
*   Arquivo `docker-compose.yml`.
*   Arquivo `requirements.txt` (contendo `Flask`).

**Critérios de Aceitação:**
*   O comando `docker compose up --build` deve iniciar a aplicação sem erros.
*   Acessar `http://localhost:5000` (ou a porta mapeada) no navegador deve exibir a mensagem de boas-vindas.

---

#### **Prompt para a Fase 2: Integração do Core Logic e Frontend de Upload**

**Objetivo da Fase:**
Integrar a lógica de negócio existente do `meu-dash` na aplicação Flask e criar uma interface de frontend que permita aos usuários fazer o upload de arquivos `.csv`.

**Requisitos Técnicos / Tarefas:**
1.  Crie um template HTML (`upload.html`) com um formulário que permita o upload de um único arquivo (`<input type="file">`).
2.  Modifique o endpoint raiz (`/`) para renderizar este template.
3.  Crie um novo endpoint (`/upload`, método `POST`) para receber o arquivo enviado.
4.  Neste endpoint:
    *   Salve o arquivo `.csv` enviado em um diretório temporário (ex: `data/uploads/`).
    *   Refatore o script `analisar_alertas.py` para que sua lógica principal possa ser importada e chamada como uma função, recebendo o caminho do arquivo CSV como parâmetro.
    *   Chame esta função para processar o arquivo.
    *   Após o processamento, redirecione o usuário para uma página de sucesso ou, idealmente, diretamente para o relatório gerado.
5.  Garanta que os relatórios HTML gerados sejam salvos no diretório `reports/`, como no projeto original.

**Entregáveis Esperados:**
*   Templates HTML para o formulário de upload.
*   `app.py` atualizado com as novas rotas e lógica de integração.
*   Scripts do `meu-dash` (`analisar_alertas.py`, etc.) refatorados para serem modulares.

**Critérios de Aceitação:**
*   A página inicial exibe o formulário de upload.
*   Fazer o upload de um arquivo `.csv` válido aciona a análise e gera o dashboard HTML correspondente no diretório `reports/`.

---

#### **Prompt para a Fase 3: Persistência e Histórico de Relatórios**

**Objetivo da Fase:**
Implementar um banco de dados para armazenar metadados sobre cada relatório gerado e criar uma página para que os usuários possam visualizar e acessar relatórios anteriores.

**Requisitos Técnicos / Tarefas:**
1.  Integre o SQLite à aplicação Flask (usando uma extensão como `Flask-SQLAlchemy` é recomendado).
2.  Defina um modelo de dados (tabela) para armazenar informações sobre cada execução, como: `id`, `timestamp`, `nome_arquivo_original`, `caminho_relatorio_gerado`.
3.  Modifique o endpoint `/upload` para, após gerar um relatório com sucesso, salvar um novo registro nesta tabela.
4.  Crie um novo endpoint (`/relatorios`) que:
    *   Consulte o banco de dados para obter a lista de todos os relatórios gerados.
    *   Renderize um novo template HTML (`relatorios.html`).
5.  O template `relatorios.html` deve exibir uma tabela com os relatórios, mostrando a data e o nome do arquivo original, e um link para visualizar cada relatório HTML.
6.  Atualize o `docker-compose.yml` para montar um volume para o arquivo do banco de dados SQLite, garantindo que os dados persistam entre as reinicializações do container.

**Entregáveis Esperados:**
*   Configuração do banco de dados e modelo de dados.
*   `app.py` atualizado com a lógica de persistência e a nova rota `/relatorios`.
*   Template `relatorios.html`.
*   `docker-compose.yml` atualizado com o volume de dados.

**Critérios de Aceitação:**
*   Cada upload bem-sucedido cria um registro no banco de dados.
*   A página `/relatorios` exibe corretamente a lista de todos os relatórios processados.
*   Clicar em um link na página de relatórios abre o dashboard HTML correto.
*   Reiniciar o container com `docker compose down` e `docker compose up` não apaga o histórico de relatórios.

---

#### **Prompt para a Fase 4: Preparação para Produção e Kubernetes**

**Objetivo da Fase:**
Otimizar a aplicação e o container para um ambiente de produção e criar os manifestos necessários para a implantação no Kubernetes.

**Requisitos Técnicos / Tarefas:**
1.  Refatore o `Dockerfile` para seguir as melhores práticas de produção:
    *   Use um servidor WSGI (como **Gunicorn**) para executar a aplicação Flask, em vez do servidor de desenvolvimento padrão.[10]
    *   Execute o container com um usuário não-root por segurança.[9]
    *   Implemente um build multi-stage para criar uma imagem final menor e mais segura, sem as dependências de build.[9]
2.  Crie um arquivo `deployment.yaml` para o Kubernetes que:
    *   Defina um `Deployment` para a aplicação.
    *   Especifique o número de réplicas desejado (ex: 2).
    *   Aponte para a imagem Docker que será construída.
3.  Crie um arquivo `service.yaml` para o Kubernetes que:
    *   Defina um `Service` do tipo `LoadBalancer` ou `NodePort` para expor o `Deployment` externamente.[8]
    *   Mapeie a porta do serviço para a porta do container da aplicação.
4.  Crie uma documentação (`README.md`) atualizada explicando como construir a imagem Docker e como aplicar os manifestos do Kubernetes.

**Entregáveis Esperados:**
*   `Dockerfile` final e otimizado para produção.
*   `deployment.yaml`.
*   `service.yaml`.
*   `README.md` atualizado.

**Critérios de Aceitação:**
*   A imagem Docker de produção é construída com sucesso e é visivelmente menor que a imagem de desenvolvimento.
*   A aplicação funciona corretamente quando executada com Gunicorn.
*   Os arquivos de manifesto do Kubernetes são sintaticamente válidos e descrevem corretamente a implantação da aplicação.