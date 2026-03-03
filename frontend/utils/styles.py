"""
Centralized stylesheet definitions for SmartARTrainer application
"""

def get_main_stylesheet():
    """Returns the main application stylesheet with modern dark theme"""
    return """
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                   stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
    }
    
    QWidget {
        color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }
    
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: bold;
        font-size: 14px;
        min-height: 20px;
    }
    
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #764ba2, stop:1 #667eea);
    }
    
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #5a3d7a, stop:1 #4e5fb8);
    }
    
    QPushButton:disabled {
        background: #3a3a3a;
        color: #666666;
    }
    
    QPushButton#cancelButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #ff6b6b, stop:1 #ee5a6f);
    }
    
    QPushButton#cancelButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #ee5a6f, stop:1 #ff6b6b);
    }
    
    QPushButton#navButton {
        background: transparent;
        border: 2px solid #667eea;
        border-radius: 8px;
        padding: 10px 20px;
        color: #667eea;
        font-weight: bold;
    }
    
    QPushButton#navButton:hover {
        background: rgba(102, 126, 234, 0.2);
    }
    
    QPushButton#navButton:checked {
        background: #667eea;
        color: white;
    }
    
    QLineEdit {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 10px 15px;
        color: white;
        font-size: 14px;
    }
    
    QLineEdit:focus {
        border: 2px solid #667eea;
        background: rgba(255, 255, 255, 0.15);
    }
    
    QComboBox {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 10px 15px;
        color: white;
        font-size: 14px;
    }
    
    QComboBox:focus {
        border: 2px solid #667eea;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid white;
        margin-right: 10px;
    }
    
    QComboBox QAbstractItemView {
        background: #2d2d44;
        border: 2px solid #667eea;
        selection-background-color: #667eea;
        color: white;
    }
    
    QLabel {
        color: white;
        font-size: 14px;
    }
    
    QLabel#titleLabel {
        font-size: 32px;
        font-weight: bold;
        color: #667eea;
    }
    
    QLabel#subtitleLabel {
        font-size: 18px;
        color: #aaaaaa;
    }
    
    QLabel#appNameLabel {
        font-size: 48px;
        font-weight: bold;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
        -webkit-background-clip: text;
        color: transparent;
    }
    
    QScrollArea {
        border: none;
        background: transparent;
    }
    
    QScrollBar:vertical {
        background: rgba(255, 255, 255, 0.05);
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background: rgba(102, 126, 234, 0.5);
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: rgba(102, 126, 234, 0.8);
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    
    QFrame#exerciseCard {
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
    }
    
    QFrame#exerciseCard:hover {
        background: rgba(255, 255, 255, 0.08);
        border: 2px solid rgba(102, 126, 234, 0.5);
    }
    
    QProgressBar {
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.1);
        text-align: center;
        color: white;
        font-weight: bold;
    }
    
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
        border-radius: 6px;
    }
    
    QTextEdit {
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px;
        color: white;
    }
    
    QRadioButton {
        color: white;
        spacing: 8px;
    }
    
    QRadioButton::indicator {
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.1);
    }
    
    QRadioButton::indicator:checked {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
        border: 2px solid #667eea;
    }
    
    QSpinBox, QDoubleSpinBox {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 8px;
        color: white;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 2px solid #667eea;
    }
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        background: rgba(102, 126, 234, 0.3);
        border-top-right-radius: 6px;
    }
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        background: rgba(102, 126, 234, 0.3);
        border-bottom-right-radius: 6px;
    }
    """

def get_card_style():
    """Returns stylesheet for card-like containers"""
    return """
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
    """

def get_glass_effect_style():
    """Returns glassmorphism effect stylesheet"""
    return """
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        backdrop-filter: blur(10px);
    """
