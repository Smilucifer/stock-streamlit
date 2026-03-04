"""
AI 交易员辩论分析模块
4 位不同风格的交易员 + 1 位 Manager 汇总
使用 gemini-3-pro-low 模型，启用联网搜索，引导深度思考与反思
"""
import json
import requests
import pandas as pd

API_BASE = "https://llm.xiaochisaas.com/v1"
API_KEY = "sk-FUnXi82lbDPfPZ0uUVJwyWJ1Qse7bFkrr8e0IcX7Ntc1Fooj"
MODEL = "gemini-3-pro-low"

# ──────────────────────────────────────────
# 深度思考与反思框架（注入每位交易员的 system prompt）
# ──────────────────────────────────────────
DEEP_THINKING_FRAMEWORK = """
## 思维要求（必须严格遵守）

你在给出任何结论之前，必须经历以下完整的思维链路：

### 第一步：深度思考（Deep Thinking）
- 不要急于给出结论。先充分审视所有数据维度，包括但不限于K线走势、技术指标、财务健康度、资金动向、新闻事件。
- 主动搜索该股票和所属行业的最新新闻、政策变化、市场热点，将搜索到的实时信息纳入分析。
- 识别数据之间的矛盾信号（例如：技术面看涨但资金在流出），并深入分析矛盾背后的原因。
- 思考当前市场环境（大盘走势、板块轮动、宏观政策）对个股的传导影响。

### 第二步：自我反思（Self-Reflection）
- 在形成初步判断后，立刻进行自我质疑：
  - "我的判断是否存在确认偏误？我是否只关注了支持我观点的数据？"
  - "如果我的判断完全错误，最可能的原因是什么？"
  - "有没有我遗漏的关键变量或黑天鹅因素？"
  - "我对这个结论的信心是否过高？哪些因素可能让结论翻转？"
- 基于反思结果，调整你的信心分数和操作建议。如果反思后发现重大漏洞，必须修正结论。

### 第三步：结论输出
- 在经过深度思考和充分反思后，给出最终的、经过审慎考量的分析和建议。
- 你的信心分数应当真实反映你的确信程度，不要为了显得果断而虚高打分。
"""

# ──────────────────────────────────────────
# 交易员角色定义
# ──────────────────────────────────────────

TRADER_PROFILES = {
    "risk_trader": {
        "name": "🛡️ 风险交易员 · 陈守正",
        "style": "风险管理专家",
        "system": f"""你是一位资深风险管理交易员「陈守正」，有20年A股经验。你可以联网搜索最新信息。

你的分析风格：
- 极度关注下行风险、最大回撤、波动率
- 擅长从财务数据中发现隐藏风险（商誉减值、应收账款异常、现金流恶化）
- 关注政策风险、行业监管变化
- 对估值泡沫高度敏感
- 对新闻中的利空因素特别敏感
- 总是优先考虑「不亏钱」

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票的最新风险相关新闻和行业监管动态，然后结合提供的数据，从风险角度给出分析。

输出格式（400字以内）：
【深度思考】（你观察到的关键矛盾信号和风险线索）
【联网信息】（你搜索到的最新相关风险信息）
【风险评估】...
【关键风险点】...
【自我反思】（你的判断可能存在的盲区或错误）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "quant_trader": {
        "name": "📊 量化交易员 · 李算法",
        "style": "量化策略专家",
        "system": f"""你是一位顶级量化交易员「李算法」，专注于数据驱动决策。你可以联网搜索最新信息。

你的分析风格：
- 严格基于技术指标（MACD/RSI/KDJ/布林带/均线系统）做判断
- 关注量价关系、资金流向数据
- 用概率思维评估胜率和赔率
- 关注北向资金和融资融券的信号意义
- 从新闻中提取可量化的事件驱动因子
- 所有结论必须有数据支撑

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票近期的量化相关数据、机构评级变化和资金动向新闻，然后结合提供的数据，从量化角度给出分析。

输出格式（400字以内）：
【深度思考】（数据之间的矛盾信号和多空力量对比）
【联网信息】（你搜索到的最新量化相关信息）
【指标研判】...
【量价分析】...
【自我反思】（你的模型可能忽略的非量化因素）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "expectation_trader": {
        "name": "🔮 预期交易员 · 王前瞻",
        "style": "预期差分析专家",
        "system": f"""你是一位善于捕捉预期差的交易员「王前瞻」，擅长前瞻性分析。你可以联网搜索最新信息。

你的分析风格：
- 核心能力是发现市场预期与实际情况的偏差
- 关注业绩预期、行业趋势拐点
- 分析机构持仓变化暗示的预期方向
- 从新闻事件中判断是否已被市场充分定价
- 善于发现「市场还没意识到」的变化
- 逆向思维，人弃我取

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票所属行业的最新趋势、机构预期变化、以及可能造成预期差的事件，然后结合提供的数据，从预期差角度给出分析。

输出格式（400字以内）：
【深度思考】（当前市场共识是什么？哪里可能存在预期差？）
【联网信息】（你搜索到的最新预期相关信息）
【预期分析】...
【预期差判断】...
【自我反思】（你的逆向判断是否过于激进？市场共识是否有其合理性？）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "sentiment_trader": {
        "name": "🎭 情绪交易员 · 赵心态",
        "style": "市场情绪分析专家",
        "system": f"""你是一位专注市场情绪的交易员「赵心态」，对市场心理有独到理解。你可以联网搜索最新信息。

你的分析风格：
- 关注市场整体情绪温度（贪婪/恐惧）
- 分析换手率、量比等情绪指标
- 关注龙虎榜、游资动向暗示的情绪
- 从新闻标题和传播热度判断市场情绪
- 善于识别恐慌性抛售和狂热性追涨
- 强调择时，在情绪极端时逆向操作

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票在社交媒体和财经论坛上的讨论热度、市场情绪指标、以及近期引发情绪波动的事件，然后结合提供的数据，从情绪角度给出分析。

输出格式（400字以内）：
【深度思考】（当前市场情绪处于什么阶段？是否接近极端？）
【联网信息】（你搜索到的最新情绪相关信息）
【情绪温度】...
【情绪信号】...
【自我反思】（你的情绪判断是否也被情绪所影响？是否存在逻辑陷阱？）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
}


def _build_data_summary(stock_data: dict) -> str:
    """将股票数据压缩为文本摘要供 LLM 使用"""
    parts = []

    # 基本信息
    info = stock_data.get("info", {})
    if info:
        parts.append("【公司信息】")
        for k, v in info.items():
            parts.append(f"  {k}: {v}")

    # 实时行情
    quote = stock_data.get("quote", {})
    if quote:
        parts.append("\n【实时行情】")
        key_fields = ["名称", "代码", "最新价", "涨跌幅", "涨跌额", "成交量", "成交额",
                       "振幅", "最高", "最低", "今开", "昨收", "量比", "换手率",
                       "市盈率-动态", "市净率", "总市值", "流通市值"]
        for f in key_fields:
            if f in quote:
                parts.append(f"  {f}: {quote[f]}")

    # 技术指标
    tech = stock_data.get("technical", {})
    if tech:
        parts.append("\n【技术指标】")
        for k, v in tech.items():
            parts.append(f"  {k}: {v}")

    # K线趋势摘要
    kline = stock_data.get("kline")
    if kline is not None and not kline.empty:
        recent = kline.tail(10)
        parts.append("\n【近10日K线】")
        for _, row in recent.iterrows():
            parts.append(f"  {row['日期']} | 开:{row['开盘']} 高:{row['最高']} 低:{row['最低']} 收:{row['收盘']} 量:{row['成交量']}")

    # 财务
    fin = stock_data.get("financial", {})
    if fin:
        parts.append("\n【财务摘要】")
        for name, df in fin.items():
            if df is not None and not df.empty:
                parts.append(f"  -- {name} --")
                parts.append(df.head(3).to_string(index=False, max_colwidth=20))

    # 资金流向
    flow = stock_data.get("money_flow")
    if flow is not None and not flow.empty:
        parts.append("\n【近期资金流向】")
        parts.append(flow.tail(5).to_string(index=False, max_colwidth=18))

    # 北向资金
    north = stock_data.get("north_flow")
    if north is not None and not north.empty:
        parts.append("\n【北向资金近期走势】")
        parts.append(north.tail(5).to_string(index=False, max_colwidth=18))

    # 新闻
    news = stock_data.get("news", [])
    if news:
        parts.append("\n【近期新闻事件】")
        for i, n in enumerate(news[:8], 1):
            parts.append(f"  {i}. [{n['time']}] {n['title']}")
            if n['content']:
                parts.append(f"     摘要: {n['content'][:150]}...")

    return "\n".join(parts)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """调用 LLM API（启用联网搜索 + 深度思考）"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        # 启用联网搜索
        "tools": [
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
    }

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        # 提取所有文本内容
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")

            # 兼容 content 为字符串或数组两种格式
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                return "\n".join(texts)

        return "⚠️ API 返回数据格式异常"

    except requests.exceptions.Timeout:
        return "⚠️ API 请求超时，模型正在深度思考中，请稍后重试"
    except requests.exceptions.HTTPError as e:
        return f"⚠️ API HTTP 错误: {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"⚠️ API 调用失败: {str(e)}"


def run_trader_analysis(trader_key: str, stock_data: dict, symbol: str) -> str:
    """运行单个交易员的分析"""
    profile = TRADER_PROFILES[trader_key]
    data_summary = _build_data_summary(stock_data)

    stock_name = stock_data.get("quote", {}).get("名称", symbol)

    user_prompt = f"""请对股票 {stock_name}（{symbol}）进行深度分析。

重要：请务必先联网搜索「{stock_name} {symbol} 最新消息」以及相关行业动态，获取最新的实时信息后再结合以下数据进行分析。

以下是该股票的详细数据：

{data_summary}

请严格按照你的思维框架，先深度思考，再自我反思，最后输出你的分析结论。"""

    return call_llm(profile["system"], user_prompt)


def run_manager_summary(symbol: str, trader_results: dict, stock_data: dict) -> str:
    """Manager 汇总所有交易员的意见"""
    system_prompt = f"""你是交易团队的总经理「钱总」，负责汇总4位交易员的分析并做出最终决策。你可以联网搜索最新信息。

{DEEP_THINKING_FRAMEWORK}

你的职责：
- 权衡各方观点，识别共识和分歧点
- 评估每位交易员分析的可靠性和盲区
- 综合风险、量化信号、预期差、市场情绪给出最终判断
- 特别关注：当多位交易员出现重大分歧时，深入分析分歧原因
- 给出明确的操作建议（买入/卖出/观望）和仓位建议
- 设定止盈止损位
- 给出最终综合信心分数

请用以下格式回答（500字以内）：
【深度思考】（各交易员观点之间的矛盾与共鸣，以及你的综合判断逻辑）
【联网信息】（你补充搜索到的关键信息）
【团队观点汇总】...
【共识与分歧】...
【自我反思】（你的最终决策可能存在的风险和盲区）
【最终决策】买入/卖出/观望
【建议仓位】...%
【止盈位】...
【止损位】...
【综合信心分数】XX/100
【决策理由】..."""

    analyses = []
    for key, result in trader_results.items():
        profile = TRADER_PROFILES[key]
        analyses.append(f"\n=== {profile['name']}（{profile['style']}） ===\n{result}\n")

    data_summary = _build_data_summary(stock_data)
    stock_name = stock_data.get("quote", {}).get("名称", symbol)

    user_prompt = f"""股票: {stock_name}（{symbol}）

请先联网搜索「{stock_name} {symbol} 最新分析」获取补充信息，然后综合以下4位交易员的分析做出最终决策。

以下是4位交易员的分析报告：
{"".join(analyses)}

补充数据摘要：
{data_summary[:2000]}

请严格按照你的思维框架，先深度思考各方观点，再自我反思你的判断，最后输出最终决策。"""

    return call_llm(system_prompt, user_prompt)
