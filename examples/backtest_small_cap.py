#!/usr/bin/env python3
"""
小市值策略回测示例
"""

import sys
import os
sys.path.append('..')

import pandas as pd
import numpy as np
from data_processor import DataProcessor
from strategies.small_cap_strategy import SmallCapStrategy


def get_stock_universe(processor, date: str = '20260206') -> pd.DataFrame:
    """
    获取指定日期的股票池
    
    Args:
        processor: DataProcessor实例
        date: 查询日期
        
    Returns:
        全市场股票DataFrame
    """
    print(f"获取全市场股票数据 (日期: {date})...")
    
    # 获取全市场股票列表
    stock_list = processor.pro.stock_basic(exchange='', list_status='L', 
                                         fields='ts_code,symbol,name,industry,list_date,circ_mv')
    
    # 获取最新交易日数据
    trade_cal = processor.pro.trade_cal(exchange='SSE', is_open='1', 
                                     start_date=date, end_date=date)
    
    if len(trade_cal) == 0:
        # 如果当天不是交易日，找最近的交易日
        trade_cal = processor.pro.trade_cal(exchange='SSE', is_open='1', 
                                         start_date='20230101', end_date=date)
        date = trade_cal.iloc[-1]['cal_date']
    
    # 获取当日行情数据
    df_daily = processor.pro.daily(trade_date=date)
    
    # 获取财务指标
    fina_indicator = processor.pro.fina_indicator(ann_date='20251231', 
                                               fields='ts_code,profit,pe,roe,operating_cashflow')
    
    # 合并数据
    merged_df = pd.merge(stock_list, df_daily[['ts_code', 'close', 'pct_chg', 'turnover']], 
                       on='ts_code', how='left')
    
    merged_df = pd.merge(merged_df, fina_indicator, on='ts_code', how='left')
    
    # 数据清洗
    merged_df = merged_df.dropna(subset=['circ_mv', 'close'])
    merged_df = merged_df[merged_df['circ_mv'] > 0]
    
    # 转换数据类型
    merged_df['circ_mv'] = merged_df['circ_mv'].astype(float) * 10000  # 转换为元
    merged_df['profit'] = merged_df['profit'].fillna(0) * 100000000  # 转换为元
    merged_df['turnover'] = merged_df['turnover'].fillna(0) * 10000  # 转换为元
    
    return merged_df


def backtest_small_cap_strategy(processor):
    """
    回测小市值策略
    
    Args:
        processor: DataProcessor实例
    """
    print("=== 小市值策略回测 ===")
    
    # 初始化策略
    strategy = SmallCapStrategy(
        universe_size=300,
        filter_conditions={
            'positive_profit': True,
            'reasonable_pe': True,
            'liquidity': True
        },
        rebalance_frequency='monthly'
    )
    
    # 获取测试数据（这里简化为单日期数据，实际应使用多日期滚动回测）
    test_date = '20260201'
    stock_universe = get_stock_universe(processor, date=test_date)
    
    print(f"\n总股票数量: {len(stock_universe)}")
    
    # 基础版小市值选股
    basic_selection = strategy.basic_small_cap_selection(stock_universe)
    print(f"\n基础版小市值策略选择股票数量: {len(basic_selection)}")
    print(f"平均流通市值: {basic_selection['circ_mv'].mean() / 100000000:.2f}亿")
    print(f"平均市盈率: {basic_selection['pe'].mean():.2f}")
    print(f"平均涨跌幅: {basic_selection['pct_chg'].mean():.2f}%")
    
    # 增强版小市值选股
    enhanced_selection = strategy.enhanced_small_cap_selection(stock_universe)
    print(f"\n增强版小市值策略选择股票数量: {len(enhanced_selection)}")
    print(f"平均流通市值: {enhanced_selection['circ_mv'].mean() / 100000000:.2f}亿")
    print(f"平均市盈率: {enhanced_selection['pe'].mean():.2f}")
    print(f"平均涨跌幅: {enhanced_selection['pct_chg'].mean():.2f}%")
    print(f"盈利股票占比: {(enhanced_selection['profit'] > 0).mean() * 100:.2f}%")
    
    # 多因子小市值选股
    multi_factor_selection = strategy.multi_factor_small_cap_selection(stock_universe)
    print(f"\n多因子小市值策略选择股票数量: {len(multi_factor_selection)}")
    print(f"平均流通市值: {multi_factor_selection['circ_mv'].mean() / 100000000:.2f}亿")
    print(f"平均市盈率: {multi_factor_selection['pe'].mean():.2f}")
    print(f"平均ROE: {multi_factor_selection['roe'].mean():.2f}%")
    
    # 保存选股结果
    output_dir = '../backtest/results'
    os.makedirs(output_dir, exist_ok=True)
    
    basic_selection.to_csv(f"{output_dir}/basic_small_cap_selection_{test_date}.csv", index=False, encoding='utf-8-sig')
    enhanced_selection.to_csv(f"{output_dir}/enhanced_small_cap_selection_{test_date}.csv", index=False, encoding='utf-8-sig')
    multi_factor_selection.to_csv(f"{output_dir}/multi_factor_small_cap_selection_{test_date}.csv", index=False, encoding='utf-8-sig')
    
    print(f"\n📊 选股结果已保存至: {output_dir}")
    
    # 生成选股报告
    report_content = f"""# 小市值策略选股报告

## 回测日期: {test_date}

## 策略参数
- 选股数量: 300只
- 调仓频率: 月度调仓
- 基本面过滤: 盈利为正、市盈率0-50倍、日成交额>1000万

## 选股结果

### 基础版小市值策略
| 指标 | 数值 |
|------|------|
| 选股数量 | {len(basic_selection)}只 |
| 平均流通市值 | {basic_selection['circ_mv'].mean() / 100000000:.2f}亿 |
| 平均市盈率 | {basic_selection['pe'].mean():.2f} |
| 平均ROE | {basic_selection['roe'].mean():.2f}% |
| 平均日成交额 | {basic_selection['turnover'].mean() / 10000:.2f}万 |
| 平均涨跌幅 | {basic_selection['pct_chg'].mean():.2f}% |

### 增强版小市值策略
| 指标 | 数值 |
|------|------|
| 选股数量 | {len(enhanced_selection)}只 |
| 平均流通市值 | {enhanced_selection['circ_mv'].mean() / 100000000:.2f}亿 |
| 平均市盈率 | {enhanced_selection['pe'].mean():.2f} |
| 平均ROE | {enhanced_selection['roe'].mean():.2f}% |
| 平均日成交额 | {enhanced_selection['turnover'].mean() / 10000:.2f}万 |
| 平均涨跌幅 | {enhanced_selection['pct_chg'].mean():.2f}% |
| 盈利股票占比 | {(enhanced_selection['profit'] > 0).mean() * 100:.2f}% |

### 多因子小市值策略
| 指标 | 数值 |
|------|------|
| 选股数量 | {len(multi_factor_selection)}只 |
| 平均流通市值 | {multi_factor_selection['circ_mv'].mean() / 100000000:.2f}亿 |
| 平均市盈率 | {multi_factor_selection['pe'].mean():.2f} |
| 平均ROE | {multi_factor_selection['roe'].mean():.2f}% |
| 平均日成交额 | {multi_factor_selection['turnover'].mean() / 10000:.2f}万 |
| 平均涨跌幅 | {multi_factor_selection['pct_chg'].mean():.2f}% |
| 盈利股票占比 | {(multi_factor_selection['profit'] > 0).mean() * 100:.2f}% |

## 行业分布

"""
    
    # 添加行业分布
    report_content += "\n### 增强版小市值策略行业分布\n\n"
    industry_dist = enhanced_selection['industry'].value_counts()[:10].to_string()
    report_content += f"```\n{industry_dist}\n```\n"
    
    # 保存报告
    report_path = f"{output_dir}/small_cap_strategy_report_{test_date}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📝 选股报告已保存至: {report_path}")
    
    # 生成飞书报告
    feishu_report = f"""# 📈 小市值策略选股结果

## 回测日期: {test_date}

**基础版策略**:
- 选股数量: {len(basic_selection)}只
- 平均流通市值: {basic_selection['circ_mv'].mean() / 100000000:.2f}亿
- 平均市盈率: {basic_selection['pe'].mean():.2f}

**增强版策略**:
- 选股数量: {len(enhanced_selection)}只
- 平均流通市值: {enhanced_selection['circ_mv'].mean() / 100000000:.2f}亿
- 平均市盈率: {enhanced_selection['pe'].mean():.2f}
- 盈利股票占比: {(enhanced_selection['profit'] > 0).mean() * 100:.2f}%

**多因子策略**:
- 选股数量: {len(multi_factor_selection)}只
- 平均流通市值: {multi_factor_selection['circ_mv'].mean() / 100000000:.2f}亿
- 平均ROE: {multi_factor_selection['roe'].mean():.2f}%

💡 完整报告已保存到GitHub仓库
"""
    
    return {
        'feishu_report': feishu_report,
        'basic_selection_size': len(basic_selection),
        'enhanced_selection_size': len(enhanced_selection),
        'multi_factor_selection_size': len(multi_factor_selection)
    }


def main():
    """
    主函数
    """
    print("=== 小市值策略回测 ===")
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    try:
        # 回测小市值策略
        results = backtest_small_cap_strategy(processor)
        
        print("\n=== 回测完成 ===")
        
        # 发送飞书报告
        try:
            from message import message
            message(action='send', channel='feishu', target='ou_e39fd3529ff7fea2eca6b1e0b35ed98f', message=results['feishu_report'])
            print("💌 飞书报告已发送")
        except Exception as e:
            print(f"⚠️ 发送飞书报告失败: {e}")
            
    except Exception as e:
        print(f"❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
