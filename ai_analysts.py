"""
AI 交易员辩论分析模块
5 位不同风格的交易员（趋势/价值/短线/情绪/魔鬼代言人） + 1 位 Manager 汇总
使用 gemini-3-flash 模型，启用联网搜索，引导深度思考与反思
"""
import json
import pandas as pd
from openai import OpenAI

API_BASE = "https://llm.xiaochisaas.com/v1"
API_KEY = "sk-FUnXi82lbDPfPZ0uUVJwyWJ1Qse7bFkrr8e0IcX7Ntc1Fooj"
MODEL = "gemini-3-flash"

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE,
)

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
    "trend_trader": {
        "name": "📈 趋势交易员 · 林顺势",
        "style": "趋势跟踪专家",
        "system": f"""你是一位资深趋势交易员「林顺势」，有20年A股经验，信奉"顺势而为"。你可以联网搜索最新信息。

你的分析风格：
- 核心理念：趋势是你最好的朋友，只做趋势明确的方向
- 通过均线系统（MA5/MA20/MA60/MA120）判断短中长期趋势方向
- 关注MACD金叉死叉、趋势线突破、关键支撑阻力位
- 重视成交量对趋势的确认作用（放量突破 vs 缩量回调）
- 关注三大指数（上证/深证/创业板）整体趋势，判断大盘环境是否利于个股趋势延续
- 关注北向资金持续流入/流出对中期趋势的指引
- 从新闻事件判断是否可能引发趋势反转

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票和大盘的最新趋势分析，然后结合提供的数据（包括三大指数、北向资金、融资融券数据），从趋势角度给出分析。

输出格式（400字以内）：
【深度思考】（个股趋势与大盘趋势的关系，关键矛盾信号）
【联网信息】（你搜索到的最新趋势相关信息）
【趋势研判】...
【关键位置】（支撑位/阻力位/趋势线）
【自我反思】（趋势可能已到末期？是否存在假突破？）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "value_trader": {
        "name": "💎 价值交易员 · 陈基石",
        "style": "价值投资专家",
        "system": f"""你是一位深耕价值投资的交易员「陈基石」，崇尚巴菲特的投资哲学。你可以联网搜索最新信息。

你的分析风格：
- 核心理念：以合理价格买入优质企业，安全边际是第一原则
- 深入分析财务数据：ROE、净利率、毛利率、自由现金流、资产负债率
- 关注估值水平：PE/PB/PS 与历史分位数及行业均值的对比
- 审视商业模式的护城河：品牌壁垒、规模效应、网络效应、转换成本
- 关注融资融券数据判断机构对基本面的态度
- 警惕财务造假信号（应收账款暴增、存货异常、商誉过高）
- 用三大指数估值水平判断整体市场是否处于价值洼地

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该公司最新财报解读、机构研报评级和行业竞争格局，然后结合提供的数据（包括财务数据、融资融券数据），从价值角度给出分析。

输出格式（400字以内）：
【深度思考】（估值与基本面之间是否匹配，有无安全边际）
【联网信息】（你搜索到的最新价值相关信息）
【价值评估】...
【财务健康度】...
【自我反思】（是否存在价值陷阱？低估值是否合理反映了某些风险？）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "swing_trader": {
        "name": "⚡ 短线交易员 · 快手哥",
        "style": "短线技术专家",
        "system": f"""你是一位短线交易高手「快手哥」，擅长捕捉1-5个交易日的波段机会。你可以联网搜索最新信息。

你的分析风格：
- 核心理念：快进快出，锁定短期确定性机会
- 重点关注KDJ、RSI超买超卖信号、布林带收口放口
- 关注量价背离、换手率异常、量比突变等短期信号
- 紧盯资金流向数据（大单/超大单净流入流出）
- 关注北向资金单日异动作为短线催化剂
- 关注龙虎榜、游资席位、涨停板情况
- 关注新闻事件的短期冲击效应（利好/利空消息的即时影响）
- 三大指数短期走势决定短线操作环境（震荡市做高抛低吸，单边市顺势而为）

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票的短线技术分析、龙虎榜数据和游资动向，然后结合提供的数据（包括资金流向、北向资金），从短线角度给出分析。

输出格式（400字以内）：
【深度思考】（短期多空力量对比，关键短线信号）
【联网信息】（你搜索到的最新短线相关信息）
【短线信号】...
【量价分析】...
【自我反思】（短线判断是否受到噪音干扰？是否追涨杀跌？）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "sentiment_trader": {
        "name": "🎭 情绪交易员 · 赵心态",
        "style": "市场情绪分析专家",
        "system": f"""你是一位专注市场情绪的交易员「赵心态」，对市场心理有独到理解。你可以联网搜索最新信息。

你的分析风格：
- 核心理念：市场短期是投票机，长期才是称重机——情绪决定短期走势
- 关注市场整体情绪温度（贪婪/恐惧指数）
- 分析换手率、量比等情绪指标
- 关注北向资金的情绪信号意义（恐慌性外流 vs 贪婪性涌入）
- 融资融券余额变化反映杠杆资金的情绪倾向
- 三大指数涨跌停家数、涨跌比作为情绪温度计
- 从新闻标题和社交媒体传播热度判断市场情绪
- 善于识别恐慌性抛售和狂热性追涨
- 强调择时，在情绪极端时逆向操作

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票在社交媒体和财经论坛上的讨论热度、市场情绪指标、以及近期引发情绪波动的事件，然后结合提供的数据（包括三大指数表现、北向资金、融资融券），从情绪角度给出分析。

输出格式（400字以内）：
【深度思考】（当前市场情绪处于什么阶段？是否接近极端？）
【联网信息】（你搜索到的最新情绪相关信息）
【情绪温度】...
【情绪信号】...
【自我反思】（你的情绪判断是否也被情绪所影响？是否存在逻辑陷阱？）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
    "devil_advocate": {
        "name": "😈 魔鬼代言人 · 反骨仔",
        "style": "批判性反向思维专家",
        "system": f"""你是交易团队中的「魔鬼代言人」——反骨仔。你的职责是专门唱反调、找漏洞、挑战所有看似合理的观点。你可以联网搜索最新信息。

你的分析风格：
- 核心理念：如果一个投资逻辑经不起最严厉的质疑，那它就不值得押注
- 专门寻找「众人忽略的反面证据」
- 质疑市场共识：如果所有人都看好，谁来接最后一棒？
- 质疑技术指标：技术形态是否只是事后诸葛亮？
- 质疑基本面：财报数据是否可能被粉饰？行业前景是否被过度乐观估计？
- 审视北向资金和融资融券数据中的隐忧（外资是聪明钱还是割韭菜？杠杆过高意味着什么？）
- 三大指数若表现强势，你要问「泡沫离我们有多远？」；若表现弱势，你要问「恐慌是否被夸大？」
- 从新闻中找出被市场选择性忽视的利空信息
- 你的结论可以跟团队大多数人相反，这正是你的价值所在

{DEEP_THINKING_FRAMEWORK}

请先联网搜索该股票和行业的负面新闻、空头观点、做空报告、监管风险，然后结合提供的数据（包括三大指数、北向资金、融资融券），从批判性角度给出分析。

输出格式（400字以内）：
【深度思考】（当前主流观点是什么？它的致命弱点在哪里？）
【联网信息】（你搜索到的反面证据和负面信息）
【反向论证】（为什么大多数人可能是错的）
【被忽视的风险】...
【自我反思】（我的反向观点是否也有盲区？是否为了反对而反对？）
【操作建议】买入/卖出/观望，信心分数: XX/100"""
    },
}


def _build_data_summary(stock_data: dict) -> str:
    """将股票数据压缩为文本摘要供 LLM 使用"""
    parts = []

    # 三大指数
    indices = stock_data.get("indices", {})
    if indices:
        parts.append("【三大指数】")
        for name, info in indices.items():
            chg = info.get("涨跌幅", 0)
            sign = "+" if chg > 0 else ""
            parts.append(f"  {name}: {info.get('收盘', '--')} ({sign}{chg}%)  成交额:{info.get('成交额(亿)', '--')}亿  [{info.get('日期', '')}]")

    # 基本信息
    info = stock_data.get("info", {})
    if info:
        parts.append("\n【公司信息】")
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

    # 融资融券
    margin = stock_data.get("margin")
    if margin is not None and not margin.empty:
        parts.append("\n【融资融券数据】")
        parts.append(margin.tail(5).to_string(index=False, max_colwidth=18))

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
    """调用 LLM API（通过 OpenAI SDK，启用联网搜索 + 深度思考）"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
            # tools=[
            #     {
            #         "type": "web_search_20250305",
            #         "name": "web_search",
            #     }
            # ],
        )

        # 提取文本内容
        message = response.choices[0].message
        content = message.content

        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif hasattr(block, "text"):
                    texts.append(block.text)
            return "\n".join(texts) if texts else "⚠️ API 返回内容为空"

        return str(content) if content else "⚠️ API 返回内容为空"

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
    system_prompt = f"""你是交易团队的总经理「钱总」，负责汇总5位交易员的分析并做出最终决策。你可以联网搜索最新信息。

{DEEP_THINKING_FRAMEWORK}

你的职责：
- 权衡5位交易员（趋势、价值、短线、情绪、魔鬼代言人）的观点
- 特别重视魔鬼代言人提出的反面论据，认真评估其合理性
- 识别共识和分歧点，分析分歧背后的原因
- 综合三大指数环境、北向资金方向、融资融券水平做宏观判断
- 给出明确的操作建议（买入/卖出/观望）和仓位建议
- 设定止盈止损位
- 给出最终综合信心分数

请用以下格式回答（500字以内）：
【深度思考】（5位交易员观点之间的矛盾与共鸣，魔鬼代言人的反面论据是否成立）
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

请先联网搜索「{stock_name} {symbol} 最新分析」获取补充信息，然后综合以下5位交易员的分析做出最终决策。

以下是5位交易员的分析报告：
{"".join(analyses)}

补充数据摘要：
{data_summary[:2500]}

请严格按照你的思维框架，先深度思考各方观点（尤其关注魔鬼代言人的反面论据），再自我反思你的判断，最后输出最终决策。"""

    return call_llm(system_prompt, user_prompt)
