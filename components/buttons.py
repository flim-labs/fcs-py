import json
import os
from PyQt6.QtWidgets import QComboBox,QStyledItemDelegate,QStyle, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QCheckBox, QLabel
from PyQt6.QtCore import QEvent, QPropertyAnimation, Qt, QSize, QPoint, QRect
from PyQt6.QtGui import  QIcon, QPixmap, QStandardItem, QStandardItemModel,QColor
from components.intensity_tracing_controller import IntensityTracingButtonsActions
from components.plots_config_widget import PlotsConfigPopup
from components.read_data import ReadData, ReadDataControls, ReaderMetadataPopup, ReaderPopup
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.controls_bar_builder import ControlsBarBuilder
from components.settings import *
from load_data import plot_fcs_data


current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class CollapseButton(QWidget):
    def __init__(self, collapsible_widget, parent=None):
        super().__init__(parent)
        self.collapsible_widget = collapsible_widget
        self.collapsed = True
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(
            QIcon(resource_path("assets/arrow-up-dark-grey.png"))
        )
        self.toggle_button.setFixedSize(30, 30)
        self.toggle_button.setStyleSheet(GUIStyles.toggle_collapse_button())
        self.toggle_button.clicked.connect(self.toggle_collapsible)
        self.toggle_button.move(self.toggle_button.x(), self.toggle_button.y() - 100)
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self.toggle_button)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.animation = QPropertyAnimation(self.collapsible_widget, b"maximumHeight")
        self.animation.setDuration(300)

    def toggle_collapsible(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.collapsible_widget.sizeHint().height())
            self.toggle_button.setIcon(
                QIcon(resource_path("assets/arrow-up-dark-grey.png"))
            )
        else:
            self.animation.setStartValue(self.collapsible_widget.sizeHint().height())
            self.animation.setEndValue(0)
            self.toggle_button.setIcon(
                QIcon(resource_path("assets/arrow-down-dark-grey.png"))
            )
        self.animation.start()


class ActionButtons(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window

        layout = self.create_buttons()
        self.setLayout(layout)

    def create_buttons(self):
        (
            buttons_row_layout,
            start_button,
            stop_button,
            reset_button,
            read_bin_data_button,
            bin_metadata_button,
            export_plot_img_button,
        ) = ControlsBarBuilder.create_buttons(
            self.start_button_pressed,
            self.stop_button_pressed,
            self.reset_button_pressed,
            self.plot_read_data_button_pressed,
            self.read_bin_metadata_button_pressed,
            self.app.enabled_channels,
            self.app
        )
        self.app.control_inputs[START_BUTTON] = start_button
        self.app.control_inputs[STOP_BUTTON] = stop_button
        self.app.control_inputs[RESET_BUTTON] = reset_button
        read_bin_data_button.setVisible(self.app.acquire_read_mode == "read")
        bin_metadata_btn_visible = ReadDataControls.read_bin_metadata_enabled(self.app)
        bin_metadata_button.setVisible(bin_metadata_btn_visible)
        self.app.control_inputs[BIN_METADATA_BUTTON] = bin_metadata_button
        self.app.control_inputs[READ_FILE_BUTTON] = read_bin_data_button
        return buttons_row_layout

    def start_button_pressed(self):
        open_popup = len(self.app.gt_plots_to_show) == 0
        if open_popup:
            popup = PlotsConfigPopup(self.app, start_acquisition=True)
            popup.show()
        else:
            IntensityTracingButtonsActions.start_button_pressed(self.app)

    def stop_button_pressed(self):
        IntensityTracingButtonsActions.stop_button_pressed(self.app)

    def reset_button_pressed(self):
        IntensityTracingButtonsActions.reset_button_pressed(self.app)

    def plot_read_data_button_pressed(self):
        popup = ReaderPopup(self.app)
        popup.show()
        
    
    def read_bin_metadata_button_pressed(self):
        popup = ReaderMetadataPopup(self.app)
        popup.show()
            


class GTModeButtons(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window

        layout = self.create_buttons()
        self.setLayout(layout)

    def create_buttons(self):
        buttons_row_layout, realtime_button, post_processing_button = (
            ControlsBarBuilder.create_gt_calc_mode_buttons(
                self.realtime_button_pressed,
                self.post_processing_button_pressed,
                self.app.selected_gt_calc_mode,
            )
        )
        self.app.control_inputs[REALTIME_BUTTON] = realtime_button
        self.app.control_inputs[POST_PROCESSING_BUTTON] = post_processing_button
        return buttons_row_layout

    def realtime_button_pressed(self, checked):
        self.app.control_inputs[REALTIME_BUTTON].setChecked(checked)
        self.app.control_inputs[POST_PROCESSING_BUTTON].setChecked(not checked)
        self.app.settings.setValue(
            SETTINGS_GT_CALC_MODE, "realtime" if checked else "post-processing"
        )

    def post_processing_button_pressed(self, checked):
        self.app.control_inputs[REALTIME_BUTTON].setChecked(not checked)
        self.app.control_inputs[POST_PROCESSING_BUTTON].setChecked(checked)
        self.app.settings.setValue(
            SETTINGS_GT_CALC_MODE, "post-processing" if checked else "realtime"
        )


class ReadAcquireModeButton(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        layout = QVBoxLayout()
        buttons_row = self.create_buttons()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(buttons_row)
        self.setLayout(layout)

    def create_buttons(self):
        buttons_row_layout = QHBoxLayout()
        buttons_row_layout.setSpacing(0)
        # Acquire button
        acquire_button = QPushButton("ACQUIRE")
        acquire_button.setCursor(Qt.CursorShape.PointingHandCursor)
        acquire_button.setCheckable(True)
        acquire_button.setObjectName("acquire_btn")  # Set objectName
        acquire_button.setChecked(self.app.acquire_read_mode == "acquire")
        acquire_button.clicked.connect(self.on_acquire_btn_pressed)
        buttons_row_layout.addWidget(acquire_button)
        # Read button
        read_button = QPushButton("READ")
        read_button.setCheckable(True)
        read_button.setCursor(Qt.CursorShape.PointingHandCursor)
        read_button.setObjectName("read_btn")  # Set objectName
        read_button.setChecked(self.app.acquire_read_mode != "acquire")
        read_button.clicked.connect(self.on_read_btn_pressed)
        buttons_row_layout.addWidget(read_button)
        self.app.control_inputs[ACQUIRE_BUTTON] = acquire_button
        self.app.control_inputs[READ_BUTTON] = read_button
        self.apply_base_styles()
        self.set_buttons_styles()
        return buttons_row_layout

    def apply_base_styles(self):
        base_style = GUIStyles.acquire_read_btn_style()
        self.app.control_inputs[ACQUIRE_BUTTON].setStyleSheet(base_style)
        self.app.control_inputs[READ_BUTTON].setStyleSheet(base_style)

    def set_buttons_styles(self):
        def get_buttons_style(color_acquire, color_read, bg_acquire, bg_read):
            return f"""
            QPushButton {{
                font-family: "Montserrat";
                letter-spacing: 0.1em;
                padding: 10px 12px;
                font-size: 14px;
                font-weight: bold;
                min-width: 60px;
            }}
            QPushButton#acquire_btn {{
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                color: {color_acquire};
                background-color: {bg_acquire};
            }}
            QPushButton#read_btn {{
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                color: {color_read};
                background-color: {bg_read};
            }}
        """

        read_mode = self.app.acquire_read_mode == "read"
        if read_mode:
            style = get_buttons_style(
                color_acquire="#8c8b8b",
                color_read="#222222",
                bg_acquire="#cecece",
                bg_read="#ffff00",
            )
        else:
            style = get_buttons_style(
                color_acquire="#222222",
                color_read="#8c8b8b",
                bg_acquire="#ffff00",
                bg_read="#cecece",
            )
        self.app.control_inputs[ACQUIRE_BUTTON].setStyleSheet(style)
        self.app.control_inputs[READ_BUTTON].setStyleSheet(style)

    def on_acquire_btn_pressed(self, checked):
        from components.intensity_tracing_controller import IntensityTracingButtonsActions 
        IntensityTracingButtonsActions.clear_plots(self.app)
        self.app.control_inputs[ACQUIRE_BUTTON].setChecked(checked)
        self.app.control_inputs[READ_BUTTON].setChecked(not checked)
        self.app.acquire_read_mode = "acquire" if checked else "read"
        self.app.settings.setValue(
            SETTINGS_ACQUIRE_READ_MODE, self.app.acquire_read_mode
        )
        self.set_buttons_styles()
        self.app.reader_data = deepcopy(DEFAULT_READER_DATA)
        ReadDataControls.handle_widgets_visibility(
            self.app, self.app.acquire_read_mode == "read"
        )
        self.app.gt_plots_to_show = []        
        self.app.settings.setValue(SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(self.app.gt_plots_to_show))         

    def on_read_btn_pressed(self, checked):
        from components.intensity_tracing_controller import IntensityTracingButtonsActions 
        IntensityTracingButtonsActions.clear_plots(self.app)
        self.app.control_inputs[ACQUIRE_BUTTON].setChecked(not checked)
        self.app.control_inputs[READ_BUTTON].setChecked(checked)
        self.app.acquire_read_mode = "read" if checked else "acquire"
        self.app.settings.setValue(
            SETTINGS_ACQUIRE_READ_MODE, self.app.acquire_read_mode
        )
        self.set_buttons_styles()
        ReadDataControls.handle_widgets_visibility(
            self.app, self.app.acquire_read_mode == "read"
        )

class ExportPlotImageButton(QWidget):
    def __init__(self, app, show = True, parent=None):
        super().__init__(parent)
        self.app = app
        self.show = show
        self.data = None
        self.export_img_button = self.create_button()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.export_img_button)
        self.setLayout(layout)
        
    def create_button(self):
        export_img_button = QPushButton()
        export_img_button.setIcon(
            QIcon(resource_path("assets/save-img-icon.png"))
        )
        export_img_button.setIconSize(QSize(30, 30))
        export_img_button.setStyleSheet("background-color: #FB8C00; padding: 0 14px;")
        export_img_button.setFixedHeight(55)
        export_img_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_img_button.clicked.connect(self.on_export_plot_image)
        button_visible = ReadDataControls.read_bin_metadata_enabled(self.app) and self.show
        export_img_button.setVisible(button_visible)
        self.app.control_inputs[EXPORT_PLOT_IMG_BUTTON] = export_img_button
        return export_img_button
    
    
    def on_export_plot_image(self):
        g2_correlations, lag_index = ReadData.prepare_fcs_data_for_export_img(self.app)
        plot = plot_fcs_data(g2_correlations, lag_index, show_plot=False)
        ReadData.save_plot_image(plot)        
  
   

class TimeTaggerWidget(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        write_data = self.app.write_data
        time_tagger_container = QWidget()
        time_tagger_container.setObjectName("container")
        time_tagger_container.setStyleSheet(GUIStyles.time_tagger_style())
        time_tagger_container.setFixedHeight(48)
        time_tagger_container.setContentsMargins(0, 0, 0, 0)
        time_tagget_layout = QHBoxLayout()
        time_tagget_layout.setSpacing(0)
        # time tagger icon
        pixmap = QPixmap(resource_path("assets/time-tagger-icon.png")).scaledToWidth(25)
        icon = QLabel(pixmap=pixmap)
        # time tagger checkbox
        time_tagger_checkbox = QCheckBox("TIME TAGGER")
        time_tagger_checkbox.setChecked(self.app.time_tagger)
        time_tagger_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        time_tagger_checkbox.toggled.connect(
            lambda checked: self.on_time_tagger_state_changed(
                checked
            )
        )        
        time_tagget_layout.addWidget(time_tagger_checkbox)
        time_tagget_layout.addWidget(icon)
        time_tagger_container.setLayout(time_tagget_layout)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(time_tagger_container)
        self.app.widgets[TIME_TAGGER_WIDGET] = self
        self.setLayout(main_layout)
        self.setVisible(write_data)
        
    def on_time_tagger_state_changed(self, checked):
        self.app.time_tagger = checked  
    
    
    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def get_export_options(self):
        return {
               "intensity_tracing": self.intensity_tracing_checkbox.isChecked(),
                "fcs": self.fcs_checkbox.isChecked(),
                "time_tagger": self.time_tagger_checkbox.isChecked(),
            }
        
    def update_from_settings(self):
        self.intensity_tracing_checkbox.setChecked(self.app.settings.value(SETTINGS_EXPORT_INTENSITY_TRACING, DEFAULT_EXPORT_INTENSITY_TRACING))
        self.fcs_checkbox.setChecked(self.app.settings.value(SETTINGS_EXPORT_FCS, DEFAULT_EXPORT_FCS))
        self.time_tagger_checkbox.setChecked(self.app.settings.value(SETTINGS_TIME_TAGGER, DEFAULT_TIME_TAGGER))




# USED BY MULTI SELECT DROPDOWN
class IconRightDelegate(QStyledItemDelegate):
    """
    Custom delegate for rendering multi-select dropdown items with checkboxes and icons.
    
    This delegate provides a custom rendering layout for QComboBox items with the following features:
    - Checkboxes positioned on the left side (orange when checked, gray border when unchecked)
    - Item text displayed in the center
    - Optional icons displayed on the right side
    - Custom background colors for different states (selected, hover, default)
    - Interactive checkbox toggling via mouse clicks
    
    The delegate overrides three main methods:
    - paint(): Custom rendering of item appearance including checkbox, text, and icon
    - sizeHint(): Defines the size of each item (40px height)
    - editorEvent(): Handles mouse click events for checkbox toggling
    
    Parameters:
        parent (QWidget, optional): Parent widget, typically the QComboBox using this delegate
    
    Visual Layout:
        [Checkbox] [Item Text]                    [Icon]
         (left)     (center)                     (right)
    
    Color Scheme:
        - Checked checkbox: #FB8C00 (orange) with white checkmark
        - Unchecked checkbox: #8c8c8c (gray) border, transparent fill
        - Selected item background: #FB8C00 (orange)
        - Hover item background: #2a2a2a (dark gray)
        - Default item background: #1e1e1e (very dark gray)
    """
    
    def paint(self, painter, option, index):
        painter.save()
        
        text = index.data(Qt.ItemDataRole.DisplayRole)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        checkState = index.data(Qt.ItemDataRole.CheckStateRole)
        
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        
       

        
        margin = 8
        checkbox_size = 18
        icon_size = 20
        spacing = 8
        
        checkbox_rect = QRect(
            option.rect.left() + margin,
            option.rect.top() + (option.rect.height() - checkbox_size) // 2,
            checkbox_size,
            checkbox_size
        )
        
        if checkState == Qt.CheckState.Checked:
            painter.setPen(QColor("#FB8C00"))
            painter.setBrush(QColor("#FB8C00"))
            painter.drawRoundedRect(checkbox_rect, 3, 3)
            
            painter.setPen(QColor("#ffffff"))
            painter.setRenderHint(painter.RenderHint.Antialiasing)
            pen = painter.pen()
            pen.setWidth(2)
            painter.setPen(pen)
            
            check_points = [
                QPoint(checkbox_rect.left() + 4, checkbox_rect.top() + 9),
                QPoint(checkbox_rect.left() + 7, checkbox_rect.top() + 12),
                QPoint(checkbox_rect.left() + 14, checkbox_rect.top() + 5)
            ]
            painter.drawPolyline(check_points)
        else:
            painter.setPen(QColor("#8c8c8c"))
            painter.setBrush(Qt.GlobalColor.transparent)
            painter.drawRoundedRect(checkbox_rect, 3, 3)
        
        has_icon = icon and isinstance(icon, QIcon) and not icon.isNull()
        icon_space = icon_size + spacing if has_icon else 0
        
        text_x = option.rect.left() + margin + checkbox_size + spacing
        text_width = option.rect.width() - margin * 2 - checkbox_size - spacing - icon_space
        text_rect = QRect(
            text_x,
            option.rect.top(),
            text_width,
            option.rect.height()
        )
        
        painter.setPen(QColor("#f8f8f8"))
        painter.setFont(option.font)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text
        )
        
        if has_icon:
            icon_x = option.rect.right() - margin - icon_size
            icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2
            icon_rect = QRect(icon_x, icon_y, icon_size, icon_size)
            icon.paint(painter, icon_rect)
        
        painter.restore()
    
    def sizeHint(self, option, index):
        return QSize(option.rect.width() if option.rect.width() > 0 else 200, 40)
    
    def editorEvent(self, event, model, option, index):
        """Gestisce i click sulle checkbox"""
        if event.type() == QEvent.Type.MouseButtonRelease:
            if option.rect.contains(event.pos()):
                current_state = index.data(Qt.ItemDataRole.CheckStateRole)
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
                
                if option.widget and hasattr(option.widget, 'view'):
                    option.widget.view().viewport().update()
                
                return True
        
        return False  

          
class MultiSelectDropdown(QComboBox):
    """
    A custom QComboBox widget that supports multiple item selection with checkboxes.
    
    This dropdown component allows users to select multiple items simultaneously using checkboxes.
    Each item can optionally display an icon on the right side. The component uses the custom
    IconRightDelegate for rendering items with orange checkboxes when selected.
    
    Features:
    - Multiple item selection via checkboxes
    - Optional icons for each item (displayed on the right)
    - Custom styling with orange accent color
    - Animated dropdown arrow (down when closed, up when open)
    - Rounded corners that adapt to open/closed state
    
    Parameters:
        parent (QWidget, optional): Parent widget. Defaults to None.
    """
    
    def __init__(self, parent=None):
      
        super().__init__(parent)   

        model = QStandardItemModel()
        self.setModel(model)
        
        self.setIconSize(QSize(20, 20))
        
        self.setItemDelegate(IconRightDelegate(self))
        
        self.setStyleSheet(GUIStyles.multi_select_dropdown_style())

   

    def addItems(self, items, itemList=None):
        """
        Add multiple items to the dropdown at once.
        
        Iterates through the items list and adds each item with its corresponding
        userData (if provided).

        Parameters:
            items (list): List of string labels to display in the dropdown
            itemList (list, optional): List of user data objects corresponding to each item.
                                      Can be icon paths (*.png) or custom data. Defaults to None.
        """
        for indx, text in enumerate(items):
            try:
                data = itemList[indx] if itemList else None
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def addItem(self, text, userData=None):
        """
        Add a single item to the dropdown with optional icon or custom data.
        
        Creates a new item with a checkbox (initially unchecked). If userData is a path
        to a PNG file, it will be displayed as an icon on the right side of the item.
        Otherwise, userData is stored as UserRole data for later retrieval.
        
        Parameters:
            text (str): The display text for the item
            userData (str or object, optional): Either a file path to a PNG icon to display,
                                               or custom data to associate with the item.
                                               Defaults to None.
        
        Icon Behavior:
            - If userData ends with '.png', it's treated as an icon path
            - Icon is scaled to 20x20 pixels with smooth transformation
            - If userData is not a PNG path, it's stored as custom data

        """
        item = QStandardItem()
        item.setText(text)
        
        if userData is not None and isinstance(userData, str) and userData.endswith('.png'):
            icon_pixmap = QPixmap(userData)
            if not icon_pixmap.isNull():
                scaled_pixmap = icon_pixmap.scaled(
                    20, 20, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                icon = QIcon(scaled_pixmap)
                item.setIcon(icon)
        elif userData is not None:
            item.setData(userData, Qt.ItemDataRole.UserRole)
        
        # Enable checkbox for the item
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        
        self.model().appendRow(item)
    
    def getCheckedItems(self):
        """
        Get a list of text labels for all checked items.
        
        Iterates through all items in the dropdown and returns the display text
        of items that have their checkbox checked.
        
        Returns:
            list: List of strings containing the text labels of checked items.
                 Returns empty list if no items are checked.

        """
        checked = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.append(item.text())
        return checked
    
    def getCheckedItemsData(self):
        """
        Get a list of UserRole data for all checked items.
        
        Iterates through all items in the dropdown and returns the custom data
        (stored as UserRole) of items that have their checkbox checked. This is
        useful when items were added with custom data objects instead of icon paths.
        
        Returns:
            list: List of user data objects associated with checked items.
                 Returns empty list if no items are checked or if items don't have UserRole data.
        
        Note:
            Items that were added with PNG icon paths won't have UserRole data,
            so they may return None values in the list.

        """
        checked = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                checked.append(data)
        return checked


  

    
