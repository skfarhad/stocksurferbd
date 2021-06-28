import time
from scipy import stats
import warnings
import pandas as pd
from fbprophet import Prophet


class TSxFBProphet(object):

    def __init__(
            self,
            s_data,
            t_len=4,
            check_stats=False,
            check_outliers=False,
            ma_ord=10,
            z_score_limit=3.0
    ):
        self.s_data = s_data
        self.t_len = t_len
        self.ma_ord = ma_ord
        self.check_stats = check_stats
        self.check_outliers = check_outliers
        self.z_score_limit = z_score_limit

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

    def get_fb_model(self, training_data):
        t1 = time.time()
        warnings.filterwarnings("ignore")
        if self.check_outliers:
            training_data = self.filter_outliers(training_data)
        model_init = Prophet(
            yearly_seasonality=False
        )
        model_fit = model_init.fit(training_data)
        # print(arima_model.summary())
        t2 = time.time()
        t_diff = t2 - t1
        tr_time = t_diff * 1000  # ms
        tr_time = str(round(tr_time, 2))
        return model_fit, tr_time

    def get_rolling_forecast_fb(
            self,
            is_interval=False,
    ):
        data_len = len(self.s_data)
        test_data = self.s_data['y'].iloc[data_len - self.t_len:]
        total_tr = 0.0
        predictions = []
        for i in range(0, self.t_len):
            training_data = self.s_data.iloc[:data_len - (self.t_len - i)]
            fb_model, tr_time = self.get_fb_model(training_data)
            total_tr += float(tr_time)
            forecast_ds = fb_model.make_future_dataframe(periods=1, include_history=False)
            cur_forecast = fb_model.predict(forecast_ds)
            cur_forecast = cur_forecast[['ds', 'yhat']]
            # print(training_data.tail())
            # print(cur_forecast)
            forecast_val = cur_forecast['yhat'].values[0]
            forecast_val = abs(forecast_val)
            if is_interval:
                forecast_val = round(forecast_val)
                if forecast_val < 1.0:
                    forecast_val = 1.0
            predictions.append(forecast_val)
            # print("Cur List: ", predictions)
        predictions = pd.Series(predictions, index=test_data.index)
        # print(predictions)
        residuals = test_data - predictions
        total_tr = str(round(total_tr, 2))
        return predictions, residuals, total_tr

    def get_rolling_forecast_avg(
            self,
            is_interval=False,
    ):
        self.s_data = self.s_data['y']
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

    def get_forecast_fb_prod(
            self,
            is_interval=False,
    ):
        training_data = self.s_data
        fb_model, tr_time = self.get_fb_model(training_data)
        cur_forecast = fb_model.make_future_dataframe(periods=1, include_history=False)
        forecast_val = cur_forecast['yhat'].values[0]
        if is_interval:
            forecast_val = round(forecast_val)
            if forecast_val < 1.0:
                forecast_val = 1.0
        return forecast_val


