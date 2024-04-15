from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QComboBox

class SelectControl:
    @staticmethod
    def setup(label, selectedValue, container, options, event_callback, spacing=20, control_layout="vertical", label_style = None):
        q_label = QLabel(label)
        if label_style is not None:
            q_label.setStyleSheet(label_style)
        control = QVBoxLayout() if control_layout == 'vertical' else QHBoxLayout()
        input = QComboBox()
        for value in options:
            input.addItem(str(value))
        input.setCurrentText(str(selectedValue))
        input.currentIndexChanged.connect(event_callback)
        control.addWidget(q_label)
        control.addWidget(input)
        container.addLayout(control)
        if spacing:
            container.addSpacing(spacing)
        return control, input