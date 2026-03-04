"""
A股智能分析系统 - 多交易员辩论决策平台
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time

from data_fetcher import fetch_all_data
from ai_analysts import TRADER_PROFILES, run_trader_analysis, run_manager_summary

# ──────────────────────────────────────────
# 页面配置
# ──────────────────────────────────────────
st.set_page_config(
    page_title="A股智能分析 · 多空辩论系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# 自定义样式
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');

/* 全局 */
.stApp {
    font-family: 'Noto Sans SC', sans-serif;
}

/* 标题区域 */
.main-header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.06);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(230,57,70,0.08) 0%, transparent 60%);
    animation: pulse 6s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}
.main-header h1 {
    font-size: 2rem;
    font-weight: 900;
    background: linear-gradient(90deg, #E63946, #FF6B6B, #FFE66D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    position: relative;
}
.main-header p {
    color: #8888aa;
    font-size: 0.9rem;
    margin-top: 0.3rem;
    position: relative;
}

/* 指标卡片 */
.metric-card {
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-card .label {
    color: #6c7293;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.metric-card .value {
    font-size: 1.5rem;
    font-weight: 700;
    margin-top: 0.2rem;
}
.up { color: #E63946; }
.down { color: #2ECC71; }
.neutral { color: #E8E8ED; }

/* 交易员卡片 */
.trader-card {
    background: linear-gradient(145deg, #12121c, #1a1a2e);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s;
}
.trader-card:hover {
    border-color: rgba(230,57,70,0.3);
    box-shadow: 0 4px 20px rgba(230,57,70,0.08);
}
.trader-name {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.trader-style {
    color: #6c7293;
    font-size: 0.8rem;
    margin-bottom: 0.8rem;
}

/* Manager 卡片 */
.manager-card {
    background: linear-gradient(145deg, #1a0a0a, #2a1020);
    border: 2px solid rgba(230,57,70,0.3);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 1rem;
}

/* 新闻列表 */
.news-item {
    background: rgba(255,255,255,0.02);
    border-left: 3px solid #E63946;
    padding: 0.6rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
}
.news-time {
    color: #6c7293;
    font-size: 0.7rem;
}

/* 侧边栏 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a14, #12121e);
}

/* 按钮 */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    transition: all 0.3s;
}

/* 去掉 Streamlit 水印 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# Header
# ──────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📈 A股智能分析 · 多空辩论决策系统</h1>
    <p>4位 AI 交易员实时辩论 × 量化数据驱动 × 新闻事件分析</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# 侧边栏 - 股票输入
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 股票查询")
    symbol = st.text_input(
        "输入股票代码",
        value="000001",
        placeholder="例: 600519, 000001",
        help="输入6位A股代码，如 600519（贵州茅台）",
    )

    st.markdown("---")
    st.markdown("### ⚙️ 设置")
    st.caption("模型 API 已内置，无需额外配置。")
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#555;font-size:0.7rem;'>"
        "Powered by AKShare + LLM<br>仅供学习参考，不构成投资建议</div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────
# 初始化 Session State
# ──────────────────────────────────────────
if "stock_data" not in st.session_state:
    st.session_state.stock_data = None
if "trader_results" not in st.session_state:
    st.session_state.trader_results = {}
if "manager_result" not in st.session_state:
    st.session_state.manager_result = None
if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = ""


# ──────────────────────────────────────────
# Step 1: 数据获取
# ──────────────────────────────────────────
col_btn1, col_btn2, _ = st.columns([1, 1, 2])

with col_btn1:
    fetch_clicked = st.button("📡 获取股票数据", type="primary", use_container_width=True)

with col_btn2:
    analyze_clicked = st.button(
        "🧠 启动 AI 辩论分析",
        type="secondary",
        use_container_width=True,
        disabled=(st.session_state.stock_data is None),
    )

# ── 获取数据 ──
if fetch_clicked:
    st.session_state.trader_results = {}
    st.session_state.manager_result = None
    st.session_state.current_symbol = symbol
    with st.spinner(f"正在获取 {symbol} 的全量数据，请稍候..."):
        data = fetch_all_data(symbol)
        st.session_state.stock_data = data
    st.rerun()


# ──────────────────────────────────────────
# 展示数据
# ──────────────────────────────────────────
if st.session_state.stock_data is not None:
    data = st.session_state.stock_data
    sym = st.session_state.current_symbol

    # ── 行情概览 ──
    quote = data.get("quote", {})
    if quote:
        name = quote.get("名称", sym)
        price = quote.get("最新价", "--")
        change_pct = quote.get("涨跌幅", 0)
        change_amt = quote.get("涨跌额", 0)

        try:
            pct_val = float(change_pct)
            css_class = "up" if pct_val > 0 else ("down" if pct_val < 0 else "neutral")
            sign = "+" if pct_val > 0 else ""
        except (ValueError, TypeError):
            css_class = "neutral"
            sign = ""
            pct_val = 0

        st.markdown(f"""
        <div style="display:flex;align-items:baseline;gap:1rem;margin-bottom:0.5rem;">
            <span style="font-size:1.6rem;font-weight:900;color:#E8E8ED;">{name}</span>
            <span style="color:#6c7293;font-size:0.9rem;">{sym}</span>
            <span class="{css_class}" style="font-size:2rem;font-weight:900;">¥{price}</span>
            <span class="{css_class}" style="font-size:1rem;">{sign}{change_pct}%  ({sign}{change_amt})</span>
        </div>
        """, unsafe_allow_html=True)

        # 指标卡片行
        cols = st.columns(6)
        card_data = [
            ("今开", quote.get("今开", "--")),
            ("最高", quote.get("最高", "--")),
            ("最低", quote.get("最低", "--")),
            ("成交量", quote.get("成交量", "--")),
            ("换手率", f"{quote.get('换手率', '--')}%"),
            ("市盈率", quote.get("市盈率-动态", "--")),
        ]
        for col, (label, val) in zip(cols, card_data):
            col.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="value neutral">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 选项卡 ──
    tab_chart, tab_tech, tab_fin, tab_flow, tab_news, tab_info = st.tabs(
        ["📊 K线图表", "📐 技术指标", "💰 财务数据", "💧 资金流向", "📰 新闻事件", "🏢 公司信息"]
    )

    # ── K线图 ──
    with tab_chart:
        kline = data.get("kline")
        if kline is not None and not kline.empty:
            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
            )
            fig.add_trace(go.Candlestick(
                x=kline["日期"], open=kline["开盘"], high=kline["最高"],
                low=kline["最低"], close=kline["收盘"], name="K线",
                increasing_line_color="#E63946", decreasing_line_color="#2ECC71",
                increasing_fillcolor="#E63946", decreasing_fillcolor="#2ECC71",
            ), row=1, col=1)

            # 均线
            close = kline["收盘"].astype(float)
            for w, color in [(5, "#FFE66D"), (20, "#4ECDC4"), (60, "#FF6B6B")]:
                ma = close.rolling(w).mean()
                fig.add_trace(go.Scatter(
                    x=kline["日期"], y=ma, name=f"MA{w}",
                    line=dict(width=1, color=color),
                ), row=1, col=1)

            # 成交量
            colors = ["#E63946" if c >= o else "#2ECC71"
                      for c, o in zip(kline["收盘"].astype(float), kline["开盘"].astype(float))]
            fig.add_trace(go.Bar(
                x=kline["日期"], y=kline["成交量"], name="成交量",
                marker_color=colors, opacity=0.7,
            ), row=2, col=1)

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0A0A0F",
                plot_bgcolor="#0A0A0F",
                height=550,
                margin=dict(l=50, r=20, t=30, b=30),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", y=1.06),
                font=dict(family="Noto Sans SC"),
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("未获取到K线数据")

    # ── 技术指标 ──
    with tab_tech:
        tech = data.get("technical", {})
        if tech:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("##### 均线系统")
                for k in ["MA5", "MA10", "MA20", "MA60"]:
                    v = tech.get(k)
                    if v:
                        st.metric(k, f"¥{v}")

            with col2:
                st.markdown("##### MACD / RSI / KDJ")
                for k in ["MACD_DIF", "MACD_DEA", "MACD", "RSI_14", "KDJ_K", "KDJ_D", "KDJ_J"]:
                    v = tech.get(k)
                    if v is not None:
                        st.metric(k, f"{v}")

            with col3:
                st.markdown("##### 布林带 / 风险")
                for k in ["BOLL_UPPER", "BOLL_MID", "BOLL_LOWER", "VOLATILITY_20D", "MAX_DRAWDOWN_60D"]:
                    v = tech.get(k)
                    if v is not None:
                        unit = "%" if "VOLATILITY" in k or "DRAWDOWN" in k else "¥"
                        st.metric(k, f"{v}{unit}")
        else:
            st.info("技术指标计算中...")

    # ── 财务数据 ──
    with tab_fin:
        fin = data.get("financial", {})
        if fin:
            for name, df in fin.items():
                if df is not None and not df.empty:
                    label_map = {"financial_abstract": "📋 主要财务指标", "profit": "📈 利润表", "balance": "📊 资产负债表"}
                    st.markdown(f"##### {label_map.get(name, name)}")
                    st.dataframe(df, use_container_width=True, height=250)
        else:
            st.info("未获取到财务数据")

    # ── 资金流向 ──
    with tab_flow:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### 💰 个股资金流向")
            flow = data.get("money_flow")
            if flow is not None and not flow.empty:
                st.dataframe(flow, use_container_width=True, height=300)
            else:
                st.info("未获取到资金流向数据")

        with col_b:
            st.markdown("##### 🌏 北向资金")
            north = data.get("north_flow")
            if north is not None and not north.empty:
                st.dataframe(north.tail(10), use_container_width=True, height=300)
            else:
                st.info("未获取到北向资金数据")

        st.markdown("##### 📊 融资融券")
        margin = data.get("margin")
        if margin is not None and not margin.empty:
            st.dataframe(margin, use_container_width=True)
        else:
            st.info("未获取到融资融券数据")

    # ── 新闻 ──
    with tab_news:
        news = data.get("news", [])
        if news:
            for n in news:
                st.markdown(f"""
                <div class="news-item">
                    <div class="news-time">{n['time']}  ·  {n['source']}</div>
                    <div style="margin-top:0.3rem;font-weight:500;">{n['title']}</div>
                    <div style="color:#8888aa;font-size:0.8rem;margin-top:0.2rem;">{n['content'][:200]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("未获取到相关新闻")

    # ── 公司信息 ──
    with tab_info:
        info = data.get("info", {})
        if info:
            for k, v in info.items():
                st.markdown(f"**{k}**：{v}")
        else:
            st.info("未获取到公司信息")


# ──────────────────────────────────────────
# Step 2: AI 辩论分析
# ──────────────────────────────────────────
if analyze_clicked and st.session_state.stock_data is not None:
    sym = st.session_state.current_symbol
    data = st.session_state.stock_data

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;margin:1.5rem 0;">
        <span style="font-size:1.5rem;font-weight:900;
        background:linear-gradient(90deg,#E63946,#FFE66D);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        🧠 AI 交易团队辩论分析中...
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 4 位交易员并行分析
    trader_results = {}
    cols = st.columns(2)

    for idx, (key, profile) in enumerate(TRADER_PROFILES.items()):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"""
                <div class="trader-card">
                    <div class="trader-name">{profile['name']}</div>
                    <div class="trader-style">{profile['style']}</div>
                </div>
                """, unsafe_allow_html=True)

                with st.spinner(f"{profile['name']} 分析中..."):
                    result = run_trader_analysis(key, data, sym)
                    trader_results[key] = result
                    st.markdown(result)

    st.session_state.trader_results = trader_results

    # Manager 汇总
    st.markdown("---")
    st.markdown("""
    <div class="manager-card">
        <div style="font-size:1.3rem;font-weight:900;
        background:linear-gradient(90deg,#E63946,#FF6B6B);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        👔 总经理 · 钱总 — 最终决策
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("钱总正在综合各方意见..."):
        manager_result = run_manager_summary(sym, trader_results, data)
        st.session_state.manager_result = manager_result

    st.markdown(f"""
    <div class="manager-card" style="margin-top:0.5rem;">
        <div style="white-space:pre-wrap;">{manager_result}</div>
    </div>
    """, unsafe_allow_html=True)

# ── 展示之前的分析结果 ──
elif st.session_state.trader_results and not analyze_clicked:
    sym = st.session_state.current_symbol
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center;margin:1rem 0;">
        <span style="font-size:1.2rem;font-weight:700;color:#8888aa;">
        📋 上次分析结果 ({sym})
        </span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for idx, (key, profile) in enumerate(TRADER_PROFILES.items()):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="trader-card">
                <div class="trader-name">{profile['name']}</div>
                <div class="trader-style">{profile['style']}</div>
            </div>
            """, unsafe_allow_html=True)
            result = st.session_state.trader_results.get(key, "")
            if result:
                st.markdown(result)

    if st.session_state.manager_result:
        st.markdown("---")
        st.markdown(f"""
        <div class="manager-card">
            <div style="font-size:1.3rem;font-weight:900;
            background:linear-gradient(90deg,#E63946,#FF6B6B);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            👔 总经理 · 钱总 — 最终决策
            </div>
            <div style="white-space:pre-wrap;margin-top:1rem;">{st.session_state.manager_result}</div>
        </div>
        """, unsafe_allow_html=True)
