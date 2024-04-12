APP_VERSION = "1.0"
APP_NAME = "FCS"
APP_DEFAULT_WIDTH = 1460
APP_DEFAULT_HEIGHT = 800

CORR_POPUP_WIDTH = 900
CORR_POPUP_HEIGHT = 550


SETTINGS_ACQUISITION_STOPPED = "acquisition_stopped"
DEFAULT_ACQUISITION_STOPPED = False

SETTINGS_TAUS_INPUTS = "tau_inputs"
TAUS_INPUTS = "[1,  50,  100,  200,  500,  1000,  5000,  10000,  50000, 100000]"

SETTINGS_TAU = "tau"
DEFAULT_TAU = "[]"

SETTINGS_GT_CALC_MODE = "gt_calc_mode"
DEFAULT_GT_CALC_MODE = "realtime"

SETTINGS_CH_CORRELATIONS = "ch_correlations"
DEFAULT_CH_CORRELATIONS = "[]"

EXPORT_DATA_GUIDE_LINK = "https://flim-labs.github.io/fcs-py/python-flim-labs/fcs-file-format.html"
GUI_GUIDE_LINK = f"https://flim-labs.github.io/fcs-py/v{APP_VERSION}"


CONN_CHANNELS = ["USB", "SMA"]

SETTINGS_CONN_CHANNEL = "conn_channel"
DEFAULT_CONN_CHANNEL = "USB"

FIRMWARES = ["intensity_tracing_usb.flim", "intensity_tracing_sma.flim"]

SETTINGS_FIRMWARE = "firmware"
DEFAULT_FIRMWARE = "intensity_tracing_usb.flim"

SETTINGS_BIN_WIDTH_MICROS = "bin_width_micros"
DEFAULT_BIN_WIDTH_MICROS = 1000

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

START_BUTTON = "start_button"
STOP_BUTTON = "stop_button"
RESET_BUTTON = "reset_button"
DOWNLOAD_BUTTON = "download_button"
DOWNLOAD_MENU = "download_menu"
CHECKBOX_CONTROLS = "ch_and_tau_controls"
TAU_COMPONENT = "tau_component"
ADD_TAU_POPUP = "add_tau_popup"
CHANNELS_COMPONENT = "channels_component"
CH_CORRELATIONS_POPUP = "ch_correlations_popup"

REALTIME_BUTTON = "realtime_button"
POST_PROCESSING_BUTTON = "post_processing_button"



EXPORTED_DATA_BYTES_UNIT = 12083.2