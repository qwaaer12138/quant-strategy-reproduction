#!/usr/bin/env python3
"""
小市值策略实现
基于小市值效应的量化策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class SmallCapStrategy:
    """
    小市值策略类，实现多种小市值选股策略
    """
    
    def __init__(self, 
                 universe_size: int = 300,
                 filter_conditions: Optional[Dict] = None,
                 rebalance_frequency: str = 'monthly'):
        """
        初始化小市值策略
        
        Args:
            universe_size: 选股数量
            filter_conditions: 筛选条件字典
            rebalance_frequency: 调仓频率 ('daily', 'weekly', 'monthly', 'quarterly')
        """
        self.universe_size = universe_size
        self.filter_conditions = filter_conditions or {}
        self.rebalance_frequency = rebalance_frequency
        self.last_rebalance_date = None
    
    def calculate_size_ranking(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算股票市值排名
        
        Args:
            data: 包含股票数据的DataFrame
            
        Returns:
            包含市值排名的DataFrame
        """
        df = data.copy()
        
        # 计算市值排名（越小分越高）
        df['size_rank'] = df['circ_mv'].rank(ascending=True, pct=True)
        df['size_score'] = 1 - df['size_rank']  # 市值越小得分越高
        
        return df
    
    def basic_small_cap_selection(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        基础版小市值策略：只筛选市值最小的股票
        
        Args:
            data: 包含股票数据的DataFrame
            
        Returns:
            筛选后的小市值股票组合
        """
        df = data.copy()
        
        # 按流通市值升序排序
        sorted_df = df.sort_values('circ_mv', ascending=True)
        
        # 选择市值最小的N只股票
        small_cap_stocks = sorted_df.head(self.universe_size)
        
        return small_cap_stocks
    
    def enhanced_small_cap_selection(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        增强版小市值策略：结合基本面筛选
        
        Args:
            data: 包含股票数据的DataFrame
            
        Returns:
            增强版筛选后的小市值股票组合
        """
        df = data.copy()
        
        # 先筛选市值最小的两倍数量股票
        temp_universe = df.sort_values('circ_mv', ascending=True).head(self.universe_size * 2)
        
        # 应用基本面过滤条件
        filters = []
        
        # 默认过滤条件
        if not self.filter_conditions or self.filter_conditions.get('positive_profit', True):
            filters.append(temp_universe['profit'] > 0)  # 盈利为正
        
        if not self.filter_conditions or self.filter_conditions.get('reasonable_pe', True):
            filters.append((temp_universe['pe'] < 50) & (temp_universe['pe'] > 0))  # 市盈率0-50倍
        
        if not self.filter_conditions or self.filter_conditions.get('liquidity', True):
            filters.append(temp_universe['turnover'] > 1000)  # 成交额大于1000万
        
        if not self.filter_conditions or self.filter_conditions.get('positive_cashflow', False):
            filters.append(temp_universe['operating_cashflow'] > 0)  # 经营现金流为正
        
        # 应用所有过滤条件
        if filters:
            combined_filter = np.logical_and.reduce(filters)
            filtered_df = temp_universe[combined_filter]
        else:
            filtered_df = temp_universe
        
        # 如果过滤后数量不足，补充未过滤的股票
        if len(filtered_df) < self.universe_size:
            remaining = self.universe_size - len(filtered_df)
            supplement = temp_universe[~temp_universe.index.isin(filtered_df.index)].head(remaining)
            final_df = pd.concat([filtered_df, supplement])
        else:
            final_df = filtered_df.head(self.universe_size)
        
        return final_df
    
    def multi_factor_small_cap_selection(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        多因子小市值策略：结合市值、盈利、估值多维度评分
        
        Args:
            data: 包含股票数据的DataFrame
            
        Returns:
            多因子评分筛选后的小市值股票组合
        """
        df = data.copy()
        
        # 计算各因子排名
        df['size_rank'] = df['circ_mv'].rank(ascending=True, pct=True)
        df['profit_rank'] = df['profit'].rank(ascending=False, pct=True)
        df['pe_rank'] = df['pe'].rank(ascending=True, pct=True)  # 市盈率越小分越高
        df['roe_rank'] = df['roe'].rank(ascending=False, pct=True)
        df['volatility_rank'] = df['close'].rolling(20).std().rank(ascending=True, pct=True)
        
        # 计算综合因子得分
        df['total_score'] = (
            0.4 * df['size_rank'] +       # 市值因子权重40%
            0.2 * df['profit_rank'] +     # 盈利因子权重20%
            0.2 * df['pe_rank'] +         # 估值因子权重20%
            0.1 * df['roe_rank'] +        # 净资产收益率权重10%
            0.1 * df['volatility_rank']   # 波动率因子权重10%
        )
        
        # 选择得分最高的N只股票
        sorted_df = df.sort_values('total_score', ascending=False)
        final_df = sorted_df.head(self.universe_size)
        
        return final_df
    
    def should_rebalance(self, current_date: pd.Timestamp) -> bool:
        """
        判断是否需要调仓
        
        Args:
            current_date: 当前日期
            
        Returns:
            是否需要调仓
        """
        if self.last_rebalance_date is None:
            return True
            
        if self.rebalance_frequency == 'monthly':
            return current_date.month != self.last_rebalance_date.month
        
        elif self.rebalance_frequency == 'quarterly':
            return current_date.quarter != self.last_rebalance_date.quarter
        
        elif self.rebalance_frequency == 'weekly':
            return current_date.week != self.last_rebalance_date.week
            
        elif self.rebalance_frequency == 'daily':
            return True
            
        return False
    
    def calculate_weighted_portfolio(self, data: pd.DataFrame, method: str = 'equal_weight') -> pd.DataFrame:
        """
        计算组合权重
        
        Args:
            data: 筛选后的股票组合
            method: 权重分配方法 ('equal_weight', 'value_weight', 'risk_parity')
            
        Returns:
            包含权重的DataFrame
        """
        df = data.copy()
        
        if method == 'equal_weight':
            # 等权分配
            df['weight'] = 1 / len(df)
            
        elif method == 'value_weight':
            # 市值加权
            total_market_cap = df['circ_mv'].sum()
            df['weight'] = df['circ_mv'] / total_market_cap
            
        elif method == 'risk_parity':
            # 风险平价（基于波动率）
            df['volatility'] = df['close'].rolling(20).std().fillna(df['close'].std())
            inv_volatility = 1 / df['volatility']
            total_inv_vol = inv_volatility.sum()
            df['weight'] = inv_volatility / total_inv_vol
            
        else:
            # 默认等权
            df['weight'] = 1 / len(df)
        
        return df
    
    def backtest_strategy(self, data: List[pd.DataFrame], strategy_type: str = 'enhanced') -> Dict:
        """
        回测小市值策略
        
        Args:
            data: 分时间节点的股票数据列表
            strategy_type: 策略类型 ('basic', 'enhanced', 'multi_factor')
            
        Returns:
            回测结果字典
        """
        portfolio_value = 1.0
        portfolio_history = []
        last_portfolio = None
        
        for date_data in data:
            current_date = pd.to_datetime(date_data.index[0])
            
            # 检查是否需要调仓
            if self.should_rebalance(current_date) or last_portfolio is None:
                # 根据策略类型选择股票
                if strategy_type == 'basic':
                    selected_stocks = self.basic_small_cap_selection(date_data)
                elif strategy_type == 'multi_factor':
                    selected_stocks = self.multi_factor_small_cap_selection(date_data)
                else:
                    selected_stocks = self.enhanced_small_cap_selection(date_data)
                
                # 计算组合权重
                last_portfolio = self.calculate_weighted_portfolio(selected_stocks)
                self.last_rebalance_date = current_date
            
            # 计算当日组合收益
            if last_portfolio is not None and len(last_portfolio) > 0:
                # 获取持仓股票的当日收益
                returns = []
                for _, stock in last_portfolio.iterrows():
                    ts_code = stock['ts_code']
                    stock_data = date_data[date_data['ts_code'] == ts_code]
                    if len(stock_data) > 0:
                        daily_return = stock_data['pct_chg'].iloc[0] / 100
                        returns.append(stock['weight'] * daily_return)
                
                # 计算组合当日收益
                portfolio_return = sum(returns) if returns else 0
                portfolio_value *= (1 + portfolio_return)
                
                portfolio_history.append({
                    'date': current_date,
                    'portfolio_value': portfolio_value,
                    'daily_return': portfolio_return
                })
        
        # 计算回测指标
        if portfolio_history:
            portfolio_df = pd.DataFrame(portfolio_history)
            portfolio_df.set_index('date', inplace=True)
            
            total_return = portfolio_value - 1
            trading_days = len(portfolio_df)
            annualized_return = (1 + total_return) ** (252 / trading_days) - 1
            
            # 计算最大回撤
            portfolio_df['peak'] = portfolio_df['portfolio_value'].cummax()
            portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['peak']) / portfolio_df['peak']
            max_drawdown = portfolio_df['drawdown'].min()
            
            # 计算夏普比率
            sharpe_ratio = np.sqrt(252) * portfolio_df['daily_return'].mean() / portfolio_df['daily_return'].std() if portfolio_df['daily_return'].std() != 0 else 0
            
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'total_trading_days': trading_days,
                'portfolio_history': portfolio_df
            }
            
        return {}


def example_usage():
    """示例用法"""
    print("=== 小市值策略示例 ===")
    
    try:
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
        
        # 生成模拟数据（实际使用中应从Tushare获取全市场数据）
        stock_count = 2000
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='M')
        
        # 生成模拟全市场数据
        test_data = []
        
        for date in dates:
            # 生成模拟股票数据
            data = {
                'ts_code': [f'60000{i}.SH' for i in range(stock_count)],
                'name': [f'TestStock{i}' for i in range(stock_count)],
                'circ_mv': np.random.uniform(1, 1000, stock_count),  # 随机市值
                'pe': np.random.uniform(0, 100, stock_count),        # 随机市盈率
                'profit': np.random.uniform(-10, 100, stock_count),   # 随机利润
                'turnover': np.random.uniform(500, 5000, stock_count), # 随机成交额
                'pct_chg': np.random.uniform(-10, 10, stock_count),  # 随机涨跌幅
                'close': np.random.uniform(1, 100, stock_count)       # 随机收盘价
            }
            
            # 确保部分股票盈利为负，模拟真实市场
            data['profit'][:200] = np.random.uniform(-10, 0, 200)
            
            df = pd.DataFrame(data)
            df['date'] = date
            
            test_data.append(df)
        
        # 回测基础版小市值策略
        basic_results = strategy.backtest_strategy(test_data, strategy_type='basic')
        print("\n=== 基础版小市值策略回测结果 ===")
        print(f"总收益率: {basic_results['total_return']*100:.2f}%")
        print(f"年化收益率: {basic_results['annualized_return']*100:.2f}%")
        print(f"最大回撤: {basic_results['max_drawdown']*100:.2f}%")
        print(f"夏普比率: {basic_results['sharpe_ratio']:.2f}")
        
        # 回测增强版小市值策略
        enhanced_results = strategy.backtest_strategy(test_data, strategy_type='enhanced')
        print("\n=== 增强版小市值策略回测结果 ===")
        print(f"总收益率: {enhanced_results['total_return']*100:.2f}%")
        print(f"年化收益率: {enhanced_results['annualized_return']*100:.2f}%")
        print(f"最大回撤: {enhanced_results['max_drawdown']*100:.2f}%")
        print(f"夏普比率: {enhanced_results['sharpe_ratio']:.2f}")
        
        # 回测多因子小市值策略
        multi_factor_results = strategy.backtest_strategy(test_data, strategy_type='multi_factor')
        print("\n=== 多因子小市值策略回测结果 ===")
        print(f"总收益率: {multi_factor_results['total_return']*100:.2f}%")
        print(f"年化收益率: {multi_factor_results['annualized_return']*100:.2f}%")
        print(f"最大回撤: {multi_factor_results['max_drawdown']*100:.2f}%")
        print(f"夏普比率: {multi_factor_results['sharpe_ratio']:.2f}")
        
    except Exception as e:
        print(f"示例运行失败: {e}")


if __name__ == '__main__':
    example_usage()
