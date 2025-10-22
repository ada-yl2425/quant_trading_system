import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import *
from data_loader import DataLoader, DataCleaner, MacroDataEnhancer
from feature_processor import FeatureSelector, FeatureProcessor
from signal_builder import OnlineTreeModel, AdvancedPortfolioManager
from backtester import EnhancedStrategyBacktester

def run_data_pipeline():
    print("=" * 60)
    print("开始数据处理流程")
    print("=" * 60)

    print("\n1. 加载数据...")
    data_loader = DataLoader(DATA_FOLDER_PATH)
    try:
        main_data = data_loader.load_parquet_files()
        print(f"成功加载数据: {main_data.shape[0]} 行 × {main_data.shape[1]} 列")
        print(f"时间范围: {main_data.index.min().strftime('%Y-%m-%d')} 至 {main_data.index.max().strftime('%Y-%m-%d')}")

        target_col = data_loader.find_target_column(main_data)
        if target_col:
            main_data = main_data.rename(columns={target_col: 'ret_21D'})
            target_stats = main_data['ret_21D'].describe()
            print(f"目标变量: 均值={target_stats['mean']:.4f}, 标准差={target_stats['std']:.4f}")
        else:
            print("警告: 数据中未找到目标变量 'ret_21D'")
            return None

    except Exception as e:
        print(f"数据加载失败: {e}")
        return None

    print("\n2. 添加宏观数据...")
    try:
        macro_enhancer = MacroDataEnhancer()
        start_date = main_data.index.min().strftime('%Y-%m-%d')
        end_date = main_data.index.max().strftime('%Y-%m-%d')
        enhanced_data = macro_enhancer.add_all_macro_data(main_data, start_date, end_date)
        print(f"成功添加 {len(macro_enhancer.macro_features)} 个宏观特征")
    except Exception as e:
        print(f"宏观数据添加失败: {e}")
        enhanced_data = main_data.copy()

    print("\n3. 数据清洗...")
    try:
        cleaner = DataCleaner(nan_threshold=0.8)
        cleaned_data = cleaner.clean_data(enhanced_data)
        print(f"清洗完成: 保留 {len(cleaner.kept_features)} 个特征")
    except Exception as e:
        print(f"数据清洗失败: {e}")
        return None

    print("\n4. 特征选择...")
    try:
        feature_selector = FeatureSelector(max_features=1000)
        selected_data = feature_selector.select_features_static(cleaned_data)
        print(f"特征选择完成: 从 {len(cleaned_data.columns)} 个特征中选择 {len(feature_selector.selected_features)} 个")
    except Exception as e:
        print(f"特征选择失败: {e}")
        selected_data = cleaned_data

    print("\n5. 特征工程...")
    try:
        processor = FeatureProcessor()
        data_with_lags = processor.create_lag_features(selected_data, lags=[1, 5, 21])
        data_with_features = processor.calculate_rolling_features(data_with_lags, windows=[5, 21, 63])
        print(f"特征工程完成")
        print(f"最终数据维度: {data_with_features.shape[0]} 样本 × {data_with_features.shape[1]} 特征")

    except Exception as e:
        print(f"特征工程失败: {e}")
        return None

    print("\n" + "=" * 60)
    print("✅ 数据处理流程完成!")
    print("=" * 60)

    return data_with_features

def run_online_learning_strategy(processed_data):
    print("开始在线学习树模型策略")

    print("\n1. 初始化在线学习模型...")
    online_model = OnlineTreeModel(
        model_type='xgboost',
        model_params={
            'n_estimators': 50,
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'random_state': 42,
            'n_jobs': -1
        },
        train_window=756,
        retrain_freq=42,
        prediction_horizon=21,
        dynamic_feature_selection=True,
        max_features=200
    )

    print("2. 初始化投资组合管理器...")
    portfolio_manager = AdvancedPortfolioManager(
        initial_capital=1000000,
        max_position=0.02,
        transaction_cost=0.005,
        kelly_fraction=0.08,
        min_volatility=0.03,
        prediction_threshold=0.01
    )

    print("3. 初始化策略回测器...")
    backtester = EnhancedStrategyBacktester(online_model, portfolio_manager)

    print("4. 运行回测...")
    split_idx = int(len(processed_data) * 0.3)
    start_date = processed_data.index[split_idx]
    end_date = processed_data.index[-1]

    print(f"回测期间: {start_date} 到 {end_date}")
    print(f"回测数据量: {len(processed_data[processed_data.index >= start_date])} 个交易日")

    print("进行初始模型训练...")
    initial_success = online_model.train_model(processed_data, start_date, initial_training=True)
    if not initial_success:
        print("初始训练失败，调整参数重试...")
        online_model.train_window = min(online_model.train_window, len(processed_data) // 2)
        initial_success = online_model.train_model(processed_data, start_date, initial_training=True)

    if initial_success:
        backtest_results = backtester.run_enhanced_backtest(processed_data, start_date, end_date)
        print("\n5. 生成回测报告...")
        backtester.generate_enhanced_report(backtest_results)
        return backtest_results, online_model, backtester
    else:
        print("初始训练失败，无法进行回测")
        return None, None, None

def save_results(backtest_results, model, backtester):
    Path(OUTPUT_CSV_PATH).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_CHARTS_PATH).mkdir(parents=True, exist_ok=True)

    print("\n保存结果...")
    predictions_df = pd.DataFrame(model.prediction_history)
    predictions_df.to_csv(f"{OUTPUT_CSV_PATH}/prediction_history.csv", index=False)
    print("预测历史已保存")

    if model.feature_importance_history:
        feature_importance_df = pd.concat(model.feature_importance_history)
        feature_importance_df.to_csv(f"{OUTPUT_CSV_PATH}/feature_importance_history.csv", index=False)
        print("特征重要性历史已保存")

    portfolio_results = pd.DataFrame({
        'date': backtest_results['portfolio_dates'],
        'portfolio_value': backtest_results['portfolio_values']
    })
    portfolio_results.to_csv(f"{OUTPUT_CSV_PATH}/portfolio_results.csv", index=False)
    print("投资组合结果已保存")

    metrics_df = pd.DataFrame([backtest_results['metrics']])
    metrics_df.to_csv(f"{OUTPUT_CSV_PATH}/performance_metrics.csv", index=False)
    print("绩效指标已保存")

    if 'weights_history' in backtest_results:
        weights_history = pd.DataFrame(backtest_results['weights_history'])
        weights_history.to_csv(f"{OUTPUT_CSV_PATH}/weights_history.csv", index=False)
        print("权重历史已保存")

def main():
    print("=" * 80)
    print("开始在线学习模型训练和回测流程")
    print("=" * 80)

    processed_data_path = Path(PROCESSED_DATA_PATH)
    if processed_data_path.exists():
        print("加载已处理的数据...")
        processed_data = pd.read_parquet(processed_data_path)
    else:
        print("处理原始数据...")
        processed_data = run_data_pipeline()
        if processed_data is not None:
            Path(processed_data_path.parent).mkdir(parents=True, exist_ok=True)
            processed_data.to_parquet(processed_data_path)
            print(f"处理后的数据已保存至: {processed_data_path}")

    if processed_data is not None:
        print("\n运行模型训练与回测...")
        backtest_results, model, backtester = run_online_learning_strategy(processed_data)

        if backtest_results is not None:
            save_results(backtest_results, model, backtester)

            print("\n" + "=" * 60)
            print("流程完成摘要")
            print("=" * 60)
            metrics = backtest_results['metrics']
            print(f"最终绩效:")
            print(f"总收益率: {metrics.get('Total Return (%)', 0):.2f}%")
            print(f"年化收益率: {metrics.get('Annual Return (%)', 0):.2f}%")
            print(f"夏普比率: {metrics.get('Sharpe Ratio', 0):.4f}")
            print(f"最大回撤: {metrics.get('Max Drawdown (%)', 0):.2f}%")
            print(f"预测准确率: {metrics.get('Direction Accuracy', 0):.4f}")
            print(f"交易次数: {metrics.get('Number of Trades', 0)}")
            print(f"交易胜率: {metrics.get('Trade Win Rate (%)', 0):.2f}%")

            initial = metrics.get('Initial Capital', 0)
            final = metrics.get('Final Portfolio Value', 0)
            print(f"资金变化:")
            print(f"初始: ${initial:,.0f}")
            print(f"最终: ${final:,.0f}")
            print(f"收益: ${final - initial:,.0f}")

            print("\n" + "=" * 80)
            print("所有流程完成!")
            print("=" * 80)
        else:
            print("模型训练失败")
    else:
        print("数据处理失败")

if __name__ == "__main__":
    main()