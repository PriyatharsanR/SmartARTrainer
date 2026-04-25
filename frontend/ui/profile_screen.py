"""
User Profile Screen with Edit Capabilities
Professional UI with glassmorphism and matching theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QLineEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from backend.models.data_manager import get_trainee, update_trainee
from backend.models.data_manager import plan_level_and_index

class ProfileScreen(QWidget):
    """User profile and settings screen"""

    backRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trainee_id = None
        self.profile = {}
        self.edit_mode = False
        self.init_ui()

    def set_user(self, user_data):
        """Set user ID and load data"""
        self.trainee_id = user_data.get("trainee_id")
        self.load_data()

    def load_data(self):
        """Fetch latest trainee data from DB"""
        if not self.trainee_id:
            return
            
        self.profile = get_trainee(self.trainee_id)
        if self.profile:
            self.refresh_display()

    def init_ui(self):
        self.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Navigation Bar (Consistent)
        nav_bar = QFrame()
        nav_bar.setFixedHeight(80)
        nav_bar.setStyleSheet("""
            QFrame {
                background: rgba(15, 12, 41, 0.4);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(50, 0, 50, 0)

        app_title = QLabel("SmartARTrainer")
        app_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #667eea; background: transparent;")
        nav_layout.addWidget(app_title)
        
        nav_layout.addStretch()

        btn_style = """
            QPushButton {
                background: %s;
                color: white;
                border: %s;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.3);
            }
        """
        
        self.dash_btn = QPushButton("Workout")
        self.dash_btn.setStyleSheet(btn_style % ("transparent", "1px solid rgba(255, 255, 255, 0.4)"))
        self.dash_btn.clicked.connect(self.backRequested.emit)
        
        self.analytics_btn = QPushButton("Dashboard")
        self.analytics_btn.setStyleSheet(btn_style % ("transparent", "1px solid rgba(255, 255, 255, 0.4)"))
        self.analytics_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analytics_btn.clicked.connect(self.on_analytics_clicked)
        
        self.profile_btn = QPushButton("Profile")
        self.profile_btn.setStyleSheet(btn_style % ("rgba(102, 126, 234, 0.8)", "none"))

        nav_layout.addWidget(self.analytics_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.dash_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.profile_btn)
        
        main_layout.addWidget(nav_bar)

        # 2. Page Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(50, 30, 50, 40)
        content_layout.setSpacing(25)

        # Header Title and Edit Button
        header_row = QHBoxLayout()
        title = QLabel("My Profile")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_row.addWidget(title)
        
        header_row.addStretch()
        
        self.edit_btn = QPushButton("Edit Profile")
        self.edit_btn.setFixedSize(140, 45)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        self.edit_btn.clicked.connect(self.toggle_edit)
        header_row.addWidget(self.edit_btn)
        
        content_layout.addLayout(header_row)

        # Main Layout Grid
        grid = QGridLayout()
        grid.setSpacing(30)

        # --- LEFT: IDENTITY CARD ---
        self.id_card = QFrame()
        self.id_card.setFixedWidth(400)
        self.id_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
            }
        """)
        id_layout = QVBoxLayout(self.id_card)
        id_layout.setContentsMargins(30, 40, 30, 40)
        id_layout.setSpacing(20)

        self.avatar = QLabel("A")
        self.avatar.setFixedSize(120, 120)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
        self.avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
            color: white;
            border-radius: 60px;
        """)
        id_layout.addWidget(self.avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name Display/Input
        self.name_label = QLabel("Loading...")
        self.name_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: white; background: transparent;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.name_input = QLineEdit()
        self.name_input.setFont(QFont("Segoe UI", 16))
        self.name_input.setStyleSheet("background: rgba(255,255,255,0.1); color: white; padding: 8px; border-radius: 8px;")
        self.name_input.setVisible(False)
        
        id_layout.addWidget(self.name_label)
        id_layout.addWidget(self.name_input)

        # Email
        self.email_label = QLabel("user@example.com")
        self.email_label.setStyleSheet("color: white; background: transparent; font-size: 15px; font-weight: bold;")
        self.email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_layout.addWidget(self.email_label)

        id_layout.addSpacing(20)
        
        # Details List (DOB, Gender)
        details_box = QFrame()
        details_box.setStyleSheet("background: rgba(0,0,0,0.15); border-radius: 16px; border: none;")
        details_layout = QGridLayout(details_box)
        details_layout.setSpacing(20)
        details_layout.setContentsMargins(20, 20, 20, 20)

        label_style = "color: rgba(255, 255, 255, 0.85); font-size: 15px; font-weight: 500;"
        value_style = "color: white; font-size: 16px; font-weight: bold;"

        dob_title = QLabel("Date of Birth")
        dob_title.setStyleSheet(label_style)
        details_layout.addWidget(dob_title, 0, 0)
        
        self.dob_label = QLabel("2000-01-01")
        self.dob_label.setStyleSheet(value_style)
        self.dob_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        details_layout.addWidget(self.dob_label, 0, 1)

        self.dob_input = QLineEdit()
        self.dob_input.setStyleSheet("background: #2d3748; color: white; border-radius: 5px; padding: 4px;")
        self.dob_input.setVisible(False)
        details_layout.addWidget(self.dob_input, 0, 1)

        gender_title = QLabel("Gender")
        gender_title.setStyleSheet(label_style)
        details_layout.addWidget(gender_title, 1, 0)
        
        self.gender_label = QLabel("Male")
        self.gender_label.setStyleSheet(value_style)
        self.gender_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        details_layout.addWidget(self.gender_label, 1, 1)

        self.gender_input = QComboBox()
        self.gender_input.addItems(["Male", "Female", "Other"])
        self.gender_input.setStyleSheet("background: #2d3748; color: white; border-radius: 5px; padding: 2px;")
        self.gender_input.setVisible(False)
        details_layout.addWidget(self.gender_input, 1, 1)

        id_layout.addWidget(details_box)
        grid.addWidget(self.id_card, 0, 0)

        # --- RIGHT: STATS GRID ---
        stats_pane = QFrame()
        stats_pane.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
            }
        """)
        stats_main_layout = QVBoxLayout(stats_pane)
        stats_main_layout.setContentsMargins(30, 30, 30, 30)

        stats_head = QLabel("Fitness Profile")
        stats_head.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        stats_head.setStyleSheet("color: #667eea; background: transparent;")
        stats_main_layout.addWidget(stats_head)
        stats_main_layout.addSpacing(20)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)

        self.h_box = self.create_stat_widget("Height", "175 cm")
        self.w_box = self.create_stat_widget("Weight", "70 kg")
        self.d_box = self.create_stat_widget("Workout Duration", "45 min")
        self.f_box = self.create_stat_widget("Weekly Frequency", "4 days")

        stats_grid.addWidget(self.h_box, 0, 0)
        stats_grid.addWidget(self.w_box, 0, 1)
        stats_grid.addWidget(self.d_box, 1, 0)
        stats_grid.addWidget(self.f_box, 1, 1)

        stats_main_layout.addLayout(stats_grid)
        stats_main_layout.addSpacing(30)

        # Current Plan Card
        plan_card = QFrame()
        plan_card.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);")
        plan_layout = QVBoxLayout(plan_card)
        
        self.plan_val = QLabel("Intermediate")
        self.plan_val.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.plan_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plan_val.setStyleSheet("color: white; border: none;")
        plan_layout.addWidget(self.plan_val)

        p_lbl = QLabel("Current Plan")
        p_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_lbl.setStyleSheet("color: #cbd5e0; border: none; font-size: 16px;")
        plan_layout.addWidget(p_lbl)

        stats_main_layout.addWidget(plan_card)

        grid.addWidget(stats_pane, 0, 1)
        content_layout.addLayout(grid)

        scroll.setWidget(content_wrapper)
        main_layout.addWidget(scroll)

    def create_stat_widget(self, title, value):
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 18px;
                padding: 20px;
            }
        """)
        layout = QVBoxLayout(box)
        
        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setStyleSheet("color: white; border: none;")
        layout.addWidget(val)
        
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #cbd5e0; text-transform: uppercase; font-size: 13px; font-weight: bold; border: none;")
        layout.addWidget(lbl)
        
        # Add input for editing
        inp = QLineEdit()
        inp.setStyleSheet("background: #2d3748; color: white; border-radius: 8px; padding: 5px;")
        inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inp.setVisible(False)
        layout.addWidget(inp)
        
        box.value_label = val
        box.input_field = inp
        return box

    def toggle_edit(self):
        if not self.edit_mode:
            # Enter Edit Mode - Only for Personal Details
            self.edit_mode = True
            self.edit_btn.setText("Save Changes")
            

            # Toggle Visibility - Personal Details Only
            self.name_label.setVisible(False)
            self.name_input.setVisible(True)
            self.name_input.setText(self.profile.get("name", ""))

            self.dob_label.setVisible(False)
            self.dob_input.setVisible(True)
            self.dob_input.setText(self.profile.get("dob", ""))
            
            self.gender_label.setVisible(False)
            self.gender_input.setVisible(True)
            self.gender_input.setCurrentText(self.profile.get("gender", "Male"))

            # Toggle Visibility - Fitness Stats
            for box in [self.h_box, self.w_box, self.d_box, self.f_box]:
                box.value_label.setVisible(False)
                box.input_field.setVisible(True)
            
            self.h_box.input_field.setText(str(self.profile.get("height", "")))
            self.w_box.input_field.setText(str(self.profile.get("weight", "")))
            self.d_box.input_field.setText(str(self.profile.get("workout_duration", "")))
            self.f_box.input_field.setText(str(self.profile.get("weekly_frequency", "")))
        else:
            self.save_data()

    def save_data(self):
        """Save changes to DB and exit edit mode - Personal Details Only"""
        try:
            # Only update personal details, not fitness profile
            updates = {
                "name": self.name_input.text().strip(),
                "dob": self.dob_input.text().strip(),
                "gender": self.gender_input.currentText(),
                "height": self.h_box.input_field.text().strip(),
                "weight": self.w_box.input_field.text().strip(),
                "workout_duration": self.d_box.input_field.text().strip(),
                "weekly_frequency": self.f_box.input_field.text().strip()
            }
            
            success, msg = update_trainee(self.trainee_id, **updates)
            if success:
                QMessageBox.information(self, "Success", "Profile updated successfully!")
                self.edit_mode = False
                self.edit_btn.setText("Edit Profile")
                self.load_data() # Reload from DB
            else:
                QMessageBox.critical(self, "Error", f"Failed to update profile: {msg}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")

    def refresh_display(self):
        """Update UI elements with data from self.profile"""
        self.name_label.setText(self.profile.get("name", "User"))
        self.avatar.setText(self.profile.get("name", "U")[0].upper())
        self.email_label.setText(self.profile.get("email", "No Email"))
        self.dob_label.setText(self.profile.get("dob", "Not Set"))
        self.gender_label.setText(self.profile.get("gender", "Not Set"))
        
        self.h_box.value_label.setText(f"{self.profile.get('height', 0)} cm")
        self.w_box.value_label.setText(f"{self.profile.get('weight', 0)} kg")
        self.d_box.value_label.setText(f"{self.profile.get('workout_duration', 0)} min")
        self.f_box.value_label.setText(f"{self.profile.get('weekly_frequency', 0)} days")
        
        self.plan_val.setText(self.profile.get("fitness_level") or "Standard Plan")

        plan_id = self.profile.get("plan_id", 1)
        main_level, _ = plan_level_and_index(plan_id)
        self.plan_val.setText(main_level) 

        # Ensure inputs are hidden and labels visible
        self.name_label.setVisible(True); self.name_input.setVisible(False)
        self.dob_label.setVisible(True); self.dob_input.setVisible(False)
        self.gender_label.setVisible(True); self.gender_input.setVisible(False)
        for b in [self.h_box, self.w_box, self.d_box, self.f_box]:
            b.value_label.setVisible(True); b.input_field.setVisible(False)

    def on_analytics_clicked(self):
        """Notify main window to show analytics"""
        main_win = self.window()
        if hasattr(main_win, "show_analytics"):
            main_win.show_analytics()
