"""
数据获取模块 - 通过 Tushare 获取 A 股数据
自定义 API 地址，Token 已内置
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ──────────────────────────────────────────
# Tushare 自定义配置
# ──────────────────────────────────────────
TUSHARE_API_URL = "http://tushare.nlink.vip"
TUSHARE_TOKEN = "b007202603040326140ovpip78movej0o9"


def _ts_query(api_name: str, params: dict = None, fields: str = "") -> pd.DataFrame:
    """通用 Tushare HTTP 请求封装"""
    payload = {
        "api_name": api_name,
        "token": TUSHARE_TOKEN,
        "params": params or {},
        "fields": fields,
    }
    try:
        resp = requests.post(TUSHARE_API_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            return pd.DataFrame()
        fields_list = data.get("data", {}).get("fields", [])
        items = data.get("data", {}).get("items", [])
        if not fields_list or not items:
            return pd.DataFrame()
        return pd.DataFrame(items, columns=fields_list)
    except Exception:
        return pd.DataFrame()


def _to_ts_code(symbol: str) -> str:
    """纯数字代码 -> tushare ts_code 格式"""
    if symbol.startswith(("6", "9")):
        return f"{symbol}.SH"
    else:
        return f"{symbol}.SZ"


def _format_yi(val):
    """数值转亿元显示"""
    if val is None or pd.isna(val):
        return "--"
    try:
        v = float(val)
        if abs(v) >= 1e8:
            return f"{v / 1e8:.2f}亿"
        elif abs(v) >= 1e4:
            return f"{v / 1e4:.2f}万"
        else:
            return f"{v:.2f}"
    except (ValueError, TypeError):
        return "--"


def _format_market_cap(val):
    """万元 -> 可读格式"""
    if val is None or pd.isna(val):
        return "--"
    try:
        v = float(val)
        if v >= 10000:
            return f"{v / 10000:.2f}亿"
        else:
            return f"{v:.2f}万"
    except (ValueError, TypeError):
        return "--"


# ──────────────────────────────────────────
# K线数据
# ──────────────────────────────────────────
def get_stock_kline(symbol: str) -> pd.DataFrame:
    """获取近一年日K线（前复权），包含最新交易日数据"""
    ts_code = _to_ts_code(symbol)
    now = datetime.now()
    end = now.strftime("%Y%m%d")
    start = (now - timedelta(days=365)).strftime("%Y%m%d")

    df = _ts_query("daily", {
        "ts_code": ts_code,
        "start_date": start,
        "end_date": end,
    })
    if df.empty:
        return df

    # 获取复权因子做前复权
    adj_df = _ts_query("adj_factor", {
        "ts_code": ts_code,
        "start_date": start,
        "end_date": end,
    })

    if not adj_df.empty and "adj_factor" in adj_df.columns:
        df = df.merge(adj_df[["trade_date", "adj_factor"]], on="trade_date", how="left")
        latest_factor = df["adj_factor"].iloc[0]  # 最新日期的因子（df默认倒序）
        if latest_factor and latest_factor != 0:
            ratio = df["adj_factor"] / latest_factor
            for col in ["open", "high", "low", "close"]:
                if col in df.columns:
                    df[col] = (df[col] * ratio).round(2)

    df = df.sort_values("trade_date").reset_index(drop=True)

    df = df.rename(columns={
        "trade_date": "日期",
        "open": "开盘",
        "high": "最高",
        "low": "最低",
        "close": "收盘",
        "vol": "成交量",
        "amount": "成交额",
        "pct_chg": "涨跌幅",
        "change": "涨跌额",
    })
    return df


# ──────────────────────────────────────────
# 公司基本信息
# ──────────────────────────────────────────
def get_stock_info(symbol: str) -> dict:
    """获取公司基本信息"""
    ts_code = _to_ts_code(symbol)
    info = {}

    df = _ts_query("stock_basic", {
        "ts_code": ts_code,
    }, fields="ts_code,symbol,name,area,industry,market,list_date,exchange,fullname")

    if not df.empty:
        row = df.iloc[0]
        info["股票代码"] = row.get("ts_code", "")
        info["股票名称"] = row.get("name", "")
        info["公司全称"] = row.get("fullname", "")
        info["所在地区"] = row.get("area", "")
        info["所属行业"] = row.get("industry", "")
        info["市场类型"] = row.get("market", "")
        info["上市日期"] = row.get("list_date", "")
        info["交易所"] = row.get("exchange", "")

    df2 = _ts_query("stock_company", {
        "ts_code": ts_code,
    }, fields="chairman,manager,reg_capital,setup_date,province,city,employees,main_business")

    if not df2.empty:
        row2 = df2.iloc[0]
        info["董事长"] = row2.get("chairman", "")
        info["总经理"] = row2.get("manager", "")
        info["注册资本(万元)"] = row2.get("reg_capital", "")
        info["员工人数"] = row2.get("employees", "")
        main_biz = str(row2.get("main_business", ""))
        info["主要业务"] = main_biz[:200] if main_biz else ""

    return info


# ──────────────────────────────────────────
# 最新行情
# ──────────────────────────────────────────
def get_realtime_quote(symbol: str) -> dict:
    """获取最新行情快照（最近交易日数据）"""
    ts_code = _to_ts_code(symbol)
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

    df = _ts_query("daily", {
        "ts_code": ts_code,
        "start_date": start,
        "end_date": end,
    })
    if df.empty:
        return {}

    latest = df.sort_values("trade_date", ascending=False).iloc[0]

    # 基本面指标
    df_basic = _ts_query("daily_basic", {
        "ts_code": ts_code,
        "start_date": start,
        "end_date": end,
    })
    basic = {}
    if not df_basic.empty:
        basic = df_basic.sort_values("trade_date", ascending=False).iloc[0].to_dict()

    # 股票名称
    name_df = _ts_query("stock_basic", {"ts_code": ts_code}, fields="name")
    name = name_df.iloc[0]["name"] if not name_df.empty else symbol

    pre_close = latest.get("pre_close", 1) or 1
    high_val = latest.get("high", 0) or 0
    low_val = latest.get("low", 0) or 0
    amplitude = round(((high_val - low_val) / pre_close) * 100, 2) if pre_close else 0

    quote = {
        "名称": name,
        "代码": symbol,
        "最新价": latest.get("close", "--"),
        "涨跌幅": round(latest.get("pct_chg", 0) or 0, 2),
        "涨跌额": round(latest.get("change", 0) or 0, 2),
        "成交量": latest.get("vol", "--"),
        "成交额": latest.get("amount", "--"),
        "振幅": amplitude,
        "最高": latest.get("high", "--"),
        "最低": latest.get("low", "--"),
        "今开": latest.get("open", "--"),
        "昨收": latest.get("pre_close", "--"),
        "量比": basic.get("volume_ratio", "--"),
        "换手率": basic.get("turnover_rate", "--"),
        "市盈率-动态": basic.get("pe_ttm", "--"),
        "市净率": basic.get("pb", "--"),
        "总市值": _format_market_cap(basic.get("total_mv")),
        "流通市值": _format_market_cap(basic.get("circ_mv")),
    }
    return quote


# ──────────────────────────────────────────
# 财务数据
# ──────────────────────────────────────────
def get_financial_data(symbol: str) -> dict:
    """获取财务数据：主要指标、利润表、资产负债表"""
    ts_code = _to_ts_code(symbol)
    result = {}

    # 主要财务指标
    df = _ts_query("fina_indicator", {
        "ts_code": ts_code,
    }, fields="ann_date,end_date,eps,bps,roe,roe_dt,netprofit_yoy,or_yoy,debt_to_assets,grossprofit_margin,netprofit_margin,current_ratio,quick_ratio")

    if not df.empty:
        df = df.sort_values("end_date", ascending=False).head(8)
        df = df.rename(columns={
            "end_date": "报告期", "eps": "每股收益", "bps": "每股净资产",
            "roe": "ROE(%)", "roe_dt": "ROE(扣非%)",
            "netprofit_yoy": "净利润同比(%)", "or_yoy": "营收同比(%)",
            "debt_to_assets": "资产负债率(%)",
            "grossprofit_margin": "毛利率(%)", "netprofit_margin": "净利率(%)",
            "current_ratio": "流动比率", "quick_ratio": "速动比率",
        })
        df = df.drop(columns=["ann_date"], errors="ignore")
        result["financial_abstract"] = df

    # 利润表
    df = _ts_query("income", {
        "ts_code": ts_code,
    }, fields="end_date,revenue,oper_cost,total_profit,n_income,n_income_attr_p,ebit")

    if not df.empty:
        df = df.sort_values("end_date", ascending=False).head(4)
        df = df.rename(columns={
            "end_date": "报告期", "revenue": "营业总收入",
            "oper_cost": "营业成本", "total_profit": "利润总额",
            "n_income": "净利润", "n_income_attr_p": "归母净利润",
            "ebit": "息税前利润",
        })
        for col in ["营业总收入", "营业成本", "利润总额", "净利润", "归母净利润", "息税前利润"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: _format_yi(x))
        result["profit"] = df

    # 资产负债表
    df = _ts_query("balancesheet", {
        "ts_code": ts_code,
    }, fields="end_date,total_assets,total_liab,total_hldr_eqy_exc_min_int,money_cap,accounts_receiv,inventories,goodwill")

    if not df.empty:
        df = df.sort_values("end_date", ascending=False).head(4)
        df = df.rename(columns={
            "end_date": "报告期", "total_assets": "总资产",
            "total_liab": "总负债", "total_hldr_eqy_exc_min_int": "归母净资产",
            "money_cap": "货币资金", "accounts_receiv": "应收账款",
            "inventories": "存货", "goodwill": "商誉",
        })
        for col in ["总资产", "总负债", "归母净资产", "货币资金", "应收账款", "存货", "商誉"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: _format_yi(x))
        result["balance"] = df

    return result


# ──────────────────────────────────────────
# 资金流向
# ──────────────────────────────────────────
def get_money_flow(symbol: str) -> pd.DataFrame:
    """获取个股资金流向"""
    ts_code = _to_ts_code(symbol)
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=40)).strftime("%Y%m%d")

    df = _ts_query("moneyflow", {
        "ts_code": ts_code,
        "start_date": start,
        "end_date": end,
    })
    if df.empty:
        return df

    df = df.sort_values("trade_date").tail(20)
    df = df.rename(columns={
        "trade_date": "日期",
        "buy_sm_vol": "小单买入(手)",
        "sell_sm_vol": "小单卖出(手)",
        "buy_lg_vol": "大单买入(手)",
        "sell_lg_vol": "大单卖出(手)",
        "net_mf_vol": "净流入(手)",
    })
    keep = ["日期", "小单买入(手)", "小单卖出(手)", "大单买入(手)", "大单卖出(手)", "净流入(手)"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].reset_index(drop=True)


# ──────────────────────────────────────────
# 北向资金
# ──────────────────────────────────────────
def get_north_flow() -> pd.DataFrame:
    """获取北向资金近期流向"""
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=40)).strftime("%Y%m%d")

    df = _ts_query("moneyflow_hsgt", {
        "start_date": start,
        "end_date": end,
    })
    if df.empty:
        return df

    df = df.sort_values("trade_date").tail(20)
    df = df.rename(columns={
        "trade_date": "日期",
        "north_money": "北向资金(百万)",
        "south_money": "南向资金(百万)",
        "ggt_ss": "沪股通(百万)",
        "ggt_sz": "深股通(百万)",
    })
    keep = ["日期", "北向资金(百万)", "南向资金(百万)", "沪股通(百万)", "深股通(百万)"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].reset_index(drop=True)


# ──────────────────────────────────────────
# 融资融券
# ──────────────────────────────────────────
def get_margin_trading(symbol: str) -> pd.DataFrame:
    """获取融资融券数据"""
    ts_code = _to_ts_code(symbol)
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=40)).strftime("%Y%m%d")

    df = _ts_query("margin_detail", {
        "ts_code": ts_code,
        "start_date": start,
        "end_date": end,
    })
    if df.empty:
        return df

    df = df.sort_values("trade_date").tail(15)
    df = df.rename(columns={
        "trade_date": "日期",
        "rzye": "融资余额",
        "rzmre": "融资买入额",
        "rzche": "融资偿还额",
        "rqye": "融券余额",
        "rqmcl": "融券卖出量(股)",
        "rqchl": "融券偿还量(股)",
        "rzrqye": "融资融券余额",
    })
    for col in ["融资余额", "融资买入额", "融资偿还额", "融券余额", "融资融券余额"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _format_yi(x))
    keep = ["日期", "融资余额", "融资买入额", "融券余额", "融资融券余额"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].reset_index(drop=True)


# ──────────────────────────────────────────
# 新闻 / 公告
# ──────────────────────────────────────────
def get_news(symbol: str) -> list:
    """获取近期新闻（公司公告 + 市场快讯）"""
    ts_code = _to_ts_code(symbol)
    news_list = []

    # 公司公告
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    df = _ts_query("anns", {
        "ts_code": ts_code,
        "start_date": start,
        "end_date": end,
    })
    if not df.empty:
        for _, row in df.head(5).iterrows():
            news_list.append({
                "title": str(row.get("title", "")),
                "content": str(row.get("content", ""))[:300],
                "time": str(row.get("ann_date", "")),
                "source": "公司公告",
            })

    # 新闻快讯
    start_dt = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df2 = _ts_query("news", {
        "src": "sina",
        "start_date": start_dt,
        "end_date": end_dt,
    })
    if not df2.empty:
        for _, row in df2.head(10).iterrows():
            title = str(row.get("title", ""))
            content = str(row.get("content", ""))[:300]
            news_list.append({
                "title": title,
                "content": content,
                "time": str(row.get("datetime", "")),
                "source": "市场快讯",
            })

    # 去重
    seen = set()
    unique = []
    for n in news_list:
        if n["title"] and n["title"] not in seen:
            seen.add(n["title"])
            unique.append(n)
    return unique[:10]


# ──────────────────────────────────────────
# 技术指标计算
# ──────────────────────────────────────────
def compute_technical_indicators(df: pd.DataFrame) -> dict:
    """基于K线数据计算技术指标"""
    if df.empty or "收盘" not in df.columns:
        return {}

    indicators = {}
    close = df["收盘"].astype(float)
    high = df["最高"].astype(float)
    low = df["最低"].astype(float)
    volume = df["成交量"].astype(float)

    # 均线
    for window in [5, 10, 20, 60]:
        indicators[f"MA{window}"] = round(close.rolling(window).mean().iloc[-1], 2) if len(close) >= window else None

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9).mean()
    macd = 2 * (dif - dea)
    indicators["MACD_DIF"] = round(dif.iloc[-1], 4)
    indicators["MACD_DEA"] = round(dea.iloc[-1], 4)
    indicators["MACD"] = round(macd.iloc[-1], 4)

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    indicators["RSI_14"] = round(rsi.iloc[-1], 2) if not rsi.empty else None

    # 布林带
    ma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    indicators["BOLL_UPPER"] = round((ma20 + 2 * std20).iloc[-1], 2)
    indicators["BOLL_MID"] = round(ma20.iloc[-1], 2)
    indicators["BOLL_LOWER"] = round((ma20 - 2 * std20).iloc[-1], 2)

    # KDJ
    low_9 = low.rolling(9).min()
    high_9 = high.rolling(9).max()
    rsv = (close - low_9) / (high_9 - low_9) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    indicators["KDJ_K"] = round(k.iloc[-1], 2)
    indicators["KDJ_D"] = round(d.iloc[-1], 2)
    indicators["KDJ_J"] = round(j.iloc[-1], 2)

    # 成交量均线
    indicators["VOL_MA5"] = round(volume.rolling(5).mean().iloc[-1], 0)
    indicators["VOL_MA20"] = round(volume.rolling(20).mean().iloc[-1], 0)

    # 波动率
    returns = close.pct_change().dropna()
    indicators["VOLATILITY_20D"] = round(returns.tail(20).std() * (252 ** 0.5) * 100, 2)

    # 最大回撤(近60日)
    recent = close.tail(60)
    max_drawdown = ((recent / recent.cummax()) - 1).min()
    indicators["MAX_DRAWDOWN_60D"] = round(max_drawdown * 100, 2)

    return indicators


# ──────────────────────────────────────────
# 实时行情（通过 akshare，可选）
# ──────────────────────────────────────────
def get_realtime_quote_ak(symbol: str) -> dict:
    """
    通过 akshare 获取个股盘中实时行情快照，
    返回与 get_realtime_quote() 完全一致的字段名。
    """
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return {}
        row = df[df["代码"] == symbol]
        if row.empty:
            return {}
        r = row.iloc[0]

        def _safe(val, default="--"):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return default
            return val

        total_mv = _safe(r.get("总市值"), None)
        circ_mv = _safe(r.get("流通市值"), None)

        quote = {
            "名称": _safe(r.get("名称")),
            "代码": symbol,
            "最新价": _safe(r.get("最新价")),
            "涨跌幅": round(float(_safe(r.get("涨跌幅"), 0)), 2),
            "涨跌额": round(float(_safe(r.get("涨跌额"), 0)), 2),
            "成交量": _safe(r.get("成交量")),
            "成交额": _safe(r.get("成交额")),
            "振幅": _safe(r.get("振幅")),
            "最高": _safe(r.get("最高")),
            "最低": _safe(r.get("最低")),
            "今开": _safe(r.get("今开")),
            "昨收": _safe(r.get("昨收")),
            "量比": _safe(r.get("量比")),
            "换手率": _safe(r.get("换手率")),
            "市盈率-动态": _safe(r.get("市盈率-动态")),
            "市净率": _safe(r.get("市净率")),
            "总市值": _format_market_cap_raw(total_mv),
            "流通市值": _format_market_cap_raw(circ_mv),
        }
        return quote
    except ImportError:
        return {}
    except Exception:
        return {}


def _format_market_cap_raw(val):
    """将元为单位的市值转为可读格式"""
    if val is None or val == "--":
        return "--"
    try:
        v = float(val)
        if v >= 1e8:
            return f"{v / 1e8:.2f}亿"
        elif v >= 1e4:
            return f"{v / 1e4:.2f}万"
        else:
            return f"{v:.2f}"
    except (ValueError, TypeError):
        return "--"


def get_market_indices_ak() -> dict:
    """
    通过 akshare 获取三大指数的盘中实时行情，
    返回与 get_market_indices() 完全一致的字段结构。
    """
    try:
        import akshare as ak
        df = ak.stock_zh_index_spot_em()
        if df is None or df.empty:
            return {}

        indices = {}
        target = {
            "000001": "上证指数",
            "399001": "深证成指",
            "399006": "创业板指",
        }
        for code, name in target.items():
            row = df[df["代码"] == code]
            if row.empty:
                continue
            r = row.iloc[0]
            close_val = r.get("最新价", 0) or 0
            chg_pct = r.get("涨跌幅", 0) or 0
            chg_amt = r.get("涨跌额", 0) or 0
            amount = r.get("成交额", 0) or 0

            indices[name] = {
                "收盘": round(float(close_val), 2),
                "涨跌幅": round(float(chg_pct), 2),
                "涨跌额": round(float(chg_amt), 2),
                "成交额(亿)": round(float(amount) / 1e8, 2),
                "日期": datetime.now().strftime("%Y%m%d") + " (实时)",
            }
        return indices
    except ImportError:
        return {}
    except Exception:
        return {}


# ──────────────────────────────────────────
# 实时K线（通过 akshare，可选）
# ──────────────────────────────────────────
def get_realtime_kline_ak(symbol: str) -> pd.DataFrame:
    """
    通过 akshare 获取当日实时/分钟级K线，
    汇总为一条「当日实时」记录，列名与 tushare K线一致。
    """
    try:
        import akshare as ak
        # 获取当日分钟级数据
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", adjust="qfq")
        if df is None or df.empty:
            return pd.DataFrame()

        # 汇总为一条当日记录
        today_str = datetime.now().strftime("%Y-%m-%d")
        df["时间"] = pd.to_datetime(df["时间"])
        df_today = df[df["时间"].dt.strftime("%Y-%m-%d") == today_str]
        if df_today.empty:
            # 可能盘后，取最后一天的数据
            last_date = df["时间"].dt.strftime("%Y-%m-%d").iloc[-1]
            df_today = df[df["时间"].dt.strftime("%Y-%m-%d") == last_date]

        if df_today.empty:
            return pd.DataFrame()

        summary = pd.DataFrame([{
            "日期": df_today["时间"].dt.strftime("%Y-%m-%d").iloc[-1] + " (实时)",
            "开盘": float(df_today["开盘"].iloc[0]),
            "最高": float(df_today["最高"].max()),
            "最低": float(df_today["最低"].min()),
            "收盘": float(df_today["收盘"].iloc[-1]),
            "成交量": float(df_today["成交量"].sum()),
            "成交额": float(df_today["成交额"].sum()) if "成交额" in df_today.columns else 0,
        }])
        return summary
    except ImportError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def merge_realtime_kline(kline_df: pd.DataFrame, realtime_df: pd.DataFrame) -> pd.DataFrame:
    """将实时K线追加到历史K线末尾（如果日期不重复）"""
    if kline_df.empty:
        return realtime_df
    if realtime_df.empty:
        return kline_df

    # 去掉日期中的 " (实时)" 后缀用于比较
    rt_date_clean = str(realtime_df["日期"].iloc[0]).replace(" (实时)", "")
    last_hist_date = str(kline_df["日期"].iloc[-1])

    if rt_date_clean == last_hist_date:
        # 同一天，用实时数据替换最后一行
        kline_df = kline_df.iloc[:-1]

    merged = pd.concat([kline_df, realtime_df], ignore_index=True)
    return merged


# ──────────────────────────────────────────
# 三大指数
# ──────────────────────────────────────────
def get_market_indices() -> dict:
    """获取上证指数、深证成指、创业板指的最新行情"""
    indices = {}
    index_map = {
        "000001.SH": "上证指数",
        "399001.SZ": "深证成指",
        "399006.SZ": "创业板指",
    }
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

    for ts_code, name in index_map.items():
        df = _ts_query("index_daily", {
            "ts_code": ts_code,
            "start_date": start,
            "end_date": end,
        })
        if not df.empty:
            latest = df.sort_values("trade_date", ascending=False).iloc[0]
            indices[name] = {
                "收盘": latest.get("close", "--"),
                "涨跌幅": round(latest.get("pct_chg", 0) or 0, 2),
                "涨跌额": round(latest.get("change", 0) or 0, 2),
                "成交额(亿)": round((latest.get("amount", 0) or 0) / 1e3, 2),
                "日期": latest.get("trade_date", "--"),
            }
    return indices


# ──────────────────────────────────────────
# 统一入口
# ──────────────────────────────────────────
def fetch_all_data(symbol: str, enable_realtime_kline: bool = False) -> dict:
    """
    统一获取所有数据。
    enable_realtime_kline=True 时，通过 AKShare 获取：
      - 个股盘中实时行情（替换 Tushare 延迟 quote）
      - 三大指数盘中实时数据（替换 Tushare 延迟 indices）
      - 当日实时K线（合并到历史K线）
    其余数据始终走 Tushare。
    """
    data = {}

    # ── 始终走 Tushare 的数据 ──
    data["kline"] = get_stock_kline(symbol)
    data["info"] = get_stock_info(symbol)
    data["financial"] = get_financial_data(symbol)
    data["money_flow"] = get_money_flow(symbol)
    data["north_flow"] = get_north_flow()
    data["margin"] = get_margin_trading(symbol)
    data["news"] = get_news(symbol)

    # ── 根据开关选择数据源 ──
    if enable_realtime_kline:
        # 个股行情：优先 AKShare 实时，失败回退 Tushare
        ak_quote = get_realtime_quote_ak(symbol)
        if ak_quote:
            data["quote"] = ak_quote
            data["quote_source"] = "AKShare (实时)"
        else:
            data["quote"] = get_realtime_quote(symbol)
            data["quote_source"] = "Tushare (实时获取失败，已回退)"

        # 三大指数：优先 AKShare 实时，失败回退 Tushare
        ak_indices = get_market_indices_ak()
        if ak_indices:
            data["indices"] = ak_indices
            data["indices_source"] = "AKShare (实时)"
        else:
            data["indices"] = get_market_indices()
            data["indices_source"] = "Tushare (实时获取失败，已回退)"

        # 实时K线合并
        rt_kline = get_realtime_kline_ak(symbol)
        if not rt_kline.empty:
            data["kline"] = merge_realtime_kline(data["kline"], rt_kline)
            data["realtime_kline_status"] = "已合并实时K线数据"
        else:
            data["realtime_kline_status"] = "实时K线获取失败（可能非交易时段）"
    else:
        data["quote"] = get_realtime_quote(symbol)
        data["quote_source"] = "Tushare"
        data["indices"] = get_market_indices()
        data["indices_source"] = "Tushare"
        data["realtime_kline_status"] = "未启用"

    # 技术指标基于最终K线计算（已含实时数据如果有的话）
    data["technical"] = compute_technical_indicators(data["kline"])
    return data
