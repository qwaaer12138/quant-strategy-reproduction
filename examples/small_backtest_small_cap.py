#!/usr/bin/env python3
"""
简化版小市值策略回测
使用现有15只股票池进行小规模回测
"""

import sys
import os
sys.path.append('..')

import pandas as pd
import numpy as np
from data_processor import DataProcessor
from strategies.small_cap_strategy import SmallCapStrategy


def get_stock_list():
    """
    获取测试股票列表
    """
    return [
        {'ts_code': '600519.SH', 'name': '贵州茅台', 'industry': '消费'},
        {'ts_code': '300750.SZ', 'name': '宁德时代', 'industry': '新能源'},
        {'ts_code': '600036.SH', 'name': '招商银行', 'industry': '银行'},
        {'ts_code': '002594.SZ', 'name': '比亚迪', 'industry': '汽车'},
        {'ts_code': '300059.SZ', 'name': '东方财富', 'industry': '证券'},
        {'ts_code': '600276.SH', 'name': '恒瑞医药', 'industry': '医药'},
        {'ts_code': '601012.SH', 'name': '隆基绿能', 'industry': '光伏'},
        {'ts_code': '600900.SH', 'name': '长江电力', 'industry': '公用事业'},
        {'ts_code': '600309.SH', 'name': '万华化学', 'industry': '化工'},
        {'ts_code': '002049.SZ', 'name': '紫光国微', 'industry': '半导体'},
        {'ts_code': '000858.SZ', 'name': '五粮液', 'industry': '消费'},
        {'ts_code': '601318.SH', 'name': '中国平安', 'industry': '保险'},
        {'ts_code': '688981.SH', 'name': '中芯国际', 'industry': '半导体'},
        {'ts_code': '600887.SH', 'name': '伊利股份', 'industry': '消费'},
        {'ts_code': '600030.SH', 'name': '中信证券', 'industry': '证券'}
    ]


def get_historical_data(processor, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取单只股票的历史数据
    
    Args:
        processor: DataProcessor实例
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        历史数据DataFrame
    """
    try:
        # 获取日线数据
        df_daily = processor.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        # 获取基本面数据
        df_basic = processor.pro.stock_basic(ts_code=ts_code, fields='ts_code,circ_mv')
        
        # 获取财务数据
        df_fina = processor.pro.fina_indicator(ts_code=ts_code, start_date=start_date, 
                                             end_date=end_date, fields='ts_code,profit,pe,roe')
        
        # 合并数据
        merged_df = pd.merge(df_daily, df_basic, on='ts_code', how='left')
        merged_df = pd.merge(merged_df, df_fina, on=['ts_code'], how='left')
        
        # 数据清洗
        merged_df['circ_mv'] = merged_df['circ_mv'].fillna(method='bfill') * 10000  # 转换为元
        merged_df['profit'] = merged_df['profit'].fillna(0) * 100000000  # 转换为元
        merged_df['pe'] = merged_df['pe'].fillna(method='bfill')
        merged_df['roe'] = merged_df['roe'].fillna(method='bfill')
        
        return merged_df
        
    except Exception as e:
        print(f"获取{ts_code}数据失败: {e}")
        return pd.DataFrame()


def simulate_small_cap_backtest(processor):
    """
    模拟小市值策略回测
    
    Args:
        processor: DataProcessor实例
        
    Returns:
        回测结果字典
    """
    print("=== 小市值策略小规模回测 ===")
    
    # 回测参数
    start_date = '20250201'
    end_date = '20260206'
    rebalance_months = 3  # 每3个月调仓一次
    selection_size = 5  # 每次选择5只最小市值股票
    
    print(f"回测时间范围: {start_date} 至 {end_date}")
    print(f"调仓频率: 每{rebalance_months}个月")
    print(f"选股数量: 每次选{selection_size}只最小市值股票")
    
    # 获取股票列表
    stock_list = get_stock_list()
    
    # 获取所有股票的历史数据
    all_data = []
    
    for stock in stock_list:
        print(f"获取{stock['name']}({stock['ts_code']})数据...")
        df = get_historical_data(processor, stock['ts_code'], start_date, end_date)
        if not df.empty:
            df['name'] = stock['name']
            df['industry'] = stock['industry']
            all_data.append(df)
    
    if len(all_data) == 0:
        print("没有获取到任何数据，回测无法进行")
        return {}
    
    # 合并所有数据
    all_data_df = pd.concat(all_data)
    all_data_df['trade_date'] = pd.to_datetime(all_data_df['trade_date'])
    all_data_df = all_data_df.sort_values('trade_date')
    
    # 生成调仓日期
    rebalance_dates = pd.date_range(start=start_date, end=end_date, freq=f'{rebalance_months}MS')
    
    # 初始化策略
    strategy = SmallCapStrategy(
        universe_size=selection_size,
        filter_conditions={'positive_profit': True},
        rebalance_frequency='monthly'
    )
    
    # 回测主逻辑
    portfolio_value = 1.0
    portfolio_history = []
    current_portfolio = []
    
    # 按调仓周期分组回测
    grouped = all_data_df.groupby(pd.Grouper(key='trade_date', freq='M'))
    
    for date, group_df in grouped:
        print(f"\n处理月份: {date.strftime('%Y-%m')}")
        
        # 转换数据格式
        monthly_data = group_df.copy()
        monthly_data['circ_mv'] = monthly_data['circ_mv'].fillna(method='ffill')
        
        # 检查是否需要调仓
        if date.month % rebalance_months == 0 or not current_portfolio:
            print("  执行调仓...")
            
            # 计算当前市值
            latest_day = monthly_data.groupby('ts_code').last().reset_index()
            
            # 过滤掉亏损股票
            filtered = latest_day[latest_day['profit'] > 0]
            
            if len(filtered) >= selection_size:
                # 选择市值最小的股票
                sorted_stocks = filtered.sort_values('circ_mv', ascending=True)
                selected_stocks = sorted_stocks.head(selection_size)
                current_portfolio = selected_stocks['ts_code'].tolist()
                
                print(f"  新组合: {', '.join(selected_stocks['name'].tolist())}")
                print(f"  平均市值: {selected_stocks['circ_mv'].mean()/100000000:.2f}亿")
            else:
                print(f"  盈利股票不足{selection_size}只，不调仓")
        
        # 计算当月组合收益
        if current_portfolio:
            # 获取持仓股票当月数据
            holding_data = group_df[group_df['ts_code'].isin(current_portfolio)]
            
            # 计算每只股票当月收益
            stock_returns = holding_data.groupby('ts_code')['pct_chg'].apply(
                lambda x: (1 + x/100).prod() - 1
            )
            
            # 等权计算组合收益
            if not stock_returns.empty:
                monthly_return = stock_returns.mean()
                portfolio_value *= (1 + monthly_return)
                portfolio_history.append({
                    'date': date,
                    'portfolio_value': portfolio_value,
                    'monthly_return': monthly_return,
                    'stock_count': len(current_portfolio)
                })
                
                print(f"  组合收益率: {monthly_return*100:.2f}%")
                print(f"  累计净值: {portfolio_value:.4f}")
    
    # 计算回测指标
    if portfolio_history:
        portfolio_df = pd.DataFrame(portfolio_history)
        portfolio_df.set_index('date', inplace=True)
        
        total_return = portfolio_value - 1
        months = len(portfolio_df)
        annualized_return = (1 + total_return) ** (12/months) - 1
        
        # 计算最大回撤
        portfolio_df['peak'] = portfolio_df['portfolio_value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['peak']) / portfolio_df['peak']
        max_drawdown = portfolio_df['drawdown'].min()
        
        # 计算夏普比率
        sharpe_ratio = np.sqrt(12) * portfolio_df['monthly_return'].mean() / portfolio_df['monthly_return'].std() if portfolio_df['monthly_return'].std() != 0 else 0
        
        # 生成报告
        report_content = f"""# 小市值策略回测报告

## 回测参数
- 回测时间: {start_date} 至 {end_date}
- 股票池规模: {len(stock_list)}只
- 选股数量: {selection_size}只
- 调仓频率: 每{rebalance_months}个月
- 过滤条件: 盈利为正的股票

## 回测结果
| 指标 | 数值 |
|------|------|
| 总收益率 | {total_return*100:.2f}% |
| 年化收益率 | {annualized_return*100:.2f}% |
| 最大回撤 | {max_drawdown*100:.2f}% |
| 夏普比率 | {sharpe_ratio:.2f} |
| 回测月份数 | {len(portfolio_df)}个月 |
| 最终组合净值 | {portfolio_value:.4f} |

## 组合表现历史

| 月份 | 组合净值 | 月度收益率 |
|------|------|----------|
"""
        
        for _, row in portfolio_df.iterrows():
            report_content += f"| {row.name.strftime('%Y-%m')} | {row['portfolio_value']:.4f} | {row['monthly_return']*100:.2f}% |\n"
        
        report_content += f"""

## 🎯 结论

"""
        
        if annualized_return > 0.05:  # 年化5%以上表现优秀
            report_content += "✅ 小市值策略在本次回测中表现优秀，年化收益率超过5%\n"
        elif annualized_return > 0:
            report_content += "⚠️ 小市值策略表现一般，勉强跑赢通胀\n"
        else:
            report_content += "❌ 小市值策略表现不佳，未能获得正收益\n"
        
        # 保存报告
        output_dir = '../backtest/results'
        os.makedirs(output_dir, exist_ok=True)
        
        report_path = f"{output_dir}/small_cap_backtest_result_{start_date}_{end_date}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📊 回测报告已保存至: {report_path}")
        
        # 保存详细数据
        portfolio_df.to_csv(f"{output_dir}/small_cap_backtest_history_{start_date}_{end_date}.csv", encoding='utf-8-sig')
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'months_analyzed': len(portfolio_df),
            'final_portfolio_value': portfolio_value,
            'report_path': report_path,
            'feishu_report': f"""# 📈 小市值策略回测结果

**回测时间**: {start_date} 至 {end_date}
**调仓频率**: 每{rebalance_months}个月
**选股数量**: {selection_size}只

**核心指标**:
- 总收益率: {total_return*100:.2f}%
- 年化收益率: {annualized_return*100:.2f}%
- 最大回撤: {max_drawdown*100:.2f}%
- 夏普比率: {sharpe_ratio:.2f}

**结论**: {'✅ 策略表现优秀' if annualized_return>0.05 else '⚠️ 策略表现一般' if annualized_return>0 else '❌ 策略表现不佳'}

💡 完整报告已保存到GitHub仓库"""
        }
        
    return {}


def main():
    """
    主函数
    """
    print("=== 简化版小市值策略回测 ===")
    
    # 初始化数据处理器
    processor = DataProcessor()
    
    try:
        # 执行回测
        results = simulate_small_cap_backtest(processor)
        
        print("\n=== 回测完成 ===")
        
        if results:
            print(f"\n📝 回测结果:")
            print(f"总收益率: {results['total_return']*100:.2f}%")
            print(f"年化收益率: {results['annualized_return']*100:.2f}%")
            print(f"最大回撤: {results['max_drawdown']*100:.2f}%")
            print(f"夏普比率: {results['sharpe_ratio']:.2f}")
            
            # 发送飞书报告
            try:
                from message import message
                message(action='send', channel='feishu', target='ou_e39fd3529ff7fea2eca6b1e0b35ed98f', message=results['feishu_report'])
                print("\n💌 飞书报告已发送")
            except Exception as e:
                print(f"\n⚠️ 发送飞书报告失败: {e}")
        else:
            print("\n⚠️ 没有获得回测结果")
            
    except Exception as e:
        print(f"\n❌ 回测执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
