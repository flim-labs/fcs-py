import os
from PyQt6.QtCore import Qt, QSize
from components.buttons import ReadAcquireModeButton
from components.resource_path import resource_path
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, ".."))

from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QMenu,
)

from PyQt6.QtGui import QPixmap, QAction
from components.gui_styles import GUIStyles
from components.switch_control import SwitchControl
from components.gradient_text import GradientText
from components.link_widget import LinkWidget
from components.settings import *


class TopBarBuilder:

    @staticmethod
    def create_header_layout(
            logo_and_title,
            export_data_widget,
            gt_calc_mode_buttons_row_layout,
            app
    ):
        header_layout = QHBoxLayout()
        # Header row: Link to User Guide
        app_guide_link_widget = LinkWidget(
            icon_filename=resource_path("assets/info-icon.png"), text="User Guide", link=GUI_GUIDE_LINK
        )
        app_guide_link_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addLayout(logo_and_title)
        header_layout.addSpacing(10)
        header_layout.addWidget(gt_calc_mode_buttons_row_layout)
        header_layout.addStretch(1)
        read_acquire_button = ReadAcquireModeButton(app=app)
        header_layout.addWidget(read_acquire_button)
        header_layout.addWidget(export_data_widget)
        header_layout.addWidget(app_guide_link_widget)

        return header_layout

    @staticmethod   
    def create_logo_and_title(self):
        row = QHBoxLayout()
        row.addSpacing(10)
        pixmap = QPixmap(
            resource_path("assets/fcs-logo-white.png")
        ).scaledToWidth(40)
        ctl = QLabel(pixmap=pixmap)
        row.addWidget(ctl)
        row.addSpacing(10)
        ctl = GradientText(self,
                           text="FCS",
                           colors=[(0.5, "#31c914"), (1.0, "#ffff00")],
                           stylesheet=GUIStyles.set_main_title_style())
        ctl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(ctl)
        ctl = QWidget()
        ctl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(ctl)
        return row

    @staticmethod
    def create_export_data_input(value, change_cb):
        # Link to export data documentation
        info_link_widget = LinkWidget(
            icon_filename=resource_path("assets/info-icon.png"),
            link=EXPORT_DATA_GUIDE_LINK,
        )
        info_link_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        info_link_widget.show()

        # Export data switch control
        export_data_control = QHBoxLayout()
        export_data_label = QLabel("Export data:")
        inp = SwitchControl(
            active_color="#FB8C00", width=70, height=30, checked=value)
        inp.toggled.connect(change_cb)
        export_data_control.addWidget(export_data_label)
        export_data_control.addWidget(inp)

        return info_link_widget, export_data_control, inp

    @staticmethod
    def create_file_size_info_row(app, bin_file_size, bin_file_size_label, write_data, cb_calc_file_size):
        file_size_info_layout = QHBoxLayout()
        bin_file_size_label.setText("")
        bin_file_size_label.setStyleSheet("QLabel { color : #FFA726; }")

        file_size_info_layout.addWidget(bin_file_size_label)
        bin_file_size_label.show() if write_data is True else bin_file_size_label.hide()
        cb_calc_file_size()

        return file_size_info_layout

    @staticmethod
    def create_download_files_menu(
            self,
            write_data,
            acquisition_stopped,
            show_download_options_cb,
            download_python_cb, 
            download_matlab_cb
            ):
        # download button
        download_button = QPushButton("DOWNLOAD ")
        download_button.setEnabled(write_data and acquisition_stopped)
        download_button.setStyleSheet(GUIStyles.button_style("#31c914", "#57D33D", "#7FE777", "#31c914", "100px"))
        download_button.setIconSize(QSize(16, 16))
        download_button.clicked.connect(show_download_options_cb)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(download_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        # context menu
        download_menu = QMenu()
        python_action = QAction("PYTHON FORMAT", self)
        matlab_action = QAction("MATLAB FORMAT", self)
        download_menu.setStyleSheet(GUIStyles.set_context_menu_style("#31c914", "#57D33D", "#7FE777"))
        download_menu.addAction(python_action)
        python_action.triggered.connect(download_python_cb)
        download_menu.addAction(matlab_action)
        matlab_action.triggered.connect(download_matlab_cb)

        return download_button, download_menu