# Development Log

> 本文件只追加开发记录。项目设计见 `docs/implementation.md`。

## Progress

| Module | Status | Notes |
|---|---|---|
| Requirements and architecture | Done | Scope and acceptance criteria frozen. |
| Domain and configuration | Done | Typed configuration and action protocol implemented. |
| Index and safe tools | Done | AST index, contained reads, atomic exact edits, pytest allowlist. |
| Agent runtime and persistence | Done | Explicit state machine, SQLite events and checkpoints. |
| Evaluation and demo | In progress | Frozen demo implemented; Windows output fix pending verification. |
| CLI/API | Done | Demo/run/eval/inspect/serve and local API implemented. |
| Tests and review | In progress | 12 tests pass; coverage 65%; static checks pass. |

## Entries

### 2026-08-27 — Project initialization

- Confirmed a from-scratch implementation instead of wrapping an existing agent framework.
- Chose a single explicit controller plus deterministic verifier.
- Recorded the offline demo requirement so development does not depend on an API key.
- Selected `gpt-5.6-terra` as the configurable default for cost/quality balance; `gpt-5.6-sol` remains available for the strongest evaluation setting.

### 2026-08-27 — Core MVP implementation

- Implemented typed action contracts, AST symbol lookup, repository path containment and atomic exact edits.
- Added a pytest-only deterministic verifier with secret stripping and command validation.
- Added SQLite event/checkpoint persistence and a budgeted state machine with repeated-action detection.
- Added OpenAI Responses API and offline scripted model adapters.
- Added CLI, FastAPI inspection endpoints, evaluation records and a frozen discount bug repository.
- First test run: 12 passed, 65% statement coverage. Fixed unclosed SQLite connection warnings.
- The first CLI demo completed its run but failed while printing a replacement character to a GBK console; updated subprocess decoding and console error handling for Windows.

## Running Notes

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\veripatch.exe demo
.\.venv\Scripts\veripatch.exe serve
```

### 2026-08-27 — 迭代 #1：运行时可靠性设计同步

**改动原因**：核心运行时已验证成功，但恢复、隔离执行、异步 API、评测标注和交付文档尚未达到可靠性交付标准。

**改动内容**：

- `docs/implementation.md`：增加真实恢复语义、测试运行器协议、Docker 沙箱、后台 API、轨迹页面、评测标注和交付物契约。
- 明确离线 scripted demo 只验证运行时，不作为模型效果指标。

**预期效果**：实现范围与最终验收完全对齐，后续代码变更均有明确接口和失败语义。

**文档同步**：implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #1：覆盖率补强

**改动原因**：首轮扩展测试为 25 passed / 76%，未达到计划中的 80% 目标。

**改动内容**：

- `tests/test_cli.py`：覆盖命令注册、离线 Demo、inspect 和真实 run 包装路径。
- `tests/test_testing.py`：覆盖 Docker runner 成功与超时结果。
- `pyproject.toml`：仅对内嵌 HTML/JS 文件豁免 E501，其他静态规则保持不变。

**预期效果**：公共 CLI 与 Docker 执行路径获得回归保护，整体覆盖率超过 80%。

**文档同步**：implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #1：最终安全审查修正

**改动原因**：代码审查发现 baseline 阶段崩溃、API 并发恢复、源码快照暴露和评测 task_id 路径边界需要显式处理。

**改动内容**：

- `src/veripatch/agent.py`：resume 在缺少 baseline 证据时重新执行固定测试，而非跳过复现。
- `src/veripatch/api.py`：按 run_id 跟踪活动任务，拒绝并发恢复；公共响应排除原始源码和内部动作指纹。
- `src/veripatch/evaluation.py`：限制 task_id 字符与父目录片段。
- `src/veripatch/testing.py`：阻止 `--override-ini=...` 形式绕过参数限制。

**预期效果**：恢复、API 数据最小化和评测临时目录边界更加完整。

**文档同步**：implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #1：交付物与项目文档

**改动原因**：代码闭环已通过，但缺少容器、CI、安全说明和可复现的完整入口文档。

**改动内容**：

- `Dockerfile`、`compose.yaml`、`sandbox/Dockerfile`：增加 API 容器和 pytest 沙箱定义。
- `.github/workflows/ci.yml`：增加 Ruff、格式和 80% 覆盖率门禁。
- `docs/architecture.md`、`docs/threat_model.md`：记录数据流、恢复语义、信任边界、控制与残余风险。
- `README.md`：补全安装、Demo、真实模型、resume、API、评测、容器、失败模式、限制和使用说明。

**预期效果**：仓库可直接用于演示、代码审查和技术讲解。

**文档同步**：implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #1：CLI 恢复与评测语义

**改动原因**：CLI 缺少 resume，旧评测结果无法区分运行时演示和真实模型能力。

**改动内容**：

- `src/veripatch/cli.py`：增加 `resume` 和 `--runner`；Demo 明确使用 local + scripted-demo。
- `src/veripatch/evaluation.py`：记录 benchmark kind、provider、runner、模型调用与 Token 汇总；scripted 结果标记为 runtime validation。

**预期效果**：公开结果不会误导，真实模型和离线运行时验证共用可比较的输出格式。

**文档同步**：implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #1：可靠性与接口测试扩充

**改动原因**：新增公共接口需要用故障场景证明，而不只验证成功 Demo。

**改动内容**：

- `tests/`：增加事务回滚、秘密清理、Docker 安全参数、崩溃后恢复、重复动作、预算耗尽、模型失败、终态拒绝恢复、OpenAI Fake Client、后台 API 和评测标注测试。

**预期效果**：可靠性、安全和可恢复性均有可执行证据，覆盖率向 80% 目标提升。

**文档同步**：implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #1：后台 API 与轨迹页面

**改动原因**：同步 POST 会长时间占用连接，且缺少独立结果接口和可演示轨迹页面。

**改动内容**：

- `src/veripatch/api.py`：任务创建改为 202 + run_id；增加后台执行、恢复、状态、事件、结果端点；增加依赖为零的 HTML 轨迹查看器。
- 后台调度异常会落库为失败事件，不会留下无解释的 queued 状态。

**预期效果**：演示者可实时查看任务执行过程，API 调用方可轮询而不阻塞。

**文档同步**：implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #1：测试运行器抽象与 Docker 沙箱

**改动原因**：外部仓库不能在宿主机以任意依赖和网络权限执行测试。

**改动内容**：

- `src/veripatch/testing.py`：定义 `TestRunner` 协议，将原 runner 明确为 `LocalPytestRunner`，新增带禁网、只读根目录和资源限制的 `DockerPytestRunner`。
- 本地 runner 自动使用当前虚拟环境 Python，避免 Windows PATH 解析到错误解释器。

**预期效果**：测试证据接口统一，真实仓库可默认进入受限容器执行。

**文档同步**：implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #1：OpenAI 适配可测试化

**改动原因**：真实 API 不应成为单元测试前提，供应商错误也需要稳定的运行时错误语义。

**改动内容**：

- `src/veripatch/models/openai.py`：支持注入 Fake Client，保留默认 Responses API；统一包装供应商异常并继续统计结构化响应 Token。

**预期效果**：无需 API Key 即可验证请求参数、结构化输出和错误传播。

**文档同步**：implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #1：可恢复 Agent 状态机

**改动原因**：原实现只持久化状态，无法从中断点继续，也没有保存完整 Diff 上下文。

**改动内容**：

- `src/veripatch/agent.py`：统一新建与继续执行路径；新增 `resume(run_id)`；持久化 provider、runner、动作指纹、原始文件和最终 Diff；基线执行失败转为明确终态。
- 外部运行器通过工厂注入，便于本地、Docker 和测试替身共用相同状态机。

**预期效果**：非终态任务可从下一步继续，恢复后仍能生成从原始代码到最终代码的完整 Patch。

**文档同步**：implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #1：状态与运行配置契约

**改动原因**：恢复和隔离执行需要在 checkpoint 中保存运行器、模型供应商、原始文件与重复动作窗口。

**改动内容**：

- `.env.example`、`src/veripatch/config.py`：增加 Docker runner、镜像和资源限制配置。
- `src/veripatch/domain.py`：增加 queued 状态、runner 类型、provider、原始文件快照、动作指纹与最终 Diff。

**预期效果**：运行中断后可重建上下文，API 和评测可准确区分执行方式。

**文档同步**：implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #1：事务化工作区编辑

**改动原因**：多文件编辑在后续文件写入失败时必须回滚已写入文件，避免留下半应用 Patch。

**改动内容**：

- `src/veripatch/workspace.py`：增加原始快照导入导出、统一原子写入和动作级事务回滚。

**预期效果**：Checkpoint 可恢复 Diff 跟踪，任何单次编辑动作保持全有或全无。

**文档同步**：implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #2：运行时交付设计同步

**改动原因**：现有离线运行时验证成功，但质量门禁仍有 Ruff/格式错误，Docker bind mount 可写，恢复缺少跨崩溃事务，且没有真实供应商 Benchmark 和 Git 交付。

**改动内容**：

- `docs/user_requirements.md`：确认 DeepSeek 真实评测、OpenAI 可选适配、私有 GitHub 和英文优先双语文档。
- `docs/implementation.md`：定义持久编辑事务、工作区漂移、SQLite 原子记录、双供应商认证、Token 预算、分页 API、8 题评测和 90% 质量门禁。

**预期效果**：将已可运行的 MVP 收敛为有真实证据、可安全演示、可代码审查的软件项目。

**文档同步**：idea_report.md 否（本项目不是论文阶段） | implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #2：事务与模型使用契约

**改动原因**：恢复需要持久化编辑准备状态，真实供应商评测需要区分缓存/推理 Token，并且现有运行只限制步骤数。

**改动内容**：

- `src/veripatch/domain.py`：增加持久编辑事务、待处理事务、实际模型、请求 ID、缓存与推理 Token。
- `src/veripatch/config.py`、`.env.example`：增加模型调用、输入 Token、输出 Token 预算和 DeepSeek 配置。
- `src/veripatch/models/base.py`、`models/openai.py`：扩展统一回复元数据并映射 OpenAI usage 明细。

**预期效果**：为跨崩溃恢复、双供应商和可复现实验建立统一持久化契约。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #2：八题固定评测集

**改动原因**：单一 discount Demo 只能证明运行时闭环，不能覆盖模型在不同修复模式下的行为。

**改动内容**：

- `benchmarks/interview_tasks.jsonl`：定义 8 个固定任务、Issue、类别和测试命令。
- `benchmarks/cases/`：新增分页边界、缓存键、布尔解析、库存状态、异常范围、重试序列和多文件费率任务；discount 复用离线示例。

**预期效果**：真实 DeepSeek 评测覆盖 7 类单文件错误和 1 个多文件修复，并可用任务树哈希复现。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #2：只读沙箱与可复现评测记录

**改动原因**：只读容器根目录不能阻止测试修改可写 bind mount；旧评测也缺少模型、任务哈希、预算和失败分类。

**改动内容**：

- `src/veripatch/testing.py`：仓库 bind mount 改为 readonly，移除全部 capabilities，扩展秘密环境变量清理。
- `src/veripatch/evaluation.py`：增加任务树哈希、模型/推理配置、预算、缓存/推理 Token、失败分类和 Markdown 报告。
- `src/veripatch/cli.py`：`eval` 自动生成同名 Markdown 报告并支持 `--report`。

**预期效果**：测试代码无法写回宿主仓库，真实评测可独立核验且不会把运行时演示冒充模型成绩。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 是
### 2026-08-27 — 迭代 #2：事务 API 兼容修正

**改动原因**：快速回归测试发现旧 `apply_edits()` 包装器在普通写入失败后保留了本次快照，与既有全回滚契约不一致。

**改动内容**：

- `src/veripatch/workspace.py`：兼容包装器在普通异常时恢复调用前快照；Agent 使用的 prepare/apply 持久路径不变。
- `agent.py`、`config.py`、`providers.py`：修复 Ruff/format 门禁报告的格式问题。

**预期效果**：旧事务回滚测试与新跨崩溃恢复语义同时成立。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #2：供应商入口与本地产品页

**改动原因**：模型适配需要在 CLI/API 上可选择，凭据状态和近期运行也需要无需查看数据库即可演示。

**改动内容**：

- `src/veripatch/providers.py`：集中 OpenAI、DeepSeek、scripted-demo 模型创建和退役模型拒绝。
- `src/veripatch/cli.py`：增加 `auth login/status/logout` 和 DeepSeek provider 选择。
- `src/veripatch/api.py`：增加首页创建表单、供应商状态、运行/事件分页，并过滤内部恢复状态。

**预期效果**：项目演示可从一个本地页面创建和追踪任务，供应商与秘密边界清晰可讲解。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #2：DeepSeek 与安全凭据适配

**改动原因**：用户只有 ChatGPT Plus 而没有 OpenAI API Key，需要 DeepSeek 成为真实运行供应商，同时保持统一 Agent 协议和秘密隔离。

**改动内容**：

- `src/veripatch/credentials.py`：环境变量优先、系统 keyring 其次的 API Key 管理与非敏感状态查询。
- `src/veripatch/models/deepseek.py`：V4 Flash Responses JSON Schema、V4 Pro Chat JSON Output、一次非法输出重试和 usage 映射。
- `src/veripatch/models/openai.py`、`models/__init__.py`、`config.py`：接入统一凭据与供应商配置。
- `pyproject.toml`：增加 keyring、mypy 和 build 开发门禁依赖。

**预期效果**：同一状态机可安全选择 OpenAI 或 DeepSeek，真实评测不依赖 ChatGPT 登录令牌。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 是

### 2026-08-27 — 迭代 #2：持久编辑事务与原子存储

**改动原因**：原动作级回滚只能处理进程内异常，无法识别写入后、checkpoint 前的进程崩溃；状态和事件分开提交也会产生不一致窗口。

**改动内容**：

- `src/veripatch/workspace.py`：新增编辑准备、before/after 哈希、已写/未写/混合状态协调和外部漂移拒绝。
- `src/veripatch/store.py`：启用 WAL、busy timeout、状态+事件原子记录，并增加运行/事件分页查询。

**预期效果**：恢复逻辑可依据持久事务确定性收敛，后台并发运行减少 SQLite 锁竞争和轨迹错位。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否

### 2026-08-27 — 迭代 #2：Agent 崩溃恢复与预算门禁

**改动原因**：持久事务必须由状态机在写入前落库并在 resume 时协调；同时需要阻止模型调用或 Token 无界增长。

**改动内容**：

- `src/veripatch/domain.py`、`workspace.py`：记录当前工作文件哈希并拒绝未知外部漂移。
- `src/veripatch/agent.py`：编辑准备/提交事件、pending transaction 恢复、工作区漂移失败，以及模型调用和输入/输出 Token 预算。

**预期效果**：准备前、写入中、写入后崩溃均有明确恢复路径，费用和循环具有硬上限。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 是
### Iteration #2 — curated benchmark baseline verification

- Added eight fixed Python/pytest bug tasks spanning boundary conditions, cache keys, parsing, state updates, exception handling, retry timing, and multi-file configuration.
- Verified all eight repositories start from a reproducible failing test state (8/8 baselines fail for their intended assertions).
- These tasks are explicitly a curated benchmark and are not represented as SWE-bench.
### 2026-08-27 — 迭代 #2：交付质量门禁与 Docker 实跑

**改动原因**：交付版需要以可复现验收代替静态配置声明，并将新增供应商、恢复和 API 代码纳入覆盖率。

**改动内容**：

- 测试扩展到 67 项，覆盖事务四态恢复、漂移、预算、DeepSeek/OpenAI Fake Client、凭据、API 脱敏分页和沙箱边界。
- 本地门禁通过：90.28% coverage、Ruff、格式、strict mypy、sdist/wheel 构建和隔离安装冒烟。
- 离线 Demo 与 runtime eval 成功；Docker 中完成失败测试、编辑、成功测试闭环。
- 实跑验证 Docker 禁网、只读仓库挂载；API 与 sandbox 两个镜像均构建成功。
- DeepSeek/OpenAI 凭据状态均为 none，因此未生成或伪造真实模型成绩。

**预期效果**：仓库可直接用于本地演示和技术讲解；真实 8 题报告只需用户配置 DeepSeek Key 后执行固定命令。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 是
### 2026-08-28 — 迭代 #2：供应商额度监控

**改动原因**：真实模型评测前需要确认 API 可用与余额余量，同时不能把供应商 Key 或个人余额混入运行轨迹。

**改动内容**：

- `src/veripatch/quota.py`：增加 DeepSeek 官方余额查询、币种明细、低余额阈值和安全失败快照。
- CLI 增加 `quota status openai|deepseek`；API 增加 `/providers/{provider}/quota`。
- 首页每 60 秒刷新 DeepSeek 余额与 LOW 提示；OpenAI 标明标准 Key 不支持剩余额度查询。
- Fake Client 覆盖成功、低余额、无 Key、401、网络失败、非法响应和秘密不泄露。

**预期效果**：评测前可快速发现无余额或低余额，监控数据不进入 SQLite、事件或 Git。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 是
### 2026-08-28 — 迭代 #3：真实评测驱动的 DeepSeek 结构化输出加固

**改动原因**：首轮 8 题真实评测中，4 题因 `edits: null` 或相邻 JSON 导致供应商适配失败，不能把协议兼容问题误记为模型能力失败。

**改动内容**：

- 非编辑动作的 `edits: null` 安全归一化为空数组，最终仍统一经过 `AgentDecision` 校验。
- 支持从带围栏或相邻对象的响应中选择唯一可验证决策，不放宽动作字段约束。
- 第二次请求附带截断后的校验错误和原响应，要求只返回一个修正 JSON 对象。
- 成功重试时累计两次请求的输入、缓存、输出和推理 Token，避免低报用量。
- 新增真实失败形状的回归测试；完整门禁为 79 tests、90.75% coverage、Ruff 与 strict mypy 通过。

**预期效果**：供应商格式波动由适配层吸收，Benchmark 的失败分类更接近 Agent/模型真实能力。

**文档同步**：idea_report.md 否 | implementation.md 否 | configs 否

### 2026-08-28 — 迭代 #4：DeepSeek 八题真实 Docker 评测

**改动原因**：交付标准要求用真实模型验证固定任务，并公开可复现指标而不是使用 scripted demo 成绩。

**改动内容**：

- 使用 `deepseek-v4-flash`、只读禁网 Docker runner 执行全部 8 个固定任务。
- 结果为 8/8 resolved；平均 4.38 步、11.57 秒，无失败分类。
- 总用量为 78,969 input、27,008 cached input、6,454 output、3,831 reasoning Tokens。
- 报告固定记录源 Git SHA、Docker image ID 和每题仓库树哈希，不记录凭据或个人余额。

**预期效果**：README 与技术文档可以引用一次真实、可审计的小型 curated benchmark，同时明确它不是 SWE-bench 或泛化能力证明。

**文档同步**：idea_report.md 否 | implementation.md 否 | configs 否

### 2026-08-28 — 迭代 #5：项目演示级本地图形界面

**改动原因**：旧页面能够查看数据，但信息密度、交互反馈和视觉层次更接近内部调试工具，不适合候选人现场演示。

**改动内容**：

- 新增独立 `ui.py`，实现响应式本地控制台、模型供应商卡片、任务创建向导、运行器与测试命令配置。
- 首页展示 DeepSeek 实时额度、总体成功率、活跃任务、状态过滤和最近运行卡片。
- 详情页增加修复生命周期、实时指标、决策/测试/Diff/事件 Tab、Diff 着色与复制功能。
- 新增 `POST /demo` 和“一键离线 Demo”，每次复制冻结示例到独立工作区后执行，不污染原始项目。
- 对动态文本统一转义；run ID 在嵌入脚本前进行 HTML-safe JSON 编码，公开页面继续使用脱敏 API。
- 自动化扩展到 82 项；真实页面接口联调完成 4 步离线修复并产生成功证据。

**预期效果**：使用者可以从一个页面创建任务、观察 Agent 思考与工具证据、审查最终 Patch，同时保留本地安全边界。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否

### 2026-08-28 — 迭代 #6：Apple 风格视觉重构

**改动原因**：上一版使用大标题、蓝绿渐变、发光和多层卡片，具有明显的模板化 AI 后台观感，缺少成熟桌面开发者工具应有的克制与层次。

**改动内容**：

- 全量移除旧版渐变科技风，采用 Apple 浅灰画布、SF 字体栈、细分隔线、软阴影和克制的蓝色强调。
- 首页改为 macOS 应用结构：固定侧边栏、半透明工具栏、紧凑指标、运行列表和系统状态。
- 创建任务由常驻大表单改为居中 Sheet，支持背景模糊、Esc/遮罩关闭和移动端底部面板。
- 详情页改为证据工作区，主区域承载 Diff/测试/决策，右侧显示指标与修复生命周期。
- 增加持久浅色/深色外观切换，并保留窄屏响应式布局。
- 实际 HTTP 联调确认首页、Sheet、主题结构、离线 Demo 和详情工作区均可用；浏览器截图连接组件仍存在运行时兼容限制。

**预期效果**：视觉更接近成熟 macOS 工具而非营销落地页，任务和证据成为主角。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否

### 2026-08-28 — 迭代 #7：安全凭据面板与工作台导航修复

**改动原因**：首页“概览”和“运行记录”指向同一文档却呈现冲突的导航状态，同时真实模型必须离开 GUI 才能配置 Key，影响现场演示的完整性。

**改动内容**：

- 侧栏收敛为唯一“工作台”状态，将新建任务、API 配置和 API 文档拆为语义明确的动作。
- 新增 OpenAI/DeepSeek API 配置 Sheet，支持写入和二次确认移除 Windows 凭据库；环境变量来源只读。
- 后端使用 `SecretStr` 接收凭据且响应只返回配置状态；Key 不进入 SQLite、事件、日志或前端存储。
- 创建真实模型任务前检查供应商状态，未配置时保留表单并引导到对应 Key 输入框。
- Sheet 控制器统一处理按钮、遮罩和 Esc 关闭，所有动作按钮显式声明类型，消除隐式提交和重复导航交互。
- 增加凭据接口、环境变量删除边界和前端安全结构回归测试，自动化扩展到 84 项。

**预期效果**：项目演示可以完全在本地 GUI 中完成配置、建任务和查看证据，同时保持秘密隔离与一致导航状态。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否

### 2026-08-28 — 迭代 #8：API Key 配置流程简化

**改动原因**：双供应商卡片同时展示模型协议、输入框和删除动作，增加了首次使用认知负担；用户只需要选择供应商并粘贴密钥。

**改动内容**：

- API 配置 Sheet 改为 DeepSeek/OpenAI 分段选择、单一密钥输入框和一个保存按钮。
- 保存成功后清空输入并明确提示下次启动自动读取；已有 Key 可直接覆盖更新。
- 后端写入后立即回读凭据状态，无法持久化时返回失败，避免“假保存成功”。
- Windows 凭据读写端点改为事件线程执行，避免 FastAPI 工作线程缺少 WinVault 登录会话；额度网络请求仍在线程中执行，但由事件线程预先解析密钥。
- 增加 WinVault 故障回退、真实 DPAPI 非明文往返和 API 持久化回读测试，自动化扩展到 86 项。
- 下方连接状态单独展示已保存、未配置或环境变量接管，删除降级为次要操作。
- 创建任务缺少凭据时自动选中对应供应商并聚焦唯一输入框。
- 保留 Credential Manager 优先、Windows DPAPI 用户级加密后备、秘密不回显、请求校验脱敏和环境变量只读边界。

**预期效果**：首次配置只需“选供应商、粘贴、保存”，同时不牺牲原有秘密隔离设计。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否

### 2026-08-28 — 迭代 #9：原生代码仓库目录选择

**改动原因**：要求用户手写 Windows 仓库绝对路径容易输错，也不符合桌面工具的使用习惯；浏览器自身无法向网页暴露本机目录绝对路径。

**改动内容**：

- 新增 localhost 原生目录选择端点，通过 Tk 8.6 打开 Windows 文件夹选择器。
- 新建任务表单增加“选择文件夹”按钮，选择后自动回填绝对路径，并保留粘贴路径能力。
- 系统选择器置顶显示、限制单实例；取消不会覆盖原输入，异常通过表单反馈。
- Windows 选择器在创建后两次查找并提升到前台；重复请求会再次尝试置顶，不再只返回无法定位的忙碌错误。
- Sheet 禁止点击背景遮罩关闭，只保留关闭/取消按钮和 Esc，避免切换窗口或复制文本时误关表单。
- 目录选择端点要求自定义本地 UI 请求头，使跨站网页必须经过被拒绝的 CORS 预检，避免恶意页面触发系统弹窗。
- 全测试套件强制使用每项测试独立的临时凭据保险库，禁止自动化读取或删除用户真实 API Key。
- 增加选择、取消、并发冲突、不可用状态、API 响应和页面结构测试，自动化扩展到 89 项。

**预期效果**：创建真实仓库任务无需手工查找和输入绝对路径，现场演示路径更短且错误更少。

**文档同步**：idea_report.md 否 | implementation.md 是 | configs 否
