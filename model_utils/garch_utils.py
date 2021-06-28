import time
import itertools

from arch import arch_model


def get_arch_model(training_data, order):
    t1 = time.time()
    model_init = arch_model(training_data, mean='Zero', vol='ARCH', p=order[0])
    model_fit = model_init.fit(disp='off', cov_type='robust')
    # print(arima_model.summary())
    t2 = time.time()
    t_diff = t2 - t1
    tr_time = t_diff * 1000  # ms
    tr_time = str(round(tr_time, 2))
    return model_fit, tr_time
