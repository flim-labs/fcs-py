import os

from components.acquisitions_progress_bar import AcquisitionsProgressBar, GtProgressBar
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, ".."))
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QSizePolicy,
    QApplication,
    QLabel,
    QSizePolicy
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import  QSize, Qt
from components.resource_path import resource_path
from components.settings import *
from components.logo_utilities import LogoOverlay, TitlebarIcon
from components.gui_styles import GUIStyles
from components.loading_spinner import Spinner




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
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    layout.addWidget(spacer_widget, 0, Qt.AlignmentFlag.AlignTop)
    layout.addWidget(separator, 0, Qt.AlignmentFlag.AlignTop)

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
    main_layout.setSpacing(0)
    main_layout.setContentsMargins(0,0,0,0)
    main_layout.addLayout(top_utilities_layout)
    
 
    progress_bar_layout = QVBoxLayout()
    acquisition_progress_bar_widget = AcquisitionsProgressBar(self)
    acquisition_progress_bar_widget.setVisible(False)
    progress_bar_layout.addWidget(acquisition_progress_bar_widget)
    
    gt_progress_bar_widget = GtProgressBar(self)
    gt_progress_bar_widget.setVisible(False)
    progress_bar_layout.addWidget(gt_progress_bar_widget)
    
    plot_grids_container = QHBoxLayout()
    plot_grids_container.setSpacing(0)
    plot_grids_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
    intensity_widget = create_intensity_layout(self)
    gt_widget = create_gt_wait_layout(self)
    plot_grids_container.addWidget(intensity_widget)
    plot_grids_container.addWidget(gt_widget)
    
    main_layout.addLayout(progress_bar_layout)
    main_layout.addLayout(plot_grids_container)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    self.setLayout(main_layout)
    
    self.layouts[MAIN_LAYOUT] = main_layout
    self.layouts[PLOT_GRIDS_CONTAINER] = plot_grids_container
    self.layouts[PROGRESS_BAR_LAYOUT] = progress_bar_layout
    self.widgets[ACQUISITION_PROGRESS_BAR_WIDGET] = acquisition_progress_bar_widget
    self.widgets[GT_PROGRESS_BAR_WIDGET] = gt_progress_bar_widget
    
    self.resize(self.settings.value("size", QSize(APP_DEFAULT_WIDTH, APP_DEFAULT_HEIGHT)))
    self.move(self.settings.value("pos", QApplication.primaryScreen().geometry().center() - self.frameGeometry().center()))


def create_intensity_layout(app):    
    intensity_widget = QWidget()
    intensity_widget.setFixedWidth(int(app.width() / 2.1))
    intensity_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    app.widgets[INTENSITY_WIDGET_WRAPPER] = intensity_widget
    intensity_v_box = QVBoxLayout()
    intensity_plots_grid = QGridLayout()
    only_cps_grid = QGridLayout()
    intensity_v_box.addLayout(intensity_plots_grid)
    intensity_v_box.addLayout(only_cps_grid)
    intensity_widget.setLayout(intensity_v_box)
    app.layouts[INTENSITY_PLOTS_GRID] = intensity_plots_grid
    app.layouts[INTENSITY_ONLY_CPS_GRID] = only_cps_grid
    return intensity_widget


def create_gt_wait_layout(app):    
    gt_widget = QWidget()
    gt_widget.setObjectName("container")
    gt_widget.setFixedWidth(int(app.width() / 1.95))
    gt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    gt_v_box = QVBoxLayout()
    gt_plot_icon = QLabel()
    gt_plot_icon.setPixmap(QPixmap(resource_path("assets/gt-wait-grey.png")).scaledToWidth(150))
    gt_plot_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title = QLabel("G(τ) plots")
    title.setObjectName("title")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    desc = QLabel("Waiting for the acquisition end...")
    desc.setObjectName("desc")
    desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    gt_v_box.addWidget(gt_plot_icon)
    gt_v_box.addWidget(title)
    gt_v_box.addWidget(desc)
    gt_widget.setStyleSheet(GUIStyles.gt_wait_widget_container())    
    gt_v_box.setAlignment(Qt.AlignmentFlag.AlignCenter) 
    gt_widget.setLayout(gt_v_box)
    gt_widget.setVisible(False)
    app.widgets[GT_WIDGET_WRAPPER] = gt_widget
    return gt_widget


def create_gt_loading_layout(app):   
    gt_widget = QWidget()
    gt_widget.setObjectName("container")
    gt_widget.setFixedWidth(int(app.width() / 1.95))
    gt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    spinner = Spinner()
    gt_v_box = QVBoxLayout()
    desc = QLabel("Post-processing in progress...")
    desc.setObjectName("desc")
    desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    gt_v_box.addWidget(spinner)
    gt_v_box.addWidget(desc)
    gt_widget.setStyleSheet(GUIStyles.gt_wait_widget_container())    
    gt_v_box.setAlignment(Qt.AlignmentFlag.AlignCenter) 
    gt_widget.setLayout(gt_v_box)
    app.widgets[GT_WIDGET_WRAPPER] = gt_widget
    return gt_widget


def create_gt_layout(app):    
    gt_widget = QWidget()
    gt_widget.setObjectName("container")
    title_widget = QWidget()
    title_widget.setStyleSheet("border-bottom: 1px solid #3b3b3b")
    title_layout = QVBoxLayout()
    title = QLabel("G(τ)")
    title.setObjectName("title")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_layout.addWidget(title)
    title_widget.setLayout(title_layout)
    
    gt_widget.setFixedWidth(int(app.width() / 1.95))
    gt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    app.widgets[GT_WIDGET_WRAPPER] = gt_widget
    gt_v_box = QVBoxLayout()
    gt_plots_grid = QGridLayout()
    gt_v_box.addWidget(title_widget)
    gt_widget.setStyleSheet(GUIStyles.gt_widget_container()) 
    gt_v_box.addLayout(gt_plots_grid)
    gt_widget.setLayout(gt_v_box)
    app.layouts[GT_PLOTS_GRID] = gt_plots_grid
    return gt_widget


def remove_widget(layout, widget):
    layout.removeWidget(widget)
    widget.setParent(None)
    widget.deleteLater() 
    del widget
    
    
def insert_widget(layout, widget, position):
    layout.insertWidget(position, widget)
        





    
