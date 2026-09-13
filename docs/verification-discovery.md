# 自动验证发现（第一版）

新会话默认不设置固定测试命令。验证命令留空时，模型上下文获得候选命令及来源；自动验证兜底优先采用发现结果。填写命令则覆盖自动发现。

当前支持项目根目录：
- pytest.ini 或 pyproject.toml 的 tool.pytest 配置：pytest。
- 修改的 Python 文件：py_compile 语法检查，不能视为测试通过。
- package.json 的 test/typecheck/lint/build 脚本；识别 pnpm/yarn 锁文件，跳过默认 no test specified 占位脚本。
- Cargo.toml：cargo test。
- go.mod：go test ./...。

发现命令不会执行命令；实际执行仍经过原有任务约束与权限检查。严格模式仍需手动命令。
旧会话的已存命令不会自动清除；要启用发现，请在会话设置清空验证命令。

限制：未覆盖子项目工作目录、CI/Makefile、unittest 识别及测试依赖图；不保证候选命令所需工具已安装。
验证：121 项 Studio 测试、5 项发现器测试、Ruff 和前端构建通过。未运行真实模型自动选命令评测。
