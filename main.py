"""
SmartARTrainer - AI-Powered Fitness Training Application
Main entry point
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from frontend.ui.main_window import MainWindow

def main():
    """Main application entry point"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("SmartARTrainer")
    app.setOrganizationName("SmartARTrainer")
    
    try:
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon("frontend/assets/logo.png"))
    except Exception as e:
        print(f"Icon load error: {e}")

    # Apply global stylesheet
    from frontend.utils.styles import get_main_stylesheet
    app.setStyleSheet(get_main_stylesheet())
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
