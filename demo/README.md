# 可直接运行的演示

一个能直接跑起来的最小闭环。没有 API Key 时使用内置的本地引导流程；配置了 Anthropic API Key 后，会自动把学习契约、老师角色和学习者画像交给 Claude，进行自由多轮对话。

## 直接运行（无需安装、无需 API Key）

在仓库根目录执行：

```sh
python3 demo/tutor.py
```

本地模式是一个轻量、确定性的教学引导器，不会冒充大模型，也不具备自由知识问答能力。它用于让刚拉取的项目立即可体验。

切换老师或携带档案：

```sh
python3 demo/tutor.py --tutor zhouzhou
python3 demo/tutor.py --tutor zhiyuan --profile examples/learner-profile.example.json
```

## 可选：启用 Claude 完整对话

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填入你的 ANTHROPIC_API_KEY
source .env
python tutor.py
```

## 用法

```sh
# 自动选择：有密钥用 Claude，无密钥用本地模式
python tutor.py

# 明确指定本地模式
python tutor.py --mode local

# 明确指定 Claude（缺少密钥时会给出提示）
python tutor.py --mode anthropic

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
