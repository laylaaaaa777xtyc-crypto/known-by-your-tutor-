# 专属自适应老师（Adaptive Personal Tutor）

一套用于构建"了解—测试—动态适应"型 AI 学习陪伴的规范集合。它不是一个应用，而是一份可以直接喂给大模型、也可以被产品团队用来对齐的**教学契约**、**角色定义**、**评审清单**和**能跑起来的 Demo**。

版本：契约 v3 / 老师角色 v2 · 日期：2026-09-20 · 状态：已批准，等待真实使用验证。

## 这套 skill 想解决什么

把常见的"AI 学习助手"从**一份固定课程 + 一堆问卷 + 一个笼统的成绩**，升级成一位真正能承接进度的老师：

- 会先花两三次对话**了解学习者**，而不是直接开讲。
- 用**可检验的证据**判断"学会了没有"，不用"你自己觉得懂了吗"糊弄过关。
- 跨会话**记得上次卡在哪、答应了什么、什么该复习**。
- 遇到卡点会**换教法**，而不是把同一种讲法讲得更慢。
- 允许学习者按今天的心情**换一位老师**：温柔陪伴（小禾）、严格要求（舟舟）、启发探索（知远）。

## 仓库结构

```
outputs/                              # 原始契约文档（v3 + v2）
├── adaptive-personal-tutor-learning-contract.md
└── three-tutor-personas.md

prompts/                              # ready-to-paste system prompts
├── _shared_contract.md               # 三位老师共享的底层契约
├── xiaohe.md                         # 小禾老师
├── zhouzhou.md                       # 舟舟老师
└── zhiyuan.md                        # 知远老师

schemas/
└── learner-profile.schema.json       # 学习者画像 JSON Schema

examples/
└── learner-profile.example.json      # 一份真实填过的档案样例

evaluation.md                         # 12 项指标 + 4 场景 + 8 停止条件的评审清单

demo/                                 # 能跑起来的最小 Python demo
├── tutor.py                          # 60 行，anthropic SDK + prompt caching + adaptive thinking
├── requirements.txt
├── .env.example
└── README.md
```

## 快速上手

### A. 只想读文档、拷进你自己的 prompt

1. 打开 `prompts/_shared_contract.md`，作为 system 提示的前半段。
2. 从 `prompts/xiaohe.md` / `zhouzhou.md` / `zhiyuan.md` 里选一位老师，拼在后半段。
3. 可选：把 `examples/learner-profile.example.json` 作为跨会话承接的样例塞进去。

### B. 直接跑 Demo

```sh
cd demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填入 ANTHROPIC_API_KEY
source .env

python tutor.py                                    # 小禾，无档案
python tutor.py --tutor zhouzhou                   # 严格模式
python tutor.py --profile ../examples/learner-profile.example.json  # 带上次档案
```

Demo 用了 `claude-opus-4-7` + adaptive thinking + prompt caching + streaming。每轮对话会打印 token 使用量和缓存命中，方便验证承接是否真的读到了。

### C. 用作评审清单

对任何一段真实的老师-学习者对话，用 `evaluation.md` 打分。12 项指标全部达标 = 通过；任一守护指标违反 = 不通过。

## 核心设计（一屏速览）

### 1. 必须先建立三类画像

前两三次对话里通过自然交流建立，写入长期档案。**未建立前不得**为学习者安排"每天几点学"或复习时段。

- **认知入口偏好**：例子 / 概念 / 类比 / 动手 / 问题 先行。
- **每日节奏与时段**：单次时长、频率、可学时段、中断成本、休息偏好。
- **验收方式**：复述 / 造新例子 / 教一遍 / 迁移题 / 改错 / 动手复现。

### 2. 验收先行、延迟验收

- 验收方式**在学习开始前**就说清楚，不能事后临时决定"这样算过"。
- 至少通过一次**延迟验收**才计入"应用/迁移"层。
- "感觉懂了"不算掌握证据。

### 3. 三位可切换老师，差异在动作层

| 老师 | 教学哲学 | 卡点时默认动作 |
|---|---|---|
| 小禾（温柔陪伴） | 先保住"愿意继续"再谈进度 | 换讲法 → 拆更小 → 允许今天只做这一点 |
| 舟舟（严格要求） | 含糊过关是浪费你时间 | 要求再试一次 → 指出具体偏差 → 错完必须重做到对 |
| 知远（启发探索） | 想明白一次胜过被讲明白十次 | 反问"你到哪一步了" → 换条件让学习者自己发现矛盾 |

三人共享同一份学习者画像，但**如何采集、如何用、验收严格程度**必须显著不同——否则视为"只改了名字"。

### 4. 12 项首轮指标 + 8 条停止条件

见 `evaluation.md`。任一停止条件触发 = 暂停持久个性化功能。

## 不做什么

为了让 MVP 可落地，本 skill **暂不实现**：

- 完整 BKT / FSRS 掌握度算法。
- 学习者画像的自动更新（demo 里画像是只读的）。
- 自动化提醒与外部数据库集成。
- 隐藏遥测——首轮只使用明确授权的档案 + 人工测试。

以上都留在契约的"复审触发点"里，等真实使用证据够了再考虑。

## 复审触发点

- 完成 5–10 次合格真实使用；
- 第一次发现错误记忆或删除失败；
- 用户连续两次认为对话机械；
- 准备加入自动提醒、外部数据库或复杂掌握度算法之前。

## License

本仓库当前未附加正式开源许可。使用、修改、复述前请与作者确认。
