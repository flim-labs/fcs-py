from PyQt6.QtGui import QColor, QPalette, QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtWidgets import QStyleFactory



class GUIStyles:
    @staticmethod
    def set_default_theme(theme):
        QApplication.setStyle(QStyleFactory.create(theme))

    @staticmethod
    def customize_theme(window, bg = QColor(28, 28, 28, 128), fg = QColor(255, 255, 255)):
        palette = QPalette()
        background_color = bg
        palette.setColor(QPalette.ColorRole.Window, background_color)
        palette.setColor(QPalette.ColorRole.WindowText, fg)
        window.setPalette(palette)

    @staticmethod
    def set_fonts():
        general_font = QFont("Montserrat", 10)
        QApplication.setFont(general_font)

    @staticmethod
    def set_label_style(color="#f8f8f8"):
        return """
            QLabel{
                color: #f8f8f8;
                font-family: "Montserrat";
            }
        """

    @staticmethod
    def set_main_title_style():
        return """
            QLabel{
                color: #23F3AB;
                font-family: "Montserrat";
                font-size: 40px;
                font-weight: 100;
                font-style: italic;
            }
        """

    @staticmethod
    def button_style(color_base, color_border, color_hover, color_pressed, min_width):
        return f"""
            QPushButton {{
                background-color: {color_base};
                border: 1px solid {color_border};
                font-family: "Montserrat";
                color: white;
                letter-spacing: 0.1em;
                min-width: {min_width};
                padding: 10px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}

        
            QPushButton:hover {{
                background-color: {color_hover};
                border: 2px solid {color_hover};
            }}

            QPushButton:focus {{
                background-color: {color_pressed};
                border: 2px solid {color_pressed};
            }}

            QPushButton:pressed {{
                background-color: {color_pressed};
                border: 2px solid {color_pressed};
            }}
            
            QPushButton:disabled {{
                background-color: #cecece;
                border: 2px solid #cecece;
                color: #8c8b8b;
            }}
        """

    @staticmethod
    def _set_button_style(button, color_dict, min_width):
        color_base, color_border, color_hover, color_pressed = (
            color_dict["base"],
            color_dict["border"],
            color_dict["hover"],
            color_dict["pressed"],
        )
        button.setStyleSheet(
            GUIStyles.button_style(
                color_base, color_border, color_hover, color_pressed, min_width
            )
        )

    @staticmethod
    def set_start_btn_style(button):
        color_dict = {
            "base": "#31c914",
            "border": "#31c914",
            "hover": "#57D33D",
            "pressed": "#7FE777",
        }
        GUIStyles._set_button_style(button, color_dict, min_width="150px")

    @staticmethod
    def set_stop_btn_style(button):
        color_dict = {
            "base": "#FFA726",
            "border": "#FFA726",
            "hover": "#FB8C00",
            "pressed": "#E65100",
        }
        GUIStyles._set_button_style(button, color_dict, min_width="150px")

    @staticmethod
    def set_reset_btn_style(button):
        color_dict = {
            "base": "#3b3b3b",
            "border": "#3b3b3b",
            "hover": "#555555",
            "pressed": "#292929",
        }
        GUIStyles._set_button_style(button, color_dict, min_width="100px")

    @staticmethod
    def set_config_btn_style(button):
        color_dict = {
            "base": "black",
            "border": "#FFA726",
            "hover": "#FB8C00",
            "pressed": "#E65100",
        }
        GUIStyles._set_button_style(button, color_dict, min_width="100px")

    @staticmethod
    def set_checkbox_style():
        return """
            QCheckBox {
                spacing: 5px;
                color: #f8f8f8;
                font-family: "Montserrat";
                font-size: 11px;
                letter-spacing: 0.1em;
                border: 1px solid #252525;
                border-radius: 5px;
                padding: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px;  
            }

            QCheckBox::indicator:unchecked {
                background-color: #6b6a6a;
            }

            QCheckBox::indicator:checked {
                background-color: #8d4ef2;
            }
        """


    @staticmethod    
    def set_tau_checkbox_style():
        return """
            QCheckBox {
                spacing: 5px;
                color: #f8f8f8;
                font-family: "Montserrat";
                font-size: 12px;
                letter-spacing: 0.1em;
                border-radius: 5px;
            }
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                border-radius: 6px;  
            }

            QCheckBox::indicator:unchecked {
                background-color: #6b6a6a;
            }

            QCheckBox::indicator:checked {
                background-color: #f5f538;
            }
        """


    @staticmethod    
    def checkbox_wrapper_style():
        return """
            QWidget#ch_checkbox_wrapper, QWidget#tau_checkbox_wrapper{
                border: 1px solid #222222;
                background-color: transparent;
                padding: 0;
            } 
            QWidget#tau_checkbox_wrapper{
                border-radius: 5px;
            } 
            QWidget{
                color: #f8f8f8;
                font-family: "Montserrat";
                font-size: 12px;
                padding: 0;
            }        
        """

    @staticmethod       
    def toggle_collapse_button():
        return """
            QPushButton{
                background-color: transparent;
                border-radius: 15px;
                qproperty-iconSize: 15px;
                border: 1px solid #808080;
            } 
        """    


    @staticmethod
    def set_input_number_style():
        return """
            QDoubleSpinBox, QSpinBox, QLineEdit {
                color: #f8f8f8;
                font-family: "Montserrat";
                font-size: 12px;
                padding: 8px;
                min-width: 120px;
                border-radius: 5px;
                background-color: transparent;
            }
            QDoubleSpinBox, QSpinBox {
                border: 1px solid #31c914;

            }
            QLineEdit {
                border: 1px solid #f5f538;

            }
            QDoubleSpinBox:disabled, QSpinBox:disabled {
            color: #404040;  
            border-color: #404040;
            }        
        """

    @staticmethod
    def set_input_select_style():
        return """
            QComboBox {
                color: #f8f8f8;
                font-family: "Montserrat";
                font-size: 12px;
                padding: 8px;
                min-width: 120px;
                border: 1px solid #31c914;
                border-radius: 5px;
                background-color: transparent;
            }
            QSpinBox:disabled {
                color: #404040;  
                border-color: #404040;
            } 
            QComboBox:on { 
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }

           QComboBox QAbstractItemView {
            font-family: "Montserrat";
            border: 1px solid #31c914;
            border-bottom-left-radius: 5px;
            border-bottom-right-radius: 5px;
            background-color: #181818;
            color: #f8f8f8;
            selection-background-color: #31c914;
            }   
        """

    @staticmethod
    def set_msg_box_style():
        return """
            QMessageBox {
                background-color: #080808;   
            }
            QMessageBox QLabel {
                color: #f8f8f8;
                font-family: "Montserrat";
                font-weight: 300;
                font-size: 16px;
            }
            QMessageBox QIcon {
                width: 20px;
            }  
            QMessageBox QPushButton {
                background-color: #181818;
                color: white;
                width: 150px;
                padding: 12px;
                font-size: 14px;
                font-family: "Montserrat";
            }   
                 
        """

    @staticmethod
    def set_cps_label_style():
        return """
            QLabel{
                color: white;
                font-weight: 700;
                font-family: "Montserrat";
                font-size: 22px;
            }
        """

    @staticmethod
    def set_context_menu_style(base, selected, pressed):
        return f"""

        QWidget {{
            background-color: #181818;  
        }}
        
        QMenu {{
            margin: 0;   
            padding: 5px;
            border-radius: 20px;
            background: #181818;       
        }}

        QMenu::item {{
            background-color: {base}; 
            color: white; 
            height: 20px;
            width: 60px;
            margin: 5px 0px 5px 0px;
            border-radius: 4px;   
            font-family: "Montserrat";
            font-size: 14px;
            font-weight: bold;
            padding:10px 13px 10px 10px;
            min-width:120px
        }}

        QMenu::item:selected {{
            background-color: {selected};  
         }}
        QMenu::item:pressed {{
            background-color: {pressed};  
         }}

        """

    @staticmethod    
    def correlation_menu(width):
        return f"""

        QWidget {{
            background-color: #3b3b3b;  
            width: {width};
        }}
        
        QMenu {{
            margin: 0;   
            padding: 5px;
            width: {width};
            border-radius: 4px;
            background: #3b3b3b; 
              
        }}

        QMenu::item {{
            color: white; 
            margin: 0;
            width: {width};
            border-radius: 4px;   
            font-family: "Montserrat";
            font-size: 12px;
            font-weight: bold;
            padding: 8px 12px 8px 12px;
        }}

        QMenu::item:pressed {{
            color: #8d4ef2;
        }}

        """

    
    @staticmethod
    def gt_calc_mode_btn_style():
        return f"""
            QPushButton {{
                font-family: "Montserrat";
                letter-spacing: 0.1em;
                padding: 10px 12px;
                font-size: 11px;
                font-weight: bold;
                background-color: #cecece;
                color: #8c8b8b;
            }}

            QPushButton:checked {{
                background-color: #FB8C00;
                color: white;
            }}

            QPushButton#realtime_btn{{
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                min-width: 80px;

            }}
            QPushButton#post_processing_btn{{ 
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                min-width: 120px;   
                
            }}
        """

    @staticmethod    
    def add_tau_btn_style():
        return f"""
            QPushButton, QPushButton:released {{
                font-family: "Montserrat";
                letter-spacing: 0.1em;
                padding: 10px 12px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                background-color: #f5f538;
                border: 2px solid #f5f538;
                color: black;
            }}
            
            QPushButton:hover {{
                background-color: #d4d400;
                border: 2px solid #d4d400;
            }}

            QPushButton:focus {{
                background-color: #c8b900;
                border: 2px solid #c8b900;
            }}

            QPushButton:pressed {{
                background-color: #c8b900;
                border: 2px solid #c8b900;
            }}

            QPushButton:disabled {{
                background-color: #cecece;
                border: 2px solid #cecece;
                color: #8c8b8b;
            }}
        """

    @staticmethod           
    def remove_tau_button():
        return """
            QPushButton{
                background-color: #990000;
                border-radius: 5px;
                qproperty-iconSize: 8px;
            } 
        """ 

    @staticmethod       
    def correlations_btn_style():
        return f"""
            QPushButton, QPushButton:released {{
                font-family: "Montserrat";
                letter-spacing: 0.1em;
                padding: 10px 12px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                background-color: #31c914;
                border: 2px solid #31c914;
                color: white;
            }}
            
            QPushButton:hover {{
                background-color: #57D33D;
                border: 2px solid #57D33D;
            }}

            QPushButton:focus {{
                background-color: #7FE777;
                border: 2px solid #7FE777;
            }}

            QPushButton:pressed {{
                background-color: #7FE777;
                border: 2px solid #7FE777;
            }}

            QPushButton:disabled {{
                background-color: #cecece;
                border: 2px solid #cecece;
                color: #8c8b8b;
            }}
        """

    @staticmethod
    def set_correlation_table_style():
        return f"""
            QTableWidget {{
                background-color: #141414;
                color: white;
                border: none;
                gridline-color: #3b3b3b;
                
            }}
            QTableWidget::item {{
                background-color: #141414;
                text-align: center;
                border: none;
                
            }}
            QHeaderView::section:vertical {{
                background-color: #222222;
                color: white;

               
            }}
            QHeaderView::section:horizontal {{
                background-color: #222222;
                color: white;
               
            }}
            QHeaderView::section {{
                padding: 14px;
               
            }}
            QTableCornerButton::section{{
                background-color: #141414;
            }}
        """  

    @staticmethod    
    def set_correlations_checkbox_style():
        return """
            QCheckBox::indicator {
                width: 0;
                height: 0;
                border: 0; 
            }

            QCheckBox::indicator:unchecked {
                background-color: transparent;
            }

            QCheckBox::indicator:checked {
                background-color: transparent;
            }
        """      
                