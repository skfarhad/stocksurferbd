import time
import itertools
from scipy import stats

import warnings
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, kpss

from proc_utils.async_class import AsyncTask


def get_stat_avg(df, z_score_limit=3.0):
    data_list = df.values
    if len(data_list) < 5:
        avg = sum(data_list)/len(data_list)
        return avg
    same_val = len(set(data_list)) == 1
    if same_val:
        return same_val
    z_score = stats.zscore(data_list)
    data = []
    for i in range(0, len(z_score)):
        if z_score[i] < z_score_limit:
            data.append(data_list[i])
    avg = sum(data)/len(data)
    return avg


class TSxARIMA(object):

    def __init__(
            self,
            s_data,
            t_len=4,
            ar_ord=2,
            ma_ord=2,
            optimize=False,
            check_stats=False,
            check_outliers=False,
            use_sarimax=False,
            z_score_limit=3.0
    ):
        self.s_data = s_data
        self.t_len = t_len
        self.ar_ord = ar_ord
        self.ma_ord = ma_ord
        self.diff_ord = 0
        self.optimize = optimize
        self.check_stats = check_stats
        self.check_outliers = check_outliers
        self.z_score_limit = z_score_limit
        self.use_sarimax = use_sarimax

    def get_order(self):
        order = (self.ar_ord, self.diff_ord, self.ma_ord)
        return order

    def filter_outliers(self, df):
        data_list = df.values
        same_val = len(set(data_list)) == 1
        if same_val:
            return df
        z_score = stats.zscore(data_list)
        data = []
        for i in range(0, len(z_score)):
            if z_score[i] < self.z_score_limit:
                data.append(data_list[i])
        df = pd.Series(data)
        return df

    def set_diff_ord(self, nlags="legacy"):
        self.diff_ord = 0
        if self.check_stats:
            adf_result = adfuller(self.s_data)
            p_value_adf = adf_result[1]
            kpss_result = kpss(self.s_data, nlags=nlags)
            p_value_kpss = kpss_result[1]

            if p_value_adf < 0.05 and p_value_kpss >= 0.05:
                # Strictly Stationary
                diff_order = 0
            elif p_value_adf < 0.05 and p_value_kpss < 0.05:
                # Difference Stationary
                diff_order = 1
            elif p_value_adf >= 0.05 and p_value_kpss >= 0.05:
                # Trend Stationary
                # TODO: Theoretical explanations needed
                diff_order = 1
            else:
                # Not-Stationary
                # TODO: Use manual transformations?
                diff_order = 0
            self.diff_ord = diff_order

    def get_arima_model(self, training_data):
        t1 = time.time()
        warnings.filterwarnings("ignore")
        if self.check_outliers:
            training_data = self.filter_outliers(training_data)
        if self.use_sarimax:
            ts_model = SARIMAX
        else:
            ts_model = ARIMA
        model_init = ts_model(
            endog=training_data,
            order=self.get_order(),
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        model_fit = model_init.fit()
        # print(arima_model.summary())
        t2 = time.time()
        t_diff = t2 - t1
        tr_time = t_diff * 1000  # ms
        tr_time = str(round(tr_time, 2))
        return model_fit, tr_time

    def get_arima_task(self, args):
        model_fit = None
        # print(args)
        t1 = time.time()
        training_data = args["y_endog"]
        if self.check_outliers:
            training_data = self.filter_outliers(training_data)
        if self.use_sarimax:
            ts_model = SARIMAX
        else:
            ts_model = ARIMA
        try:
            model_init = ts_model(
                training_data,
                order=args["param"],
                enforce_stationarity=False,
                enforce_invertibility=False,
                # concentrate_scale=True
            )
            model_fit = model_init.fit()
        except Exception as e:
            print("Exception: " + str(e))
        t2 = time.time()
        diff = t2 - t1
        return model_fit, diff

    def get_optimized_arima_async(
            self,
            y_endog,
            x_exog=None,
            p_range=range(1, 5),
            d_range=range(0, 2),
            q_range=range(1, 5),
    ):
        """
            Return best model based on AIC
        """

        # Generate all different combinations of p, q and q triplets
        if self.check_stats:
            self.set_diff_ord()
            pdq = list(itertools.product(p_range, [self.diff_ord], q_range))
        else:
            pdq = list(itertools.product(p_range, d_range, q_range))
        workers = len(pdq) // 2

        warnings.filterwarnings("ignore")
        async_task_exec = AsyncTask(workers=workers)
        param_list = []
        t1 = time.time()
        for param in pdq:
            param_list.append({
                "y_endog": y_endog, "param": param
            })
        results = async_task_exec.run_tasks(self.get_arima_task, param_list)
        valid_models = [model for model in results if model]
        best_model = sorted(valid_models, key=lambda pair: pair[0].aic, reverse=False)[0][0]
        t2 = time.time()
        t_diff = t2 - t1
        tr_time = t_diff  # ms
        tr_time = str(round(tr_time, 2))

        return best_model, tr_time

    def get_rolling_forecast_arima(
            self,
            is_interval=False,
    ):
        data_len = len(self.s_data)
        test_data = self.s_data[data_len - self.t_len:]
        total_tr = 0.0
        predictions = []
        for i in range(0, self.t_len):
            training_data = self.s_data[:data_len - (self.t_len - i)]
            if self.optimize:
                arima_model, tr_time = self.get_optimized_arima_async(training_data)
            else:
                self.set_diff_ord()
                arima_model, tr_time = self.get_arima_model(training_data)
            total_tr += float(tr_time)
            cur_forecast = arima_model.forecast()
            forecast_val = cur_forecast.values[0]
            if is_interval:
                forecast_val = round(forecast_val)
                if forecast_val < 1.0:
                    forecast_val = 1.0
            predictions.append(forecast_val)
            # print("Cur List: ", predictions)
        predictions = pd.Series(predictions, index=test_data.index)
        residuals = test_data - predictions
        total_tr = str(round(total_tr, 2))
        return predictions, residuals, total_tr

    def get_forecast_arima_prod(
            self,
            is_interval=False,
    ):
        training_data = self.s_data
        if self.optimize:
            arima_model, tr_time = self.get_optimized_arima_async(training_data)
        else:
            self.set_diff_ord()
            arima_model, tr_time = self.get_arima_model(training_data)
        cur_forecast = arima_model.forecast()
        forecast_val = cur_forecast.values[0]
        if is_interval:
            forecast_val = round(forecast_val)
            if forecast_val < 1.0:
                forecast_val = 1.0
        return forecast_val

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

    def get_forecast_task(self, args):
        if args["optimize"]:
            arima_model, tr_time = self.get_optimized_arima_async(
                args["training_data"],
            )
        else:
            arima_model, tr_time = self.get_arima_model(args["training_data"])
        forecast = arima_model.forecast().values[0]
        return forecast, args["i"]

    def get_rolling_forecast_async(self):
        data_len = len(self.s_data)
        order = None
        if not self.optimize:
            order = self.get_order()

        test_data = self.s_data[data_len - self.t_len:]
        param_list = []
        t1 = time.time()
        async_task_exec = AsyncTask(workers=self.t_len)
        for i in range(0, self.t_len):
            training_data = self.s_data[0:data_len - (self.t_len - i)]
            param_list.append({
                "training_data": training_data,
                "order": order,
                "optimize": self.optimize,
                "check_stats": True,
                "i": i
            })
        results = async_task_exec.run_tasks(self.get_forecast_task, param_list)
        t2 = time.time()
        results = sorted(results, key=lambda r: r[1], reverse=False)
        predictions = [res[0] for res in results]
        predictions = pd.Series(predictions, index=test_data.index)
        # print(predictions)
        residuals = test_data - predictions
        total_tr = str(round(t2 - t1, 2))
        return predictions, residuals, total_tr
