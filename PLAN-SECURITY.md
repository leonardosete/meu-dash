# 🛡️ Plano de Implementação: Travas de Segurança e Administração

Este documento descreve o plano de ação para implementar uma camada de segurança na aplicação, focando em proteger funcionalidades críticas como a exclusão de relatórios.

A estratégia adotada será a **Proteção por Token de Ambiente**, que oferece um bom equilíbrio entre segurança e complexidade de implementação.

## Roadmap da Funcionalidade

### Prioridade 1: Implementação do Backend

- [x] **Configuração:**
  - Modificar `src/app.py` para ler uma nova variável de ambiente, `ADMIN_TOKEN`. Se a variável não for definida, a aplicação deve funcionar normalmente, mas com as funcionalidades de admin desativadas.

- [x] **Criação da Rota de Admin:**
  - Criar uma nova rota `/admin` em `src/app.py` que renderiza uma página de login simples (`admin_login.html`).
  - Criar uma rota `POST /admin/login` que valida se o token fornecido no formulário corresponde ao `ADMIN_TOKEN` do ambiente.
  - Usar a sessão do Flask (`flask.session`) para armazenar que o usuário está autenticado como admin.

- [x] **Proteger a Exclusão:**
  - Modificar a rota `delete_report` para verificar se o usuário está autenticado como admin (verificando a sessão) antes de permitir a exclusão. Se não estiver, redirecionar ou retornar um erro 403 (Forbidden).

### Prioridade 2: Interface do Usuário (UI)

- [x] **Criar Página de Login do Admin:**
  - Desenvolver um novo template `templates/admin_login.html` com um formulário simples para inserir o token.

- [x] **Ajustar a Página de Histórico:**
  - Modificar o template `templates/relatorios.html`. O botão "Excluir" deve ser movido ou só ser visível em uma nova página de gerenciamento acessível apenas pelo admin. A abordagem mais simples é remover o botão da visão pública e tê-lo apenas na visão do admin.

### Prioridade 3: Testes e Validação

- [x] **Criar Testes de Integração:**
  - Adicionar testes em `tests/test_integracao.py` para validar o novo fluxo:
    - Testar que o acesso à rota de exclusão sem autenticação falha.
    - Testar que o login com um token inválido falha.
    - Testar que o login com o token correto funciona e permite a exclusão.

- [x] **Teste Manual:**
  - Executar o fluxo completo: tentar excluir sem login, fazer login com token errado, fazer login com token certo e confirmar que a exclusão funciona.
  - **Resultado:** Teste bem-sucedido, identificou e levou à correção de um bug de integridade de dados na exclusão.