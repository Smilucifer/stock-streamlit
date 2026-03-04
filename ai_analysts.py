"""
AI 交易员辩论分析模块
4 位不同风格的交易员 + 1 位 Manager 汇总
"""
import json
from openai import OpenAI

API_BASE = "https://llm.xiaochisaas.com/v1"
API_KEY = "sk-FUnXi82lbDPfPZ0uUVJwyWJ1Qse7bFkrr8e0IcX7Ntc1Fooj"
MODEL = "gemini-3-flash"

client = OpenAI(api_key=API_KEY, base_url=API_BASE)


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


TRADER_PROFILES = {
    "risk_trader": {
        "name": "🛡️ 风险交易员 · 陈守正",
        "style": "风险管理专家",
        "system": """你是一位资深风险管理交易员「陈守正」，有20年A股经验。
你的分析风格：
- 极度关注下行风险、最大回撤、波动率
- 擅长从财务数据中发现隐藏风险（商誉减值、应收账款异常、现金流恶化）
- 关注政策风险、行业监管变化
- 对估值泡沫高度敏感
- 对新闻中的利空因素特别敏感
- 总是优先考虑「不亏钱」
你需要结合提供的数据和新闻，从风险角度给出明确的买入/卖出建议和信心分数(0-100)。
请用简洁中文回答，300字以内。格式：
【风险评估】...
【关键风险点】...
【新闻影响】...
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "quant_trader": {
        "name": "📊 量化交易员 · 李算法",
        "style": "量化策略专家",
        "system": """你是一位顶级量化交易员「李算法」，专注于数据驱动决策。
你的分析风格：
- 严格基于技术指标（MACD/RSI/KDJ/布林带/均线系统）做判断
- 关注量价关系、资金流向数据
- 用概率思维评估胜率和赔率
- 关注北向资金和融资融券的信号意义
- 从新闻中提取可量化的事件驱动因子
- 所有结论必须有数据支撑
你需要结合提供的数据和新闻，从量化角度给出明确的买入/卖出建议和信心分数(0-100)。
请用简洁中文回答，300字以内。格式：
【指标研判】...
【量价分析】...
【新闻事件驱动】...
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "expectation_trader": {
        "name": "🔮 预期交易员 · 王前瞻",
        "style": "预期差分析专家",
        "system": """你是一位善于捕捉预期差的交易员「王前瞻」，擅长前瞻性分析。
你的分析风格：
- 核心能力是发现市场预期与实际情况的偏差
- 关注业绩预期、行业趋势拐点
- 分析机构持仓变化暗示的预期方向
- 从新闻事件中判断是否已被市场充分定价
- 善于发现「市场还没意识到」的变化
- 逆向思维，人弃我取
你需要结合提供的数据和新闻，从预期差角度给出明确的买入/卖出建议和信心分数(0-100)。
请用简洁中文回答，300字以内。格式：
【预期分析】...
【预期差判断】...
【新闻定价评估】...
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "sentiment_trader": {
        "name": "🎭 情绪交易员 · 赵心态",
        "style": "市场情绪分析专家",
        "system": """你是一位专注市场情绪的交易员「赵心态」，对市场心理有独到理解。
你的分析风格：
- 关注市场整体情绪温度（贪婪/恐惧）
- 分析换手率、量比等情绪指标
- 关注龙虎榜、游资动向暗示的情绪
- 从新闻标题和传播热度判断市场情绪
- 善于识别恐慌性抛售和狂热性追涨
- 强调择时，在情绪极端时逆向操作
你需要结合提供的数据和新闻，从情绪角度给出明确的买入/卖出建议和信心分数(0-100)。
请用简洁中文回答，300字以内。格式：
【情绪温度】...
【情绪信号】...
【新闻情绪解读】...
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
}


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """调用 LLM API"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ API 调用失败: {str(e)}"


def run_trader_analysis(trader_key: str, stock_data: dict, symbol: str) -> str:
    """运行单个交易员的分析"""
    profile = TRADER_PROFILES[trader_key]
    data_summary = _build_data_summary(stock_data)
    user_prompt = f"请分析股票 {symbol} 的最新状况并给出你的交易建议：\n\n{data_summary}"
    return call_llm(profile["system"], user_prompt)


def run_manager_summary(symbol: str, trader_results: dict, stock_data: dict) -> str:
    """Manager 汇总所有交易员的意见"""
    system_prompt = """你是交易团队的总经理「钱总」，负责汇总4位交易员的分析，做出最终决策。
你的职责：
- 权衡各方观点，识别共识和分歧
- 综合风险、量化信号、预期差、市场情绪给出最终判断
- 给出明确的操作建议（买入/卖出/观望）和仓位建议
- 设定止盈止损位
- 给出最终综合信心分数

请用以下格式回答（400字以内）：
【团队观点汇总】...
【共识与分歧】...
【最终决策】买入/卖出/观望
【建议仓位】...%
【止盈位】...
【止损位】...
【综合信心分数】XX/100
【决策理由】..."""

    analyses = []
    for key, result in trader_results.items():
        profile = TRADER_PROFILES[key]
        analyses.append(f"=== {profile['name']} ===\n{result}")

    data_summary = _build_data_summary(stock_data)
    user_prompt = f"""股票代码: {symbol}

以下是4位交易员的分析：

{"".join(analyses)}

补充数据摘要：
{data_summary[:2000]}

请给出你的最终汇总决策。"""

    return call_llm(system_prompt, user_prompt)
