import os
from pathlib import Path

import litellm
from common import config as common_config  # Makes sure .env is loaded  # pylint: disable=unused-import
from common.refresh import ensure_token_fresh
from common.utils import env_var_to_bool


# NOTE: If any of the three env vars below are set to an empty string, the
# defaults will NOT be used. The defaults are used only when these env vars are
# not set at all. This is intentional - setting them to empty strings should
# result in no remapping.
REMAP_CLAUDE_HAIKU_TO = os.getenv("REMAP_CLAUDE_HAIKU_TO", "gpt-5.1-codex-mini-reason-none")
REMAP_CLAUDE_SONNET_TO = os.getenv("REMAP_CLAUDE_SONNET_TO", "gpt-5-codex-reason-medium")
REMAP_CLAUDE_OPUS_TO = os.getenv("REMAP_CLAUDE_OPUS_TO", "gpt-5.1-reason-high")

ENFORCE_ONE_TOOL_CALL_PER_RESPONSE = env_var_to_bool(os.getenv("ENFORCE_ONE_TOOL_CALL_PER_RESPONSE"), "true")

# TODO Move these two constants to common/config.py ?
ALWAYS_USE_RESPONSES_API = env_var_to_bool(os.getenv("ALWAYS_USE_RESPONSES_API"), "false")
ALWAYS_USE_STREAMING = env_var_to_bool(os.getenv("ALWAYS_USE_STREAMING"), "false")
SYSTEM_REMINDER_REMOVE = env_var_to_bool(os.getenv("SYSTEM_REMINDER_REMOVE"), "false")

OPENAI_REQUEST = os.getenv("OPENAI_REQUEST", "api")

ensure_token_fresh()

OPENAI_API_KEY_SUBSCRIPTION = os.getenv("OPENAI_API_KEY_SUBSCRIPTION")
OPENAI_ACCOUNT_ID = os.getenv("OPENAI_ACCOUNT_ID")


def get_openai_api_key_subscription():
    return os.getenv("OPENAI_API_KEY_SUBSCRIPTION")


def get_openai_account_id():
    return os.getenv("OPENAI_ACCOUNT_ID")

_CODEX_INSTRUCTIONS_PATH = Path(__file__).parent / "codex_instructions.txt"
CODEX_SUBSCRIPTION_INSTRUCTIONS = _CODEX_INSTRUCTIONS_PATH.read_text(encoding="utf-8").strip()

ANTHROPIC = "anthropic"
OPENAI = "openai"

# When ALWAYS_USE_STREAMING is true, monkey-patch litellm so that it never
# falls back to fake-streaming (which strips "stream" from the request body
# and breaks the ChatGPT subscription endpoint).
if ALWAYS_USE_STREAMING:
    litellm.utils.supports_native_streaming = lambda model, custom_llm_provider: True
