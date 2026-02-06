#!/usr/bin/env python3
"""
双均线策略回测示例
使用Tushare获取5支知名股票数据并进行回测
"""

import sys
import os
sys.path.append('..')

import pandas as pd
from data_processor import DataProcessor
from strategies.moving_average_cross import MovingAverageCrossStrategy


def backtest_stock(processor, ts_code: str, start_date: str, end_date: str, 
                   short_window: int = 20, long_window: int = 60):
    """
    对单只股票进行回测
    
    Args:
        processor: DataProcessor实例
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        short_window: 短期均线窗口
        long_window: 长期均线窗口
        
    Returns:
        回测结果字典和交易信号
    """
    print(f"\n=== 正在回测 {ts_code} ===")
    
    # 获取数据
    df = processor.get_daily_data(ts_code, start_date, end_date)
    if df.empty:
        print(f"获取数据失败: {ts_code}")
        return None, None
    
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
    
    # 生成交易信号
    trade_signals = strategy.generate_trade_signals(df_with_signals)
    
    # 保存回测数据
    output_dir = '../backtest/results'
    os.makedirs(output_dir, exist_ok=True)
    df_with_signals.to_csv(f'{output_dir}/{ts_code}_backtest_data.csv')
    trade_signals.to_csv(f'{output_dir}/{ts_code}_trade_signals.csv')
    
    return results, trade_signals


def print_backtest_summary(results, ts_code: str, stock_name: str = ''):
    """
    打印回测结果摘要
    
    Args:
        results: 回测结果字典
        ts_code: 股票代码
        stock_name: 股票名称
    """
    if not results:
        return
    
    name = f"{stock_name}({ts_code})" if stock_name else ts_code
    
    print(f"\n📈 {name} 回测结果摘要")
    print("=" * 60)
    print(f"初始资金: {results['initial_capital']:,.2f} 元")
    print(f"最终组合价值: {results['final_portfolio_value']:,.2f} 元")
    print(f"市场总收益率: {results['total_market_return']*100:>6.2f}%")
    print(f"策略总收益率: {results['total_strategy_return']*100:>6.2f}%  {'(超越市场)' if results['total_strategy_return'] > results['total_market_return'] else '(落后市场)'}")
    print(f"年化市场收益率: {results['annualized_market_return']*100:>6.2f}%")
    print(f"年化策略收益率: {results['annualized_strategy_return']*100:>6.2f}%")
    print(f"市场最大回撤: {results['max_drawdown_market']*100:>6.2f}%")
    print(f"策略最大回撤: {results['max_drawdown_strategy']*100:>6.2f}%  {'(优于市场)' if results['max_drawdown_strategy'] > results['max_drawdown_market'] else '(劣于市场)'}")
    print(f"胜率: {results['win_rate']*100:>10.2f}%")
    print(f"夏普比率: {results['sharpe_ratio']:>12.2f}")
    print(f"交易次数: {results['trade_count']:>12} 次")
    print(f"总交易日数: {results['total_trading_days']:>10} 天")


def main():
    """
    主函数
    """
    print("=== 双均线策略批量回测 ===")
    print("使用20日均线和60日均线交叉策略")
    print("回测时间范围: 2023-01-01 至 2026-02-06")
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    # 要回测的股票列表（知名股票）
    stocks = [
        {'ts_code': '600519.SH', 'name': '贵州茅台'},
        {'ts_code': '000858.SZ', 'name': '五粮液'},
        {'ts_code': '002415.SZ', 'name': '海康威视'},
        {'ts_code': '601318.SH', 'name': '中国平安'},
        {'ts_code': '600036.SH', 'name': '招商银行'}
    ]
    
    # 回测参数
    start_date = '20230101'
    end_date = '20260206'
    short_window = 20
    long_window = 60
    
    # 批量回测
    all_results = []
    
    for stock in stocks:
        results, trade_signals = backtest_stock(
            processor, stock['ts_code'], start_date, end_date,
            short_window=short_window, long_window=long_window
        )
        
        if results:
            all_results.append({
                'ts_code': stock['ts_code'],
                'name': stock['name'],
                'results': results
            })
            
            # 打印结果
            print_backtest_summary(results, stock['ts_code'], stock['name'])
            
            # 打印最近的交易记录
            if not trade_signals.empty:
                print("\n最近5次交易记录:")
                print(trade_signals.tail(5)[['trade_date', 'trade_type', 'price']])
                print("-" * 60)
    
    # 生成综合报告
    print("\n" + "=" * 60)
    print("📊 双均线策略回测综合报告")
    print("=" * 60)
    
    # 计算平均表现
    if all_results:
        avg_market_return = sum(r['results']['total_market_return'] for r in all_results) / len(all_results)
        avg_strategy_return = sum(r['results']['total_strategy_return'] for r in all_results) / len(all_results)
        avg_win_rate = sum(r['results']['win_rate'] for r in all_results) / len(all_results)
        avg_sharpe = sum(r['results']['sharpe_ratio'] for r in all_results) / len(all_results)
        
        print(f"\n平均市场总收益率: {avg_market_return*100:.2f}%")
        print(f"平均策略总收益率: {avg_strategy_return*100:.2f}%")
        print(f"平均胜率: {avg_win_rate*100:.2f}%")
        print(f"平均夏普比率: {avg_sharpe:.2f}")
        
        # 统计超越市场的数量
        beat_market_count = sum(1 for r in all_results 
                               if r['results']['total_strategy_return'] > r['results']['total_market_return'])
        print(f"\n超越市场的股票数量: {beat_market_count}/{len(all_results)}")
        
        # 表现最好和最差的股票
        best_performer = max(all_results, key=lambda x: x['results']['total_strategy_return'])
        worst_performer = min(all_results, key=lambda x: x['results']['total_strategy_return'])
        
        print(f"\n表现最好: {best_performer['name']}({best_performer['ts_code']})")
        print(f"  策略收益率: {best_performer['results']['total_strategy_return']*100:.2f}%")
        print(f"  市场收益率: {best_performer['results']['total_market_return']*100:.2f}%")
        
        print(f"\n表现最差: {worst_performer['name']}({worst_performer['ts_code']})")
        print(f"  策略收益率: {worst_performer['results']['total_strategy_return']*100:.2f}%")
        print(f"  市场收益率: {worst_performer['results']['total_market_return']*100:.2f}%")
    
    # 保存综合报告
    report_dir = '../backtest/reports'
    os.makedirs(report_dir, exist_ok=True)
    
    report_content = f"""# 双均线策略回测综合报告

## 回测参数
- 短期均线窗口: {short_window} 日
- 长期均线窗口: {long_window} 日
- 回测时间范围: {start_date} 至 {end_date}
- 初始资金: 100,000 元

## 回测结果摘要
"""
    
    for result in all_results:
        report_content += f"""
### {result['name']}({result['ts_code']})
| 指标 | 策略表现 | 市场表现 |
|------|----------|----------|
| 总收益率 | {result['results']['total_strategy_return']*100:.2f}% | {result['results']['total_market_return']*100:.2f}% |
| 年化收益率 | {result['results']['annualized_strategy_return']*100:.2f}% | {result['results']['annualized_market_return']*100:.2f}% |
| 最大回撤 | {result['results']['max_drawdown_strategy']*100:.2f}% | {result['results']['max_drawdown_market']*100:.2f}% |
| 胜率 | {result['results']['win_rate']*100:.2f}% | - |
| 夏普比率 | {result['results']['sharpe_ratio']:.2f} | - |
| 交易次数 | {result['results']['trade_count']} 次 | - |
"""
    
    if all_results:
        report_content += f"""
## 综合统计
- 平均市场总收益率: {avg_market_return*100:.2f}%
- 平均策略总收益率: {avg_strategy_return*100:.2f}%
- 平均胜率: {avg_win_rate*100:.2f}%
- 平均夏普比率: {avg_sharpe:.2f}
- 超越市场的股票数量: {beat_market_count}/{len(all_results)}

"""
    
    report_path = f'{report_dir}/ma_cross_backtest_summary_{start_date}_{end_date}.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📝 综合报告已保存至: {report_path}")
    print("\n=== 回测完成 ===")


if __name__ == '__main__':
    main()
