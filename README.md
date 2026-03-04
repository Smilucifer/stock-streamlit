# 📈 A股智能分析 · 多空辩论决策系统

基于 Streamlit + AKShare + LLM 的 A 股股票智能分析平台。

4 位不同风格的 AI 交易员实时辩论，结合量化数据、技术指标、财务分析与新闻事件，为你提供多维度的买卖决策参考。

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ 功能特色

### 📡 全量数据获取
- **K线数据**：日K线 + MA5/MA20/MA60 均线系统
- **实时行情**：最新价、涨跌幅、换手率、量比等
- **技术指标**：MACD、RSI、KDJ、布林带、波动率、最大回撤
- **财务数据**：主要财务指标、利润表、资产负债表
- **资金流向**：个股主力资金、北向资金、融资融券
- **新闻事件**：近期个股相关新闻

### 🧠 AI 多交易员辩论系统

| 交易员 | 风格 | 关注维度 |
|--------|------|----------|
| 🛡️ 陈守正 | 风险管理专家 | 下行风险、财务隐患、政策风险 |
| 📊 李算法 | 量化策略专家 | 技术指标、量价关系、资金信号 |
| 🔮 王前瞻 | 预期差分析专家 | 预期偏差、行业拐点、逆向思维 |
| 🎭 赵心态 | 市场情绪专家 | 情绪温度、恐慌/贪婪、择时 |
| 👔 钱总 | 团队总经理 | 综合决策、仓位建议、止盈止损 |

每位交易员都会结合 **近期新闻事件** 进行分析，最终由总经理汇总形成统一决策。

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/a-stock-analyzer.git
cd a-stock-analyzer
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501` 即可使用。

---

## 📖 使用流程

1. 在左侧边栏输入 **6位A股代码**（如 `600519` 贵州茅台）
2. 点击 **「📡 获取股票数据」** 按钮，等待数据加载完成
3. 浏览 K线图表、技术指标、财务数据、资金流向、新闻等多个维度
4. 点击 **「🧠 启动 AI 辩论分析」** 按钮
5. 4 位交易员将依次给出分析，最后由总经理汇总决策

---

## 🏗️ 项目结构

```
a-stock-analyzer/
├── app.py              # Streamlit 主应用
├── data_fetcher.py     # AKShare 数据获取模块
├── ai_analysts.py      # AI 交易员辩论模块
├── requirements.txt    # 依赖清单
├── .streamlit/
│   └── config.toml     # Streamlit 主题配置
└── README.md
```

---

## ⚠️ 免责声明

本项目仅供 **学习和研究** 使用，不构成任何投资建议。股市有风险，投资需谨慎。

---

## 📄 License

MIT License
