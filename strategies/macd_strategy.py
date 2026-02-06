#!/usr/bin/env python3
"""
MACD策略实现
MACD(Moving Average Convergence Divergence) - 指数平滑异同移动平均线
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


class MACDStrategy:
    """
    MACD策略类，封装MACD指标计算和交易信号生成
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        初始化MACD策略参数
        
        Args:
            fast_period: 短期EMA周期
            slow_period: 长期EMA周期
            signal_period: 信号线EMA周期
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算MACD指标
        
        Args:
            data: 包含日线数据的DataFrame，需要包含'close'列
            
        Returns:
            带有MACD指标的DataFrame
        """
        df = data.copy().sort_index()
        
        # 计算EMA
        df['ema_fast'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # 计算MACD线和信号线
        df['macd'] = df['ema_fast'] - df['ema_slow']
        df['signal_line'] = df['macd'].ewm(span=self.signal_period, adjust=False).mean()
        
        # 计算柱状线
        df['macd_histogram'] = df['macd'] - df['signal_line']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成MACD交易信号
        
        Args:
            data: 带有MACD指标的DataFrame
            
        Returns:
            带有交易信号的DataFrame
        """
        df = data.copy()
        
        # 1. 交叉信号
        df['signal'] = 0
        
        # 金叉：MACD线上穿信号线
        golden_cross = (df['macd'] > df['signal_line']) & \
                      (df['macd'].shift(1) <= df['signal_line'].shift(1))
        df.loc[golden_cross, 'signal'] = 1
        
        # 死叉：MACD线下穿信号线
        death_cross = (df['macd'] < df['signal_line']) & \
                     (df['macd'].shift(1) >= df['signal_line'].shift(1))
        df.loc[death_cross, 'signal'] = -1
        
        # 2. 零轴穿越信号
        df['zero_cross'] = 0
        df.loc[df['macd'] > 0, 'zero_cross'] = 1
        df.loc[df['macd'] < 0, 'zero_cross'] = -1
        
        # 3. 背离信号检测（简化版）
        df['divergence'] = 0
        
        # 顶背离：价格创新高但MACD未创新高
        price_high = df['close'] == df['close'].rolling(20).max()
        macd_high = df['macd'] == df['macd'].rolling(20).max()
        df.loc[price_high & ~macd_high, 'divergence'] = -1
        
        # 底背离：价格创新低但MACD未创新低
        price_low = df['close'] == df['close'].rolling(20).min()
        macd_low = df['macd'] == df['macd'].rolling(20).min()
        df.loc[price_low & ~macd_low, 'divergence'] = 1
        
        # 4. 计算仓位
        df['position'] = df['signal'].cumsum()
        df['position'] = df['position'].clip(0, 1)  # 仅做多
        
        return df
    
    def generate_enhanced_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成增强版MACD交易信号（结合多指标过滤）
        
        Args:
            data: 带有MACD指标的DataFrame
            
        Returns:
            带有增强交易信号的DataFrame
        """
        df = self.generate_signals(data)
        
        # 添加成交量过滤：仅在成交量高于20日均量时触发信号
        df['vol_ma20'] = df['vol'].rolling(20, min_periods=1).mean()
        volume_filter = df['vol'] > df['vol_ma20'] * 1.2
        
        # 添加RSI过滤：避免在超买超卖区域操作
        delta = df['close'].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=1).mean()
        rs = gain / loss.replace(0, 1e-6)  # 避免除以0
        df['rsi'] = 100 - (100 / (1 + rs))
        rsi_filter = (df['rsi'] < 70) & (df['rsi'] > 30)
        
        # 添加趋势强度过滤：MACD远离零轴时才操作
        trend_strength = abs(df['macd']) / df['close'].rolling(60, min_periods=1).std().replace(0, 1e-6)
        trend_filter = trend_strength > 0.5
        
        # 综合过滤
        df['enhanced_signal'] = df['signal'] * (volume_filter & rsi_filter & trend_filter)
        df['enhanced_signal'] = df['enhanced_signal'].fillna(0)
        
        # 计算增强版仓位
        df['enhanced_position'] = df['enhanced_signal'].cumsum()
        df['enhanced_position'] = df['enhanced_position'].clip(0, 1)
        
        return df
    
    def backtest(self, data: pd.DataFrame, enhanced: bool = False) -> Dict:
        """
        回测MACD策略
        
        Args:
            data: 带有信号的DataFrame
            enhanced: 是否使用增强版信号
            
        Returns:
            回测结果字典
        """
        df = data.copy()
        
        # 计算每日收益率
        df['daily_return'] = df['close'].pct_change().fillna(0)
        
        # 计算策略收益率
        if enhanced:
            df['strategy_return'] = df['daily_return'] * df['enhanced_position'].shift(1).fillna(0)
        else:
            df['strategy_return'] = df['daily_return'] * df['position'].shift(1).fillna(0)
        
        # 计算累计收益率
        df['cumulative_market'] = (1 + df['daily_return']).cumprod()
        df['cumulative_strategy'] = (1 + df['strategy_return']).cumprod()
        
        # 计算策略表现指标
        total_market_return = df['cumulative_market'].iloc[-1] - 1
        total_strategy_return = df['cumulative_strategy'].iloc[-1] - 1
        
        # 计算年化收益率
        trading_days = len(df)
        annualized_market_return = (1 + total_market_return) ** (252 / trading_days) - 1
        annualized_strategy_return = (1 + total_strategy_return) ** (252 / trading_days) - 1
        
        # 计算最大回撤
        df['peak_market'] = df['cumulative_market'].cummax()
        df['drawdown_market'] = (df['cumulative_market'] - df['peak_market']) / df['peak_market']
        max_drawdown_market = df['drawdown_market'].min()
        
        df['peak_strategy'] = df['cumulative_strategy'].cummax()
        df['drawdown_strategy'] = (df['cumulative_strategy'] - df['peak_strategy']) / df['peak_strategy']
        max_drawdown_strategy = df['drawdown_strategy'].min()
        
        # 计算胜率
        trade_signals = df[df['signal'] != 0]
        if len(trade_signals) > 0:
            winning_trades = df[(df['signal'] == 1) & (df['daily_return'].shift(-1) > 0)]
            win_rate = len(winning_trades) / len(trade_signals[trade_signals['signal'] == 1]) if len(trade_signals[trade_signals['signal'] == 1]) > 0 else 0
        else:
            win_rate = 0
        
        # 计算夏普比率（假设无风险利率为0）
        sharpe_ratio = np.sqrt(252) * df['strategy_return'].mean() / df['strategy_return'].std() if df['strategy_return'].std() != 0 else 0
        
        # 交易次数
        if enhanced:
            trade_count = len(df[df['enhanced_signal'] != 0])
        else:
            trade_count = len(df[df['signal'] != 0])
        
        return {
            'initial_capital': 100000.0,
            'total_market_return': total_market_return,
            'total_strategy_return': total_strategy_return,
            'annualized_market_return': annualized_market_return,
            'annualized_strategy_return': annualized_strategy_return,
            'max_drawdown_market': max_drawdown_market,
            'max_drawdown_strategy': max_drawdown_strategy,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'trade_count': trade_count,
            'total_trading_days': trading_days,
            'final_portfolio_value': 100000.0 * (1 + total_strategy_return),
            'strategy_version': 'enhanced' if enhanced else 'basic'
        }
    
    def generate_trade_signals(self, data: pd.DataFrame, enhanced: bool = False) -> pd.DataFrame:
        """
        生成交易信号记录
        
        Args:
            data: 带有信号的DataFrame
            enhanced: 是否使用增强版信号
            
        Returns:
            交易信号记录DataFrame
        """
        df = data.copy()
        
        # 提取交易信号
        if enhanced:
            trades = df[df['enhanced_signal'] != 0].copy()
            trades['signal_type'] = trades['enhanced_signal'].map({1: '买入', -1: '卖出'})
        else:
            trades = df[df['signal'] != 0].copy()
            trades['signal_type'] = trades['signal'].map({1: '买入', -1: '卖出'})
        
        trades['price'] = trades['close']
        
        # 计算每次交易的收益
        trades['next_close'] = trades['close'].shift(-1)
        trades['trade_return'] = (trades['next_close'] - trades['price']) / trades['price']
        
        # 转换日期格式
        if isinstance(trades.index, pd.DatetimeIndex):
            trades['trade_date'] = trades.index.strftime('%Y-%m-%d')
            return trades[['trade_date', 'signal_type', 'price', 'trade_return']]
        else:
            return trades[['trade_type', 'price', 'trade_return']]


def example_usage():
    """示例用法"""
    print("=== MACD策略示例 ===")
    
    try:
        # 初始化策略
        macd_strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        
        # 读取示例数据（假设已存在）
        # df = pd.read_csv('stock_data.csv', index_col='trade_date', parse_dates=True)
        
        # 生成测试数据（模拟数据）
        dates = pd.date_range(start='2023-01-01', end='2026-02-06', freq='B')
        prices = np.random.randn(len(dates)).cumsum() + 100
        df = pd.DataFrame({'close': prices, 'vol': np.random.randint(1000, 5000, len(dates))}, index=dates)
        
        # 计算MACD指标
        df_with_macd = macd_strategy.calculate_macd(df)
        
        # 生成信号
        df_with_signals = macd_strategy.generate_signals(df_with_macd)
        
        # 回测基础版策略
        basic_results = macd_strategy.backtest(df_with_signals, enhanced=False)
        
        # 生成增强版信号并回测
        df_with_enhanced_signals = macd_strategy.generate_enhanced_signals(df_with_macd)
        enhanced_results = macd_strategy.backtest(df_with_enhanced_signals, enhanced=True)
        
        # 打印回测结果
        print("\n=== 基础版MACD策略回测结果 ===")
        print(f"策略总收益率: {basic_results['total_strategy_return']*100:.2f}%")
        print(f"年化策略收益率: {basic_results['annualized_strategy_return']*100:.2f}%")
        print(f"最大回撤: {basic_results['max_drawdown_strategy']*100:.2f}%")
        print(f"夏普比率: {basic_results['sharpe_ratio']:.2f}")
        print(f"交易次数: {basic_results['trade_count']} 次")
        
        print("\n=== 增强版MACD策略回测结果 ===")
        print(f"策略总收益率: {enhanced_results['total_strategy_return']*100:.2f}%")
        print(f"年化策略收益率: {enhanced_results['annualized_strategy_return']*100:.2f}%")
        print(f"最大回撤: {enhanced_results['max_drawdown_strategy']*100:.2f}%")
        print(f"夏普比率: {enhanced_results['sharpe_ratio']:.2f}")
        print(f"交易次数: {enhanced_results['trade_count']} 次")
        
    except Exception as e:
        print(f"示例运行失败: {e}")


if __name__ == "__main__":
    example_usage()
