#!/usr/bin/env python3
"""OpenAI ChatGPT Pro/Plus headless login (Device Code Flow).

Run this script manually to obtain initial OAuth tokens for subscription mode.
The tokens are written to the .env file so the proxy can use them.

Usage:
    uv run python common/get_token_init.py
"""

import base64
import json
import re
import sys
import time
from pathlib import Path

import httpx

# ── Constants (from opencode codex.ts) ────────────────────────────────────────

CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
ISSUER = "https://auth.openai.com"
DEVICE_USERCODE_URL = f"{ISSUER}/api/accounts/deviceauth/usercode"
DEVICE_TOKEN_URL = f"{ISSUER}/api/accounts/deviceauth/token"
OAUTH_TOKEN_URL = f"{ISSUER}/oauth/token"
DEVICE_AUTH_PAGE = f"{ISSUER}/codex/device"
DEVICE_REDIRECT_URI = f"{ISSUER}/deviceauth/callback"
POLLING_SAFETY_MARGIN = 3  # seconds

ENV_PATH = Path(__file__).parent.parent / ".env"

# ANSI colors
_RED = "\033[1;31m"
_GREEN = "\033[1;32m"
_BLUE = "\033[1;34m"
_YELLOW = "\033[1;33m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


# ── JWT helpers ───────────────────────────────────────────────────────────────

def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload of a JWT without signature verification."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid JWT: expected 3 parts, got {len(parts)}")
    payload_b64 = parts[1]
    # base64url padding
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def _extract_account_id(tokens: dict) -> str | None:
    """Extract chatgpt_account_id from id_token or access_token JWT."""
    for key in ("id_token", "access_token"):
        raw = tokens.get(key)
        if not raw:
            continue
        try:
            claims = _decode_jwt_payload(raw)
        except Exception:
            continue
        account_id = (
            claims.get("chatgpt_account_id")
            or claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
        )
        if not account_id:
            orgs = claims.get("organizations")
            if orgs and len(orgs) > 0:
                account_id = orgs[0].get("id")
        if account_id:
            return account_id
    return None


def _extract_client_id(tokens: dict) -> str | None:
    """Extract client_id from access_token JWT payload."""
    raw = tokens.get("access_token")
    if not raw:
        return None
    try:
        claims = _decode_jwt_payload(raw)
        return claims.get("client_id")
    except Exception:
        return None


# ── .env file helpers ─────────────────────────────────────────────────────────

def _update_env_file(env_path: Path, updates: dict[str, str]) -> None:
    """Update key=value pairs in a .env file, preserving comments and order."""
    if not env_path.exists():
        env_path.write_text("", encoding="utf-8")

    content = env_path.read_text(encoding="utf-8")

    for key, value in updates.items():
        pattern = rf"^#?\s*({re.escape(key)})=.*$"
        if re.search(pattern, content, flags=re.MULTILINE):
            content = re.sub(
                pattern,
                lambda _m, k=key, v=value: f"{k}={v}",
                content,
                flags=re.MULTILINE,
            )
        else:
            if not content.endswith("\n"):
                content += "\n"
            content += f"{key}={value}\n"

    env_path.write_text(content, encoding="utf-8")


# ── Device Code Flow ──────────────────────────────────────────────────────────

def step1_request_device_code(client: httpx.Client) -> dict:
    """POST /api/accounts/deviceauth/usercode → {device_auth_id, user_code, interval}"""
    print(f"\n{_BLUE}[1/3] Requesting device code...{_RESET}")

    resp = client.post(
        DEVICE_USERCODE_URL,
        json={"client_id": CLIENT_ID},
        timeout=30.0,
    )
    if resp.status_code != 200:
        print(f"{_RED}Failed to get device code: HTTP {resp.status_code}{_RESET}")
        print(resp.text)
        sys.exit(1)

    data = resp.json()
    return data


def step2_poll_for_authorization(client: httpx.Client, device_auth_id: str, user_code: str, interval: int) -> dict:
    """Poll /api/accounts/deviceauth/token until user completes auth → {authorization_code, code_verifier}"""
    print(f"{_BLUE}[2/3] Waiting for authorization (polling every {interval + POLLING_SAFETY_MARGIN}s)...{_RESET}")

    while True:
        resp = client.post(
            DEVICE_TOKEN_URL,
            json={
                "device_auth_id": device_auth_id,
                "user_code": user_code,
            },
            timeout=30.0,
        )

        if resp.status_code == 200:
            print(f"  {_GREEN}Authorization received!{_RESET}")
            return resp.json()

        if resp.status_code not in (403, 404):
            print(f"{_RED}Unexpected response: HTTP {resp.status_code}{_RESET}")
            print(resp.text)
            sys.exit(1)

        # 403/404 = user hasn't completed auth yet
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(interval + POLLING_SAFETY_MARGIN)


def step3_exchange_tokens(client: httpx.Client, authorization_code: str, code_verifier: str) -> dict:
    """POST /oauth/token → {access_token, refresh_token, id_token, expires_in}"""
    print(f"\n{_BLUE}[3/3] Exchanging authorization code for tokens...{_RESET}")

    resp = client.post(
        OAUTH_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": DEVICE_REDIRECT_URI,
            "client_id": CLIENT_ID,
            "code_verifier": code_verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )

    if resp.status_code != 200:
        print(f"{_RED}Token exchange failed: HTTP {resp.status_code}{_RESET}")
        print(resp.text)
        sys.exit(1)

    return resp.json()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{_BOLD}=== OpenAI ChatGPT Pro/Plus Headless Login ==={_RESET}")
    print(f"  Client ID: {CLIENT_ID}")
    print(f"  .env path: {ENV_PATH}\n")

    client = httpx.Client(
        headers={"User-Agent": "claude-code-gpt-5-codex/headless-login"},
    )

    try:
        # Step 1: Get device code
        device_data = step1_request_device_code(client)
        device_auth_id = device_data["device_auth_id"]
        user_code = device_data["user_code"]
        interval = max(int(device_data.get("interval", 5)), 1)

        # Show user instructions
        print(f"\n  {_BOLD}>> Open this URL in your browser:{_RESET}")
        print(f"     {_YELLOW}{DEVICE_AUTH_PAGE}{_RESET}")
        print(f"\n  {_BOLD}>> Enter this code:{_RESET}")
        print(f"     {_YELLOW}{user_code}{_RESET}\n")

        # Step 2: Poll until authorized
        auth_data = step2_poll_for_authorization(
            client, device_auth_id, user_code, interval,
        )

        # Step 3: Exchange for tokens
        tokens = step3_exchange_tokens(
            client,
            auth_data["authorization_code"],
            auth_data["code_verifier"],
        )

        # Extract values
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        account_id = _extract_account_id(tokens) or ""
        jwt_client_id = _extract_client_id(tokens) or CLIENT_ID

        try:
            payload = _decode_jwt_payload(access_token)
            expires_at = str(payload.get("exp", ""))
        except Exception:
            expires_at = str(int(time.time()) + tokens.get("expires_in", 3600))

        # Write to .env
        updates = {
            "OPENAI_API_KEY_SUBSCRIPTION": access_token,
            "OPENAI_REFRESH_KEY_SUBSCRIPTION": refresh_token,
            "OPENAI_ACCOUNT_ID": account_id,
            "OPENAI_CLIENT_ID_SUBSCRIPTION": jwt_client_id,
            "OPENAI_SUBSCRIPTION_EXPIRES_AT": expires_at,
        }
        _update_env_file(ENV_PATH, updates)

        # Summary
        print(f"\n{_GREEN}=== Login successful! ==={_RESET}\n")
        print(f"  Updated {ENV_PATH}:\n")
        for key, val in updates.items():
            display = val[:40] + "..." if len(val) > 40 else val
            print(f"    {key} = {display}")

        print(f"\n  {_BOLD}Make sure your .env also has:{_RESET}")
        print(f"    OPENAI_REQUEST=subscription")
        print(f"    ALWAYS_USE_RESPONSES_API=true")
        print(f"    ALWAYS_USE_STREAMING=true\n")

    finally:
        client.close()


if __name__ == "__main__":
    main()
