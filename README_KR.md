<p align="center">
    <img alt="Claude Code with GPT-5 Codex"
        src="https://raw.githubusercontent.com/teremterem/claude-code-gpt-5-codex/main/images/claude-code-gpt-5-codex2.jpeg">
</p>

This repository lets you use Anthropic's **Claude Code CLI** with OpenAI models such as **GPT-5-Codex, GPT-5.1, and others** via a local LiteLLM proxy.

> **⚠️ ATTENTION ⚠️**
>
> If you're here to set up `your own LiteLLM Server` with `LibreChat` as the web UI (or any other OpenAI / Anthropic API compatible client, for that matter), head over to the [litellm-server-boilerplate](https://github.com/teremterem/litellm-server-boilerplate) repository. It contains a "boilerplate" version of this repo with Claude Code CLI stuff stripped away, **an optional `LibreChat` set up, and a `README` which specifically explains how to build `your own AI agents and assistants` on top of it.**

## Quick Start ⚡

### Prerequisites

- [OpenAI API key 🔑](https://platform.openai.com/settings/organization/api-keys)
- [Anthropic API key 🔑](https://console.anthropic.com/settings/keys) - optional (if you decide not to remap some Claude models to OpenAI)
- Either [uv](https://docs.astral.sh/uv/getting-started/installation/) or [Docker Desktop](https://docs.docker.com/desktop/), depending on your preferred setup method

### First time using GPT-5 via API?

If you are going to use GPT-5 via API for the first time, **OpenAI may require you to verify your identity via Persona.** You may encounter an OpenAI error asking you to “verify your organization.” To resolve this, you can go through the verification process here:
- [OpenAI developer platform - Organization settings](https://platform.openai.com/settings/organization/general)

### Setup 🛠️

1. **Clone this repository:**

   ```bash
   git clone https://github.com/teremterem/claude-code-gpt-5-codex.git
   cd claude-code-gpt-5-codex
   ```

2. **Configure Environment Variables:**

   Copy the template file to create your `.env`:
   ```bash
   cp .env.template .env
   ```

   Edit `.env` and add your OpenAI API key:

   ```dotenv
   OPENAI_API_KEY=your-openai-api-key-here
   # Optional: only needed if you plan to use Anthropic models
   # ANTHROPIC_API_KEY=your-anthropic-api-key-here

   # Optional (see .env.template for details):
   # LITELLM_MASTER_KEY=your-master-key-here

   # Optional: specify the remaps explicitly if you need to (the values you see
   # below are the defaults - see .env.template for more info)
   # REMAP_CLAUDE_HAIKU_TO=gpt-5.1-codex-mini-reason-none
   # REMAP_CLAUDE_SONNET_TO=gpt-5-codex-reason-medium
   # REMAP_CLAUDE_OPUS_TO=gpt-5.1-reason-high

   # Some more optional settings (see .env.template for details)
   ...
   ```

3. **Run the proxy:**

   1) **EITHER via `uv`** (make sure to install [uv](https://docs.astral.sh/uv/getting-started/installation/) first):

      **OPTION 1:** Use a script for `uv`:

      ```bash
      ./uv-run.sh
      ```

      **OPTION 2:** Run via a direct `uv` command:

      ```bash
      uv run litellm --config config.yaml
      ```

   2) **OR via `Docker`** (make sure to install [Docker Desktop](https://docs.docker.com/desktop/) first):

      **OPTION 3:** Run `Docker` in the foreground:

      ```bash
      ./run-docker.sh
      ```

      **OPTION 4:** Run `Docker` in the background:

      ```bash
      ./deploy-docker.sh
      ```

      **OPTION 5:** Run `Docker` via a direct command:

      ```bash
      docker run -d \
         --name claude-code-gpt-5 \
         -p 4000:4000 \
         --env-file .env \
         --restart unless-stopped \
         ghcr.io/teremterem/claude-code-gpt-5:latest
      ```

      > **NOTE:** To run with this command in the foreground instead of the background, remove the `-d` flag.

      To see the logs, run:

      ```bash
      docker logs -f claude-code-gpt-5
      ```

      To stop and remove the container, run:
      ```bash
      ./kill-docker.sh
      ```

      > **NOTE:** The `Docker` options above will pull the latest image from `GHCR` and will ignore all your local files except `.env`. For more detailed `Docker` deployment instructions and more options (like building `Docker` image from source yourself, using `Docker Compose`, etc.), see [docs/DOCKER_TIPS.md](docs/DOCKER_TIPS.md)

### Using with Claude Code 🎮

1. **Install Claude Code** (if you haven't already):

   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Connect it to the proxy:**

   ```bash
   ANTHROPIC_BASE_URL=http://localhost:4000 claude
   ```

   If you set `LITELLM_MASTER_KEY` in your `.env` file (see `.env.template` for details), pass it as the Anthropic API key for the CLI:
   ```bash
   ANTHROPIC_API_KEY="<LITELLM_MASTER_KEY>" \
   ANTHROPIC_BASE_URL=http://localhost:4000 \
   claude
   ```

   > **NOTE:** In this case, if you've previously authenticated, run `claude /logout` first.

**That's it!** Your Claude Code client will now use the **OpenAI models** that this repo recommends by default (unless you explicitly specified different choices in your `.env` file). 🎯

---

### Model aliases

You can find the full list of available OpenAI models in the [OpenAI API documentation](https://platform.openai.com/docs/models). Additionally, this proxy allows you to control the reasoning effort level for each model by appending it to the model name following the pattern `-reason-<effort>` (or `-reasoning-<effort>`, if you prefer). Here are some examples:

- `gpt-5.1-codex-mini-reason-none`
- `gpt-5.1-codex-mini-reason-medium`
- `gpt-5.1-codex-mini-reason-high`

If you don't specify the reasoning effort level (i.e. only specify the model name, like `gpt-5.1-codex-mini`), it will use the default level for the model.

> **NOTE:** Theoretically, you can use arbitrary models from [arbitrary providers](https://docs.litellm.ai/docs/providers), but for providers other than OpenAI or Anthropic, you will need to specify the provider as a prefix in the model name, e.g. `gemini/gemini-pro`, `gemini/gemini-pro-reason-disable` etc. (as well as set the respective API key for that provider in your `.env` file).



## SUBSCRIPTION SETTINGS

한국어 버전은 `README_KR.md` 를 참고하십시오.

chatgpt의 subscription을 사용할 수 있습니다. \
subscription 형태의 통신을 위해서는 아래와 같은 설정이 필요합니다.

먼저, `.env.template` 파일을 `.env` 파일로 복사하십시오. \
그리고 `.env` 파일을 다음과 같이 수정하십시오.

- `OPENAI_REQUEST` 를 `subscription` 으로 설정하십시오.
- `OPENAI_API_KEY_SUBSCRIPTION`, `OPENAI_ACCOUNT_ID` 변수를 세팅하십시오.
  - `OPENAI_API_KEY_SUBSCRIPTION`: access key 입력
  - `OPENAI_REFRESH_KEY_SUBSCRIPTION`: refresh key 입력
  - `OPENAI_ACCOUNT_ID`: account id 입력
- `ALWAYS_USE_RESPONSES_API`, `ALWAYS_USE_STREAMING` 값을 true로 설정하십시오.

OPENAI_API_KEY_SUBSCRIPTION, OPENAI_ACCOUNT_ID 값은 codex, opencode 등으로 로그인하여 확인하십시오.

### 프로젝트 스크립트를 통해 로그인

```bash
./get_token_init.sh
```

#### codex 로그인 후 확인 방법
```bash
codex login
```

로그인 성공 시, `$HOME/.codex/auth` 에서 "tokens.id_token", "tokens.account_id" 필드값을 통해 확인할 수 있습니다.

#### opencode 로그인 후 확인 방법
```
command: opencode auth login
- Click "OpenAI"
- Click "ChatGPT Pro/Plus (browser)" or "ChatGPT Pro/Plus (headless)"
```

이후, 당신은 `$HOME/.local/share/opencode/auth.json` 에서 "openai.access", "openai.accountId" 필드값을 통해 확인할 수 있습니다.

#### 확인 방법

`.env` 파일에서 `SYSTEM_REMINDER_REMOVE` 변수의 값을 `true` 로 설정하십시오.

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:4000"
claude --system-prompt ''
```
시스템 프롬프트를 강제로 '' 로 주입해 실행합니다. \
(claude code의 기본 system prompt 에 model 정보를 강제 기입하기 때문에 시스템 프롬프트를 초기화하지 않으면, 모델명을 물었을 때, GPT, Codex 라고 응답하지 않을 수 있습니다.) \
모델 이름을 물어봅니다.

#### 토큰 Refresh 수동 업데이트

.env에 `OPENAI_REFRESH_KEY_SUBSCRIPTION`, `OPENAI_CLIENT_ID_SUBSCRIPTION` 가 설정되어 있어야 합니다.

```bash
./refresh.sh
```

토큰 자동 업데이트는 다음 상황에서 작동합니다:

- 401 오류 발생
- 현재 시간이 `OPENAI_SUBSCRIPTION_EXPIRES_AT` 만료 시간 `-7 days` 를 지난 경우
  - `OPENAI_SUBSCRIPTION_EXPIRES_AT` 값이 비어 있을 경우, 토큰 만료시간을 체크하지 않는다.


## KNOWN PROBLEM

**subscription 모드에 대한 토큰 갱신 테스트를 하지 않아, 갱신 관련 로직이 정상 작동하지 않을 수 있습니다.**

**Fixed WebSearch issue in 2026.02.19.** \
**However, only temporary fixes have been applied, so the WebSearch functionality may not work fully.**

The `Web Search` tool currently does not work with this setup. You may see an error like:

```text
API Error (500 {"error":{"message":"Error calling litellm.acompletion for non-Anthropic model: litellm.BadRequestError: OpenAIException - Invalid schema for function 'web_search': 'web_search_20250305' is not valid under any of the given schemas.","type":"None","param":"None","code":"500"}}) · Retrying in 1 seconds… (attempt 1/10)
```

This is planned to be fixed soon.

> **NOTE:** The `Fetch` tool (getting web content from specific URLs) is not affected and works normally.

## P. S. You are welcome to join our [MiniAgents Discord Server 👥](https://discord.gg/ptSvVnbwKt)

## And if you like the project, please give it a Star 💫

<p align="center">
<a href="https://www.star-history.com/#teremterem/claude-code-gpt-5-codex&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=teremterem/claude-code-gpt-5-codex&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=teremterem/claude-code-gpt-5-codex&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=teremterem/claude-code-gpt-5-codex&type=date&legend=top-left" />
 </picture>
</a>
</p>
