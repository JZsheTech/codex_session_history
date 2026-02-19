
给定一个codex 对话session文件，要用python代码将它转化为1个可读性较好的对话-执行轨迹markdown文件。
提供两种可选的转化方式：
1. 精简版（单条消息长度超过阈值时，只截取前一部分内容输出）
2. 完整版（所有内容完整输出）
你需要阅读 单个session对应的jsonl文件（比如/Users/bytedance/.codex/sessions/2026/02/04/rollout-2026-02-04T17-12-00-019c27ec-40f1-7092-8175-bc4a8af45ab1.jsonl），分析其字段结构，然后将每条消息以合理的形式放到markdown中输出（包括用户消息、ai消息、ai思考、ai工具调用等过程；ai思考、ai工具调用算单条消息，ai回答本身也算单条消息，转换时不要把它们揉到一起，要尽量区分开）

下面请你以/Users/bytedance/.codex/sessions/2026/02/04/ 和 /Users/bytedance/.codex/sessions/2026/02/15/ 目录中的对话历史为例来写出这个markdown转化脚本。