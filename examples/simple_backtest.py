#!/usr/bin/env python3
"""
简化版双均线策略回测
仅测试贵州茅台一只股票，避免超时
"""

import sys
import os
sys.path.append('..')

import pandas as pd
from data_processor import DataProcessor
from strategies.moving_average_cross import MovingAverageCrossStrategy


def main():
    """
    主函数
    """
    print("=== 简化版双均线策略回测 ===")
    print("使用20日均线和60日均线交叉策略")
    print("回测时间范围: 2023-01-01 至 2026-02-06")
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    # 要回测的股票
    stock = {'ts_code': '600519.SH', 'name': '贵州茅台'}
    
    # 回测参数
    start_date = '20230101'
    end_date = '20260206'
    short_window = 20
    long_window = 60
    
    print(f"\n=== 正在回测 {stock['name']}({stock['ts_code']}) ===")
    
    # 获取数据
    df = processor.get_daily_data(stock['ts_code'], start_date, end_date)
    if df.empty:
        print(f"获取数据失败")
        return
    
    # 处理日期
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)
    df.sort_index(inplace=True)
    
    # 初始化策略
    strategy = MovingAverageCrossStrategy(short_window=short_window, long_window=long_window)
    
    # 计算指标和信号
    df_with_signals = strategy.calculate_indicators(df)
    
    # 回测
    results = strategy.backtest(df_with_signals)
    
    # 打印回测结果
    print(f"\n📈 {stock['name']} 回测结果摘要")
    print("=" * 60)
    print(f"初始资金: {results['initial_capital']:,.2f} 元")
    print(f"最终组合价值: {results['final_portfolio_value']:,.2f} 元")
    print(f"市场总收益率: {results['total_market_return']*100:.2f}%")
    print(f"策略总收益率: {results['total_strategy_return']*100:.2f}%  {'(超越市场)' if results['total_strategy_return'] > results['total_market_return'] else '(落后市场)'}")
    print(f"年化市场收益率: {results['annualized_market_return']*100:.2f}%")
    print(f"年化策略收益率: {results['annualized_strategy_return']*100:.2f}%")
    print(f"市场最大回撤: {results['max_drawdown_market']*100:.2f}%")
    print(f"策略最大回撤: {results['max_drawdown_strategy']*100:.2f}%  {'(优于市场)' if results['max_drawdown_strategy'] > results['max_drawdown_market'] else '(劣于市场)'}")
    print(f"胜率: {results['win_rate']*100:.2f}%")
    print(f"夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"交易次数: {results['trade_count']} 次")
    print(f"总交易日数: {results['total_trading_days']} 天")
    
    # 生成交易记录
    trade_signals = strategy.generate_trade_signals(df_with_signals)
    print("\n=== 最近10次交易记录 ===")
    print(trade_signals.tail(10)[['trade_type', 'price', 'trade_return']])
    
    # 保存回测结果
    output_dir = '../backtest/results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存数据
    df_with_signals.to_csv(f'{output_dir}/{stock['ts_code']}_backtest_data.csv')
    trade_signals.to_csv(f'{output_dir}/{stock['ts_code']}_trade_signals.csv')
    
    # 保存结果报告
    report_path = f'{output_dir}/{stock['ts_code']}_backtest_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"=== {stock['name']}({stock['ts_code']}) 双均线策略回测报告 ===\n")
        f.write(f"回测时间: {start_date} 至 {end_date}\n")
        f.write(f"均线参数: {short_window}日 / {long_window}日\n\n")
        f.write(f"初始资金: {results['initial_capital']:,.2f} 元\n")
        f.write(f"最终组合价值: {results['final_portfolio_value']:,.2f} 元\n")
        f.write(f"市场总收益率: {results['total_market_return']*100:.2f}%\n")
        f.write(f"策略总收益率: {results['total_strategy_return']*100:.2f}%\n")
        f.write(f"年化市场收益率: {results['annualized_market_return']*100:.2f}%\n")
        f.write(f"年化策略收益率: {results['annualized_strategy_return']*100:.2f}%\n")
        f.write(f"市场最大回撤: {results['max_drawdown_market']*100:.2f}%\n")
        f.write(f"策略最大回撤: {results['max_drawdown_strategy']*100:.2f}%\n")
        f.write(f"胜率: {results['win_rate']*100:.2f}%\n")
        f.write(f"夏普比率: {results['sharpe_ratio']:.2f}\n")
        f.write(f"交易次数: {results['trade_count']} 次\n")
        f.write(f"总交易日数: {results['total_trading_days']} 天\n\n")
        f.write("=== 最近10次交易记录 ===\n")
        f.write(trade_signals.tail(10)[['trade_type', 'price', 'trade_return']].to_string())
    
    print(f"\n📝 回测结果已保存至: {output_dir}")
    print("\n=== 回测完成 ===")


if __name__ == '__main__':
    main()
