# User Requirements

## Goal

构建一个可验证、可恢复、可审计的本地编码 Agent。

## Confirmed Scope

- 项目名称：VeriPatch。
- 任务：输入固定版本的 Python 仓库、Issue 描述和失败测试，输出可验证代码修复。
- 第一阶段仅支持 Python 与 pytest。
- 单个有状态 Agent Controller；不通过堆叠角色扮演制造复杂度。
- 修改必须由确定性测试验证，模型不能自行宣布成功。
- 需要代码检索、AST 符号索引、受控编辑、测试反馈、Checkpoint 和轨迹记录。
- 需要离线可运行的示例，不配置 API Key 也能验证完整闭环。
- OpenAI 模型通过环境变量配置，系统不得绑定单一模型供应商。
- 支持 OpenAI 与 DeepSeek API Key 两种供应商认证；不复用 ChatGPT Plus 或 Codex 登录令牌。
- DeepSeek 提供 CLI/API/首页额度余量监控和低余额提醒；不将 Key 或余额写入运行数据库。
- 本地 GUI 可配置或移除 Windows 用户级加密存储中的 OpenAI/DeepSeek Key，并清晰区分环境变量来源；页面不得回显 Key，明文不得进入项目数据。
- 新建任务可通过 Windows 原生目录选择器选取代码仓库并自动回填绝对路径，同时保留手动输入。
- DeepSeek 作为本轮真实模型评测供应商，OpenAI 保留可选适配和离线 Fake Client 验证。
- 优先保证评测、可靠性、安全边界和可复现性，前端仅服务于轨迹展示。

## Engineering Defaults

- Python：兼容 3.11 及以上；本机开发环境为 Python 3.13。
- 运行策略：自动运行秒级测试；完整公开 Benchmark 后续单独运行。
- 数据：第一阶段使用仓库内可控 Bug 任务；公开任务集后续接入。
- Git：完成后初始化本地仓库，创建名为 `veripatch` 的私有 GitHub 仓库并推送；外部创建和登录由用户明确授权。
- 文档：根目录 README 采用英文优先、中英双语，说明项目使用方式、技术设计和验证证据。
- 评测：使用 8 个仓库内固定 Python Bug 任务进行 DeepSeek V4 Flash 真实评测；结果明确标记为 curated benchmark，不冒充 SWE-bench。

## Out of Scope for MVP

- 多语言支持、IDE 插件、自动提交真实 PR。
- 任意 Shell 权限、宿主机密钥访问和默认联网执行。
- 微调或训练大模型。
- Kubernetes、消息队列和无评测依据的多 Agent 群聊。
