#!/usr/bin/env python3
"""
简化版银行股双均线策略回测
"""

import sys
import os
sys.path.append('..')

import pandas as pd
from data_processor import DataProcessor
from strategies.moving_average_cross import MovingAverageCrossStrategy


def backtest_stock(processor, ts_code: str, stock_name: str, 
                   start_date: str, end_date: str, 
                   short_window: int = 20, long_window: int = 60):
    """
    对单只股票进行回测
    """
    print(f"\n=== 正在回测 {stock_name}({ts_code}) ===")
    
    # 获取数据
    df = processor.get_daily_data(ts_code, start_date, end_date)
    if df.empty:
        print(f"获取数据失败")
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
    
    # 生成交易记录
    trade_signals = strategy.generate_trade_signals(df_with_signals)
    
    # 保存回测结果
    output_dir = '../backtest/results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存数据
    df_with_signals.to_csv(f'{output_dir}/{ts_code}_backtest_data.csv')
    trade_signals.to_csv(f'{output_dir}/{ts_code}_trade_signals.csv')
    
    # 生成报告文本
    report_content = f"""### {stock_name}双均线策略回测报告

**回测参数**:
- 均线配置: 20日均线 / 60日均线
- 回测时间: {start_date} 至 {end_date}
- 初始资金: {results['initial_capital']:,.2f} 元

**📊 回测结果**:
| 指标 | 市场表现 | 策略表现 |
|------|----------|----------|
| 总收益率 | {results['total_market_return']*100:.2f}% | {results['total_strategy_return']*100:.2f}% {'(超越市场)' if results['total_strategy_return'] > results['total_market_return'] else '(落后市场)'}
| 年化收益率 | {results['annualized_market_return']*100:.2f}% | {results['annualized_strategy_return']*100:.2f}% |
| 最大回撤 | {results['max_drawdown_market']*100:.2f}% | {results['max_drawdown_strategy']*100:.2f}% {'(优于市场)' if results['max_drawdown_strategy'] > results['max_drawdown_market'] else '(劣于市场)'}
| 胜率 | - | {results['win_rate']*100:.2f}% |
| 夏普比率 | - | {results['sharpe_ratio']:.2f} |
| 交易次数 | - | {results['trade_count']} 次 |
| 最终组合价值 | - | {results['final_portfolio_value']:,.2f} 元 |

**📈 最近10次交易记录**:
```
"""
    report_content += trade_signals.tail(10)[['trade_type', 'price', 'trade_return']].to_string()
    report_content += """
```

**💡 策略评价**:
"""
    
    # 添加策略评价
    if results['total_strategy_return'] > results['total_market_return']:
        report_content += "✅ 策略表现优于市场，成功跑赢大盘。\n"
    else:
        report_content += "❌ 策略表现落后于市场，未能跑赢大盘。\n"
        
    if results['max_drawdown_strategy'] > results['max_drawdown_market']:
        report_content += "✅ 策略最大回撤优于市场，风险控制较好。\n"
    else:
        report_content += "❌ 策略最大回撤劣于市场，风险控制较差。\n"
    
    if results['sharpe_ratio'] > 0:
        report_content += "✅ 夏普比率为正，风险调整后收益为正。\n"
    else:
        report_content += "❌ 夏普比率为负，风险调整后收益为负。\n"
    
    # 保存报告
    report_path = f'{output_dir}/{ts_code}_backtest_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return results, trade_signals, report_content


def main():
    """
    主函数
    """
    print("=== 银行股双均线策略回测 ===")
    print("使用20日均线和60日均线交叉策略")
    print("回测时间范围: 2023-01-01 至 2026-02-06")
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    # 要回测的股票列表
    stocks = [
        {'ts_code': '000001.SZ', 'name': '平安银行'},
        {'ts_code': '600036.SH', 'name': '招商银行'}
    ]
    
    # 回测参数
    start_date = '20230101'
    end_date = '20260206'
    short_window = 20
    long_window = 60
    
    # 批量回测
    all_results = []
    feishu_reports = []
    
    for stock in stocks:
        results, trade_signals, report_content = backtest_stock(
            processor, stock['ts_code'], stock['name'],
            start_date, end_date,
            short_window=short_window, long_window=long_window
        )
        
        if results:
            all_results.append({
                'ts_code': stock['ts_code'],
                'name': stock['name'],
                'results': results
            })
            
            feishu_reports.append(report_content)
            
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
    
    # 生成综合报告
    if all_results:
        feishu_summary = "# 银行股双均线策略回测综合报告\n\n"
        feishu_summary += "## 回测总结\n"
        
        avg_market_return = sum(r['results']['total_market_return'] for r in all_results) / len(all_results)
        avg_strategy_return = sum(r['results']['total_strategy_return'] for r in all_results) / len(all_results)
        avg_win_rate = sum(r['results']['win_rate'] for r in all_results) / len(all_results)
        avg_sharpe = sum(r['results']['sharpe_ratio'] for r in all_results) / len(all_results)
        
        beat_market_count = sum(1 for r in all_results 
                               if r['results']['total_strategy_return'] > r['results']['total_market_return'])
        
        for result in all_results:
            feishu_summary += f"\n### {result['name']}({result['ts_code']})\n"
            feishu_summary += f"- 总收益率: 市场{result['results']['total_market_return']*100:.2f}% vs 策略{result['results']['total_strategy_return']*100:.2f}%\n"
            feishu_summary += f"- 年化收益率: 市场{result['results']['annualized_market_return']*100:.2f}% vs 策略{result['results']['annualized_strategy_return']*100:.2f}%\n"
            feishu_summary += f"- 最大回撤: 市场{result['results']['max_drawdown_market']*100:.2f}% vs 策略{result['results']['max_drawdown_strategy']*100:.2f}%\n"
            feishu_summary += f"- 胜率: {result['results']['win_rate']*100:.2f}% | 夏普比率: {result['results']['sharpe_ratio']:.2f}\n"
        
        feishu_summary += f"\n## 综合统计\n"
        feishu_summary += f"- 平均市场总收益率: {avg_market_return*100:.2f}%\n"
        feishu_summary += f"- 平均策略总收益率: {avg_strategy_return*100:.2f}%\n"
        feishu_summary += f"- 平均胜率: {avg_win_rate*100:.2f}%\n"
        feishu_summary += f"- 平均夏普比率: {avg_sharpe:.2f}\n"
        feishu_summary += f"- 超越市场的股票数量: {beat_market_count}/{len(all_results)}\n"
        
        feishu_reports.append(feishu_summary)
        
        # 保存综合报告
        output_dir = '../backtest/reports'
        os.makedirs(output_dir, exist_ok=True)
        summary_path = f'{output_dir}/bank_stocks_backtest_summary.md'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(feishu_summary)
        
        print(f"\n📊 综合报告已保存")
    
    print("\n=== 回测完成 ===")
    
    # 发送到飞书
    for report in feishu_reports:
        from message import message
        message(action='send', channel='feishu', message=report)


if __name__ == '__main__':
    main()
