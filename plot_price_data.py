from stocksurferbd_pkg import CandlestickPlot

cd_plot = CandlestickPlot(csv_path='AAMRANET_history_data.xlsx', symbol='AAMRANET')
cd_plot.show_plot(
    xtick_count=90,
    resample=True,
    step='3D'
)
