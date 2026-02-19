import os
from pathlib import Path

import litellm
from common import config as common_config  # Makes sure .env is loaded  # pylint: disable=unused-import
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
RESPAPI_ONLY_MODELS = (
    "codex-mini-latest",
    "computer-use-preview",
    "gpt-5-codex",
    "gpt-5-pro",
    "gpt-5.1-codex",
    "gpt-5.1-codex-mini",
    "gpt-5.3-codex",
    "gpt-oss-120b",
    "gpt-oss-20b",
    "o1-pro",
    "o3-deep-research",
    "o3-pro",
    "o4-mini-deep-research",
)

OPENAI_REQUEST = os.getenv("OPENAI_REQUEST", "api")
OPENAI_API_KEY_SUBSCRIPTION = os.getenv("OPENAI_API_KEY_SUBSCRIPTION")
OPENAI_ACCOUNT_ID = os.getenv("OPENAI_ACCOUNT_ID")

_CODEX_INSTRUCTIONS_PATH = Path(__file__).parent / "codex_instructions.txt"
CODEX_SUBSCRIPTION_INSTRUCTIONS = _CODEX_INSTRUCTIONS_PATH.read_text(encoding="utf-8").strip()

ANTHROPIC = "anthropic"
OPENAI = "openai"

# Register models that litellm doesn't know about yet, so that it doesn't
# fall back to fake-streaming (which strips "stream" from the request body
# and breaks the ChatGPT subscription endpoint).
_OPENAI_CODEX_MODEL_DEFAULTS = {
    "max_input_tokens": 128000,
    "max_output_tokens": 128000,
    "max_tokens": 128000,
    "mode": "responses",
    "supported_endpoints": ["/v1/responses"],
    "supports_native_streaming": True,
    "supports_function_calling": True,
    "supports_parallel_function_calling": True,
    "supports_vision": True,
}
_MODELS_TO_REGISTER = {
    model: _OPENAI_CODEX_MODEL_DEFAULTS
    for model in RESPAPI_ONLY_MODELS
    if model not in litellm.model_cost
}
if _MODELS_TO_REGISTER:
    litellm.register_model(_MODELS_TO_REGISTER)
