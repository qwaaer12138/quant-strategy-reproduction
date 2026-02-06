# 量化策略复现仓库

本仓库用于复现各种量化交易策略，包含数据获取、策略实现、回测分析等模块。

## 目录结构

```
quant-strategy-reproduction/
├── data_processor.py    # 数据获取模块（基于Tushare）
├── strategies/          # 策略实现目录
├── backtest/            # 回测模块
├── utils/               # 工具函数
└── examples/            # 示例代码
```

## 数据获取模块 (data_processor.py)

基于Tushare API的金融数据获取模块，支持：

### 主要功能
1. **数据初始化**：自动从环境变量获取Tushare Token
2. **日线数据**：获取股票和指数的日线行情数据
3. **股票列表**：获取全市场股票列表及基本信息
4. **财务报表**：获取上市公司财务指标数据

### 使用方法

```python
from data_processor import DataProcessor

# 初始化数据处理器
processor = DataProcessor()

# 获取平安银行日线数据
daily_df = processor.get_daily_data('000001.SZ', '20240101', '20240131')

# 获取深交所股票列表
stock_list = processor.get_stock_list(exchange='SZ')

# 获取财务报表数据
fina_df = processor.get_financial_report('000001.SZ', 2023, 4)
```

## 环境配置

### Tushare Token设置

方法1：设置环境变量
```bash
export TUSHARE_TOKEN=your_token_here
```

方法2：在代码中指定
```python
processor = DataProcessor(token='your_token_here')
```

## 依赖安装

```bash
pip install tushare==1.4.24 pandas
```

## 后续规划

1. 实现经典量化策略（如双均线、RSI、MACD等）
2. 添加回测框架
3. 实盘交易接口
4. 可视化分析模块

## 贡献

欢迎提交Issue和Pull Request！

## License

MIT

