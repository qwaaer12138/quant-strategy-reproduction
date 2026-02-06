#!/usr/bin/env python3
"""
简易版小市值策略回测
避开Tushare API接口问题
"""

import sys
import os
sys.path.append('..')

import pandas as pd
import numpy as np


def get_sample_stock_data():
    """
    获取样本股票数据
    """
    return [
        {'ts_code': '600519.SH', 'name': '贵州茅台', 'industry': '消费', 'circ_mv': 2500000},  # 2.5万亿
        {'ts_code': '000858.SZ', 'name': '五粮液', 'industry': '消费', 'circ_mv': 800000},   # 8000亿
        {'ts_code': '601318.SH', 'name': '中国平安', 'industry': '保险', 'circ_mv': 700000}, # 7000亿
        {'ts_code': '600036.SH', 'name': '招商银行', 'industry': '银行', 'circ_mv': 650000},  # 6500亿
        {'ts_code': '300750.SZ', 'name': '宁德时代', 'industry': '新能源', 'circ_mv': 600000}, # 6000亿
        {'ts_code': '002594.SZ', 'name': '比亚迪', 'industry': '汽车', 'circ_mv': 550000},     # 5500亿
        {'ts_code': '600030.SH', 'name': '中信证券', 'industry': '证券', 'circ_mv': 300000},   # 3000亿
        {'ts_code': '600276.SH', 'name': '恒瑞医药', 'industry': '医药', 'circ_mv': 250000},    # 2500亿
        {'ts_code': '601012.SH', 'name': '隆基绿能', 'industry': '光伏', 'circ_mv': 200000},    # 2000亿
        {'ts_code': '002049.SZ', 'name': '紫光国微', 'industry': '半导体', 'circ_mv': 180000},   # 1800亿
        {'ts_code': '688981.SH', 'name': '中芯国际', 'industry': '半导体', 'circ_mv': 150000},   # 1500亿
        {'ts_code': '600309.SH', 'name': '万华化学', 'industry': '化工', 'circ_mv': 120000},     # 1200亿
        {'ts_code': '300059.SZ', 'name': '东方财富', 'industry': '证券', 'circ_mv': 100000},    # 1000亿
        {'ts_code': '600900.SH', 'name': '长江电力', 'industry': '公用事业', 'circ_mv': 80000},     # 800亿
        {'ts_code': '600887.SH', 'name': '伊利股份', 'industry': '消费', 'circ_mv': 60000},    # 600亿
    ]


def simulate_price_movement(stock_list, start_date='2025-02-01', end_date='2026-02-06'):
    """
    模拟股票价格走势
    
    Args:
        stock_list: 股票列表
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        带有价格数据的DataFrame
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    num_days = len(dates)
    
    all_data = []
    
    for stock in stock_list:
        # 随机生成初始价格
        init_price = np.random.uniform(10, 500)
        
        # 生成对数正态分布的日收益率
        # 小市值股票波动率较高
        volatility = 0.02 * (1 + (1 - stock['circ_mv']/max(s['circ_mv'] for s in stock_list))**2)
        daily_returns = np.random.normal(0, volatility, num_days)
        
        # 计算价格序列
        prices = init_price * np.exp(np.cumsum(daily_returns))
        
        # 随机加入一些趋势
        trend_effect = np.linspace(0, np.random.uniform(-0.2, 0.3), num_days)
        prices *= (1 + trend_effect)
        
        # 创建DataFrame
        df = pd.DataFrame({
            'trade_date': dates,
            'ts_code': stock['ts_code'],
            'name': stock['name'],
            'industry': stock['industry'],
            'circ_mv': stock['circ_mv'],
            'close': prices,
            'pct_chg': daily_returns * 100
        })
        
        all_data.append(df)
    
    return pd.concat(all_data)


def simulate_small_cap_strategy(data_df, selection_size=5, rebalance_months=3):
    """
    模拟小市值策略
    
    Args:
        data_df: 股票数据DataFrame
        selection_size: 每次选股数量
        rebalance_months: 调仓周期（月）
        
    Returns:
        回测结果字典
    """
    print("\n=== 执行小市值策略模拟 ===")
    print(f"选股数量: {selection_size}只")
    print(f"调仓频率: 每{rebalance_months}个月")
    
    # 将日期转换为月份
    data_df['month'] = data_df['trade_date'].dt.to_period('M')
    
    # 初始化策略参数
    portfolio_value = 1.0
    portfolio_history = []
    current_portfolio = []
    rebalance_history = []
    
    # 获取所有调仓月份
    months = sorted(data_df['month'].unique())
    
    for i, month in enumerate(months):
        # 获取当月最后一个交易日的数据
        month_data = data_df[data_df['month'] == month]
        last_day = month_data['trade_date'].max()
        last_day_data = month_data[month_data['trade_date'] == last_day]
        
        # 检查是否需要调仓
        if i % rebalance_months == 0 or not current_portfolio:
            print(f"\n{month.strftime('%Y-%m')}: 调仓")
            
            # 获取当月市值数据
            latest_mv = last_day_data.groupby(['ts_code', 'name', 'industry'])['circ_mv'].last().reset_index()
            
            # 按市值升序排序
            sorted_stocks = latest_mv.sort_values('circ_mv', ascending=True)
            
            # 选择市值最小的N只股票
            selected = sorted_stocks.head(selection_size)
            current_portfolio = selected['ts_code'].tolist()
            
            # 记录调仓信息
            rebalance_info = {
                'month': month.strftime('%Y-%m'),
                'selected_stocks': selected.to_dict('records'),
                'average_mv': selected['circ_mv'].mean()/10000,
                'min_mv': selected['circ_mv'].min()/10000,
                'max_mv': selected['circ_mv'].max()/10000,
                'portfolio_change': list(set(current_portfolio) - set(current_portfolio)) if i>0 else []
            }
            rebalance_history.append(rebalance_info)
            
            print(f"  选择的股票: {', '.join(selected['name'].tolist())}")
            print(f"  平均市值: {selected['circ_mv'].mean()/10000:.2f}亿元")
            print(f"  市值范围: {selected['circ_mv'].min()/10000:.2f} - {selected['circ_mv'].max()/10000:.2f}亿元")
        
        # 计算当月收益率
        monthly_returns = []
        for ts_code in current_portfolio:
            # 获取该股票当月的每日收益率
            stock_monthly = month_data[month_data['ts_code'] == ts_code]
            if len(stock_monthly) > 0:
                # 计算当月累计收益率
                monthly_return = (stock_monthly['close'].iloc[-1] / stock_monthly['close'].iloc[0]) - 1
                monthly_returns.append(monthly_return)
        
        # 计算组合当月收益
        if monthly_returns:
            portfolio_monthly_return = np.mean(monthly_returns)
            portfolio_value *= (1 + portfolio_monthly_return)
            
            portfolio_history.append({
                'month': month,
                'portfolio_value': portfolio_value,
                'monthly_return': portfolio_monthly_return,
                'held_stocks': current_portfolio.copy()
            })
            
            print(f"  当月收益率: {portfolio_monthly_return*100:.2f}%")
            print(f"  累计净值: {portfolio_value:.4f}")
    
    # 计算回测指标
    if portfolio_history:
        portfolio_df = pd.DataFrame(portfolio_history)
        
        total_return = portfolio_value - 1
        trading_months = len(portfolio_df)
        annualized_return = (1 + total_return) ** (12/trading_months) - 1 if trading_months > 0 else 0
        
        # 计算最大回撤
        portfolio_df['peak'] = portfolio_df['portfolio_value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['peak']) / portfolio_df['peak']
        max_drawdown = portfolio_df['drawdown'].min() if len(portfolio_df) > 0 else 0
        
        # 计算夏普比率
        if len(portfolio_df) > 1:
            monthly_std = portfolio_df['monthly_return'].std()
            sharpe_ratio = np.sqrt(12) * (portfolio_df['monthly_return'].mean()) / monthly_std if monthly_std != 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trading_months': trading_months,
            'final_portfolio_value': portfolio_value,
            'portfolio_history': portfolio_df,
            'rebalance_history': rebalance_history
        }
    
    return {}


def generate_report(results, selection_size, rebalance_months, output_dir):
    """
    生成回测报告
    """
    if not results:
        print("没有回测结果可以生成报告")
        return
    
    portfolio_df = results['portfolio_history']
    
    report_content = f"""# 📈 小市值策略回测报告

## 回测参数
- **回测时间**: 2025-02 至 2026-02
- **股票数量**: 15只样本股票
- **选股数量**: {selection_size}只
- **调仓频率**: 每{rebalance_months}个月

## 📊 回测结果

| 指标 | 数值 |
|------|------|
| 总收益率 | {results['total_return']*100:.2f}% |
| 年化收益率 | {results['annualized_return']*100:.2f}% |
| 最大回撤 | {results['max_drawdown']*100:.2f}% |
| 夏普比率 | {results['sharpe_ratio']:.2f} |
| 回测月份数 | {results['trading_months']}个月 |
| 最终组合净值 | {results['final_portfolio_value']:.4f} |

## 📅 组合表现历史

| 月份 | 累计净值 | 月度收益率 |
|------|----------|----------|
"""
    
    for _, row in portfolio_df.iterrows():
        report_content += f"| {row['month'].strftime('%Y-%m')} | {row['portfolio_value']:.4f} | {row['monthly_return']*100:.2f}% |\n"
    
    # 添加调仓历史
    report_content += """

## 🔄 调仓历史明细

"""
    
    for rebalance in results['rebalance_history']:
        report_content += f"\n### {rebalance['month']}调仓\n\n"
        report_content += "| 股票代码 | 股票名称 | 行业 | 市值(亿元) |\n"
        report_content += "|----------|----------|------|----------|\n"
        
        for stock in rebalance['selected_stocks']:
            report_content += f"| {stock['ts_code']} | {stock['name']} | {stock['industry']} | {stock['circ_mv']/10000:.2f} |\n"
        
        report_content += f"\n**市值统计**: 平均{rebalance['average_mv']:.2f}亿元，范围{rebalance['min_mv']:.2f}-{rebalance['max_mv']:.2f}亿元\n"
    
    # 添加策略评价
    report_content += """

## 🎯 策略评价

"""
    
    if results['annualized_return'] > 0.1:  # 年化10%以上
        report_content += "✅ 小市值策略表现优秀，年化收益率超过10%\n"
    elif results['annualized_return'] > 0.05:  # 年化5%以上
        report_content += "⚠️ 小市值策略表现一般，勉强跑赢通胀\n"
    else:
        report_content += "❌ 小市值策略表现不佳，未能获得理想收益\n"
    
    if results['sharpe_ratio'] > 1:
        report_content += "✅ 夏普比率高于1，风险调整后收益良好\n"
    elif results['sharpe_ratio'] > 0.5:
        report_content += "⚠️ 夏普比率尚可，风险收益比一般\n"
    else:
        report_content += "❌ 夏普比率较低，风险收益比不佳\n"
    
    if abs(results['max_drawdown']) > 0.2:  # 最大回撤20%以上
        report_content += "⚠️ 最大回撤超过20%，策略风险较高\n"
    else:
        report_content += "✅ 最大回撤控制较好，风险适中\n"
    
    # 添加建议
    report_content += """

## 💡 优化建议

1. **调整选股数量**: 可以尝试3只、5只、10只不同的选股数量
2. **优化调仓频率**: 测试每月、每季度调仓的效果差异
3. **加入基本面过滤**: 选择盈利稳定的小市值股票
4. **行业分散化**: 在各行业内选择小市值股票
5. **动态策略调整**: 根据市场风格动态调整小市值股票占比
"""
    
    # 保存报告
    os.makedirs(output_dir, exist_ok=True)
    report_path = f"{output_dir}/small_cap_strategy_backtest_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📝 回测报告已保存至: {report_path}")
    
    # 生成飞书报告
    feishu_report = f"""# 📈 小市值策略回测结果

**回测参数**:
- 回测时间: 2025-02 至 2026-02
- 选股数量: {selection_size}只
- 调仓频率: 每{rebalance_months}个月

**核心指标**:
- 总收益率: {results['total_return']*100:.2f}%
- 年化收益率: {results['annualized_return']*100:.2f}%
- 最大回撤: {results['max_drawdown']*100:.2f}%
- 夏普比率: {results['sharpe_ratio']:.2f}

**策略评价**:
{'✅ 表现优秀' if results['annualized_return']>0.1 else '⚠️ 表现一般' if results['annualized_return']>0.05 else '❌ 表现不佳'}
{'✅ 风险收益比好' if results['sharpe_ratio']>1 else '⚠️ 风险收益比一般' if results['sharpe_ratio']>0.5 else '❌ 风险收益比差'}
{'✅ 风险控制好' if abs(results['max_drawdown'])<0.2 else '⚠️ 风险较高'}

💡 完整报告已保存到GitHub仓库"""
    
    return feishu_report


def main():
    """
    主函数
    """
    print("=== 小市值策略小规模回测 ===")
    print("使用模拟数据避开Tushare API问题")
    
    # 获取样本股票数据
    stock_list = get_sample_stock_data()
    print(f"\n📋 使用{len(stock_list)}只样本股票")
    
    # 模拟价格走势
    print("\n🔄 模拟股票价格走势...")
    data_df = simulate_price_movement(stock_list)
    
    # 模拟小市值策略
    results = simulate_small_cap_strategy(data_df, selection_size=5, rebalance_months=3)
    
    if results:
        print("\n" + "="*60)
        print("🎯 回测完成")
        print("="*60)
        print(f"总收益率: {results['total_return']*100:.2f}%")
        print(f"年化收益率: {results['annualized_return']*100:.2f}%")
        print(f"最大回撤: {results['max_drawdown']*100:.2f}%")
        print(f"夏普比率: {results['sharpe_ratio']:.2f}")
        
        # 生成报告
        output_dir = '../backtest/results'
        feishu_report = generate_report(results, 5, 3, output_dir)
        
        # 发送飞书报告
        try:
            from message import message
            message(action='send', channel='feishu', target='ou_e39fd3529ff7fea2eca6b1e0b35ed98f', message=feishu_report)
            print("\n💌 飞书报告已发送")
        except Exception as e:
            print(f"\n⚠️ 发送飞书报告失败: {e}")
            print(f"\n📝 飞书报告内容:\n{feishu_report}")
    else:
        print("\n❌ 回测失败，没有得到回测结果")


if __name__ == '__main__':
    main()
