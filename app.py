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

/* ── 全局 ── */
.stApp {
    font-family: 'Noto Sans SC', sans-serif;
    color: #1A1A2E;
}

/* ── 标题区域 ── */
.main-header {
    background: linear-gradient(135deg, #1A1A2E, #2D2D5E, #3A2E6E);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(212,56,13,0.15);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(212,56,13,0.08) 0%, transparent 60%);
    animation: pulse 6s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}
.main-header h1 {
    font-size: 2rem;
    font-weight: 900;
    background: linear-gradient(90deg, #FF6B35, #FFD93D, #4ECDC4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    position: relative;
}
.main-header p {
    color: #C0C8E0;
    font-size: 0.9rem;
    margin-top: 0.3rem;
    position: relative;
}

/* ── 指标卡片 ── */
.metric-card {
    background: #F5F7FA;
    border: 1px solid #E0E4EC;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-card .label {
    color: #6B7280;
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
.up { color: #D4380D; }
.down { color: #0B8A3E; }
.neutral { color: #1A1A2E; }

/* ── 交易员卡片 ── */
.trader-card {
    background: #F5F7FA;
    border: 1px solid #E0E4EC;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s;
}
.trader-card:hover {
    border-color: #D4380D;
    box-shadow: 0 4px 16px rgba(212,56,13,0.1);
}
.trader-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #B7410E;
    margin-bottom: 0.3rem;
}
.trader-style {
    color: #6B7280;
    font-size: 0.8rem;
    margin-bottom: 0.8rem;
}

/* ── Manager 卡片 ── */
.manager-card {
    background: #FFF8F0;
    border: 2px solid #D4380D;
    border-radius: 16px;
    padding: 2rem;
    margin-top: 1rem;
    color: #1A1A2E;
}

/* ── 新闻列表 ── */
.news-item {
    background: #F9FAFB;
    border-left: 3px solid #D4380D;
    padding: 0.6rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    color: #1A1A2E;
}
.news-time {
    color: #6B7280;
    font-size: 0.7rem;
}
.news-title {
    color: #1A1A2E;
    font-weight: 500;
    margin-top: 0.3rem;
}
.news-content {
    color: #4B5563;
    font-size: 0.8rem;
    margin-top: 0.2rem;
}

/* ── 侧边栏 ── */
section[data-testid="stSidebar"] {
    background: #F5F7FA;
}
section[data-testid="stSidebar"] .stMarkdown {
    color: #1A1A2E;
}

/* ── 按钮 ── */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    transition: all 0.3s;
}

/* ── Streamlit 内置元素 ── */
.stTabs [data-baseweb="tab"] {
    color: #4B5563;
}
.stTabs [aria-selected="true"] {
    color: #D4380D !important;
}
.stMarkdown, .stMarkdown p, .stMarkdown li {
    color: #1A1A2E;
}
h1, h2, h3, h4, h5, h6 {
    color: #1A1A2E !important;
}

/* metric 组件 */
[data-testid="stMetricValue"] {
    color: #1A1A2E !important;
}
[data-testid="stMetricLabel"] {
    color: #4B5563 !important;
}

/* dataframe */
.stDataFrame {
    color: #1A1A2E;
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
    <p>5位 AI 交易员实时辩论 × 量化数据驱动 × 新闻事件分析</p>
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
    enable_realtime = st.toggle(
        "⚡ 实时数据模式（AKShare）",
        value=False,
        help="开启后通过 AKShare 获取盘中实时数据：个股实时行情（替换首页价格/涨跌幅等）、三大指数实时数据、当日实时K线合并。交易时段效果最佳。",
    )
    st.caption("模型 API 已内置，无需额外配置。")
    st.caption("数据源：Tushare（Token 已内置）")
    if enable_realtime:
        st.caption("⚡ 实时数据模式：AKShare（已开启）")
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#6B7280;font-size:0.7rem;'>"
        "Powered by Tushare + AKShare + LLM<br>仅供学习参考，不构成投资建议</div>",
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
    spinner_text = f"正在获取 {symbol} 的全量数据"
    if enable_realtime:
        spinner_text += "（含实时行情/指数/K线）"
    spinner_text += "，请稍候..."
    with st.spinner(spinner_text):
        data = fetch_all_data(symbol, enable_realtime_kline=enable_realtime)
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
            <span style="font-size:1.6rem;font-weight:900;color:#1A1A2E;">{name}</span>
            <span style="color:#6B7280;font-size:0.9rem;">{sym}</span>
            <span class="{css_class}" style="font-size:2rem;font-weight:900;">¥{price}</span>
            <span class="{css_class}" style="font-size:1rem;">{sign}{change_pct}%  ({sign}{change_amt})</span>
        </div>
        """, unsafe_allow_html=True)

        # 数据来源状态提示
        rt_status = data.get("realtime_kline_status", "未启用")
        quote_src = data.get("quote_source", "Tushare")
        indices_src = data.get("indices_source", "Tushare")
        if rt_status != "未启用":
            status_parts = []
            if "AKShare" in quote_src:
                status_parts.append("行情实时")
            if "AKShare" in indices_src:
                status_parts.append("指数实时")
            if rt_status == "已合并实时K线数据":
                status_parts.append("K线已合并")
            if status_parts:
                st.caption(f"⚡ 实时模式已开启 — {' / '.join(status_parts)}（数据来源：AKShare）")
            else:
                st.caption(f"⚠️ 实时模式已开启但获取失败，当前使用 Tushare 数据")

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

    # ── 三大指数 ──
    indices = data.get("indices", {})
    if indices:
        idx_cols = st.columns(3)
        for col, (idx_name, idx_info) in zip(idx_cols, indices.items()):
            chg = idx_info.get("涨跌幅", 0)
            try:
                chg_val = float(chg)
                idx_css = "up" if chg_val > 0 else ("down" if chg_val < 0 else "neutral")
                idx_sign = "+" if chg_val > 0 else ""
            except (ValueError, TypeError):
                idx_css = "neutral"
                idx_sign = ""
            col.markdown(f"""
            <div class="metric-card" style="border-left:3px solid {'#D4380D' if idx_css == 'up' else '#0B8A3E' if idx_css == 'down' else '#9CA3AF'};">
                <div class="label">{idx_name}</div>
                <div class="value {idx_css}">{idx_info.get('收盘', '--')}</div>
                <div class="{idx_css}" style="font-size:0.85rem;">{idx_sign}{chg}%  成交额:{idx_info.get('成交额(亿)', '--')}亿</div>
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
                increasing_line_color="#D4380D", decreasing_line_color="#0B8A3E",
                increasing_fillcolor="#D4380D", decreasing_fillcolor="#0B8A3E",
            ), row=1, col=1)

            # 均线
            close = kline["收盘"].astype(float)
            for w, color in [(5, "#E67E22"), (20, "#2980B9"), (60, "#8E44AD")]:
                ma = close.rolling(w).mean()
                fig.add_trace(go.Scatter(
                    x=kline["日期"], y=ma, name=f"MA{w}",
                    line=dict(width=1, color=color),
                ), row=1, col=1)

            # 成交量
            colors = ["#D4380D" if c >= o else "#0B8A3E"
                      for c, o in zip(kline["收盘"].astype(float), kline["开盘"].astype(float))]
            fig.add_trace(go.Bar(
                x=kline["日期"], y=kline["成交量"], name="成交量",
                marker_color=colors, opacity=0.7,
            ), row=2, col=1)

            fig.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FAFBFC",
                height=550,
                margin=dict(l=50, r=20, t=30, b=30),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", y=1.06, font=dict(color="#1A1A2E")),
                font=dict(family="Noto Sans SC", color="#1A1A2E"),
            )
            fig.update_xaxes(gridcolor="rgba(0,0,0,0.06)", tickfont=dict(color="#4B5563"))
            fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", tickfont=dict(color="#4B5563"))
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
                    <div class="news-title">{n['title']}</div>
                    <div class="news-content">{n['content'][:200]}</div>
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
        background:linear-gradient(90deg,#D4380D,#E67E22);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        🧠 AI 交易团队辩论分析中...
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 5 位交易员分析
    trader_results = {}

    # 第一行：3 位交易员
    cols_row1 = st.columns(3)
    trader_keys = list(TRADER_PROFILES.keys())

    for idx in range(3):
        key = trader_keys[idx]
        profile = TRADER_PROFILES[key]
        with cols_row1[idx]:
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

    # 第二行：2 位交易员
    cols_row2 = st.columns([1, 1, 1])
    for idx in range(3, 5):
        key = trader_keys[idx]
        profile = TRADER_PROFILES[key]
        with cols_row2[idx - 3]:
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
        background:linear-gradient(90deg,#D4380D,#E67E22);
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
        <div style="white-space:pre-wrap;color:#1A1A2E;">{manager_result}</div>
    </div>
    """, unsafe_allow_html=True)

# ── 展示之前的分析结果 ──
elif st.session_state.trader_results and not analyze_clicked:
    sym = st.session_state.current_symbol
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center;margin:1rem 0;">
        <span style="font-size:1.2rem;font-weight:700;color:#4B5563;">
        📋 上次分析结果 ({sym})
        </span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    trader_keys = list(TRADER_PROFILES.keys())
    for idx, key in enumerate(trader_keys):
        profile = TRADER_PROFILES[key]
        col_idx = idx % 3
        # Start a new row after 3
        if idx == 3:
            cols = st.columns([1, 1, 1])
        with cols[col_idx if idx < 3 else idx - 3]:
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
            background:linear-gradient(90deg,#D4380D,#E67E22);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            👔 总经理 · 钱总 — 最终决策
            </div>
            <div style="white-space:pre-wrap;margin-top:1rem;color:#1A1A2E;">{st.session_state.manager_result}</div>
        </div>
        """, unsafe_allow_html=True)
