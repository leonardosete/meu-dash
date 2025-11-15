#!/bin/bash
set -euo pipefail
REPO="leonardosete/meu-dash"

declare -a KEYS=(DOCKERHUB_USERNAME DOCKERHUB_TOKEN SECRET_KEY DATABASE_URL ADMIN_USER ADMIN_PASSWORD GH_APP_ID GH_APP_INSTALLATION_ID GH_APP_PRIVATE_KEY)

for k in "${KEYS[@]}"; do
  v="${!k:-}";
  if [[ -z "$v" ]]; then
    echo "⚠️  Variável $k não exportada, pulando." >&2
    continue
  fi
  echo -n "$v" | gh secret set "$k" --repo "$REPO"
  echo "✅ Secret $k atualizado";
done
echo "Concluído."
