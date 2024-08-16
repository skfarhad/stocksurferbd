from stocksurferbd_pkg import CandlestickPlot

cd_plot = CandlestickPlot(file_path='AAMRANET_history_data.xlsx', symbol='AAMRANET')
cd_plot.show_plot(
    data_n=90,
    resample=True,
    step='3D'
)
