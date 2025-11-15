import os
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import requests

logger = logging.getLogger(__name__)


class GitHubAppTokenProvider:
    """Gera e faz cache de tokens de instalação para um GitHub App."""

    _TOKEN_BUFFER_SECONDS = 60  # margem para evitar expiração em requests simultâneos

    def __init__(self) -> None:
        self._app_id = os.getenv("GH_APP_ID")
        self._installation_id = os.getenv("GH_APP_INSTALLATION_ID")
        self._private_key = self._load_private_key()
        self._cached_token: Optional[str] = None
        self._cached_expiration_ts: Optional[float] = None

    @staticmethod
    def _load_private_key() -> Optional[str]:
        key = os.getenv("GH_APP_PRIVATE_KEY")
        if key:
            # Permite armazenar a chave no env com \n escapado.
            return key.replace("\\n", "\n")
        key_path = os.getenv("GH_APP_PRIVATE_KEY_PATH")
        if key_path and os.path.exists(key_path):
            with open(key_path, "r", encoding="utf-8") as fh:
                return fh.read()
        return None

    def is_configured(self) -> bool:
        return bool(self._app_id and self._installation_id and self._private_key)

    def get_installation_token(self) -> Optional[str]:
        if not self.is_configured():
            logger.error(
                "GitHub App não configurado corretamente (verifique GH_APP_ID, "
                "GH_APP_INSTALLATION_ID e chave privada)."
            )
            return None

        if self._cached_token and self._cached_expiration_ts:
            if time.time() < self._cached_expiration_ts - self._TOKEN_BUFFER_SECONDS:
                return self._cached_token

        try:
            jwt_token = self._generate_app_jwt()
            token, expires_at = self._request_installation_token(jwt_token)
            self._cached_token = token
            self._cached_expiration_ts = expires_at
            return token
        except Exception:
            logger.exception("Falha ao obter token do GitHub App.")
            self._cached_token = None
            self._cached_expiration_ts = None
            return None

    def _generate_app_jwt(self) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "iat": int(now.timestamp())
            - 30,  # antecipa levemente para evitar clock skew
            "exp": int((now + timedelta(minutes=10)).timestamp()),
            "iss": self._app_id,
        }
        return jwt.encode(payload, self._private_key, algorithm="RS256")

    def _request_installation_token(self, jwt_token: str) -> tuple[str, float]:
        url = (
            f"https://api.github.com/app/installations/{self._installation_id}/"
            "access_tokens"
        )
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code != 201:
            raise RuntimeError(
                f"GitHub retornou status {response.status_code}: {response.text}"
            )
        data = response.json()
        token = data.get("token")
        expires_at_str = data.get("expires_at")
        if not token or not expires_at_str:
            raise RuntimeError("Resposta do GitHub não contém 'token' ou 'expires_at'.")
        expires_at_iso = expires_at_str.replace("Z", "+00:00")
        expires_at = datetime.fromisoformat(expires_at_iso)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return token, expires_at.timestamp()


# Instância única reutilizada pela aplicação Flask.
provider = GitHubAppTokenProvider()
