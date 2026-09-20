# 60-line 演示

一个能跑起来的最小闭环：把学习契约 + 三位老师角色 + 学习者画像喂给 Claude，跑一场多轮对话。

## 安装

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填入你的 ANTHROPIC_API_KEY
source .env
```

## 用法

```sh
# 首次会话，默认小禾老师，无档案
python tutor.py

# 切换到舟舟老师
python tutor.py --tutor zhouzhou

# 携带上次的学习者档案（跨会话承接的最小演示）
python tutor.py --tutor xiaohe --profile ../examples/learner-profile.example.json

# 切换到知远老师
python tutor.py --tutor zhiyuan
```

## 里面用到了什么

- **`claude-opus-4-7`**：最新 Opus，Claude 4.7 家族。
- **Adaptive thinking**（`thinking: {type: "adaptive"}`）：老师需要判断"要不要换讲法/换入口"、"这个验收够不够"，用推理比不推理稳。
- **Prompt caching**：底层契约 + 角色 prompt 是长且稳定的前缀（大约 2–4K token），每轮都会命中缓存。第一轮之后每次调用都能在输出里看到 `cache_read` 大于 0。
- **Streaming**：`client.messages.stream()`，逐 token 显示；`get_final_message()` 拿最终对象好读 `usage`。

## 你可以怎么改

- **换成 Sonnet 4.6**：`MODEL = "claude-sonnet-4-6"`，同样支持 adaptive thinking，便宜快一些。
- **加持久化**：现在 `messages` 只存在内存里；改成每轮把 `messages` + 档案写到文件/DB，就是最简单的跨会话记忆。
- **接 `evaluation.md` 的 12 指标**：跑完对话后把 transcript 交给评审人，或者用另一次 Claude API 调用做自动评估。

## 已知限制

- 学习者画像目前是**只读**的：老师读得到、但不会自动更新它。这是有意的——先证明"读进来会被用"，再谈"如何更新"。真正的更新逻辑属于验收之后要做的事，见契约 v3 的"复审触发点"。
- 没做 rate-limit 处理：SDK 默认 `max_retries=2` 已经够 demo 用。
