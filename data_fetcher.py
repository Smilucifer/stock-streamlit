"""
数据获取模块 - 通过 akshare 获取 A 股数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def get_stock_kline(symbol: str, period: str = "daily", adjust: str = "qfq") -> pd.DataFrame:
    """获取股票K线数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d"),
            adjust=adjust,
        )
        return df
    except Exception as e:
        return pd.DataFrame()


def get_stock_info(symbol: str) -> dict:
    """获取股票基本信息"""
    info = {}
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        if not df.empty:
            for _, row in df.iterrows():
                info[row.iloc[0]] = row.iloc[1]
    except Exception:
        pass
    return info


def get_financial_data(symbol: str) -> dict:
    """获取财务数据"""
    result = {}

    # 主要财务指标
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df is not None and not df.empty:
            result["financial_abstract"] = df.head(8)
    except Exception:
        pass

    # 利润表
    try:
        df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        if df is not None and not df.empty:
            result["profit"] = df.head(4)
    except Exception:
        pass

    # 资产负债表
    try:
        df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
        if df is not None and not df.empty:
            result["balance"] = df.head(4)
    except Exception:
        pass

    return result


def get_realtime_quote(symbol: str) -> dict:
    """获取实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == symbol]
        if not row.empty:
            return row.iloc[0].to_dict()
    except Exception:
        pass
    return {}


def get_money_flow(symbol: str) -> pd.DataFrame:
    """获取资金流向"""
    try:
        df = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith("6") else "sz")
        return df.tail(20) if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_margin_trading(symbol: str) -> pd.DataFrame:
    """获取融资融券数据"""
    try:
        df = ak.stock_margin_detail_szse(date=datetime.now().strftime("%Y%m%d"))
        if df is not None and not df.empty:
            row = df[df["证券代码"] == symbol]
            if not row.empty:
                return row
    except Exception:
        pass

    try:
        df = ak.stock_margin_detail_sse(
            date=(datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        )
        if df is not None and not df.empty:
            return df.head(5)
    except Exception:
        pass

    return pd.DataFrame()


def get_north_flow() -> pd.DataFrame:
    """获取北向资金流向"""
    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
        return df.tail(20) if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_news(symbol: str) -> list:
    """获取个股相关新闻"""
    news_list = []
    try:
        df = ak.stock_news_em(symbol=symbol)
        if df is not None and not df.empty:
            for _, row in df.head(10).iterrows():
                news_list.append({
                    "title": row.get("新闻标题", ""),
                    "content": row.get("新闻内容", "")[:300],
                    "time": str(row.get("发布时间", "")),
                    "source": row.get("文章来源", ""),
                })
    except Exception:
        pass
    return news_list


def compute_technical_indicators(df: pd.DataFrame) -> dict:
    """基于K线数据计算技术指标"""
    if df.empty:
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


def fetch_all_data(symbol: str) -> dict:
    """统一获取所有数据"""
    data = {}
    data["kline"] = get_stock_kline(symbol)
    data["info"] = get_stock_info(symbol)
    data["quote"] = get_realtime_quote(symbol)
    data["financial"] = get_financial_data(symbol)
    data["money_flow"] = get_money_flow(symbol)
    data["north_flow"] = get_north_flow()
    data["margin"] = get_margin_trading(symbol)
    data["news"] = get_news(symbol)
    data["technical"] = compute_technical_indicators(data["kline"])
    return data
