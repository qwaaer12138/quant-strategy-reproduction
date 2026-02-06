#!/usr/bin/env python3
"""
MACD策略回测示例
"""

import sys
import os
sys.path.append('..')

import pandas as pd
from data_processor import DataProcessor
from strategies.macd_strategy import MACDStrategy


def backtest_stock(processor, ts_code: str, stock_name: str,
                   start_date: str, end_date: str):
    """
    对单只股票进行MACD策略回测
    
    Args:
        processor: DataProcessor实例
        ts_code: 股票代码
        stock_name: 股票名称
        start_date: 开始日期
        end_date: 结束日期
    """
    print(f"\n=== 正在回测 {stock_name}({ts_code}) ===")
    
    # 获取数据
    df = processor.get_daily_data(ts_code, start_date, end_date)
    if df.empty:
        print(f"获取数据失败")
        return None
    
    # 处理日期
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)
    df.sort_index(inplace=True)
    
    # 初始化MACD策略
    macd_strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    
    # 计算MACD指标
    df_with_macd = macd_strategy.calculate_macd(df)
    
    # 生成基础版信号并回测
    df_with_signals = macd_strategy.generate_signals(df_with_macd)
    basic_results = macd_strategy.backtest(df_with_signals, enhanced=False)
    
    # 生成增强版信号并回测
    df_with_enhanced_signals = macd_strategy.generate_enhanced_signals(df_with_macd)
    enhanced_results = macd_strategy.backtest(df_with_enhanced_signals, enhanced=True)
    
    # 生成交易记录
    basic_trades = macd_strategy.generate_trade_signals(df_with_signals, enhanced=False)
    enhanced_trades = macd_strategy.generate_trade_signals(df_with_enhanced_signals, enhanced=True)
    
    # 保存结果
    output_dir = '../backtest/results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存详细数据
    df_with_enhanced_signals.to_csv(f'{output_dir}/{ts_code}_macd_backtest.csv')
    
    # 生成报告
    report_content = f"""# {stock_name}({ts_code}) MACD策略回测报告

## 回测参数
- 时间范围: {start_date} 至 {end_date}
- MACD参数: 12日EMA / 26日EMA / 9日信号线
- 初始资金: 100,000.00 元

## 基础版MACD策略表现
| 指标 | 市场表现 | 策略表现 |
|------|----------|----------|
| 总收益率 | {basic_results['total_market_return']*100:.2f}% | {basic_results['total_strategy_return']*100:.2f}% {'(超越市场)' if basic_results['total_strategy_return'] > basic_results['total_market_return'] else '(落后市场)'}
| 年化收益率 | {basic_results['annualized_market_return']*100:.2f}% | {basic_results['annualized_strategy_return']*100:.2f}% |
| 最大回撤 | {basic_results['max_drawdown_market']*100:.2f}% | {basic_results['max_drawdown_strategy']*100:.2f}% {'(优于市场)' if basic_results['max_drawdown_strategy'] > basic_results['max_drawdown_market'] else '(劣于市场)'}
| 胜率 | - | {basic_results['win_rate']*100:.2f}% |
| 夏普比率 | - | {basic_results['sharpe_ratio']:.2f} |
| 交易次数 | - | {basic_results['trade_count']} 次 |
| 最终组合价值 | - | {basic_results['final_portfolio_value']:,.2f} 元 |

## 增强版MACD策略表现
| 指标 | 市场表现 | 策略表现 |
|------|----------|----------|
| 总收益率 | {enhanced_results['total_market_return']*100:.2f}% | {enhanced_results['total_strategy_return']*100:.2f}% {'(超越市场)' if enhanced_results['total_strategy_return'] > enhanced_results['total_market_return'] else '(落后市场)'}
| 年化收益率 | {enhanced_results['annualized_market_return']*100:.2f}% | {enhanced_results['annualized_strategy_return']*100:.2f}% |
| 最大回撤 | {enhanced_results['max_drawdown_market']*100:.2f}% | {enhanced_results['max_drawdown_strategy']*100:.2f}% {'(优于市场)' if enhanced_results['max_drawdown_strategy'] > enhanced_results['max_drawdown_market'] else '(劣于市场)'}
| 胜率 | - | {enhanced_results['win_rate']*100:.2f}% |
| 夏普比率 | - | {enhanced_results['sharpe_ratio']:.2f} |
| 交易次数 | - | {enhanced_results['trade_count']} 次 |
| 最终组合价值 | - | {enhanced_results['final_portfolio_value']:,.2f} 元 |

## 策略对比
- 基础版 vs 增强版总收益率: {basic_results['total_strategy_return']*100:.2f}% vs {enhanced_results['total_strategy_return']*100:.2f}%
- 基础版 vs 增强版交易次数: {basic_results['trade_count']} 次 vs {enhanced_results['trade_count']} 次

## 最近10次基础版交易记录
```
{basic_trades.tail(10).to_string()}
```

## 最近10次增强版交易记录
```
{enhanced_trades.tail(10).to_string()}
```

"""
    
    # 保存报告
    report_path = f'{output_dir}/{ts_code}_macd_backtest_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 生成飞书报告
    feishu_report = f"""### {stock_name}({ts_code}) MACD策略回测报告

**📊 回测结果对比**:

| 指标 | 市场 | 基础版MACD | 增强版MACD |
|------|------|----------|----------|
| 总收益率 | {basic_results['total_market_return']*100:.2f}% | {basic_results['total_strategy_return']*100:.2f}% {'(超越市场)' if basic_results['total_strategy_return'] > basic_results['total_market_return'] else '(落后市场)'}
| 年化收益率 | {basic_results['annualized_market_return']*100:.2f}% | {basic_results['annualized_strategy_return']*100:.2f}% | {enhanced_results['annualized_strategy_return']*100:.2f}% |
| 最大回撤 | {basic_results['max_drawdown_market']*100:.2f}% | {basic_results['max_drawdown_strategy']*100:.2f}% | {enhanced_results['max_drawdown_strategy']*100:.2f}% |
| 夏普比率 | - | {basic_results['sharpe_ratio']:.2f} | {enhanced_results['sharpe_ratio']:.2f} |
| 交易次数 | - | {basic_results['trade_count']} 次 | {enhanced_results['trade_count']} 次 |

**💡 策略表现**:
"""
    
    if enhanced_results['total_strategy_return'] > basic_results['total_strategy_return']:
        feishu_report += "✅ 增强版策略表现优于基础版，信号过滤有效提升了收益\n"
    else:
        feishu_report += "❌ 增强版策略表现未超越基础版\n"
        
    if enhanced_results['trade_count'] < basic_results['trade_count']:
        feishu_report += "✅ 增强版策略交易次数更少，减少了无效交易\n"
    else:
        feishu_report += "❌ 增强版策略交易次数较多\n"
    
    # 总结
    best_strategy = "增强版" if enhanced_results['total_strategy_return'] > basic_results['total_strategy_return'] else "基础版"
    feishu_report += f"\n**结论**: 推荐使用{best_strategy}MACD策略"
    
    return {
        'stock_name': stock_name,
        'ts_code': ts_code,
        'basic_results': basic_results,
        'enhanced_results': enhanced_results,
        'feishu_report': feishu_report
    }


def main():
    """
    主函数
    """
    print("=== MACD策略批量回测 ===")
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    # 选择之前回测的股票
    stocks = [
        {'ts_code': '600036.SH', 'name': '招商银行'},
        {'ts_code': '000001.SZ', 'name': '平安银行'},
        {'ts_code': '600519.SH', 'name': '贵州茅台'}
    ]
    
    # 回测参数
    start_date = '20230101'
    end_date = '20260206'
    
    # 批量回测
    all_reports = []
    
    for stock in stocks:
        try:
            report = backtest_stock(
                processor, stock['ts_code'], stock['name'],
                start_date, end_date
            )
            if report:
                all_reports.append(report)
                
                # 打印结果摘要
                print(f"\n📈 {stock['name']} 回测完成")
                print(f"基础版MACD: {report['basic_results']['total_strategy_return']*100:.2f}%")
                print(f"增强版MACD: {report['enhanced_results']['total_strategy_return']*100:.2f}%")
                print(f"市场表现: {report['basic_results']['total_market_return']*100:.2f}%")
                
        except Exception as e:
            print(f"回测 {stock['name']} 失败: {e}")
    
    # 生成综合报告
    if all_reports:
        summary_dir = '../backtest/reports'
        os.makedirs(summary_dir, exist_ok=True)
        
        feishu_summary = "# MACD策略回测综合报告\n\n## 多股票回测结果对比\n\n"
        
        for report in all_reports:
            feishu_summary += f"""### {report['stock_name']}({report['ts_code']})

| 策略类型 | 总收益率 | 年化收益率 | 最大回撤 | 夏普比率 | 交易次数 |
|----------|----------|----------|----------|----------|----------|
| 市场 | {report['basic_results']['total_market_return']*100:.2f}% | {report['basic_results']['annualized_market_return']*100:.2f}% | {report['basic_results']['max_drawdown_market']*100:.2f}% | - | - |
| 基础版MACD | {report['basic_results']['total_strategy_return']*100:.2f}% | {report['basic_results']['annualized_strategy_return']*100:.2f}% | {report['basic_results']['max_drawdown_strategy']*100:.2f}% | {report['basic_results']['sharpe_ratio']:.2f} | {report['basic_results']['trade_count']} |
| 增强版MACD | {report['enhanced_results']['total_strategy_return']*100:.2f}% | {report['enhanced_results']['annualized_strategy_return']*100:.2f}% | {report['enhanced_results']['max_drawdown_strategy']*100:.2f}% | {report['enhanced_results']['sharpe_ratio']:.2f} | {report['enhanced_results']['trade_count']} |

"""
        
        # 统计平均表现
        avg_basic_return = sum(r['basic_results']['total_strategy_return'] for r in all_reports) / len(all_reports)
        avg_enhanced_return = sum(r['enhanced_results']['total_strategy_return'] for r in all_reports) / len(all_reports)
        avg_market_return = sum(r['basic_results']['total_market_return'] for r in all_reports) / len(all_reports)
        
        feishu_summary += f"""
## 综合统计

- 平均市场收益率: {avg_market_return*100:.2f}%
- 平均基础版MACD收益率: {avg_basic_return*100:.2f}%
- 平均增强版MACD收益率: {avg_enhanced_return*100:.2f}%
- 增强版优于基础版的股票数量: {sum(1 for r in all_reports if r['enhanced_results']['total_strategy_return'] > r['basic_results']['total_strategy_return'])}/{len(all_reports)}
"""
        
        # 保存综合报告
        summary_path = f'{summary_dir}/macd_strategy_summary_{start_date}_{end_date}.md'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(feishu_summary)
        
        print(f"\n📊 综合报告已保存至: {summary_path}")
        
        # 发送飞书报告
        from message import message
        
        # 先发送每个股票的报告
        for report in all_reports:
            try:
                message(action='send', channel='feishu', target='ou_e39fd3529ff7fea2eca6b1e0b35ed98f', message=report['feishu_report'])
            except Exception as e:
                print(f"发送飞书报告失败: {e}")
        
        # 发送综合报告
        try:
            message(action='send', channel='feishu', target='ou_e39fd3529ff7fea2eca6b1e0b35ed98f', message=feishu_summary)
        except Exception as e:
            print(f"发送综合报告失败: {e}")
    
    print("\n=== 回测完成 ===")


if __name__ == '__main__':
    main()
