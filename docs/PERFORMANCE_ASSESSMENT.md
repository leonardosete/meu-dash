# Avaliação de Performance — SmartRemedy

Data: 2025-11-06
Autor: Análise automática (agente)

## Objetivo

Documento que consolida o diagnóstico da arquitetura atual do backend (`backend/`) e recomendações práticas para evitar problemas de performance ao processar os CSVs, escalar análises e manter a responsividade da API.

## Resumo executivo

- O PostgreSQL atualmente armazena apenas metadados (modelos `Report` e `TrendAnalysis`). Os dados analíticos (linhas dos CSVs) são processados em memória com pandas e gravados como artefatos (CSV/JSON/HTML) no filesystem.
- Com este padrão, o PostgreSQL não é o gargalo imediato. O risco maior é o processamento síncrono (CPU/RAM) dentro do request que bloqueia workers do Gunicorn/Flask.
- Recomenda-se mover o processamento pesado para background workers (ex.: Celery+Redis) e usar Redis também para cache de KPIs/resumos. Ajustes de pooling/índices no Postgres são recomendados como medidas de robustez.

## O que eu verifiquei (pontos-chave)

- Arquitetura: Flask Application Factory em `backend/src/app.py`; Gunicorn é usado em produção.
- Persistência: PostgreSQL via Flask-SQLAlchemy (modelos em `backend/src/models.py`). O DB guarda metadados (paths e timestamps), não os alertas individuais.
- Processamento: `analisar_arquivo_csv` (pandas) em `backend/src/analisar_alertas.py` é executado síncronamente por `services.process_upload_and_generate_reports` durante o upload.
- Artefatos: JSON/CSV/HTML gerados por `gerador_paginas.py` e salvos em `app.data` (`/app/data/...`).
- Dependências relevantes: `pandas`, `numpy`, `psycopg2-binary`, `Flask-SQLAlchemy`.

## Riscos de performance identificados

1. Processamento síncrono durante a requisição HTTP
   - Uploads grandes ou concorrentes bloqueiam workers; leva a timeouts e redução de throughput.
2. Uso intensivo de memória/CPU pelo pandas
   - `pd.read_csv(..., engine='python')`, operações de groupby, apply/list reduz eficiência em datasets grandes.
3. I/O e contenção de storage
   - Escrita/leitura frequente de JSON/CSV/HTML em volume compartilhado pode causar latência se o storage for NFS ou houver vários pods usando o mesmo disco.
4. Concorrência de conexões ao Postgres
   - Se escalar número de workers para tentar paralelizar processamento, aumentarão conexões simultâneas; sem pool/pgBouncer, o Postgres pode sofrer.

## Quando o PostgreSQL pode se tornar gargalo

- Se vocês mudarem a estratégia e decidirem persistir todas as linhas dos CSVs no Postgres e executar agregações no banco em alto volume (milhões de linhas), será necessário:
  - Índices corretos
  - Particionamento (por data, por run)
  - Tuning de recursos (CPU/RAM/IO)
  - Pooling (pgBouncer) para gerenciar muitas conexões
- Com o uso atual (metadados apenas), Postgres não é a prioridade para otimização.

## Necessidade de Redis (quando vale a pena)

1. Broker de tarefas (alto benefício) — recomendado
   - Celery (ou RQ) com Redis como broker para mover `process_upload_and_generate_reports` para background.
   - API devolve job id, worker processa análise, grava DB/artifacts e notifica (webhook/polling).
2. Cache de resultados e KPIs (recomendado)
   - Cachear `kpi_summary` / `get_dashboard_summary_data` por 30s-5m para reduzir leituras/discos repetidas.
3. Locks/coordenação/rate-limiting (opcional)
   - Evitar execução duplicada para o mesmo run, controlar concorrência.

## MongoDB? Vale a pena migrar?

- Com a arquitetura atual (processamento analítico em pandas e persistência de metadados), MongoDB não traz vantagem clara.
- MongoDB é útil quando:
  - Dados são semi-estruturados e muitas consultas por documento são feitas;
  - Você precisa de esquema flexível para cada alerta como documento e consultas orientadas a documentos.
- Para análises e agregações tabulares (groupby/joins/aggregates), Postgres (ou uma solução OLAP como ClickHouse) é mais apropriado.
- Conclusão: Não migrar para MongoDB só por performance; considerar outras opções (Parquet + Presto/Dremio, ClickHouse) se crescer volume analítico.

## Recomendações práticas e passo-a-passo (priorizadas)

### Prioridade Alta (implementar imediatamente)

1. Mover análise para background jobs
   - Stack sugerida: Celery + Redis.
   - Alterar `process_upload_and_generate_reports` para tarefa Celery.
   - Endpoint `/api/v1/upload` enfileira job e retorna job id/ack; worker atualiza DB e publica resultado.
2. Limitar concorrência e configurar Gunicorn/Kubernetes
   - Gunicorn: reduzir workers (cada worker consome muita memória); preferir 2-4 workers por nó com limites de recursos.
   - K8s: definir `resources.requests` e `resources.limits` (CPU/MEM) para evitar OOM.
3. Cachear `get_dashboard_summary_data`
   - Implementar cache Redis com TTL (ex: 60s) e invalidar ao inserir novo `Report`.

### Prioridade Média

1. SQLAlchemy / Postgres pooling
   - Configurar engine options: pool_size, max_overflow, pool_timeout, pool_pre_ping.
   - Alternativa: pgBouncer (transaction mode) se houver muitos workers/threads.
2. Índices no Postgres (scripts SQL)
   - `CREATE INDEX IF NOT EXISTS idx_report_timestamp ON report (timestamp DESC);`
   - `CREATE INDEX IF NOT EXISTS idx_trend_timestamp ON trend_analysis (timestamp DESC);`
3. Persistir artefatos em Object Storage
   - Use S3 / MinIO em vez de NFS para reduzir contenção e aumentar resiliência.

### Prioridade Baixa / Evolução

1. Otimizações pandas e escala vertical
   - Ler com sep explícito quando possível; definir dtypes; converter colunas para `category` antes do groupby.
   - Se CSVs excederem memoria, considerar Dask/vaex ou transformar CSVs em Parquet e usar processamento distribuído.
2. Observability e Benchmarks
   - Instrumentar tempos de cada etapa (read_csv, groupby, export_json) e expor métricas (Prometheus).
   - Criar script de benchmark com CSVs representativos para medir RAM/CPU/tempo.

## Exemplos concretos (config e comandos)

### SQLAlchemy engine options (exemplo de env)

```
SQLALCHEMY_ENGINE_OPTIONS='{"pool_size":10, "max_overflow":20, "pool_timeout":30, "pool_pre_ping":true}'
```

(ou configurar no `create_engine`/`SQLALCHEMY_DATABASE_URI` conforme sua escolha de inicialização)

### Índices SQL

```sql
CREATE INDEX IF NOT EXISTS idx_report_timestamp ON report (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trend_timestamp ON trend_analysis (timestamp DESC);
```

### Exemplo mínimo de migração para Celery (arquitetura)

- Adicionar `celery.py` com configuração Redis broker.
- Tornar `process_upload_and_generate_reports` uma tarefa Celery @shared_task.
- Endpoint `/upload` salva arquivo, envia para storage temporário e chama `celery_task.delay(filepath, run_id)`.

### Gunicorn (regra prática)

- Se processo realiza trabalho leve: workers = 2 * cores + 1.
- Se workers realizam trabalho pesado (pandas): usar menos workers por nó (ex: 1-2) e dimensionar nós adequadamente.

## Checklist rápido (para execução)

- [ ] Instrumentar etapas críticas com timers/logs.
- [ ] Implementar Celery+Redis e mover processamento para background.
- [ ] Adicionar cache Redis para KPIs e invalidação no write.
- [ ] Definir pooling SQLAlchemy ou deployar pgBouncer.
- [ ] Criar índices em timestamp e testar queries.
- [ ] Mover artefatos para S3/MinIO (opcional) e ajustar `serve_report`.
- [ ] Criar script de benchmark e rodar com CSVs representativos.

## Plano de validação (como testar)

1. Criar CSVs representativos de pequeno/medio/grande porte. Medir tempo e RAM por etapa.
2. Implantar Celery workers e simular N uploads concorrentes; observar fila, throughput e latência de resposta da API.
3. Monitorar Postgres conexões e I/O; ajustar pool_size/pgBouncer.
4. Repetir testes com artifacts em S3 vs NFS para medir diferenças de I/O.

## Próximos passos (o que posso implementar agora)

Opções oferecidas (escolha uma):

- A) Proof-of-concept Celery+Redis: adiciono código básico e task wrapper.
- B) Cache Redis para `get_dashboard_summary` e invalidação ao gerar novo relatório.
- C) Instrumentação mínima e script de benchmark (gera números para decidir escala).
- D) Gerar PR com mudanças de configuração (Gunicorn, SQLAlchemy, índices SQL) e instruções de deploy.

---

Se quiser, começo pela opção que você escolher e crio os arquivos/PRs aqui no repositório. Também registrei esta ação no diário do projeto.
