"""
股票数据模块
封装AKShare库的股票相关功能，提供简洁的API
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union, Optional, Tuple

import akshare as ak
import pandas as pd
import numpy as np


class StockDataError(Exception):
    """股票数据异常"""

    pass


class StockData:
    """
    股票数据类，封装AKShare库的股票相关功能

    主要功能：
        1. 获取股票实时行情数据
        2. 获取股票历史行情数据
        3. 获取股票基本信息
        4. 获取指数数据
        5. 获取板块数据
    """

    def __init__(self, data_dir: str = None):
        """
        初始化股票数据类

        Args:
            data_dir: 数据保存目录，默认为项目根目录下的 data/stock 目录
        """
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "stock"
        )
        os.makedirs(self.data_dir, exist_ok=True)

    def get_stock_real_time(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时行情数据

        Args:
            symbol: 股票代码，支持沪深股票，格式：sh688981 或 sz000001

        Returns:
            股票实时行情数据字典

        Example:
            >>> stock_data = StockData()
            >>> stock_data.get_stock_real_time("sh688981")
        """
        try:
            symbol_clean = symbol.replace("sh", "").replace("sz", "")
            market = "sh" if symbol.startswith("sh") else "sz"

            # 使用AKShare获取股票实时行情数据
            real_data = ak.stock_zh_a_spot_em()

            # 查找对应的股票数据
            stock_data = real_data[real_data["代码"] == symbol_clean]

            if stock_data.empty:
                raise StockDataError(f"未找到股票 {symbol} 的实时行情数据")

            # 格式化数据
            first_row = stock_data.iloc[0]
            result = {
                "symbol": symbol,
                "code": symbol_clean,
                "name": first_row.get("名称", ""),
                "current_price": float(first_row.get("最新价", 0)),
                "change": float(first_row.get("涨跌额", 0)),
                "change_percent": float(first_row.get("涨跌幅", 0).replace("%", "")),
                "open": float(first_row.get("开盘价", 0)),
                "high": float(first_row.get("最高价", 0)),
                "low": float(first_row.get("最低价", 0)),
                "close": float(first_row.get("最新价", 0)),
                "pre_close": float(first_row.get("昨收", 0)),
                "volume": float(first_row.get("成交量", 0)),
                "amount": float(first_row.get("成交额", 0)),
                "market": market,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            return result
        except Exception as e:
            raise StockDataError(f"获取股票 {symbol} 实时行情数据失败: {str(e)}")

    def get_stock_history(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取股票历史行情数据

        Args:
            symbol: 股票代码，支持沪深股票，格式：sh688981 或 sz000001
            start_date: 开始日期，格式：YYYY-MM-DD，默认为近一年
            end_date: 结束日期，格式：YYYY-MM-DD，默认为今天
            period: 数据周期，可选值：daily、weekly、monthly，默认为daily
            adjust: 复权方式，可选值：qfq（前复权）、hfq（后复权）、None（不复权），默认为qfq

        Returns:
            股票历史行情数据DataFrame

        Example:
            >>> stock_data = StockData()
            >>> df = stock_data.get_stock_history("sh688981", "2022-01-01", "2022-12-31")
        """
        try:
            # 处理日期参数
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")

            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

            # 清理股票代码
            symbol_clean = symbol.replace("sh", "").replace("sz", "")

            # 根据不同周期获取数据
            if period == "daily":
                df = ak.stock_zh_a_hist(
                    symbol=symbol_clean,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
            elif period == "weekly":
                df = ak.stock_zh_a_hist_weekly(
                    symbol=symbol_clean,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
            elif period == "monthly":
                df = ak.stock_zh_a_hist_monthly(
                    symbol=symbol_clean,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
            else:
                raise StockDataError(f"不支持的数据周期: {period}")

            # 检查是否获取到数据
            if df.empty:
                raise StockDataError(
                    f"未获取到股票 {symbol} 在 {start_date} 至 {end_date} 期间的历史数据"
                )

            # 标准化列名
            if "日期" in df.columns:
                df = df.rename(
                    columns={
                        "日期": "date",
                        "开盘": "open",
                        "收盘": "close",
                        "最高": "high",
                        "最低": "low",
                        "成交量": "volume",
                        "成交额": "amount",
                        "振幅": "amplitude",
                        "涨跌幅": "change_percent",
                        "涨跌额": "change",
                        "换手率": "turnover",
                    }
                )

            # 确保日期列为datetime类型
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])

            # 添加股票代码和名称列
            df["symbol"] = symbol
            df["code"] = symbol_clean

            return df
        except Exception as e:
            raise StockDataError(f"获取股票 {symbol} 历史行情数据失败: {str(e)}")

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股所有股票列表

        Returns:
            股票列表DataFrame

        Example:
            >>> stock_data = StockData()
            >>> df = stock_data.get_stock_list()
        """
        try:
            # 获取股票列表
            df = ak.stock_zh_a_spot_em()

            # 标准化列名
            if "代码" in df.columns:
                df = df.rename(
                    columns={
                        "代码": "code",
                        "名称": "name",
                        "最新价": "current_price",
                        "涨跌幅": "change_percent",
                        "涨跌额": "change",
                        "成交量": "volume",
                        "成交额": "amount",
                        "振幅": "amplitude",
                        "最高": "high",
                        "最低": "low",
                        "今开": "open",
                        "昨收": "pre_close",
                    }
                )

            # 添加交易所标记和完整代码
            df["exchange"] = df["code"].apply(
                lambda x: "sh" if x.startswith(("6", "5")) else "sz"
            )
            df["symbol"] = df["exchange"] + df["code"]

            return df
        except Exception as e:
            raise StockDataError(f"获取股票列表失败: {str(e)}")

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票详细信息

        Args:
            symbol: 股票代码，支持沪深股票，格式：sh688981 或 sz000001

        Returns:
            股票详细信息字典

        Example:
            >>> stock_data = StockData()
            >>> stock_data.get_stock_info("sh688981")
        """
        try:
            symbol_clean = symbol.replace("sh", "").replace("sz", "")

            # 获取股票基本信息
            info = ak.stock_individual_info_em(symbol=symbol_clean)

            if info.empty:
                raise StockDataError(f"未找到股票 {symbol} 的基本信息")

            # 将DataFrame转换为字典
            result = {}
            for _, row in info.iterrows():
                if len(row) >= 2:
                    key = row.iloc[0]
                    value = row.iloc[1]
                    result[key] = value

            # 添加标准字段
            result["symbol"] = symbol
            result["code"] = symbol_clean

            return result
        except Exception as e:
            raise StockDataError(f"获取股票 {symbol} 详细信息失败: {str(e)}")

    def get_index_real_time(self, symbol: str = "000001") -> Dict[str, Any]:
        """
        获取指数实时行情数据

        Args:
            symbol: 指数代码，默认为上证指数(000001)
                  常用指数：上证指数(000001)、深证成指(399001)、创业板指(399006)、沪深300(000300)

        Returns:
            指数实时行情数据字典

        Example:
            >>> stock_data = StockData()
            >>> stock_data.get_index_real_time("000001")
        """
        try:
            # 使用AKShare获取指数实时行情数据
            index_data = ak.stock_zh_index_spot()

            # 查找对应的指数数据
            target_index = index_data[index_data["代码"] == symbol]

            if target_index.empty:
                raise StockDataError(f"未找到指数 {symbol} 的实时行情数据")

            # 格式化数据
            first_row = target_index.iloc[0]
            result = {
                "symbol": symbol,
                "name": first_row.get("名称", ""),
                "current_price": float(first_row.get("最新价", 0)),
                "change": float(first_row.get("涨跌额", 0)),
                "change_percent": float(first_row.get("涨跌幅", 0).replace("%", "")),
                "open": float(first_row.get("开盘点位", 0)),
                "high": float(first_row.get("最高点位", 0)),
                "low": float(first_row.get("最低点位", 0)),
                "pre_close": float(first_row.get("昨收", 0)),
                "volume": float(first_row.get("成交量", 0)),
                "amount": float(first_row.get("成交额", 0)),
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            return result
        except Exception as e:
            raise StockDataError(f"获取指数 {symbol} 实时行情数据失败: {str(e)}")

    def get_index_list(self) -> pd.DataFrame:
        """
        获取所有指数列表

        Returns:
            指数列表DataFrame

        Example:
            >>> stock_data = StockData()
            >>> df = stock_data.get_index_list()
        """
        try:
            # 获取指数列表
            df = ak.stock_zh_index_spot()

            # 标准化列名
            if "代码" in df.columns:
                df = df.rename(
                    columns={
                        "代码": "code",
                        "名称": "name",
                        "最新价": "current_price",
                        "涨跌额": "change",
                        "涨跌幅": "change_percent",
                        "开盘点位": "open",
                        "最高点位": "high",
                        "最低点位": "low",
                        "昨收": "pre_close",
                        "成交量": "volume",
                        "成交额": "amount",
                    }
                )

            # 添加标准字段
            df["symbol"] = df["code"]

            return df
        except Exception as e:
            raise StockDataError(f"获取指数列表失败: {str(e)}")

    def get_sector_real_time(self, sector_type: str = "bk") -> pd.DataFrame:
        """
        获取板块实时行情数据

        Args:
            sector_type: 板块类型，可选值：
                        bk: 板块指数
                        gn: 概念指数
                        hy: 行业指数

        Returns:
            板块实时行情数据DataFrame

        Example:
            >>> stock_data = StockData()
            >>> df = stock_data.get_sector_real_time("bk")
        """
        try:
            # 根据板块类型获取数据
            if sector_type == "bk":
                df = ak.stock_sector_spot()
            elif sector_type == "gn":
                df = ak.stock_sector_spot(indicator="概念")
            elif sector_type == "hy":
                df = ak.stock_sector_spot(indicator="行业")
            else:
                raise StockDataError(f"不支持的板块类型: {sector_type}")

            # 标准化列名
            if "板块代码" in df.columns:
                df = df.rename(
                    columns={
                        "板块代码": "code",
                        "板块名称": "name",
                        "最新价": "current_price",
                        "涨跌额": "change",
                        "涨跌幅": "change_percent",
                        "总市值": "market_value",
                        "换手率": "turnover",
                        "上涨家数": "up_count",
                        "下跌家数": "down_count",
                        "领涨股票": "leading_stock",
                        "领涨股票涨跌幅": "leading_change_percent",
                    }
                )

            # 添加板块类型字段
            df["sector_type"] = sector_type

            return df
        except Exception as e:
            raise StockDataError(f"获取板块实时行情数据失败: {str(e)}")

    def save_data_to_file(
        self, data: Union[Dict, pd.DataFrame], filename: str, format: str = "json"
    ) -> str:
        """
        将数据保存到文件

        Args:
            data: 要保存的数据，可以是字典或DataFrame
            filename: 文件名
            format: 保存格式，可选值：json、csv，默认为json

        Returns:
            保存的文件路径
        """
        try:
            # 确保文件扩展名正确
            if not filename.endswith(f".{format}"):
                filename = f"{filename}.{format}"

            filepath = os.path.join(self.data_dir, filename)

            # 根据数据类型和保存格式进行保存
            if isinstance(data, pd.DataFrame):
                if format == "json":
                    data.to_json(filepath, orient="records", force_ascii=False)
                elif format == "csv":
                    data.to_csv(filepath, index=False, encoding="utf-8")
                else:
                    raise StockDataError(f"不支持的保存格式: {format}")
            else:
                if format == "json":
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    raise StockDataError(f"字典类型数据只支持json格式保存")

            return filepath
        except Exception as e:
            raise StockDataError(f"保存数据到文件失败: {str(e)}")

    def load_data_from_file(
        self, filename: str, format: str = None
    ) -> Union[Dict, pd.DataFrame]:
        """
        从文件加载数据

        Args:
            filename: 文件名
            format: 文件格式，可选值：json、csv，默认根据文件扩展名自动判断

        Returns:
            加载的数据，json格式返回字典，csv格式返回DataFrame
        """
        try:
            # 如果未指定格式，根据文件扩展名自动判断
            if format is None:
                if filename.endswith(".json"):
                    format = "json"
                elif filename.endswith(".csv"):
                    format = "csv"
                else:
                    raise StockDataError(f"无法判断文件格式: {filename}")

            # 确保文件扩展名正确
            if not filename.endswith(f".{format}"):
                filename = f"{filename}.{format}"

            filepath = os.path.join(self.data_dir, filename)

            # 检查文件是否存在
            if not os.path.exists(filepath):
                raise StockDataError(f"文件不存在: {filepath}")

            # 根据格式加载数据
            if format == "json":
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            elif format == "csv":
                return pd.read_csv(filepath, encoding="utf-8")
            else:
                raise StockDataError(f"不支持的文件格式: {format}")
        except Exception as e:
            raise StockDataError(f"从文件加载数据失败: {str(e)}")


# 创建全局单例实例
stock_data = StockData()
