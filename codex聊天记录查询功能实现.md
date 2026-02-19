

自定义codex聊天记录定位查询功能
自定义脚本查询指定时间范围、指定项目目录下的codex聊天记录：

输入查询参数：
# codex session对应的工作目录
workspace_dir = /Users/bytedance/codebase_jz/worktree_exp_codex/1stphorm.com
# codex session对应的创建时间
year:2026
month:02
day:05

输出结果：
list[session_path]: 日志文件所处路径列表，比如：["/Users/bytedance/.codex/sessions/2026/02/15/rollout-2026-02-15T20-25-42-019c6143-8acd-7351-becf-f41f1b4ed484.jsonl"]。

codex的存储目录结构
${HOME}/.codex/
└── sessions/
    └── 2026/
        ├── 01/
        └── 02/
            ├── 01/
            ├── 02/
            ├── 03/
            └── 04/
                ├── rollout-2026-02-04T14-34-34-019c275c-1f1c-7620-9514-5fd0d668925a.jsonl
                ├── rollout-2026-02-04T14-52-52-019c276c-e024-75d0-aebd-a5eca0fecbcb.jsonl
                ├── rollout-2026-02-04T15-34-16-019c2792-c875-7cb0-ade6-e81f24aaf067.jsonl
                └── rollout-2026-02-04T15-58-28-019c27a8-efe4-7431-9efe-251e88996a96.jsonl


jsonl的格式和支持查询的字段：jsonl第一行：
timestamp和cwd对应时间和project-root。对于每个jsonl，只要读取第一行的下面2个字段用于查询即可。

{"timestamp":"2026-02-04T08:25:09.350Z","type":"session_meta","payload":{"id":"019c27c1-5bcd-7670-a90b-ae6fcf90c01e","timestamp":"2026-02-04T08:25:09.325Z","cwd":"/Users/bytedance/.codex/worktrees/c89d/codex_product_info_dataset_tagging",



请你根据上面的要求，给我写一个python脚本实现这个根据workspace和日期查询相关session路径的功能。

