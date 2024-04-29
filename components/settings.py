APP_VERSION = "1.0"
APP_NAME = "FCS"
APP_DEFAULT_WIDTH = 1460
APP_DEFAULT_HEIGHT = 800

CORR_POPUP_WIDTH = 900
CORR_POPUP_HEIGHT = 550


SETTINGS_ACQUISITION_STOPPED = "acquisition_stopped"
DEFAULT_ACQUISITION_STOPPED = False

TAUS_INPUTS = [10, 100, 1000]
SETTINGS_TAU = "tau"
DEFAULT_TAU = 100

BIN_WIDTH_INPUTS = [1, 10, 100, 1000]
SETTINGS_BIN_WIDTH_MICROS = "bin_width_micros"
DEFAULT_BIN_WIDTH_MICROS = 1

AVERAGES_INPUTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SETTINGS_AVERAGES = "averages"
DEFAULT_AVERAGES = 1

SETTINGS_GT_CALC_MODE = "gt_calc_mode"
DEFAULT_GT_CALC_MODE = "post-processing"

SETTINGS_CH_CORRELATIONS = "ch_correlations"
DEFAULT_CH_CORRELATIONS = "[]"

SETTINGS_INTENSITY_PLOTS_TO_SHOW = "intensity_plots_to_show"
DEFAULT_INTENSITY_PLOTS_TO_SHOW = "[]"

SETTINGS_GT_PLOTS_TO_SHOW = "gt_plots_to_show"
DEFAULT_GT_PLOTS_TO_SHOW = "[]"


EXPORT_DATA_GUIDE_LINK = "https://flim-labs.github.io/fcs-py/python-flim-labs/fcs-file-format.html"
GUI_GUIDE_LINK = f"https://flim-labs.github.io/fcs-py/v{APP_VERSION}"


CONN_CHANNELS = ["USB", "SMA"]

SETTINGS_CONN_CHANNEL = "conn_channel"
DEFAULT_CONN_CHANNEL = "USB"

FIRMWARES = ["intensity_tracing_usb.flim", "intensity_tracing_sma.flim"]

SETTINGS_FIRMWARE = "firmware"
DEFAULT_FIRMWARE = "intensity_tracing_usb.flim"


SETTINGS_TIME_SPAN = "time_span"
DEFAULT_TIME_SPAN = 5

SETTINGS_ACQUISITION_TIME_MILLIS = "acquisition_time_millis"
DEFAULT_ACQUISITION_TIME_MILLIS = None

SETTINGS_FREE_RUNNING_MODE = "free_running_mode"
DEFAULT_FREE_RUNNING_MODE = True

SETTINGS_WRITE_DATA = "write_data"
DEFAULT_WRITE_DATA = True

MAX_CHANNELS = 8

SETTINGS_ENABLED_CHANNELS = "enabled_channels"
DEFAULT_ENABLED_CHANNELS = "[0]"

SETTINGS_SHOW_CPS = "show_cps"
DEFAULT_SHOW_CPS = True

MAIN_LAYOUT = "main_layout"

START_BUTTON = "start_button"
STOP_BUTTON = "stop_button"
RESET_BUTTON = "reset_button"
DOWNLOAD_BUTTON = "download_button"
DOWNLOAD_MENU = "download_menu"
CHECKBOX_CONTROLS = "ch_and_tau_controls"
CHANNELS_COMPONENT = "channels_component"
CH_CORRELATIONS_POPUP = "ch_correlations_popup"
PLOTS_CONFIG_POPUP = "plots_config_popup"

INTENSITY_PLOTS_GRID = "intensity_plots_grid"
INTENSITY_ONLY_CPS_GRID = "intensity_only_cps_grid"
GT_PLOTS_GRID = "gt_plots_grid"
PLOT_GRIDS_CONTAINER = "plots_grids_container"

TOP_COLLAPSIBLE_WIDGET = "top_collapsible_widget"

PROGRESS_BAR_LAYOUT = "progress_bar_layout"
PROGRESS_BAR_WIDGET = "progress_bar_widget"

INTENSITY_WIDGET_WRAPPER = "intensity_widget_wrapper"
GT_WIDGET_WRAPPER = "gt_widget_wrapper"

CHANNELS_CHECKBOXES = "channels_checkboxes"

REALTIME_BUTTON = "realtime_button"
POST_PROCESSING_BUTTON = "post_processing_button"



EXPORTED_DATA_BYTES_UNIT = 12083.2

REALTIME_MS = 10
REALTIME_ADJUSTMENT = REALTIME_MS * 1000
REALTIME_HZ = 1000 / REALTIME_MS
REALTIME_SECS = REALTIME_MS / 1000

NS_IN_S = 1_000_000_000
NS_IN_MS = 1_000_000

EXPORTED_DATA_BYTES_UNIT = 12083.2