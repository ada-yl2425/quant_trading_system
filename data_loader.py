import pandas as pd
import numpy as np
from pathlib import Path
import yfinance as yf
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class DataLoader:
    def __init__(self, data_folder_path):
        self.data_folder = Path(data_folder_path)
        self.feature_data = None

    def load_parquet_files(self):
        parquet_files = list(self.data_folder.glob("*.parquet"))
        if not parquet_files:
            raise ValueError(f"在 {self.data_folder} 中没有找到parquet文件")

        features_dict = {}
        for file_path in parquet_files:
            feature_name = file_path.stem
            try:
                df = pd.read_parquet(file_path)
                df = df.add_prefix(f"{feature_name}_")
                features_dict[feature_name] = df
                print(f"成功加载特征: {feature_name}, 形状: {df.shape}")
            except Exception as e:
                print(f"加载 {feature_name} 失败: {e}")

        return self.merge_features(features_dict)

    def merge_features(self, features_dict):
        if not features_dict:
            raise ValueError("没有可用的特征数据")

        for name, df in features_dict.items():
            if df.index.name != 'date' and 'date' in df.columns:
                df = df.set_index('date')
            df.index = pd.to_datetime(df.index)
            features_dict[name] = df.sort_index()

        all_data = []
        for name, df in features_dict.items():
            all_data.append(df)

        merged_data = pd.concat(all_data, axis=1, join='outer')
        print(f"合并后数据形状: {merged_data.shape}")
        return merged_data

    def find_target_column(self, data):
        target_cols = [col for col in data.columns if 'ret_21' in col.lower()]
        if target_cols:
            return target_cols[0]
        else:
            print("警告: 未找到目标变量列")
            return None

class DataCleaner:
    def __init__(self, nan_threshold=0.8):
        self.nan_threshold = nan_threshold
        self.kept_features = []

    def remove_high_nan_features(self, data):
        if data.empty:
            return data

        nan_ratio = data.isnull().sum() / len(data)
        features_to_keep = nan_ratio[nan_ratio <= self.nan_threshold].index.tolist()
        removed_features = set(data.columns) - set(features_to_keep)
        self.kept_features = features_to_keep
        return data[features_to_keep]

    def safe_forward_fill(self, data):
        if data.empty:
            return data

        data_filled = data.ffill()
        if data_filled.isnull().any().any():
            print("检测到开头存在NaN，使用后向填充处理开头数据...")
            data_filled = data_filled.bfill()
            if data_filled.isnull().any().any():
                print("使用0填充剩余的NaN值...")
                data_filled = data_filled.fillna(0)
        return data_filled

    def clean_data(self, data):
        print(f"原始数据形状: {data.shape}")
        data_cleaned = self.remove_high_nan_features(data)
        print(f"移除高缺失率特征后形状: {data_cleaned.shape}")
        data_filled = self.safe_forward_fill(data_cleaned)
        print(f"填充后数据形状: {data_filled.shape}")
        
        remaining_nans = data_filled.isnull().sum().sum()
        if remaining_nans > 0:
            print(f"警告: 数据中仍有 {remaining_nans} 个NaN值")
        return data_filled

class MacroDataEnhancer:
    def __init__(self):
        self.macro_features = []
        self.downloaded_data = {}

    def download_macro_data(self, start_date, end_date):
        macro_tickers = {
            'dollar_index': 'DX-Y.NYB',
            'vix': '^VIX',
            'bond_yield_10y': '^TNX',
            'sp500': '^GSPC',
            'gold': 'GC=F',
            'oil': 'CL=F'
        }

        for name, ticker in macro_tickers.items():
            try:
                print(f"正在下载 {name} 数据...")
                data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
                if not data.empty:
                    if 'Adj Close' in data.columns:
                        macro_series = data['Adj Close']
                    else:
                        macro_series = data['Close']
                    macro_series.name = name
                    self.downloaded_data[name] = macro_series
                    print(f"成功下载 {name} 数据，共 {len(macro_series)} 个数据点")
                else:
                    print(f"警告: {name} 数据为空")
            except Exception as e:
                print(f"下载 {name} 失败: {str(e)}")
                empty_series = pd.Series([], dtype=float, name=name)
                self.downloaded_data[name] = empty_series

    def add_all_macro_data(self, data, start_date, end_date):
        self.download_macro_data(start_date, end_date)
        enhanced_data = data.copy()
        macro_data_added = 0

        for macro_name, macro_series in self.downloaded_data.items():
            if len(macro_series) == 0:
                print(f"跳过空的宏观数据: {macro_name}")
                continue
            try:
                macro_series.index = pd.to_datetime(macro_series.index)
                enhanced_data.index = pd.to_datetime(enhanced_data.index)
                if isinstance(macro_series, pd.DataFrame):
                    print(f"警告: {macro_name} 是DataFrame而不是Series，尝试提取第一列")
                    macro_series = macro_series.iloc[:, 0]
                    macro_series.name = macro_name
                macro_df = pd.DataFrame({macro_name: macro_series})
                enhanced_data = enhanced_data.merge(macro_df, left_index=True, right_index=True, how='left')
                self.macro_features.append(macro_name)
                macro_data_added += 1
                print(f"已添加宏观特征: {macro_name}")
            except Exception as e:
                print(f"添加宏观特征 {macro_name} 失败: {str(e)}")

        print(f"宏观数据添加完成，成功添加 {macro_data_added} 个宏观特征")
        return enhanced_data