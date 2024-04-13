import os

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, ".."))

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QGridLayout,
    QFrame,
    QSizePolicy,
    QApplication,
    QLabel
)

from PyQt6.QtCore import  QSize, Qt


from components.settings import *
from components.logo_utilities import LogoOverlay, TitlebarIcon
from components.gui_styles import GUIStyles


def draw_layout_separator(line_width=1, color="#282828", vertical_space=10):
    spacer_widget = QWidget()
    spacer_widget.setFixedSize(1, vertical_space)
    direction = QFrame.Shape.HLine
    separator = QFrame()
    separator.setFrameShape(direction)
    separator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
    separator.setLineWidth(line_width)
    separator.setStyleSheet(f"QFrame{{color: {color};}}")
    layout = QVBoxLayout()
    layout.addWidget(spacer_widget)
    layout.addWidget(separator)

    container_widget = QWidget()
    container_widget.setLayout(layout)

    return container_widget


def create_logo_overlay(self):
    # Logo overlay
    logo_overlay = LogoOverlay(self)
    logo_overlay.show()
    logo_overlay.update_visibility(self)
    logo_overlay.update_position(logo_overlay)
    logo_overlay.lower()
    return logo_overlay


def init_ui(self, top_utilities_layout):
    self.setWindowTitle("FlimLabs - FCS v" + APP_VERSION)
    TitlebarIcon.setup(self)
    GUIStyles.customize_theme(self)
    main_layout = QVBoxLayout()
    main_layout.addLayout(top_utilities_layout)
   
    intensity_widget = QWidget()
    intensity_widget.setFixedWidth(int(self.width() / 2))
    self.widgets[INTENSITY_WIDGET_WRAPPER] = intensity_widget

    intensity_v_box = QVBoxLayout()
    plot_grids_container = QHBoxLayout()
    plot_grids_container.setSpacing(0)
    intensity_plots_grid = QGridLayout()
    only_cps_grid = QGridLayout()
    gt_plots_grid = QGridLayout()


    plot_grids_container.addLayout(intensity_plots_grid)
    plot_grids_container.addLayout(gt_plots_grid)
    intensity_v_box.addLayout(plot_grids_container)
    intensity_v_box.addLayout(only_cps_grid)
    intensity_widget.setLayout(intensity_v_box)

    main_layout.addWidget(intensity_widget)

    main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    self.setLayout(main_layout)
    self.layouts[MAIN_LAYOUT] = main_layout
    self.layouts[PLOT_GRIDS_CONTAINER] = plot_grids_container
    self.layouts[INTENSITY_PLOTS_GRID] = intensity_plots_grid
    self.layouts[GT_PLOTS_GRID] = gt_plots_grid
    self.layouts[INTENSITY_ONLY_CPS_GRID] = only_cps_grid
    
    self.resize(self.settings.value("size", QSize(APP_DEFAULT_WIDTH, APP_DEFAULT_HEIGHT)))
    self.move(self.settings.value("pos", QApplication.primaryScreen().geometry().center() - self.frameGeometry().center()))
    

    