#!/usr/bin/env python3
"""
批量回测脚本：使用双均线和MACD策略对全部15只股票进行回测
"""

import sys
import os
sys.path.append('..')

import pandas as pd
import numpy as np
import yaml
from typing import Dict, List

from data_processor import DataProcessor
from strategies.moving_average_cross import MovingAverageCrossStrategy
from strategies.macd_strategy import MACDStrategy


def load_stock_pool() -> List[Dict]:
    """
    加载固定的股票池配置
    
    Returns:
        股票列表
    """
    # 直接定义股票池
    return [
        {'ts_code': '600519.SH', 'name': '贵州茅台', 'industry': '消费', 'style': '价值蓝筹'},
        {'ts_code': '300750.SZ', 'name': '宁德时代', 'industry': '新能源', 'style': '成长'},
        {'ts_code': '600036.SH', 'name': '招商银行', 'industry': '银行', 'style': '价值成长'},
        {'ts_code': '002594.SZ', 'name': '比亚迪', 'industry': '汽车', 'style': '成长周期'},
        {'ts_code': '300059.SZ', 'name': '东方财富', 'industry': '证券', 'style': '互联网金融'},
        {'ts_code': '600276.SH', 'name': '恒瑞医药', 'industry': '医药', 'style': '创新成长'},
        {'ts_code': '601012.SH', 'name': '隆基绿能', 'industry': '光伏', 'style': '成长周期'},
        {'ts_code': '600900.SH', 'name': '长江电力', 'industry': '公用事业', 'style': '高股息'},
        {'ts_code': '600309.SH', 'name': '万华化学', 'industry': '化工', 'style': '周期成长'},
        {'ts_code': '002049.SZ', 'name': '紫光国微', 'industry': '半导体', 'style': '科技成长'},
        {'ts_code': '000858.SZ', 'name': '五粮液', 'industry': '消费', 'style': '价值成长'},
        {'ts_code': '601318.SH', 'name': '中国平安', 'industry': '保险', 'style': '金融蓝筹'},
        {'ts_code': '688981.SH', 'name': '中芯国际', 'industry': '半导体', 'style': '科技周期'},
        {'ts_code': '600887.SH', 'name': '伊利股份', 'industry': '消费', 'style': '价值蓝筹'},
        {'ts_code': '600030.SH', 'name': '中信证券', 'industry': '证券', 'style': '金融蓝筹'}
    ]


def backtest_single_stock(processor, stock_info: Dict) -> Dict:
    """
    对单只股票进行双均线和MACD策略回测
    
    Args:
        processor: DataProcessor实例
        stock_info: 股票信息字典
        
    Returns:
        回测结果字典
    """
    ts_code = stock_info['ts_code']
    stock_name = stock_info['name']
    
    print(f"\n=== 正在回测 {stock_name}({ts_code}) ===")
    
    # 获取数据
    start_date = '20230101'
    end_date = '20260206'
    
    df = processor.get_daily_data(ts_code, start_date, end_date)
    if df.empty:
        print(f"❌ 获取数据失败")
        return None
    
    # 处理日期
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)
    df.sort_index(inplace=True)
    
    # 回测双均线策略
    ma_strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
    df_with_ma = ma_strategy.calculate_indicators(df)
    ma_results = ma_strategy.backtest(df_with_ma)
    ma_trades = ma_strategy.generate_trade_signals(df_with_ma)
    
    # 回测MACD策略
    macd_strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    df_with_macd = macd_strategy.calculate_macd(df)
    df_with_macd_signals = macd_strategy.generate_signals(df_with_macd)
    macd_results = macd_strategy.backtest(df_with_macd_signals, enhanced=False)
    macd_trades = macd_strategy.generate_trade_signals(df_with_macd_signals, enhanced=False)
    
    # 回测增强版MACD策略
    df_with_enhanced_macd = macd_strategy.generate_enhanced_signals(df_with_macd)
    macd_enhanced_results = macd_strategy.backtest(df_with_enhanced_macd, enhanced=True)
    macd_enhanced_trades = macd_strategy.generate_trade_signals(df_with_enhanced_macd, enhanced=True)
    
    # 生成结果
    result = {
        'ts_code': ts_code,
        'name': stock_name,
        'industry': stock_info['industry'],
        'style': stock_info['style'],
        'ma_results': ma_results,
        'macd_results': macd_results,
        'macd_enhanced_results': macd_enhanced_results,
        'ma_win_rate': ma_results.get('win_rate', 0),
        'macd_win_rate': macd_results.get('win_rate', 0),
        'market_return': ma_results.get('total_market_return', 0),
        'best_strategy': None,
        'best_return': float('-inf'),
        'best_sharpe': float('-inf')
    }
    
    # 找出表现最好的策略
    strategies = [
        ('双均线', ma_results['total_strategy_return'], ma_results['sharpe_ratio']),
        ('MACD基础版', macd_results['total_strategy_return'], macd_results['sharpe_ratio']),
        ('MACD增强版', macd_enhanced_results['total_strategy_return'], macd_enhanced_results['sharpe_ratio'])
    ]
    
    for strategy_name, total_return, sharpe_ratio in strategies:
        if total_return > result['best_return'] and sharpe_ratio > 0:
            result['best_return'] = total_return
            result['best_strategy'] = strategy_name
            result['best_sharpe'] = sharpe_ratio
    
    if result['best_strategy'] is None:
        # 如果夏普比率都为负，只看收益率
        result['best_strategy'], result['best_return'], _ = max(strategies, key=lambda x: x[1])
    
    print(f"✅ 回测完成: {stock_name}")
    print(f"  市场收益率: {result['market_return']*100:.2f}%")
    print(f"  双均线: {ma_results['total_strategy_return']*100:.2f}%")
    print(f"  MACD: {macd_results['total_strategy_return']*100:.2f}%")
    print(f"  最优策略: {result['best_strategy']} ({result['best_return']*100:.2f}%)")
    
    return result


def generate_summary_report(all_results: List[Dict], output_dir: str):
    """
    生成综合回测报告
    
    Args:
        all_results: 所有回测结果
        output_dir: 报告输出目录
    """
    if not all_results:
        print("没有回测结果可生成报告")
        return None, None
    
    # 转换为DataFrame方便统计
    summary_df = pd.DataFrame({
        '股票代码': [r['ts_code'] for r in all_results],
        '股票名称': [r['name'] for r in all_results],
        '行业': [r['industry'] for r in all_results],
        '风格': [r['style'] for r in all_results],
        '市场收益率': [r['market_return']*100 for r in all_results],
        '双均线收益率': [r['ma_results']['total_strategy_return']*100 for r in all_results],
        '双均线夏普': [r['ma_results']['sharpe_ratio'] for r in all_results],
        'MACD收益率': [r['macd_results']['total_strategy_return']*100 for r in all_results],
        'MACD夏普': [r['macd_results']['sharpe_ratio'] for r in all_results],
        'MACD增强收益率': [r['macd_enhanced_results']['total_strategy_return']*100 for r in all_results],
        'MACD增强夏普': [r['macd_enhanced_results']['sharpe_ratio'] for r in all_results],
        '最优策略': [r['best_strategy'] for r in all_results],
        '最优收益率': [r['best_return']*100 for r in all_results]
    })
    
    # 按行业分组统计
    industry_summary = summary_df.groupby('行业').agg({
        '市场收益率': 'mean',
        '双均线收益率': 'mean',
        'MACD收益率': 'mean',
        'MACD增强收益率': 'mean'
    }).round(2)
    
    # 策略表现统计
    strategy_stats = {
        '双均线平均收益率': summary_df['双均线收益率'].mean(),
        '双均线跑赢市场次数': len(summary_df[summary_df['双均线收益率'] > summary_df['市场收益率']]),
        'MACD平均收益率': summary_df['MACD收益率'].mean(),
        'MACD跑赢市场次数': len(summary_df[summary_df['MACD收益率'] > summary_df['市场收益率']]),
        'MACD增强平均收益率': summary_df['MACD增强收益率'].mean(),
        'MACD增强跑赢市场次数': len(summary_df[summary_df['MACD增强收益率'] > summary_df['市场收益率']]),
        '股票总数': len(all_results)
    }
    
    # 生成报告内容
    report_content = f"""# 量化策略回测综合报告

## 回测概述
- 回测时间范围: 2023-01-01 至 2026-02-06
- 回测股票数量: {len(all_results)} 只
- 测试策略: 双均线(20/60)、MACD基础版(12/26/9)、MACD增强版
- 初始资金: 100,000.00 元

## 综合统计

### 策略表现汇总
| 策略类型 | 平均收益率 | 跑赢市场次数 | 胜率 |
|----------|----------|----------|------|
| 市场基准 | {summary_df['市场收益率'].mean():.2f}% | - | - |
| 双均线策略 | {strategy_stats['双均线平均收益率']:.2f}% | {strategy_stats['双均线跑赢市场次数']}/{strategy_stats['股票总数']} | {summary_df['双均线夏普'].mean():.2f} |
| MACD基础版 | {strategy_stats['MACD平均收益率']:.2f}% | {strategy_stats['MACD跑赢市场次数']}/{strategy_stats['股票总数']} | {summary_df['MACD夏普'].mean():.2f} |
| MACD增强版 | {strategy_stats['MACD增强平均收益率']:.2f}% | {strategy_stats['MACD增强跑赢市场次数']}/{strategy_stats['股票总数']} | {summary_df['MACD增强夏普'].mean():.2f} |

### 最优策略分布
```
{summary_df['最优策略'].value_counts().to_string()}
```

## 分行业表现

```
{industry_summary.to_string()}
```

## 各股票详细表现

| 股票名称 | 行业 | 市场收益率 | 双均线收益率 | MACD收益率 | 增强版MACD收益率 | 最优策略 | 最优收益率 |
|----------|------|----------|----------|----------|----------|----------|----------|
"""
    
    # 添加详细数据
    for _, row in summary_df.iterrows():
        report_content += f"| {row['股票名称']} | {row['行业']} | {row['市场收益率']:.2f}% | {row['双均线收益率']:.2f}% | {row['MACD收益率']:.2f}% | {row['MACD增强收益率']:.2f}% | {row['最优策略']} | {row['最优收益率']:.2f}% |\n"
    
    # 添加结论与建议
    best_overall_strategy = max(
        ('双均线', strategy_stats['双均线平均收益率']),
        ('MACD基础版', strategy_stats['MACD平均收益率']),
        ('MACD增强版', strategy_stats['MACD增强平均收益率']),
        key=lambda x: x[1]
    )
    
    report_content += f"""
## 🎯 结论与建议

### 整体表现
- 表现最好的策略: {best_overall_strategy[0]} ({best_overall_strategy[1]:.2f}%)
- 市场平均收益率: {summary_df['市场收益率'].mean():.2f}%

### 策略选择建议

"""
    
    # 根据行业特性给出建议
    if strategy_stats['双均线平均收益率'] > strategy_stats['MACD平均收益率']:
        report_content += "✅ 双均线策略整体表现优于MACD策略\n"
        report_content += "📈 建议在高波动率、趋势性强的股票上使用双均线策略\n"
    else:
        report_content += "✅ MACD策略整体表现优于双均线策略\n"
        report_content += "📉 建议在震荡市和趋势转折时使用MACD策略\n"
    
    report_content += """
### 后续优化方向
1. 根据股票波动率动态调整均线参数
2. 结合成交量、RSI等指标过滤无效信号
3. 加入止损止盈机制控制风险
4. 构建多策略组合提升稳定性
"""
    
    # 保存报告
    os.makedirs(output_dir, exist_ok=True)
    report_path = f"{output_dir}/strategy_backtest_summary_{pd.Timestamp.now().strftime('%Y%m%d')}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📊 回测报告已保存至: {report_path}")
    
    # 生成飞书版本报告
    feishu_report = f"""# 📊 量化策略回测报告

## 回测结论

**整体表现**:
- 市场平均收益率: {summary_df['市场收益率'].mean():.2f}%
- 双均线平均收益率: {strategy_stats['双均线平均收益率']:.2f}%
- MACD平均收益率: {strategy_stats['MACD平均收益率']:.2f}%
- MACD增强版收益率: {strategy_stats['MACD增强平均收益率']:.2f}%

**最优策略**: {best_overall_strategy[0]} ({best_overall_strategy[1]:.2f}%)

**策略分布**:
{summary_df['最优策略'].value_counts().to_string()}

**分行业表现**:
{industry_summary.to_string()}

💡 详细报告已保存到GitHub仓库，建议重点关注表现最优的5只股票策略表现，考虑构建多策略组合。"""
    
    return report_path, feishu_report


def main():
    """
    主函数
    """
    print("=== 批量回测双均线和MACD策略 ===")
    print("股票池规模: 15只核心股票")
    print("回测时间: 2023-01-01 至 2026-02-06")
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    # 加载股票池
    stock_pool = load_stock_pool()
    print(f"\n📋 共加载{len(stock_pool)}只股票")
    
    # 批量回测
    all_results = []
    failed_stocks = []
    
    for stock_info in stock_pool:
        try:
            result = backtest_single_stock(processor, stock_info)
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"❌ 回测{stock_info['name']}失败: {e}")
            failed_stocks.append(stock_info['name'])
    
    print(f"\n=== 回测完成 ===")
    print(f"✅ 成功回测: {len(all_results)}只股票")
    if failed_stocks:
        print(f"❌ 回测失败: {len(failed_stocks)}只股票: {', '.join(failed_stocks)}")
    
    # 生成报告
    if all_results:
        report_path, feishu_report = generate_summary_report(all_results, '../backtest/reports')
        print(f"\n📝 报告生成完成")
        
        # 保存详细结果
        results_df = pd.DataFrame(all_results)
        results_path = f"../backtest/results/batch_backtest_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv"
        results_df.to_csv(results_path, index=False, encoding='utf-8-sig')
        print(f"📊 详细结果已保存至: {results_path}")
        
        # 打印简短总结
        avg_market = results_df['market_return'].mean() * 100
        avg_ma = results_df.apply(lambda x: x['ma_results']['total_strategy_return'], axis=1).mean() * 100
        avg_macd = results_df.apply(lambda x: x['macd_results']['total_strategy_return'], axis=1).mean() * 100
        
        print("\n📈 回测总结:")
        print(f"市场平均收益率: {avg_market:.2f}%")
        print(f"双均线平均收益率: {avg_ma:.2f}%")
        print(f"MACD平均收益率: {avg_macd:.2f}%")
        print(f"最优策略分布: {results_df['best_strategy'].value_counts().to_string()}")
        
        # 发送飞书报告
        try:
            from message import message
            message(action='send', channel='feishu', target='ou_e39fd3529ff7fea2eca6b1e0b35ed98f', message=feishu_report)
            print("\n💌 飞书报告已发送")
        except Exception as e:
            print(f"\n⚠️ 发送飞书报告失败: {e}")
    else:
        print("\n⚠️ 没有可用回测结果，无法生成报告")


if __name__ == '__main__':
    main()
