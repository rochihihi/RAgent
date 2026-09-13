# RAgent

**本地桌面编码 Agent：阅读、修改、测试并解释真实软件项目。**

RAgent 支持 OpenAI 和 DeepSeek，通过结构化动作、受控文件操作、权限确认、事务化编辑、测试验证和 SQLite 检查点，完成：

> 理解需求 → 阅读代码 → 修改文件 → 验证结果 → 汇报证据

![RAgent Studio 界面](docs/assets/ragent-studio.png)

## 主要功能

- 本地桌面工作台与持久化对话
- 项目文件浏览、搜索和受控读取
- 精确编辑、文件变更记录与 Diff 审查
- 分级权限确认，避免未经授权的写入和命令执行
- pytest 等验证命令的显式执行与结果记录
- SQLite 检查点、上下文压缩和中断恢复
- OpenAI / DeepSeek 统一的结构化 Agent 动作协议
- 本地加密凭据存储，不把 API 密钥写入项目数据库或 Git

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\ragent.exe demo
```

启动本地 Studio：

```powershell
.\.venv\Scripts\ragent.exe serve --host 127.0.0.1 --port 8000
```

然后打开 <http://127.0.0.1:8000>。

## 文档

- [架构说明](docs/architecture.md)
- [实现说明](docs/implementation.md)
- [威胁模型](docs/threat_model.md)
- [English README](README.md)

## 项目结构

```text
src/veripatch/       Agent 运行时、模型适配器、工具和 API
tests/               单元测试、安全测试和端到端测试
frontend/            Studio 前端
examples/            离线演示项目
benchmarks/          可复现评测任务
docs/                架构、实现和安全文档
```

RAgent 默认只监听本机地址 `127.0.0.1`，不应直接暴露到公网。

## 技术说明

普通 Coding Agent 容易把“模型输出了 Patch”误认为“Bug 已修复”。RAgent 让模型只选择结构化动作，由确定性运行时控制路径、编辑、测试和成功判定。编辑前会把内容与哈希写入 SQLite，再执行文件写入，以便在崩溃或外部漂移后安全恢复。外部仓库默认使用只读、禁网、限资源的 Docker 测试环境；模型没有 shell 权限，测试文件和 Git 元数据不可编辑。评测区分离线运行时演示与真实模型结果，并报告修复率、步骤、耗时、Token 和失败分类。
