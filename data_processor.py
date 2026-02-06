#!/usr/bin/env python3
"""
数据获取模块 - 基于Tushare API
用于获取股票、基金等金融数据
"""

import tushare as ts
import os
import pandas as pd
from typing import Optional, Dict, List

class DataProcessor:
    """
    数据处理类，封装Tushare API调用
    """
    
    def __init__(self, token: Optional[str] = None, api_url: str = 'http://lianghua.nanyangqiankun.top'):
        """
        初始化数据处理器
        
        Args:
            token: Tushare API token，若为None则从环境变量获取
            api_url: Tushare API地址
        """
        self.token = token or os.environ.get('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("Tushare token未设置，请通过参数或环境变量TUSHARE_TOKEN指定")
            
        self.api_url = api_url
        self.pro = self._init_api()
        
    def _init_api(self) -> ts.pro_api:
        """初始化Tushare API连接"""
        pro = ts.pro_api(self.token)
        pro._DataApi__token = self.token  # 必须设置
        pro._DataApi__http_url = self.api_url  # 必须设置
        return pro
    
    def get_daily_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            ts_code: 股票代码，如'000001.SZ'
            start_date: 开始日期，格式'YYYYMMDD'
            end_date: 结束日期，格式'YYYYMMDD'
            
        Returns:
            日线数据DataFrame
        """
        try:
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            print(f"获取日线数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_list(self, exchange: Optional[str] = None) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            exchange: 交易所代码，如'SZ'、'SH'、'BJ'，为None则返回所有
            
        Returns:
            股票列表DataFrame
        """
        try:
            df = self.pro.stock_basic(
                exchange=exchange,
                list_status='L',  # 仅返回上市状态的股票
                fields='ts_code,symbol,name,industry,list_date'
            )
            return df
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_financial_report(self, ts_code: str, year: int, quarter: int) -> pd.DataFrame:
        """
        获取财务报表数据
        
        Args:
            ts_code: 股票代码
            year: 年份，如2024
            quarter: 季度，1-4
            
        Returns:
            财务报表DataFrame
        """
        try:
            df = self.pro.fina_indicator(
                ts_code=ts_code,
                ann_date=f"{year}{quarter*3}31",  # 年报日期
                start_date=f"{year}0101",
                end_date=f"{year}1231"
            )
            return df
        except Exception as e:
            print(f"获取财务报表失败: {e}")
            return pd.DataFrame()
    
    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取指数日线数据
        
        Args:
            ts_code: 指数代码，如'000001.SH'
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数日线数据DataFrame
        """
        try:
            df = self.pro.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            print(f"获取指数数据失败: {e}")
            return pd.DataFrame()


def example_usage():
    """示例用法"""
    print("=== Tushare数据获取模块示例 ===")
    
    try:
        # 初始化数据处理器
        processor = DataProcessor()
        print("数据处理器初始化成功")
        
        # 获取平安银行日线数据
        print("\n1. 获取平安银行(000001.SZ)2024年1月日线数据")
        daily_df = processor.get_daily_data('000001.SZ', '20240101', '20240131')
        print(f"返回数据行数: {len(daily_df)}")
        if not daily_df.empty:
            print("数据预览:")
            print(daily_df[['trade_date', 'open', 'high', 'low', 'close', 'vol']].head())
        
        # 获取股票列表
        print("\n2. 获取深交所股票列表")
        stock_list = processor.get_stock_list(exchange='SZ')
        print(f"深交所股票数量: {len(stock_list)}")
        if not stock_list.empty:
            print("部分股票:")
            print(stock_list[['ts_code', 'name', 'industry']].head())
        
        # 获取财务报表
        print("\n3. 获取平安银行2023年财务报表")
        fina_df = processor.get_financial_report('000001.SZ', 2023, 4)
        if not fina_df.empty:
            print("主要财务指标:")
            print(fina_df[['ts_code', 'ann_date', 'profit', 'roe', 'eps', 'mb']].head())
        
    except Exception as e:
        print(f"示例运行失败: {e}")


if __name__ == "__main__":
    example_usage()
