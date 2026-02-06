#!/usr/bin/env python3
"""
双均线交叉策略实现
策略逻辑：
- 当短期均线上穿长期均线时买入
- 当短期均线下穿长期均线时卖出
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


class MovingAverageCrossStrategy:
    """
    双均线交叉策略类
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 60):
        """
        初始化策略参数
        
        Args:
            short_window: 短期均线窗口
            long_window: 长期均线窗口
        """
        self.short_window = short_window
        self.long_window = long_window
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算均线指标和买卖信号
        
        Args:
            data: 包含日线数据的DataFrame，需要包含'close'列
            
        Returns:
            带有指标和信号的DataFrame
        """
        df = data.copy().sort_index()
        
        # 计算均线
        df['short_ma'] = df['close'].rolling(window=self.short_window, min_periods=1).mean()
        df['long_ma'] = df['close'].rolling(window=self.long_window, min_periods=1).mean()
        
        # 生成买卖信号
        df['signal'] = 0
        df['position'] = 0
        
        # 当短期均线上穿长期均线时，生成买入信号
        golden_cross = (df['short_ma'] > df['long_ma']) & \
                      (df['short_ma'].shift(1) <= df['long_ma'].shift(1))
        df.loc[golden_cross, 'signal'] = 1
        
        # 当短期均线下穿长期均线时，生成卖出信号
        death_cross = (df['short_ma'] < df['long_ma']) & \
                     (df['short_ma'].shift(1) >= df['long_ma'].shift(1))
        df.loc[death_cross, 'signal'] = -1
        
        # 计算持仓位置
        df['position'] = df['signal'].cumsum()
        # 确保持仓位置在-1到1之间（仅做多的话应该在0到1之间）
        df['position'] = df['position'].clip(0, 1)
        
        return df
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 100000.0) -> Dict:
        """
        回测策略
        
        Args:
            data: 带有信号的DataFrame
            initial_capital: 初始资金
            
        Returns:
            回测结果字典
        """
        df = data.copy()
        
        # 计算每日收益率
        df['daily_return'] = df['close'].pct_change()
        
        # 计算策略收益率（持仓收益率）
        df['strategy_return'] = df['daily_return'] * df['position'].shift(1)
        df['strategy_return'] = df['strategy_return'].fillna(0)
        
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
        trade_count = len(df[df['signal'] != 0])
        
        return {
            'initial_capital': initial_capital,
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
            'final_portfolio_value': initial_capital * (1 + total_strategy_return)
        }
    
    def generate_trade_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号记录
        
        Args:
            data: 带有信号的DataFrame
            
        Returns:
            交易信号记录DataFrame
        """
        df = data.copy()
        
        # 提取交易信号
        trades = df[df['signal'] != 0].copy()
        trades['trade_type'] = trades['signal'].map({1: '买入', -1: '卖出'})
        trades['price'] = trades['close']
        
        # 计算每次交易的收益
        trades['next_close'] = trades['close'].shift(-1)
        trades['trade_return'] = (trades['next_close'] - trades['price']) / trades['price']
        
        # 如果索引是datetime，转换为trade_date列
        if isinstance(trades.index, pd.DatetimeIndex):
            trades['trade_date'] = trades.index.strftime('%Y%m%d')
            return trades[['trade_date', 'trade_type', 'price', 'trade_return']]
        else:
            return trades[['trade_date', 'trade_type', 'price', 'trade_return']]


def plot_backtest_results(df: pd.DataFrame, stock_name: str = 'Stock'):
    """
    绘制回测结果可视化图
    
    Args:
        df: 包含回测结果的DataFrame
        stock_name: 股票名称
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        sns.set_style('whitegrid')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # 绘制价格和均线
        ax1.plot(df.index, df['close'], label='收盘价', alpha=0.5)
        ax1.plot(df.index, df['short_ma'], label=f'{short_window}日均线')
        ax1.plot(df.index, df['long_ma'], label=f'{long_window}日均线')
        
        # 标记买卖信号
        buy_signals = df[df['signal'] == 1]
        sell_signals = df[df['signal'] == -1]
        ax1.scatter(buy_signals.index, buy_signals['close'], marker='^', color='g', label='买入信号', s=100)
        ax1.scatter(sell_signals.index, sell_signals['close'], marker='v', color='r', label='卖出信号', s=100)
        
        ax1.set_title(f'{stock_name} 双均线策略回测结果')
        ax1.set_ylabel('价格')
        ax1.legend()
        
        # 绘制累计收益率
        ax2.plot(df.index, df['cumulative_market'], label='市场基准')
        ax2.plot(df.index, df['cumulative_strategy'], label='策略收益')
        ax2.set_title('累计收益率对比')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('累计收益率')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(f'backtest_results_{stock_name}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"回测结果图已保存为: backtest_results_{stock_name}.png")
        
    except ImportError:
        print("matplotlib或seaborn未安装，无法绘制图表")


if __name__ == '__main__':
    # 示例用法
    import sys
    sys.path.append('..')
    
    from data_processor import DataProcessor
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    # 获取股票数据
    df = processor.get_daily_data('600519.SH', '20230101', '20260206')
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)
    
    # 初始化策略
    strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
    
    # 计算指标和信号
    df_with_signals = strategy.calculate_indicators(df)
    
    # 回测
    results = strategy.backtest(df_with_signals)
    
    # 打印回测结果
    print("=== 双均线策略回测结果 ===")
    print(f"初始资金: {results['initial_capital']:,.2f} 元")
    print(f"最终组合价值: {results['final_portfolio_value']:,.2f} 元")
    print(f"市场总收益率: {results['total_market_return']*100:.2f}%")
    print(f"策略总收益率: {results['total_strategy_return']*100:.2f}%")
    print(f"年化市场收益率: {results['annualized_market_return']*100:.2f}%")
    print(f"年化策略收益率: {results['annualized_strategy_return']*100:.2f}%")
    print(f"市场最大回撤: {results['max_drawdown_market']*100:.2f}%")
    print(f"策略最大回撤: {results['max_drawdown_strategy']*100:.2f}%")
    print(f"胜率: {results['win_rate']*100:.2f}%")
    print(f"夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"交易次数: {results['trade_count']} 次")
    print(f"总交易日数: {results['total_trading_days']} 天")
    
    # 生成交易记录
    trade_signals = strategy.generate_trade_signals(df_with_signals)
    print("\n=== 最近10次交易记录 ===")
    print(trade_signals.tail(10))
