"""OpenAI OAuth token refresh module.

Refreshes the OpenAI subscription access token and updates the .env file.
"""

import base64
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

import httpx

from common.utils import ProxyError

_PROJECT_ROOT = Path(__file__).parent.parent
_DEFAULT_ENV_PATH = _PROJECT_ROOT / ".env"
_OPENAI_TOKEN_URL = "https://auth.openai.com/oauth/token"

# ANSI color codes (matching project conventions from config.py / utils.py)
_RED = "\033[1;31m"
_BLUE = "\033[1;34m"
_GREEN = "\033[1;32m"
_RESET = "\033[0m"


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode the payload (2nd part) of a JWT without signature verification."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ProxyError(f"Invalid JWT: expected 3 parts, got {len(parts)}")

    payload_b64 = parts[1]
    # Add padding for base64url decoding
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception as exc:
        raise ProxyError(f"Failed to decode JWT payload: {exc}") from exc


def _update_env_file(env_path: Path, updates: dict[str, str]) -> None:
    """Update key=value pairs in a .env file, preserving comments, blanks, and order."""
    content = env_path.read_text(encoding="utf-8")

    for key, value in updates.items():
        pattern = rf"^({re.escape(key)})=.*$"
        if re.search(pattern, content, flags=re.MULTILINE):
            # lambda with default arg to avoid late-binding issues in the loop
            content = re.sub(
                pattern,
                lambda m, v=value: f"{m.group(1)}={v}",
                content,
                flags=re.MULTILINE,
            )
        else:
            # Key not found — append to end of file
            if not content.endswith("\n"):
                content += "\n"
            content += f"{key}={value}\n"

    env_path.write_text(content, encoding="utf-8")


def _rollback(env_path: Path, backup_path: Path) -> None:
    """Restore .env from backup if available."""
    try:
        if backup_path.exists():
            shutil.copy2(backup_path, env_path)
            backup_path.unlink()
            print(f"{_BLUE}Rolled back .env from backup.{_RESET}")
        else:
            print(f"{_RED}Warning: backup file not found, cannot rollback.{_RESET}")
    except Exception as exc:
        print(f"{_RED}Rollback failed: {exc}{_RESET}")


def refresh_openai_token(env_path: Path | None = None) -> dict[str, str]:
    """Refresh OpenAI subscription token and update .env file.

    Returns a dict of the 5 updated key-value pairs.
    """
    if env_path is None:
        env_path = _DEFAULT_ENV_PATH
    backup_path = env_path.parent / ".env.backup"

    # 1. Read required env vars
    client_id = os.getenv("OPENAI_CLIENT_ID_SUBSCRIPTION")
    refresh_token = os.getenv("OPENAI_REFRESH_KEY_SUBSCRIPTION")
    if not client_id or not refresh_token:
        raise ProxyError(
            "Missing required env vars: "
            "OPENAI_CLIENT_ID_SUBSCRIPTION and/or OPENAI_REFRESH_KEY_SUBSCRIPTION"
        )

    # 2. Backup .env
    try:
        shutil.copy2(env_path, backup_path)
    except Exception as exc:
        raise ProxyError(f"Failed to backup .env: {exc}") from exc

    # 3. Request new token
    try:
        response = httpx.post(
            _OPENAI_TOKEN_URL,
            json={
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "openid profile email",
            },
            timeout=30.0,
        )
    except Exception as exc:
        _rollback(env_path, backup_path)
        raise ProxyError(f"Token request failed: {exc}") from exc

    # 4. Check response status
    if response.status_code != 200:
        _rollback(env_path, backup_path)
        raise ProxyError(
            f"Token request returned HTTP {response.status_code}: {response.text}"
        )

    # 5. Parse response JSON
    try:
        data = response.json()
        access_token = data["access_token"]
        new_refresh_token = data["refresh_token"]
    except Exception as exc:
        _rollback(env_path, backup_path)
        raise ProxyError(f"Failed to parse token response: {exc}") from exc

    # 6. Decode JWT payload to extract identity fields
    try:
        payload = _decode_jwt_payload(access_token)
        jwt_client_id = payload["client_id"]
        auth_info = payload.get("https://api.openai.com/auth", {})
        chatgpt_account_id = auth_info["chatgpt_account_id"]
        expires_at = str(payload["exp"])
    except ProxyError:
        _rollback(env_path, backup_path)
        raise
    except Exception as exc:
        _rollback(env_path, backup_path)
        raise ProxyError(f"Failed to extract fields from JWT: {exc}") from exc

    # 7. Update .env file
    updates = {
        "OPENAI_API_KEY_SUBSCRIPTION": access_token,
        "OPENAI_ACCOUNT_ID": chatgpt_account_id,
        "OPENAI_REFRESH_KEY_SUBSCRIPTION": new_refresh_token,
        "OPENAI_CLIENT_ID_SUBSCRIPTION": jwt_client_id,
        "OPENAI_SUBSCRIPTION_EXPIRES_AT": expires_at,
    }
    try:
        _update_env_file(env_path, updates)
    except Exception as exc:
        _rollback(env_path, backup_path)
        raise ProxyError(f"Failed to update .env: {exc}") from exc

    # 8. Update in-memory environment
    for key, value in updates.items():
        os.environ[key] = value

    # 9. Clean up backup (non-critical)
    try:
        backup_path.unlink()
    except Exception as exc:
        print(f"{_RED}Warning: failed to remove backup: {exc}{_RESET}")

    return updates


if __name__ == "__main__":
    import litellm  # noqa: F401 — triggers load_dotenv()

    try:
        result = refresh_openai_token()
        print(f"{_GREEN}Token refreshed successfully:{_RESET}")
        for k, v in result.items():
            print(f"  {k} = {v[:20]}...")
    except ProxyError as e:
        print(f"{_RED}Token refresh failed: {e}{_RESET}")
        raise SystemExit(1) from e
