import os
import time
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
# from sklearn.metrics import mean_squared_error


os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
tf.get_logger().setLevel('ERROR')


class TSxLSTM(object):

    def __init__(
            self,
            dataset,
            units=3,
            epochs=30,
            target_field='NET',
            look_back=1,
            time_step=1,
            round_result=False,
            check_outliers=False,
            z_score_limit=3.0

    ):
        self.dataset = dataset
        self.lstm_units = units
        self.epochs = epochs
        self.target_field = target_field
        self.target_data = None
        if target_field == -1:
            self.target_data = dataset
        else:
            self.target_data = dataset[target_field]
        pre_target_field = str(target_field) + 'Pre'
        self.input_fields = ['WeekDay', 'MonthDay', 'DayDiff', pre_target_field]
        self.feature_n = len(self.input_fields)
        self.look_back = look_back
        self.scl_x = MinMaxScaler(feature_range=(0, 1))
        self.scl_y = MinMaxScaler(feature_range=(0, 1))
        self.time_step = time_step
        self.round_result = round_result
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

    def create_dataset(self, dataset, is_train=True):
        dataset = dataset.values.reshape(-1, 1)
        dataset = dataset.astype('float32')
        dataset = self.scl_x.fit_transform(dataset)
        data_x, data_y = [], []
        for i in range(self.look_back, len(dataset)):
            a = dataset[i - self.look_back:i, 0]
            data_x.append(a)
            data_y.append(dataset[i, 0])
        return np.array(data_x), np.array(data_y)

    def create_multivariate_dataset(self):
        input_fields = self.input_fields
        target_field = self.target_field
        scaled_features = self.scl_x.fit_transform(
            self.dataset[input_fields].values.astype('float32')
        )
        target = self.dataset[target_field].values.astype('float32').reshape(-1, 1)
        scaled_target = self.scl_y.fit_transform(target)
        data_len = len(scaled_features)
        data_x, data_y = [], []
        for i in range(data_len):
            a = scaled_features[i][0:self.feature_n]
            data_x.append(a)
            data_y.append(scaled_target[i][0])
        return np.array(data_x), np.array(data_y)

    def get_model(self, train_x, train_y, features):
        t1 = time.time()
        model_nn = tf.keras.models.Sequential()
        model_nn.add(tf.keras.layers.LSTM(
            units=self.lstm_units,
            input_shape=(1, features),
        ))
        model_nn.add(tf.keras.layers.Dense(
            units=1,
            activation='linear'
        ))
        model_nn.compile(
            loss='mean_squared_error',
            optimizer='adam'
        )
        model_nn.fit(
            train_x, train_y,
            epochs=self.epochs,
            batch_size=1,
            verbose=0
        )
        t2 = time.time()
        tr_time = (t2 - t1)  # seconds
        tr_time = str(round(tr_time, 2))
        return model_nn, tr_time

    def get_predictions(self, t_len):
        s_data = self.target_data
        look_back = self.look_back
        test_data = s_data[-t_len:]
        data_len = len(s_data)
        if self.check_outliers:
            s_data_train = self.filter_outliers(s_data[:data_len-t_len])
        else:
            s_data_train = s_data[:data_len-t_len]

        s_data_test = s_data[-(t_len + look_back):]
        train_x, train_y = self.create_dataset(s_data_train, is_train=True)
        test_x, test_y = self.create_dataset(s_data_test, is_train=False)
        # reshape input to be [samples, time steps, features]
        train_x_lstm = np.reshape(
            train_x, (train_x.shape[0], self.time_step, train_x.shape[1])
        )
        test_x_lstm = np.reshape(
            test_x, (test_x.shape[0], self.time_step, test_x.shape[1])
        )

        model, tr_time = self.get_model(train_x_lstm, train_y, look_back)
        test_predict = model.predict(test_x_lstm)
        test_predict = self.scl_x.inverse_transform(test_predict)
        predictions = test_predict[:, 0]
        if self.round_result:
            predictions = round(predictions)
        predictions = pd.Series(predictions, index=test_data.index)
        residuals = test_data - predictions

        return predictions, residuals, tr_time

    def get_predictions_multivariate(self, t_len=10):
        d_df = self.dataset
        test_data = d_df.iloc[-t_len:][self.target_field]
        data_len = len(d_df.index)
        self.create_multivariate_dataset()
        data_x, data_y = self.create_multivariate_dataset()
        train_x = data_x[:data_len - t_len]
        train_y = data_y[:data_len - t_len]
        test_x = data_x[-t_len:]
        train_x_lstm = np.reshape(train_x, (train_x.shape[0], 1, train_x.shape[1]))
        test_x_lstm = np.reshape(test_x, (test_x.shape[0], 1, test_x.shape[1]))
        model, tr_time = self.get_model(train_x_lstm, train_y, self.feature_n)
        test_predict = model.predict(test_x_lstm)

        test_predict = self.scl_y.inverse_transform(test_predict)
        predictions = test_predict[:, 0]
        predictions = pd.Series(predictions, index=test_data.index)
        residuals = test_data - predictions

        return predictions, residuals, tr_time
