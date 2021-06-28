import time
import itertools
import numpy as np
from scipy import stats
import warnings
import pandas as pd
from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
from proc_utils.async_class import AsyncTask


class TSAModelEXP(object):
    # TODO: Provide full Implementation

    def __init__(
            self,
            s_data,
            t_len=4,
            alpha=0.8,
            beta=0.2,
            optimize=False,
            check_stats=False,
            check_outliers=False,
            ma_ord=8,
            z_score_limit=3.0
    ):
        self.s_data = s_data
        self.t_len = t_len
        self.smoothing_level = alpha
        self.smoothing_trend = beta
        self.ma_ord = ma_ord
        self.optimize = optimize
        self.check_stats = check_stats
        self.check_outliers = check_outliers
        self.z_score_limit = z_score_limit

    def filter_outliers(self, df):
        data_list = df.values
        same_val = len(set(data_list)) == 1
        if same_val:
            return df
        if len(data_list) < 5:
            return df
        z_score = stats.zscore(data_list)
        data = []
        for i in range(0, len(z_score)):
            if z_score[i] < self.z_score_limit:
                data.append(data_list[i])
        df = pd.Series(data)
        return df

    def get_holt_exp_model(self, training_data):
        t1 = time.time()
        warnings.filterwarnings("ignore")
        if self.check_outliers:
            training_data = self.filter_outliers(training_data)
        training_data = training_data.astype(float)
        model_fit = Holt(
            training_data, initialization_method="estimated"
        ).fit(
            smoothing_level=self.smoothing_level,
            smoothing_trend=self.smoothing_trend,
            optimized=self.optimize
        )
        # print(arima_model.summary())
        t2 = time.time()
        t_diff = t2 - t1
        tr_time = t_diff * 1000  # ms
        tr_time = str(round(tr_time, 2))
        return model_fit, tr_time

    def get_hw_exp_model(self, training_data):
        t1 = time.time()
        warnings.filterwarnings("ignore")
        if self.check_outliers:
            training_data = self.filter_outliers(training_data)
        training_data = training_data.astype(float)
        model_fit = ExponentialSmoothing(
            training_data, initialization_method="estimated"
        ).fit(
            smoothing_level=self.smoothing_level,
            smoothing_trend=self.smoothing_trend,
            optimized=self.optimize
        )
        # print(arima_model.summary())
        t2 = time.time()
        t_diff = t2 - t1
        tr_time = t_diff * 1000  # ms
        tr_time = str(round(tr_time, 2))
        return model_fit, tr_time

    def get_exp_model(self, training_data):
        t1 = time.time()
        warnings.filterwarnings("ignore")
        if self.check_outliers:
            training_data = self.filter_outliers(training_data)
        training_data = training_data.astype(float)
        if self.optimize:
            model_fit = SimpleExpSmoothing(
                training_data, initialization_method="estimated"
            ).fit(
                optimized=self.optimize, use_brute=True
            )
        else:
            model_fit = SimpleExpSmoothing(
                training_data, initialization_method="estimated"
            ).fit(
                smoothing_level=self.smoothing_level,
            )
        # print(arima_model.summary())
        t2 = time.time()
        t_diff = t2 - t1
        tr_time = t_diff * 1000  # ms
        tr_time = str(round(tr_time, 2))
        return model_fit, tr_time

    def get_rolling_forecast_exp(
            self,
            is_interval=False,
    ):
        data_len = len(self.s_data)
        test_data = self.s_data[data_len - self.t_len:]
        total_tr = 0.0
        predictions = []
        for i in range(0, self.t_len):
            training_data = self.s_data[:data_len - (self.t_len - i)]
            exp_model, tr_time = self.get_exp_model(training_data)
            total_tr += float(tr_time)
            cur_forecast = exp_model.forecast(1)
            forecast_val = cur_forecast.values[0]
            if is_interval:
                forecast_val = round(forecast_val)
                if forecast_val < 1.0:
                    forecast_val = 1.0
            predictions.append(forecast_val)
            # print("Cur List: ", predictions)
        predictions = pd.Series(predictions, index=test_data.index)
        # Removing negative delays which might occur due to sharp decay
        # predictions = predictions.where(predictions > 0.0, 0.0)
        residuals = test_data - predictions
        total_tr = str(round(total_tr, 2))
        return predictions, residuals, total_tr

    def get_rolling_forecast_avg(
            self,
            is_interval=False,
    ):
        data_len = len(self.s_data)
        test_data = self.s_data[data_len - self.t_len:]
        t_i = time.time()
        predictions = []
        for i in range(0, self.t_len):
            training_data = self.s_data[:data_len - (self.t_len - i)]
            if self.check_outliers:
                training_data = self.filter_outliers(training_data)
            data_block = training_data[-self.ma_ord:].values
            forecast_val = sum(data_block)/len(data_block)
            if is_interval:
                forecast_val = round(forecast_val)
                if forecast_val < 1.0:
                    forecast_val = 1.0
            predictions.append(forecast_val)
            # print("Cur List: ", predictions)
        predictions = pd.Series(predictions, index=test_data.index)
        residuals = test_data - predictions
        t_f = time.time()
        total_tr = str(round(t_f-t_i, 2))
        return predictions, residuals, total_tr

    def get_forecast_exp_prod(
            self,
            is_interval=False,
    ):
        training_data = self.s_data
        exp_model, tr_time = self.get_exp_model(training_data)
        cur_forecast = exp_model.forecast()
        forecast_val = cur_forecast.values[0]
        if is_interval:
            forecast_val = round(forecast_val)
            if forecast_val < 1.0:
                forecast_val = 1.0
        return forecast_val

    def get_forecast_avg_prod(
            self,
            is_interval=False,
    ):
        training_data = self.s_data
        if self.check_outliers:
            training_data = self.filter_outliers(training_data)
        data_block = training_data[-self.ma_ord:].values
        forecast_val = sum(data_block)/len(data_block)
        if is_interval:
            forecast_val = round(forecast_val)
            if forecast_val < 1.0:
                forecast_val = 1.0
        return forecast_val

