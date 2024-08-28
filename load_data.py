from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec


def plot_fcs_data(g2_correlations, lag_index, show_plot=True):
    num_plots = len(g2_correlations)
    num_plots_per_row = 1
    if num_plots < 2:
        num_plots_per_row = 1
    if num_plots > 1 and num_plots < 4:
        num_plots_per_row = 2
    if num_plots >= 4:
        num_plots_per_row = 4
    if num_plots >= 12:
        num_plots_per_row = 6        
    num_rows = (num_plots + num_plots_per_row - 1) // num_plots_per_row  
    fig = plt.figure(figsize=(12, 3 * num_rows))
    fig.suptitle("Fluorescence Spectroscopy Correlations")
    gs = GridSpec(num_rows, num_plots_per_row, figure=fig)
    for i, ((channel1, channel2), data_list) in enumerate(g2_correlations):
        row = i // num_plots_per_row
        col = i % num_plots_per_row
        ax = fig.add_subplot(gs[row, col])
        for data_index, data in enumerate(data_list):
            label = f"G(τ) {data_index + 1}" if data_index != 0 else f"G(τ) mean"
            ax.plot(lag_index, data, label=label)
        ax.set_xlabel("τ(μs)")
        ax.set_ylabel("G(τ)")
        ax.set_title(f"Channel {channel1 + 1}- Channel {channel2 + 1}")
        ax.set_xscale("log")
        ax.grid(True)
        ax.legend()      
    fig.tight_layout()
    if show_plot:
        plt.show()
    return fig