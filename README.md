# 专属自适应老师（Adaptive Personal Tutor）

一套可以直接拷进 **ChatGPT / Claude / 豆包 / Gemini / DeepSeek / Kimi** 等任何大模型对话框的**教学 prompt**。不需要 API key，不需要装东西，不需要注册任何服务。

版本：契约 v3 / 老师角色 v2 · 状态：已批准，等待真实使用验证。

## 用法（最快 30 秒）

打开你常用的大模型对话（ChatGPT、Claude.ai、豆包、Kimi、DeepSeek……都可以），然后：

1. 从下面三位老师里挑一位：

   - [`prompts/xiaohe.md`](prompts/xiaohe.md) —— **小禾老师**（温柔陪伴）：适合基础薄弱、被过挫败、容易被压力劝退的时候。
   - [`prompts/zhouzhou.md`](prompts/zhouzhou.md) —— **舟舟老师**（严格要求）：适合有明确目标 / 截止日期、缺执行和监督的时候。
   - [`prompts/zhiyuan.md`](prompts/zhiyuan.md) —— **知远老师**（启发探索）：适合已有基础、更看重"想通"而不是"记住"的时候。

2. 把选中文件的**全部内容**复制粘贴到对话里作为**第一条消息**（或者，如果对话工具有 "system prompt" / "自定义指令" / "角色设定" 字段，就贴在那里）。

3. 开始正常聊——问问题、说卡在哪、说今天想学什么，老师会承接。

**跨会话承接**：想让老师"记住上次进度"？把 [`examples/learner-profile.example.json`](examples/learner-profile.example.json) 里的 JSON 也贴进对话（可以作为第一条消息里 prompt 之后的一段，或者第二条消息发过去）。老师会把它当成"上次的档案"，从上次卡住的地方接着来。想自己写一份档案，看 [`schemas/learner-profile.schema.json`](schemas/learner-profile.schema.json) 的字段定义。

**换老师**：另开一段对话，贴另一位老师的 prompt。三位老师共享同一套画像逻辑，所以 profile JSON 是通用的。

## 这套 prompt 到底改了什么

普通"AI 学习助手"的三个痛点：**开场问卷太长 / 说"你自己觉得懂了吗"糊弄验收 / 每次都从零开始**。这套 prompt 逐个解掉：

- **不预设固定课程**：老师会先花两三次对话**了解你**——你怎么学得进去、什么时段能学、什么算学会了——才开始安排。
- **验收先行**：每节学习**开始前**就说清楚"什么样算过关"，事后不能改口。同一内容还要通过**延迟验收**（隔几天再验一次）才算真的会。
- **卡壳时换教法**：不会把同一种讲法讲得更慢；会切换到另一种"认知入口"（例子 / 概念 / 类比 / 动手 / 问题 先行）。
- **三种严格度可选**：小禾允许"今天只做一点"；舟舟"错完必须重做到对"；知远"不给答案，让你自己发现矛盾"。选择 = 你今天希望被怎么对待。

## 仓库里都有什么

```
prompts/               <── 拷进任何 LLM 对话框直接用
├── xiaohe.md          小禾老师（温柔陪伴）
├── zhouzhou.md        舟舟老师（严格要求）
└── zhiyuan.md         知远老师（启发探索）

examples/
└── learner-profile.example.json    一份填过的档案样例，用于跨会话承接

schemas/
└── learner-profile.schema.json     档案的字段定义

outputs/                            设计源文档（读这个可以理解为什么这么做）
├── adaptive-personal-tutor-learning-contract.md
└── three-tutor-personas.md

evaluation.md                       12 项指标 + 4 场景 + 8 停止条件的评审清单

demo/                               可直接运行的命令行体验
├── tutor.py                        无密钥用本地模式，有密钥自动使用 Claude
├── requirements.txt
├── .env.example
└── README.md
```

## 常见问题

**Q：粘贴 prompt 后模型说"作为一个 AI 我不能扮演老师"怎么办？**
A：多数情况是把 prompt 贴到了"用户消息"位置而不是"系统提示"。如果工具没有系统提示位，直接以 prompt 作为**对话的第一条消息**发出去、然后**接一条**"好的，那我们开始吧"，多数模型会自然承接。ChatGPT / 豆包 / Kimi / DeepSeek / Claude.ai 都实测可用。

**Q：能不能同时用三位老师？**
A：一段对话里只用一位。想切换就另开一段对话贴新的 prompt——把 profile JSON 也带过去，进度不丢。

**Q：JSON profile 里"陈述 / 观察 / 推测"这些字段是什么意思？**
A：档案要区分事实和假设——学习者说过的话是"陈述"，教学中观察到的是"证据"，老师的假设是"推测"。**推测不得被当作事实使用**。这是让老师不乱贴标签的关键。详细字段见 `schemas/learner-profile.schema.json`。

**Q：为什么强调"验收先行"和"延迟验收"？**
A：正确率不等于掌握。当场答对可能只是短时记忆，真正的应用/迁移能力要靠**换一段时间再问一次、换一个情境再问一次**才能露出来。详细在 `outputs/adaptive-personal-tutor-learning-contract.md`。

**Q：想改 prompt 或做产品对齐怎么办？**
A：`outputs/` 里有设计的原文档（契约 v3 + 老师角色 v2）；`evaluation.md` 是评审用的 12 项指标 + 停止条件——**任一停止条件触发 = 回退**。三位老师的差异必须体现在"教学动作"上，不能只体现在"语气"上。

## 可选：运行命令行演示或通过 API 自动化

直接执行 `python3 demo/tutor.py` 即可进入无需密钥的本地引导模式。它不具备大模型的自由问答能力，但能演示三位老师不同的教学动作。

如果你在做产品集成、要跑批测试、想把老师接到自己的系统里，[`demo/`](demo/) 也支持 Anthropic Claude API（Opus 4.7 + adaptive thinking + prompt caching + streaming）；配置 `ANTHROPIC_API_KEY` 后，程序会自动启用完整模型。

## 复审触发点

- 完成 5–10 次合格真实使用；
- 第一次发现错误记忆或删除失败；
- 用户连续两次认为对话机械；
- 准备加入自动提醒、外部数据库或复杂掌握度算法之前。

