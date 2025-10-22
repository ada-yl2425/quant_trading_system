import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns

class EnhancedStrategyBacktester:
    def __init__(self, model, portfolio_manager):
        self.model = model
        self.portfolio_manager = portfolio_manager
        self.performance_metrics = {}

    def run_enhanced_backtest(self, data, start_date, end_date):
        print("=" * 60)
        print("开始策略回测")
        print("=" * 60)

        backtest_data = data[(data.index >= start_date) & (data.index <= end_date)]
        if backtest_data.empty:
            print("警告: 回测期间没有数据!")
            return {
                'portfolio_values': [self.portfolio_manager.initial_capital],
                'portfolio_dates': [start_date],
                'weights_history': [],
                'predictions': [],
                'actual_returns': [],
                'signal_dates': [],
                'metrics': {},
                'feature_importance': self.model.feature_importance_history
            }

        dates = backtest_data.index.unique()
        dates = sorted(dates)

        capital = self.portfolio_manager.initial_capital
        portfolio_values = [capital]
        portfolio_dates = [dates[0] if len(dates) > 0 else start_date]
        portfolio_weights_history = []
        predictions_list = []
        actual_returns_list = []
        signal_dates = []

        print(f"回测期间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"总交易日: {len(dates)}")

        for i, current_date in enumerate(dates):
            if i % self.model.retrain_freq == 0:
                success = self.model.train_model(data, current_date)

            prediction = self.model.predict(data, current_date)
            if prediction is not None:
                predictions_list.append(prediction)
                signal_dates.append(current_date)

                actual_return_data = data.loc[data.index == current_date, 'ret_21D']
                if len(actual_return_data) > 0:
                    actual_return = actual_return_data.iloc[0]
                    actual_returns_list.append(actual_return)
                else:
                    actual_returns_list.append(0)

                asset_data = self.prepare_asset_data(data, current_date)
                try:
                    capital, portfolio_return, weights = self.portfolio_manager.execute_advanced_trades(
                        current_date, asset_data, {'primary_asset': prediction}, capital
                    )
                    portfolio_values.append(capital)
                    portfolio_dates.append(current_date)
                    portfolio_weights_history.append({
                        'date': current_date,
                        'weights': weights,
                        'portfolio_return': portfolio_return,
                        'prediction': prediction,
                        'actual_return': actual_returns_list[-1] if actual_returns_list else None
                    })
                except Exception as e:
                    portfolio_values.append(capital)
                    portfolio_dates.append(current_date)

        self.performance_metrics = self.calculate_enhanced_metrics(
            portfolio_values, portfolio_weights_history, predictions_list, actual_returns_list
        )

        print(f"回测完成: {len(predictions_list)} 次预测, {len(portfolio_weights_history)} 次交易")
        return {
            'portfolio_values': portfolio_values,
            'portfolio_dates': portfolio_dates,
            'weights_history': portfolio_weights_history,
            'predictions': predictions_list,
            'actual_returns': actual_returns_list,
            'signal_dates': signal_dates,
            'metrics': self.performance_metrics,
            'feature_importance': self.model.feature_importance_history
        }

    def prepare_asset_data(self, data, current_date):
        historical_data = data[data.index <= current_date]
        asset_data = {
            'primary_asset': {
                'returns': historical_data['ret_21D'],
                'prices': self.calculate_price_series(historical_data['ret_21D']),
                'volatility': self.calculate_rolling_volatility(historical_data['ret_21D'])
            }
        }
        return asset_data

    def calculate_price_series(self, returns_series, initial_price=100):
        if len(returns_series) == 0:
            return pd.Series([initial_price])
        cumulative_returns = (1 + returns_series).cumprod()
        price_series = initial_price * cumulative_returns
        return price_series

    def calculate_rolling_volatility(self, returns_series, window=63):
        if len(returns_series) < window:
            return returns_series.std() if len(returns_series) > 0 else 0.02
        return returns_series.rolling(window=window, min_periods=10).std().iloc[-1] if len(returns_series) > 0 else 0.02

    def calculate_enhanced_metrics(self, portfolio_values, weights_history, predictions, actual_returns):
        portfolio_returns = pd.Series(portfolio_values).pct_change().dropna()
        if len(portfolio_returns) == 0:
            return {}

        total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100
        annual_return = portfolio_returns.mean() * 252 * 100
        annual_volatility = portfolio_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0

        downside_returns = portfolio_returns[portfolio_returns < 0]
        sortino_ratio = annual_return / (downside_returns.std() * np.sqrt(252) * 100) if len(downside_returns) > 0 else 0

        max_drawdown = self.calculate_max_drawdown(portfolio_values) * 100
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        winning_periods = len([r for r in portfolio_returns if r > 0])
        win_rate = winning_periods / len(portfolio_returns) if len(portfolio_returns) > 0 else 0

        prediction_accuracy = 0
        if len(predictions) > 0 and len(actual_returns) > 0:
            min_len = min(len(predictions), len(actual_returns))
            predictions_arr = np.array(predictions[:min_len])
            actual_arr = np.array(actual_returns[:min_len])

            if min_len > 1:
                correlation_matrix = np.corrcoef(predictions_arr, actual_arr)
                correlation = correlation_matrix[0, 1] if not np.isnan(correlation_matrix[0, 1]) else 0
            else:
                correlation = 0

            mse = mean_squared_error(actual_arr, predictions_arr) if min_len > 0 else 0
            direction_correct = np.sum((predictions_arr > 0) == (actual_arr > 0)) / min_len if min_len > 0 else 0
            ic = correlation
        else:
            correlation = 0
            mse = 0
            direction_correct = 0
            ic = 0

        total_trades = len(weights_history)
        positive_trades = len([w for w in weights_history if w.get('portfolio_return', 0) > 0])
        trade_win_rate = positive_trades / total_trades if total_trades > 0 else 0
        avg_position_size = np.mean([sum(w['weights'].values()) for w in weights_history]) if weights_history else 0

        metrics = {
            'Total Return (%)': total_return,
            'Annual Return (%)': annual_return,
            'Annual Volatility (%)': annual_volatility,
            'Sharpe Ratio': sharpe_ratio,
            'Sortino Ratio': sortino_ratio,
            'Calmar Ratio': calmar_ratio,
            'Max Drawdown (%)': max_drawdown,
            'Win Rate (%)': win_rate,
            'Prediction Correlation': correlation,
            'Information Coefficient': ic,
            'Prediction MSE': mse,
            'Direction Accuracy': direction_correct,
            'Number of Trades': total_trades,
            'Trade Win Rate (%)': trade_win_rate * 100,
            'Average Position Size (%)': avg_position_size * 100,
            'Final Portfolio Value': portfolio_values[-1],
            'Initial Capital': self.portfolio_manager.initial_capital
        }
        return metrics

    def calculate_max_drawdown(self, portfolio_values):
        portfolio_series = pd.Series(portfolio_values)
        rolling_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - rolling_max) / rolling_max
        return drawdown.min()

    def generate_enhanced_report(self, backtest_results):
        print("\n" + "=" * 60)
        print("回测结果报告")
        print("=" * 60)

        metrics = backtest_results['metrics']
        print("\n核心绩效指标:")
        print("-" * 40)
        print("\n收益表现:")
        print(f"   总收益率: {metrics.get('Total Return (%)', 0):.2f}%")
        print(f"   年化收益率: {metrics.get('Annual Return (%)', 0):.2f}%")
        print(f"   年化波动率: {metrics.get('Annual Volatility (%)', 0):.2f}%")
        print(f"   夏普比率: {metrics.get('Sharpe Ratio', 0):.4f}")
        print("\n风险控制:")
        print(f"   最大回撤: {metrics.get('Max Drawdown (%)', 0):.2f}%")
        print(f"   索提诺比率: {metrics.get('Sortino Ratio', 0):.4f}")
        print("\n预测质量:")
        print(f"   预测相关性: {metrics.get('Prediction Correlation', 0):.4f}")
        print(f"   方向准确率: {metrics.get('Direction Accuracy', 0):.4f}")
        print("\n交易统计:")
        print(f"   交易次数: {metrics.get('Number of Trades', 0)}")
        print(f"   交易胜率: {metrics.get('Trade Win Rate (%)', 0):.2f}%")
        print("\n资金信息:")
        print(f"   初始资本: ${metrics.get('Initial Capital', 0):,.0f}")
        print(f"   最终价值: ${metrics.get('Final Portfolio Value', 0):,.0f}")
        print(f"   绝对收益: ${metrics.get('Final Portfolio Value', 0) - metrics.get('Initial Capital', 0):,.0f}")