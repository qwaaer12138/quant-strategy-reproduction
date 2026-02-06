# 增强版双均线策略优化方案

## 现状问题分析

1. **当前策略局限性**
   - 仅使用20/60日均线交叉信号
   - 缺乏信号过滤机制
   - 对震荡市适应能力差
   - 未结合成交量、MACD等辅助指标

2. **回测暴露的问题**
   - 平安银行表现不佳，震荡市频繁止损
   - 胜率不高，交易成本吞噬收益
   - 夏普比率不理想，风险调整后收益不足

## 优化方向

### 1. 策略参数优化

```python
# 针对不同股票类型优化均线参数
PARAMS = {
    'high_volatility': {'short_window': 10, 'long_window': 30},  # 高波动率股票
    'medium_volatility': {'short_window': 20, 'long_window': 60},  # 中等波动率
    'low_volatility': {'short_window': 50, 'long_window': 200},  # 低波动率（如银行股）
}
```

### 2. 添加信号过滤机制

```python
def filter_signals(df):
    """多指标信号过滤"""
    
    # 1. 成交量过滤：仅在成交量高于20日均量时触发信号
    df['vol_ma20'] = df['vol'].rolling(20).mean()
    volume_filter = df['vol'] > df['vol_ma20'] * 1.2
    
    # 2. MACD过滤：MACD柱线与价格背离
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    macd_filter = (df['macd'] > df['signal_line']) == (df['short_ma'] > df['long_ma'])
    
    # 3. RSI过滤：避免在超买超卖区域操作
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    rsi_filter = (df['rsi'] < 70) & (df['rsi'] > 30)
    
    # 4. 趋势强度过滤：仅在价格远离均线时操作
    df['distance_from_ma'] = (df['close'] - df['long_ma']) / df['long_ma']
    trend_filter = abs(df['distance_from_ma']) > 0.02  # 价格偏离长期均线2%以上
    
    # 综合过滤
    df['filtered_signal'] = df['signal'] * (volume_filter & macd_filter & rsi_filter & trend_filter)
    df['filtered_signal'] = df['filtered_signal'].fillna(0)
    
    return df
```

### 3. 动态仓位管理

```python
def dynamic_position_sizing(df):
    """根据市场情况动态调整仓位"""
    
    # 1. 根据波动率调整仓位
    df['volatility'] = df['close'].rolling(20).std() / df['close']
    df['position_size'] = 1 / (df['volatility'] * 100)  # 波动率越高，仓位越低
    
    # 2. 根据趋势强度调整仓位
    df['trend_strength'] = abs(df['short_ma'] - df['long_ma']) / df['long_ma']
    df['position_size'] *= np.where(df['trend_strength'] > 0.05, 1.5, 1.0)  # 强趋势时放大仓位
    
    # 3. 最大仓位限制
    df['position_size'] = df['position_size'].clip(0.3, 1.0)  # 仓位范围30%-100%
    
    return df
```

### 4. 止损止盈机制

```python
def add_stop_loss_take_profit(df):
    """添加止损止盈"""
    
    # 1. 固定比例止损
    stop_loss_pct = -0.08  # 8%止损
    
    # 2. 移动止损
    df['highest_price'] = df['close'].cummax()
    df['trailing_stop'] = df['highest_price'] * (1 - 0.05)  # 5%移动止损
    
    # 3. 止盈目标
    take_profit_pct = 0.15  # 15%止盈
    
    return df
```

### 5. 多时间维度确认

```python
def multi_timeframe_confirmation(df, weekly_df):
    """结合周线级别确认信号"""
    
    # 对齐周线数据
    weekly_df['trade_date'] = pd.to_datetime(weekly_df['trade_date'])
    weekly_df['weekly_short_ma'] = weekly_df['close'].rolling(10).mean()
    weekly_df['weekly_long_ma'] = weekly_df['close'].rolling(30).mean()
    
    # 日线信号与周线趋势一致时才确认
    weekly_trend = weekly_df['weekly_short_ma'] > weekly_df['weekly_long_ma']
    
    # 映射到日线级别
    df['weekly_trend'] = df['trade_date'].apply(
        lambda x: weekly_trend.loc[weekly_trend.index <= x].iloc[-1]
    )
    
    # 仅在周线趋势与日线信号一致时操作
    df['confirmed_signal'] = np.where(
        (df['signal'] == 1) & df['weekly_trend'] | 
        (df['signal'] == -1) & ~df['weekly_trend'],
        df['signal'], 0
    )
    
    return df
```

## 回测监控与调优

```python
def optimize_parameters(stock_data):
    """网格搜索优化参数"""
    best_score = -np.inf
    best_params = None
    
    # 参数搜索范围
    short_windows = [10, 15, 20, 25, 30]
    long_windows = [30, 40, 50, 60, 80, 100]
    
    for short_window in short_windows:
        for long_window in long_windows:
            if long_window <= short_window:
                continue
                
            # 回测策略
            strategy = MovingAverageCrossStrategy(short_window, long_window)
            df_with_signals = strategy.calculate_indicators(stock_data)
            results = strategy.backtest(df_with_signals)
            
            # 使用夏普比率作为评分标准
            score = results['sharpe_ratio']
            
            if score > best_score:
                best_score = score
                best_params = {'short_window': short_window, 'long_window': long_window}
    
    return best_params
```

## 总结

增强版策略预期效果：
- ✅ 减少无效交易，降低交易成本
- ✅ 提高信号质量，提升胜率
- ✅ 降低最大回撤，改善夏普比率
- ✅ 适应不同类型股票的市场特性

需要我实现这个增强版策略并进行回测吗？