
# 项目功能
1. 根据workspace_dir和日期(年-月-日) 查询本机本用户codex相关session的存储路径。
2. 将指定存储路径的session转化成可读性好的markdown执行轨迹文件(可使用精简模式和全文模式，精简模式将省略太长的输入和输出，只截取其部分显示出来)

# 可用python环境

```
source  /Users/bytedance/python_env/.venv/bin/activate
/Users/bytedance/python_env/.venv/bin/python

```

# 示例运行代码

指定workspace和日期的session查询
```
python query_codex_sessions.py \
    --workspace-dir /Users/bytedance/codebase_jz/codex_product_info_dataset_tagging \
    --year 2026 --month 2 --day 4
```

将 session jsonl 转成 markdown 轨迹（精简版/完整版）
```
# 单文件（精简版）
python convert_codex_session_to_md.py \
  /Users/bytedance/.codex/sessions/2026/02/04/rollout-2026-02-04T17-12-00-019c27ec-40f1-7092-8175-bc4a8af45ab1.jsonl \
  --mode concise \
  --truncate-threshold 2000 \
  --truncate-keep 800 \
  --output-dir ./session_markdown_traces

# 两个日期目录批量（精简版）
python convert_codex_session_to_md.py \
  /Users/bytedance/.codex/sessions/2026/02/04/ \
  /Users/bytedance/.codex/sessions/2026/02/15/ \
  --mode concise \
  --output-dir ./session_markdown_traces

# 单文件（完整版）
python convert_codex_session_to_md.py \
  /Users/bytedance/.codex/sessions/2026/02/15/rollout-2026-02-15T20-07-54-019c6133-3ec3-71d0-9bc6-a584a32dce06.jsonl \
  --mode full \
  --output-file ./session_markdown_traces/full_example.md
```
