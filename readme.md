
# 项目功能
1. 根据workspace_dir和日期(年-月-日) 查询本机本用户codex相关session的存储路径。
2. 将指定存储路径的session转化成可读性好的markdown对话文件(可使用精简模式和全文模式，精简模式将省略太长的输入和输出，只截取其部分显示出来)

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