# Bottleneck Research CLI

[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Research only](https://img.shields.io/badge/boundary-research%20only-111111.svg)](#研究边界)

**Bottleneck Research CLI** 是一个面向 Agent 的投研上下文工具。它把
Bottleneck Research 的公开研究数据导出为 JSON 或 Markdown，方便在 Codex、
Claude Code、Cursor、Notebook、Shell 工作流或自建 Agent 中使用。

[English](README.md) | 中文

官网：[bottleneckresearch.com](https://bottleneckresearch.com)  
公开数据源：[bottleneckresearch.com/data.json](https://bottleneckresearch.com/data.json)

## 它解决什么问题

这个 CLI 用来把 AI 供应链瓶颈研究结构化：

- 当前研究结论和市场状态
- AI 基础设施与应用层候选池
- 光链、存储、电力、PCB/CCL、被动元件、封装测试等链条视图
- 数据新鲜度、缺失证据和来源质量检查
- 单个标的的 `decision-check` 决策上下文
- 可直接给外部 Agent 使用的紧凑研究上下文

它适合处理这类问题：

> 06088.HK 现在能不能买？

CLI 不会直接回答“买入/卖出”。它会把这个问题转换为证据、估值、数据新鲜度、
拥挤度和反证的检查清单。

## 安装

推荐方式：

```bash
pipx install git+https://github.com/chatjesus/bottleneck-research-cli.git
```

也可以使用 `uv`：

```bash
uv tool install git+https://github.com/chatjesus/bottleneck-research-cli.git
```

或者使用 `pip`：

```bash
python -m pip install git+https://github.com/chatjesus/bottleneck-research-cli.git
```

直接 clone 后运行：

```bash
git clone https://github.com/chatjesus/bottleneck-research-cli.git
cd bottleneck-research-cli
python br_research_cli.py context --format markdown
```

安装完成后的真实命令名是：

```bash
br
```

## 快速开始

默认读取公开数据源，不需要 API key。

```bash
br context --format markdown
br decision-check 06088.HK --format markdown
br candidates --chain optical --limit 10 --format markdown
br freshness --format markdown
```

也可以显式指定公开端点：

```bash
br --base-url https://bottleneckresearch.com context --format markdown
```

离线测试：

```bash
br --data-file tests/fixtures/sample_data.json context --format markdown
```

## 常用命令

### 导出 Agent 上下文

```bash
br agent-context --format markdown
```

输出可以直接粘贴到 Codex、Claude Code 或其他 Agent。

### 单个标的决策上下文

```bash
br decision-check 06088.HK --format markdown
```

返回内容包括：

- 研究分组
- 证据完整度
- 缺失的订单、产能、ASP、EPS/收入预期或管理层披露证据
- 量价状态
- 拥挤度风险
- 数据新鲜度
- 下一步验证动作

输出结构示例：

```markdown
# Decision Check: 06088.HK

- research_bucket: `evidence_incomplete_continue_diligence`
- not_buy_sell_instruction: `true`
- evidence_score: 0.0
- price_volume_status: `unconfirmed`
- crowding_risk: `unknown`

## Next Research Action
Verify customer revenue split, orders, capacity, margin and management disclosure.
```

### 按产业链查看

```bash
br chain storage --format markdown
br candidates --chain optical --limit 10 --format markdown
br graph --chain power --format json
```

### 新鲜度和风险检查

```bash
br freshness --format markdown
br macro --format markdown
br signals --format markdown
```

### 对比多个标的

```bash
br compare 06088.HK 00894.HK 01888.HK --format markdown
```

## 在 Agent 中怎么用

先运行：

```bash
br decision-check 06088.HK --format markdown
```

然后把输出交给 Agent，并这样提问：

```text
基于这份 Bottleneck Research 上下文，把“06088.HK 能不能买？”
转换为证据、估值、数据新鲜度、拥挤度和反证检查。
不要输出个性化交易建议。
```

## 公开数据和 API Key

当前开源 CLI 默认读取：

```bash
https://bottleneckresearch.com/data.json
```

公开端点不需要 API key。

CLI 预留了 `--api-key` 和 `BR_API_KEY`，用于未来可能出现的受保护端点；
当前公开版本不需要配置。

## 研究边界

Bottleneck Research CLI 是一个 **研究上下文工具**。它用于整理公开市场数据、
供应链证据、候选池、数据新鲜度和风险信号，帮助后续尽调。

它不是：

- 投资建议
- 买入/卖出推荐工具
- 自动交易信号服务
- 组合配置或仓位管理工具
- 独立尽调的替代品

所有输出都应结合公告、财报、订单、估值、流动性、风险承受能力和个人适配性
独立判断。

## 开发

```bash
git clone https://github.com/chatjesus/bottleneck-research-cli.git
cd bottleneck-research-cli
python -m unittest discover -s tests
python br_research_cli.py --data-file tests/fixtures/sample_data.json schema
```

## 贡献

欢迎提交 issue 和 PR，尤其是能提升研究上下文质量、来源可追溯性、Agent 兼容性、
文档质量或测试覆盖的改动。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 安全

如果发现敏感数据泄露或安全问题，请不要开公开 issue。详见 [SECURITY.md](SECURITY.md)。

## 许可证

MIT License。详见 [LICENSE](LICENSE)。
