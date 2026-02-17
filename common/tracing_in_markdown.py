import json
from typing import Optional

from litellm import ModelResponse, ResponsesAPIResponse

from common.config import TRACES_DIR


def write_request_trace(  # pylint: disable=unused-argument
    *,
    timestamp: str,
    calling_method: str,
    inbound_api_base: Optional[str] = None,
    inbound_headers: Optional[dict] = None,
    outbound_api_base: Optional[str] = None,
    target_model: Optional[str] = None,
    requested_model: Optional[str] = None,
    use_responses_api: Optional[bool] = None,
    messages_original: Optional[list] = None,
    params_original: Optional[dict] = None,
    messages_complapi: Optional[list] = None,
    params_complapi: Optional[dict] = None,
    messages_respapi: Optional[list] = None,
    params_respapi: Optional[dict] = None,
) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    file = TRACES_DIR / f"{timestamp}_REQUEST.md"
    if file.exists():
        # TODO Replace with a warning instead ?
        raise FileExistsError(f"File {file} already exists")

    with file.open("w", encoding="utf-8") as f:
        f.write(f"# {calling_method.upper()}\n\n")

        f.write("## Routing Info\n\n")
        if requested_model is not None:
            f.write(f"- **Requested Model (Claude Code):** `{requested_model}`\n")
        if target_model is not None:
            f.write(f"- **Target Model (Proxy -> Provider):** `{target_model}`\n")
        if outbound_api_base is not None:
            f.write(f"- **Outbound URL (Proxy -> Provider):** `{outbound_api_base}`\n")
        if use_responses_api is not None:
            f.write(f"- **API Format:** `{'Responses API' if use_responses_api else 'ChatCompletions API'}`\n")
        if inbound_api_base is not None:
            f.write(f"- **Inbound URL (Claude Code -> Proxy):** `{inbound_api_base}`\n")
        f.write("\n")

        if inbound_headers:
            f.write("## Inbound Headers (Claude Code -> Proxy)\n\n")
            f.write(f"```json\n{json.dumps(inbound_headers, indent=2)}\n```\n\n")

        f.write("## Request Messages\n\n")

        if messages_original is not None:
            f.write("### Original (Claude Code -> Proxy):\n")
            f.write(f"```json\n{json.dumps(messages_original, indent=2)}\n```\n\n")

        if messages_complapi is not None:
            f.write("### ChatCompletions API:\n")
            f.write(f"```json\n{json.dumps(messages_complapi, indent=2)}\n```\n\n")

        if messages_respapi is not None:
            f.write("### Responses API:\n")
            f.write(f"```json\n{json.dumps(messages_respapi, indent=2)}\n```\n")

        f.write("## Request Params\n\n")

        if params_original is not None:
            f.write("### Original (Claude Code -> Proxy):\n")
            f.write(f"```json\n{json.dumps(params_original, indent=2)}\n```\n\n")

        if params_complapi is not None:
            f.write("### ChatCompletions API:\n")
            f.write(f"```json\n{json.dumps(params_complapi, indent=2)}\n```\n\n")

        if params_respapi is not None:
            f.write("### Responses API:\n")
            f.write(f"```json\n{json.dumps(params_respapi, indent=2)}\n```\n")


def write_response_trace(
    *,
    timestamp: str,
    calling_method: str,
    response_respapi: Optional[ResponsesAPIResponse] = None,
    response_complapi: Optional[ModelResponse] = None,
) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    file = TRACES_DIR / f"{timestamp}_RESPONSE.md"
    if file.exists():
        # TODO Replace with a warning instead ?
        raise FileExistsError(f"File {file} already exists")

    with file.open("w", encoding="utf-8") as f:
        f.write(f"# {calling_method.upper()}\n\n")

        f.write("## Response\n\n")

        if response_respapi is not None:
            f.write("### Responses API:\n")
            f.write(f"```json\n{response_respapi.model_dump_json(indent=2)}\n```\n\n")

        if response_complapi is not None:
            f.write("### ChatCompletions API:\n")
            f.write(f"```json\n{response_complapi.model_dump_json(indent=2)}\n```\n")


def write_streaming_chunk_trace(
    *,
    timestamp: str,
    calling_method: str,
    chunk_idx: int,
    respapi_chunk: Optional[ResponsesAPIResponse] = None,
    complapi_chunk: Optional[ModelResponse] = None,
    generic_chunk: Optional[dict] = None,
) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    file = TRACES_DIR / f"{timestamp}_RESPONSE_STREAM.md"
    text_file = TRACES_DIR / f"{timestamp}_RESPONSE_TEXT.md"

    # If file doesn't exist, create it with the main header
    if not file.exists():
        with file.open("a", encoding="utf-8") as f:
            f.write(f"# {calling_method.upper()}\n\n")

    # Append the chunk to the file
    with file.open("a", encoding="utf-8") as f:
        f.write(f"## Response Chunk #{chunk_idx}\n\n")

        if respapi_chunk is not None:
            f.write(f"### Responses API:\n```json\n{respapi_chunk.model_dump_json(indent=2)}\n```\n\n")

        if complapi_chunk is not None:
            f.write(f"### ChatCompletions API:\n```json\n{complapi_chunk.model_dump_json(indent=2)}\n```\n\n")

        if generic_chunk is not None:
            # TODO Do `gen_chunk.model_dump_json(indent=2)` once it's not
            #  just a dict
            f.write(f"### GenericStreamingChunk:\n```json\n{json.dumps(generic_chunk, indent=2)}\n```\n\n")

            # Append text only to the text file
            with text_file.open("a", encoding="utf-8") as text_f:
                text_f.write(generic_chunk["text"])
