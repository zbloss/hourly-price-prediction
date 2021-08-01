import numpy as np
import pandas as pd

class PerformanceAnalyzer(object):

    def __init__(self, path_to_model_metrics: str, path_to_trading_history: str):

        self.model_metrics = pd.read_csv(path_to_model_metrics)
        self.trading_history = pd.read_csv(path_to_trading_history)

        self.trading_history_descriptive_statistics = self.trading_history['total_assets'].describe()

    @property
    def train_mean_absolute_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'train']['mae'].values[0]

    @property
    def val_mean_absolute_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'val']['mae'].values[0]

    @property
    def test_mean_absolute_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'test']['mae'].values[0]

    @property
    def train_mean_squared_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'train']['mse'].values[0]

    @property
    def val_mean_squared_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'val']['mse'].values[0]

    @property
    def test_mean_squared_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'test']['mse'].values[0]

    @property
    def train_root_mean_squared_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'train']['rmse'].values[0]

    @property
    def val_root_mean_squared_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'val']['rmse'].values[0]

    @property
    def test_root_mean_squared_error(self):
        return self.model_metrics[self.model_metrics['mode'] == 'test']['rmse'].values[0]

    @property
    def train_r2(self):
        return self.model_metrics[self.model_metrics['mode'] == 'train']['r2'].values[0]

    @property
    def val_r2(self):
        return self.model_metrics[self.model_metrics['mode'] == 'val']['r2'].values[0]

    @property
    def test_r2(self):
        return self.model_metrics[self.model_metrics['mode'] == 'test']['r2'].values[0]

    @property
    def total_buys(self):
        return self.trading_history[self.trading_history['action'] == 'buy'].count()[0]

    @property
    def total_sells(self):
        return self.trading_history[self.trading_history['action'] == 'sell'].count()[0]

    @property
    def total_do_nothing(self):
        return self.trading_history[self.trading_history['action'] == 'do_nothing'].count()[0]

    @property
    def asset_periods(self):
        return self.trading_history_descriptive_statistics['count']

    @property
    def asset_mean(self):
        return self.trading_history_descriptive_statistics['mean']

    @property
    def asset_min(self):
        return self.trading_history_descriptive_statistics['min']

    @property
    def asset_inner_quartile(self):
        return self.trading_history_descriptive_statistics['25Q']

    @property
    def asset_middle_quartile(self):
        return self.trading_history_descriptive_statistics['50Q']

    @property
    def asset_outer_quartile(self):
        return self.trading_history_descriptive_statistics['75Q']

    @property
    def asset_max(self):
        return self.trading_history_descriptive_statistics['max']

    def annualized_std(self, series: pd.Series = None):
        """
        Calculates the annualized standard deviation of an hourly 
        pandas Series that has been sorted in ascending time series
        order.
        """
        
        if series is None:
            series = self.trading_history['total_assets']

        log_differential = np.log(series / series.shift(-1))
        hourly_std = np.std(log_differential)
        annualized_std = hourly_std * np.sqrt(365)
        return annualized_std    

        