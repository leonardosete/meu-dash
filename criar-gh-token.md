# 📝 Como Criar Token do GitHub para Feedback

## 🎯 **Objetivo**

Criar um Personal Access Token (PAT) do GitHub com permissões mínimas necessárias para que o mecanismo de feedback possa criar issues automaticamente no repositório.

## ⚠️ **Importante**

- O token será usado apenas para criar issues públicas
- Guarde o token em local seguro (não commite no código)
- Configure como variável de ambiente `GITHUB_TOKEN`

---

## 📋 **Passo a Passo**

### 1. **Acesse as Configurações do GitHub**

1. Abra o navegador e vá para [github.com](https://github.com)
2. Clique na sua foto de perfil (canto superior direito)
3. Selecione **"Settings"** no menu dropdown

### 2. **Navegue para Developer Settings**

1. Na barra lateral esquerda, role até o final
2. Clique em **"Developer settings"** (última opção)

### 3. **Acesse Personal Access Tokens**

1. No menu lateral esquerdo, clique em **"Personal access tokens"**
2. Clique na aba **"Tokens (classic)"**

### 4. **Gere um Novo Token**

1. Clique no botão **"Generate new token"**
2. Selecione **"Generate new token (classic)"**

### 5. **Configure o Token**

Preencha os campos da seguinte forma:

#### **Token Name**

```
meu-dash-feedback
```

#### **Expiration**

- Recomendado: **"No expiration"** (ou defina uma data longa se preferir rotação)

#### **Scopes/Permissões**

Marque APENAS os seguintes scopes (mínimo necessário):

**Para repositório público:**

- ✅ `public_repo` - Read/write access to public repositories

**Para repositório privado:**

- ✅ `repo` - Full control of private repositories

> **Nota:** Se o repositório for público, use apenas `public_repo`. Se for privado, use `repo`.

### 6. **Gere e Copie o Token**

1. Clique no botão **"Generate token"** (no final da página)
2. **IMPORTANTE:** Copie o token imediatamente (ele só aparece uma vez!)
3. Guarde em local seguro (ex: gerenciador de senhas)

---

## 🔧 **Configuração no Projeto**

### **Variável de Ambiente**

Adicione ao seu arquivo de configuração (`.env`, docker-compose, ou Kubernetes secrets):

```bash
# Token do GitHub para feedback
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### **Variáveis Opcionais**

Se necessário, ajuste o repositório alvo:

```bash
# Proprietário do repositório (padrão: leonardosete)
GITHUB_REPO_OWNER=leonardosete

# Nome do repositório (padrão: meu-dash)
GITHUB_REPO_NAME=meu-dash
```

---

## 🧪 **Teste do Token**

### **Teste Manual via cURL**

```bash
curl -H "Authorization: token SEU_TOKEN_AQUI" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user
```

**Resposta esperada:** Seus dados do GitHub em JSON.

### **Teste da Funcionalidade**

1. Inicie a aplicação
2. Abra o modal de feedback
3. Envie um feedback de teste
4. Verifique se uma issue foi criada no repositório

---

## 🔒 **Segurança**

### **Boas Práticas**

- ✅ Use apenas as permissões mínimas necessárias
- ✅ Não commite o token no código
- ✅ Use variáveis de ambiente
- ✅ Configure rotação periódica se desejar
- ✅ Monitore uso do token nos logs do GitHub

### **Revogação**

Para revogar o token:

1. Vá para **Settings → Developer settings → Personal access tokens**
2. Localize o token `meu-dash-feedback`
3. Clique em **"Delete"**

---

## 🚨 **Troubleshooting**

### **Erro: "Bad credentials"**

- Verifique se o token foi copiado corretamente
- Confirme que não expirou
- Certifique-se de que tem as permissões corretas

### **Erro: "Not Found"**

- Verifique se o `GITHUB_REPO_OWNER` e `GITHUB_REPO_NAME` estão corretos
- Confirme que o repositório existe e é acessível

### **Erro: "Validation Failed"**

- Verifique se os dados do feedback estão válidos
- Confirme que o repositório permite criação de issues

---

## 📞 **Suporte**

Se encontrar problemas:

1. Verifique os logs da aplicação
2. Teste a API do GitHub manualmente
3. Consulte a [documentação oficial do GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

**✅ Token criado com sucesso?** Agora o mecanismo de feedback está totalmente funcional!</content>
<parameter name="filePath">/Users/leonardosete/meu-dash/criar-gh-token.md
