import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from sklearn.feature_selection import mutual_info_regression

class FeatureSelector:
    def __init__(self, max_features=1000, correlation_threshold=0.01,
                 mutual_info_threshold=0.01, variance_threshold=0.01):
        self.max_features = max_features
        self.correlation_threshold = correlation_threshold
        self.mutual_info_threshold = mutual_info_threshold
        self.variance_threshold = variance_threshold
        self.selected_features = []

    def calculate_feature_variance(self, data):
        return data.var()

    def calculate_target_correlation(self, data, target_col='ret_21D'):
        correlations = {}
        target = data[target_col]

        for column in data.columns:
            if column != target_col:
                valid_data = data[[column, target_col]].dropna()
                if len(valid_data) > 10:
                    corr, _ = spearmanr(valid_data[column], valid_data[target_col])
                    correlations[column] = abs(corr) if not np.isnan(corr) else 0
        return correlations

    def calculate_mutual_information(self, data, target_col='ret_21D', sample_fraction=0.1):
        sample_data = data.sample(frac=sample_fraction, random_state=42) if len(data) > 1000 else data
        sample_data = sample_data.dropna()
        if len(sample_data) < 50:
            return {}

        X_sample = sample_data.drop(target_col, axis=1)
        y_sample = sample_data[target_col]
        max_features_to_test = min(1000, len(X_sample.columns))
        features_to_test = np.random.choice(X_sample.columns, max_features_to_test, replace=False)

        mi_scores = {}
        for feature in features_to_test:
            try:
                mi = mutual_info_regression(X_sample[[feature]].values.reshape(-1, 1), y_sample, random_state=42)[0]
                mi_scores[feature] = mi
            except:
                mi_scores[feature] = 0
        return mi_scores

    def select_features_static(self, data, target_col='ret_21D'):
        print(f"原始特征数量: {len(data.columns)}")
        variances = self.calculate_feature_variance(data.drop(target_col, axis=1))
        high_variance_features = variances[variances > self.variance_threshold].index.tolist()
        print(f"高方差特征数量: {len(high_variance_features)}")

        correlations = self.calculate_target_correlation(data[high_variance_features + [target_col]], target_col)
        mi_scores = {}
        if len(high_variance_features) > 1000:
            print("计算互信息...")
            mi_scores = self.calculate_mutual_information(data[high_variance_features + [target_col]], target_col)

        feature_scores = {}
        for feature in high_variance_features:
            corr_score = correlations.get(feature, 0)
            mi_score = mi_scores.get(feature, 0)
            combined_score = 0.7 * corr_score + 0.3 * mi_score
            feature_scores[feature] = combined_score

        sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
        selected_features = [feature for feature, score in sorted_features[:self.max_features]]
        final_features = selected_features + [target_col]

        print(f"静态特征选择完成，选择 {len(selected_features)} 个特征")
        print(f"Top 10 特征: {selected_features[:10]}")
        self.selected_features = selected_features
        return data[final_features]

class FeatureProcessor:
    def __init__(self):
        pass

    def create_lag_features(self, data, lags=[1, 7, 21]):
        lagged_data = data.copy()
        original_columns = [col for col in data.columns if col != 'ret_21D']
        lag_features_created = 0

        for lag in lags:
            for column in original_columns:
                new_col_name = f'{column}_lag_{lag}'
                lagged_data[new_col_name] = data[column].shift(lag)
                lag_features_created += 1

        print(f"滞后特征处理后数据形状: {lagged_data.shape}")
        return lagged_data

    def calculate_rolling_features(self, data, windows=[7, 21, 63]):
        print("计算滚动特征...")
        rolled_data = data.copy()
        original_columns = [col for col in data.columns if col != 'ret_21D']
        roll_features_created = 0

        for window in windows:
            for column in original_columns:
                rolled_data[f'{column}_roll_mean_{window}'] = data[column].rolling(window, min_periods=1).mean()
                rolled_data[f'{column}_roll_std_{window}'] = data[column].rolling(window, min_periods=1).std()
                roll_features_created += 2

        print(f"创建了 {roll_features_created} 个滚动特征")
        print(f"滚动特征处理后数据形状: {rolled_data.shape}")
        return rolled_data