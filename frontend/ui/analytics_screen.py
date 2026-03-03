from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QPushButton, QSizePolicy, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import MaxNLocator

from backend.models.data_manager import session_analytics, get_trainee_info
from backend.models.data_manager import get_workout_plan

from backend.utils.activity_tracker import is_inactive_30_days, update_last_activity
from backend.models.data_manager import reset_sessions_after_promotion
from backend.models.data_manager import plan_level_and_index



class AnalyticsScreen(QWidget):
    """Analytics screen showing workout completion summary and charts"""
    
    backRequested = pyqtSignal()
    logoutRequested = pyqtSignal() 
        
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trainee_id = None
        self.reset_popup_shown = False
        self.rep_totals = {}  
        self.init_ui()
        
    def set_user(self, user_data):
        """Set user and refresh analytics data"""
        self.trainee_id = user_data.get("trainee_id")
        
        trainee = get_trainee_info(self.trainee_id)
        if trainee:
            self.welcome_label.setText(f"Trainee: {trainee['name']}")

            plan_id = trainee.get("plan_id", 3)
            main_level, _ = plan_level_and_index(plan_id)
            self.plan_label.setText(f"Plan: {main_level}")
            
            plan_id = trainee.get("plan_id", 1)
            plan_data = get_workout_plan(plan_id)
            
            self.plan_targets = self.build_plan_target_map(plan_data)
            
            # Convert plan_data into format expected by calculate_plan_max_points
            plan_dict = {}
            for ex in plan_data:
                name = ex["name"]
                target = ex["target"]
                # Time-based
                if "Time" in name or "Plank" in name or "Cobra" in name:
                    plan_dict[name] = {"duration": target}
                else:
                    plan_dict[name] = {"reps": target}
            self.plan_max_points = self.calculate_plan_max_points(plan_dict)
        
        self.refresh_data()

    def init_ui(self):
        """Initialize the UI"""
        self.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Navigation Bar 
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
        
        
        self.analytics_btn = QPushButton("Dashboard")
        self.analytics_btn.setStyleSheet(btn_style % ("rgba(102, 126, 234, 0.8)", "none"))
        
        self.dash_btn = QPushButton("Workout")
        self.dash_btn.setStyleSheet(btn_style % ("transparent", "1px solid rgba(255, 255, 255, 0.4)"))
        self.dash_btn.clicked.connect(self.backRequested.emit)
        
        self.profile_btn = QPushButton("Profile")
        self.profile_btn.setStyleSheet(btn_style % ("transparent", "1px solid rgba(255, 255, 255, 0.4)"))
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_btn.clicked.connect(self.on_profile_clicked)

        nav_layout.addWidget(self.analytics_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.dash_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.profile_btn)
        main_layout.addWidget(nav_bar)
        

        # Page Content Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(50, 30, 50, 40)
        content_layout.setSpacing(25)
        
        # Header: User Info & Logout
        header_layout = QHBoxLayout()
        titles_layout = QVBoxLayout()

        self.welcome_label = QLabel("Trainee: Loading...")
        self.welcome_label.setFont(QFont("Segoe UI", 50, QFont.Weight.Bold))
        self.welcome_label.setStyleSheet("""
    QLabel {
        color: white;

        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(102,126,234,0.35),
            stop:1 rgba(118,75,162,0.35));

        border-left: 10px solid #667eea;
        border-radius: 18px;

        padding: 18px 28px;
        margin-bottom: 12px;
     
        font-size: 24px;
        letter-spacing: 2px;
    }
""")
        titles_layout.addWidget(self.welcome_label)

        self.plan_label = QLabel("Plan: Personalized")
        self.plan_label.setFont(QFont("Segoe UI", 32))
        self.plan_label.setStyleSheet("""
    QLabel {
        color: #ffffff;

        background: rgba(102,126,234,0.22);

        border: 3px solid rgba(102,126,234,0.6);
        border-radius: 16px;

        padding: 14px 24px;
        font-size: 24px;
        letter-spacing: 1.5px;
    }
""")
        titles_layout.addWidget(self.plan_label)

        header_layout.addLayout(titles_layout)
        header_layout.addStretch()

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setFixedSize(120, 45)
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: white;
                border-radius: 10px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background: rgba(255, 107, 107, 0.15);
                border-color: #ff6b6b;
                color: #ff6b6b;
            }
        """)
        self.logout_btn.clicked.connect(self.logoutRequested.emit)
        header_layout.addWidget(self.logout_btn, alignment=Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(header_layout)
        
        # Title
        title = QLabel("Workout Completion Summary")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        content_layout.addWidget(title)
        
        # Summary Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Total Score Card
        self.total_score_card = self.create_summary_card("Total Score", "0/4800")
        cards_layout.addWidget(self.total_score_card)

        # Remaining Score Card
        self.remaining_score_card = self.create_summary_card("Remaining Score", "4800")
        cards_layout.addWidget(self.remaining_score_card)

        
        cards_layout.addStretch()
        
        content_layout.addLayout(cards_layout)
        
        # WORKOUT CALENDAR / TRACKER
        tracker_section_box = QFrame()
        tracker_section_box.setStyleSheet("""
        QFrame {
            background: rgba(255, 255, 255, 0.04);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.08);
        }
    """)
        
        tracker_layout = QVBoxLayout(tracker_section_box)
        tracker_layout.setContentsMargins(25, 25, 25, 25)
        tracker_layout.setSpacing(15)
        
        title = QLabel("Workout Sessions Tracker")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        tracker_layout.addWidget(title)
        
        grid_frame = QFrame()
        grid_frame.setStyleSheet("background: transparent;")
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(10)
    
        self.session_marks = []  # store labels
    
        for row in range(4):
            for col in range(15):
                session_number = row * 15 + col + 1
                label = QLabel(str(session_number))
                label.setFixedSize(50, 50)   
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255,255,255,0.08);
                    border-radius: 25px;   /* half of size = perfect circle */
                    color: rgba(255,255,255,0.4);
                }
                """)

                # Default selection style
                label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255,255,255,0.08);
                        border-radius: 12px;
                    }
                """)

                self.session_marks.append(label)
                grid_layout.addWidget(label, row, col)

        tracker_layout.addWidget(grid_frame) 
        
        content_layout.addWidget(tracker_section_box)
        

        # Insight Label
        self.insight_label = QLabel("")
        self.insight_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.insight_label.setStyleSheet("color: #e2e8f0; padding: 10px;")
        content_layout.addWidget(self.insight_label)
        
        scroll.setWidget(content_wrapper)
        main_layout.addWidget(scroll)
        
        # ---------- LINE CHARTS SECTION ----------
        charts_section_box = QFrame()
        charts_section_box.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.04);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.08);
            }
        """)

        charts_layout = QVBoxLayout(charts_section_box)
        charts_layout.setContentsMargins(25, 25, 25, 25)
        charts_layout.setSpacing(20)

        title = QLabel("Workout Progress Trends")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        charts_layout.addWidget(title)

        self.line_charts_layout = QGridLayout()
        self.line_charts_layout.setHorizontalSpacing(25)
        self.line_charts_layout.setVerticalSpacing(25)

        charts_layout.addLayout(self.line_charts_layout)
        content_layout.addWidget(charts_section_box)

        accuracy_section_box = QFrame()
        accuracy_section_box.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.04);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.08);
            }
        """)

        accuracy_layout_main = QVBoxLayout(accuracy_section_box)
        accuracy_layout_main.setContentsMargins(25, 25, 25, 25)
        accuracy_layout_main.setSpacing(20)

        title = QLabel("Exercise Accuracy Overview")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        accuracy_layout_main.addWidget(title)

        # LAYOUT ONLY FOR BAR CHART
        self.accuracy_layout = QVBoxLayout()
        accuracy_layout_main.addLayout(self.accuracy_layout)

        content_layout.addWidget(accuracy_section_box)
        
        # Rep-Based Workout Table
        rep_section_box = QFrame()
        rep_section_box.setStyleSheet("background: rgba(255, 255, 255, 0.04); border-radius: 20px; border: 1px solid rgba(255,255,255,0.08);")
        rep_sec_layout = QVBoxLayout(rep_section_box)
        rep_sec_layout.setContentsMargins(25, 25, 25, 25)

        rep_section = QLabel("Rep-Based Workouts")
        rep_section.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        rep_section.setStyleSheet("color: white; border: none;")
        rep_sec_layout.addWidget(rep_section)
        rep_sec_layout.addSpacing(15)
        
        self.rep_table = self.create_workout_table(
            ["Workout", "Total Reps", "Correct Reps", "Wrong Reps"]
        )
        self.rep_table.setMinimumHeight(250)
        rep_sec_layout.addWidget(self.rep_table)
        
        content_layout.addWidget(rep_section_box)

        # Time-Based Workout Table
        time_section_box = QFrame()
        time_section_box.setStyleSheet("background: rgba(255, 255, 255, 0.04); border-radius: 20px; border: 1px solid rgba(255,255,255,0.08);")
        time_sec_layout = QVBoxLayout(time_section_box)
        time_sec_layout.setContentsMargins(25, 25, 25, 25)

        time_section = QLabel("Time-Based Workouts")
        time_section.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        time_section.setStyleSheet("color: white; border: none;")
        time_sec_layout.addWidget(time_section)
        time_sec_layout.addSpacing(15)
        
        self.time_table = self.create_workout_table(
            ["Workout", "Total Time Held (sec)"]
        )
        self.time_table.setMinimumHeight(150)
        time_sec_layout.addWidget(self.time_table)

        content_layout.addWidget(time_section_box)
        
    def show_popup_message(self, title: str, message: str, icon=QMessageBox.Icon.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
                
    def create_summary_card(self, label, value):
        card = QFrame()
        card.setMinimumWidth(220)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 rgba(102, 126, 234, 0.15),
                                           stop:1 rgba(118, 75, 162, 0.15));
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 20px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        val_widget = QLabel(value)
        val_widget.setObjectName("value")
        val_widget.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        val_widget.setStyleSheet("color: white; border: none;")
        val_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(val_widget)

        lbl_widget = QLabel(label.upper())
        lbl_widget.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_widget.setStyleSheet("color: #fbbf24; letter-spacing: 1px; border: none;")
        lbl_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_widget)
        
        return card
        
    def create_workout_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        table.setStyleSheet("""
            QTableWidget {
                background: transparent;
                border: none;
                gridline-color: rgba(255, 255, 255, 0.05);
                color: #e2e8f0;
                font-size: 14px;
                font-weight: bold;
                outline: none;
            }
            QTableWidget::item {
                padding: 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QHeaderView::section {
                background: rgba(102, 126, 234, 0.1);
                color: #fbbf24;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 13px;
                text-transform: uppercase;
                border-bottom: 2px solid rgba(102, 126, 234, 0.4);
            }
        """)
        
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(headers)):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        
        return table
    
    
    def build_plan_target_map(self, plan_data):
        """
        Returns:
        {
            "Jumping Jack": 15,
            "Push-up": 5,
            "Plank": 10,
            ...
        }
        """
        targets = {}
        for ex in plan_data:
            targets[ex["name"]] = ex["target"]
        return targets
    
    # =================== PROMOTION LOGIC ===================
    
    def calculate_plan_max_points(self, plan):
        """
        Calculates max points based on the trainee's workout plan
        plan: dict of exercises with 'reps' or 'duration'
        Example:
        {
           "Jumping Jack": {"reps": 15},
            "Plank": {"duration": 10}
        }
        """
        total = 0
        for _, val in plan.items():
            if "reps" in val:
                total += val["reps"] * 2
            elif "duration" in val:
                total += val["duration"] * 2
        # Multiply by factor (40) if using same scaling as example
        total *= 4
        return total

    def calculate_total_points(self):
        """
        SCORING RULE:
        +2 for each correct rep
        -1 for each wrong rep
        +2 for each correct second (time workouts)
        """
        total_points = 0

        # ----- Rep based workouts -----
        for name, stats in self.rep_totals.items():
            total = stats[0]
            correct = stats[1]
            wrong = stats[2]

            total_points += (correct * 2)          # +2 for correct
            total_points += (wrong * -1)           # -1 for wrong

        # ----- Time based workouts (Plank, Cobra) -----
        for session in session_analytics.sessions:
            if session.duration > 0:
                total_points += session.duration * 2   # +2 per second

        return total_points


    def calculate_success_rates(self):
        """
        Rep workouts:
            accuracy = correct / total × 100

        Time workouts (Plank, Cobra):
            accuracy = total_actual_time / (target_time × session_count) × 100
        """
        rates = {}

        # ----- 1) REP BASED  -----
        for name, stats in self.rep_totals.items():
            total = stats[0]
            correct = stats[1]

            if total > 0:
                rates[name] = (correct / total) * 100
            else:
                rates[name] = 0

        # ----- 2) TIME BASED  -----
        time_totals = {}
        session_counts = {}

        for s in session_analytics.sessions:
            if s.duration > 0:
                # total time
                time_totals.setdefault(s.exercise_name, 0)
                time_totals[s.exercise_name] += s.duration

                # count sessions
                session_counts.setdefault(s.exercise_name, 0)
                session_counts[s.exercise_name] += 1

        for name, actual_time in time_totals.items():

            target = self.plan_targets.get(name, 0)
            count = session_counts.get(name, 0)

            if target > 0 and count > 0:
                expected_total = target * count

                rates[name] = (actual_time / expected_total) * 100
            else:
                rates[name] = 0

        return rates



    def check_promotion_status(self):
        """
        YOUR FINAL RULE:

        A. Total Points ≥ 4800
        B. EACH exercise ≥ 60% success
        """

        total_points = self.calculate_total_points()
        rates = self.calculate_success_rates()

        # ----- Condition A -----
        points_ok = total_points >= getattr(self, "plan_max_points", 4800)  

        # ----- Condition B -----
        exercises_ok = all(rate >= 60 for rate in rates.values())

        return points_ok and exercises_ok, total_points, rates


    def refresh_data(self):
        if not self.trainee_id:
            return

        session_analytics.load_sessions(self.trainee_id)

        # ===== 30 DAYS INACTIVITY RESET =====
        if is_inactive_30_days(self.trainee_id):

            from backend.models.data_manager import reset_sessions_after_inactivity

            reset_sessions_after_inactivity(self.trainee_id)

            session_analytics.sessions.clear()
            session_analytics.total_sessions = 0
            self.rep_totals = {}

            self.update_session_tracker(0)

            self.total_score_card.findChild(QLabel, "value").setText(f"0/{self.plan_max_points}")
            self.remaining_score_card.findChild(QLabel, "value").setText(str(self.plan_max_points))

            if not self.reset_popup_shown:
                self.show_popup_message(
                    "Restarted",
                    "⚠ Inactive for 30 days – progress restarted!",
                    icon=QMessageBox.Icon.Warning
                )
                self.reset_popup_shown = True

            return


        # -----------------------------
        # Update summary cards
        # -----------------------------
        rep_totals = {}
        time_totals = {}

        total_correct_all = 0
        total_wrong_all = 0

        for s in session_analytics.sessions:
            if s.reps_completed > 0:
                if s.exercise_name not in rep_totals:
                    rep_totals[s.exercise_name] = [0, 0, 0]
                rep_totals[s.exercise_name][0] += s.reps_completed
                rep_totals[s.exercise_name][1] += s.correct_reps
                rep_totals[s.exercise_name][2] += s.wrong_reps

                total_correct_all += s.correct_reps
                total_wrong_all += s.wrong_reps

            elif s.duration > 0:
                if s.exercise_name not in time_totals:
                    time_totals[s.exercise_name] = 0
                time_totals[s.exercise_name] += s.duration

        self.rep_totals = rep_totals  # store for summary tables

        self.update_session_tracker(session_analytics.total_sessions)

        # ================= REP BASED TABLE =================
        rep_totals = {}

        for s in session_analytics.sessions:
            if s.reps_completed > 0:
                name = s.exercise_name

                if name not in rep_totals:
                    rep_totals[name] = {"total": 0, "correct": 0, "wrong": 0}

                rep_totals[name]["total"] += s.reps_completed
                rep_totals[name]["correct"] += s.correct_reps
                rep_totals[name]["wrong"] += s.wrong_reps

        self.rep_table.setRowCount(0)
        self.rep_table.setRowCount(len(rep_totals))

        for row, (name, data) in enumerate(rep_totals.items()):
            item = self._create_item(name)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.rep_table.setItem(row, 0, item)
            self.rep_table.setItem(row, 1, self._create_item(str(data["total"])))
            self.rep_table.setItem(row, 2, self._create_item(str(data["correct"]), color="#48bb78"))
            self.rep_table.setItem(row, 3, self._create_item(str(data["wrong"]), color="#f56565"))

        # ================= TIME BASED TABLE =================
        self.time_table.setRowCount(len(time_totals))
        for row, (name, duration) in enumerate(time_totals.items()):
            self.time_table.setItem(row, 0, self._create_item(name, Qt.AlignmentFlag.AlignLeft))
            self.time_table.setItem(row, 1, self._create_item(f"{duration} sec"))

        promoted, total_points, rates = self.check_promotion_status()
        if session_analytics.total_sessions >= 60:
            if not promoted:
                from backend.models.data_manager import reset_sessions_after_promotion

                reset_sessions_after_promotion(self.trainee_id)

                session_analytics.sessions.clear()
                session_analytics.total_sessions = 0
                self.rep_totals = {}

                self.update_session_tracker(0)

                self.total_score_card.findChild(QLabel, "value").setText(f"0/{self.plan_max_points}")
                self.remaining_score_card.findChild(QLabel, "value").setText(str(self.plan_max_points))

                self.show_popup_message(
                    "Level Restarted",
                    "⚠ You completed 60 sessions but did not meet promotion criteria.\nLevel restarted from Session 1!",
                    icon=QMessageBox.Icon.Warning
                )
                return

        if promoted:
            trainee = get_trainee_info(self.trainee_id)
            current_plan = trainee.get("plan_id", 1)

            next_plan = self.get_next_plan(current_plan)

            if next_plan != current_plan:
                from backend.models.data_manager import (
                    promote_trainee_plan,
                    reset_sessions_after_promotion,
                    update_fitness_level,
                    plan_level_and_index  # ✅ ADDED
                )

                ok, msg = promote_trainee_plan(self.trainee_id, next_plan)

                if ok:
                    reset_sessions_after_promotion(self.trainee_id)

                    # ✅ update fitness_level + plan_id
                    update_fitness_level(self.trainee_id, next_plan)

                    session_analytics.sessions.clear()
                    session_analytics.total_sessions = 0
                    self.rep_totals = {}

                    # ✅ Reload trainee + show only main category
                    trainee = get_trainee_info(self.trainee_id)
                    plan_id = trainee.get("plan_id", next_plan)
                    main_level, _ = plan_level_and_index(plan_id)
                    self.plan_label.setText(f"Plan: {main_level}")  # ✅ CHANGED

                    # ✅ Reload NEW plan targets correctly
                    plan_data = get_workout_plan(next_plan)
                    self.plan_targets = self.build_plan_target_map(plan_data)  # ✅ ADDED

                    plan_dict = {}
                    for ex in plan_data:
                        name = ex["name"]
                        target = ex["target"]
                        if "Plank" in name or "Cobra" in name:
                            plan_dict[name] = {"duration": target}
                        else:
                            plan_dict[name] = {"reps": target}

                    self.plan_max_points = self.calculate_plan_max_points(plan_dict)

                    self.update_session_tracker(0)

                    total_points = 0
                    self.total_score_card.findChild(QLabel, "value").setText(f"0/{self.plan_max_points}")
                    self.remaining_score_card.findChild(QLabel, "value").setText(str(self.plan_max_points))

                    self.show_popup_message(
                        "Promotion",
                        f"🎉 Congratulations! Promoted to next level: {main_level} 🎉",  # ✅ CHANGED
                        icon=QMessageBox.Icon.Information
                    )

        self.update_line_charts_from_sessions()

        # clear old accuracy chart
        while self.accuracy_layout.count():
            item = self.accuracy_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        chart = self.create_accuracy_bar_chart()
        if chart:
            self.accuracy_layout.addWidget(chart)
        if session_analytics.total_sessions == 0:
            total_points = 0

        self.total_score_card.findChild(QLabel, "value").setText(
            f"{total_points}/{self.plan_max_points}"
        )

        trainee = get_trainee_info(self.trainee_id)
        plan_id = trainee.get("plan_id", 1) if trainee else 1

        # ✅ FIX: Advanced is 11..15
        if plan_id >= 11 and total_points >= self.plan_max_points:
            self.remaining_score_card.findChild(QLabel, "value").setText("MAX LEVEL")
        else:
            remaining = max(self.plan_max_points - total_points, 0)
            self.remaining_score_card.findChild(QLabel, "value").setText(str(remaining))

    
    def update_line_charts_from_sessions(self):
        # -------- CLEAR OLD CHARTS --------
        while self.line_charts_layout.count():
            item = self.line_charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rep_exercises = ["Push-up", "Jumping Jack", "Squat", "Crunches"]
        time_exercises = ["Plank", "Cobra Stretch"]

        rep_data = {e: {"c": [], "w": []} for e in rep_exercises}
        time_data = {e: [] for e in time_exercises}

        sessions = list(reversed(session_analytics.sessions))

        # -------- COLLECT DATA --------
        for s in sessions:
            if s.exercise_name in rep_exercises:
                rep_data[s.exercise_name]["c"].append(s.correct_reps)
                rep_data[s.exercise_name]["w"].append(s.wrong_reps)

            elif s.exercise_name in time_exercises and s.duration > 0:
                time_data[s.exercise_name].append(s.duration)

        row, col = 0, 0
        MAX_COLS = 1

        # ===== REP LINE CHARTS =====
        for ex in rep_exercises:
            fig = Figure(figsize=(6, 10))
            ax = fig.add_subplot(111)

            y_correct = rep_data[ex]["c"]
            y_wrong = rep_data[ex]["w"]
            x = list(range(1, len(y_correct) + 1))

            ax.plot(x, y_correct, marker="o", label="Correct Reps")
            ax.plot(x, y_wrong, marker="o", label="Wrong Reps")

            # correct plan target
            plan_name = self.normalize_exercise_name(ex)
            target = self.plan_targets.get(plan_name, max(y_correct + [0]) + 1)

            ax.set_ylim(0, target)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            

            ax.set_xticks(x)  

            ax.set_title(f"{ex} (Target: {target})")
            ax.set_xlabel("Session")
            ax.set_ylabel("Reps")
            ax.legend()
            ax.grid(True)

            canvas = FigureCanvas(fig)
            canvas.setMinimumSize(900, 500)
            canvas.draw()

            self.line_charts_layout.addWidget(canvas, row, col)

            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

        # ===== TIME LINE CHARTS =====
        for ex in time_exercises:
            fig = Figure(figsize=(6, 14))
            ax = fig.add_subplot(111)

            y = time_data[ex]
            x = list(range(1, len(y) + 1))

            ax.plot(x, y, marker="o", label="Time (sec)")

            plan_name = self.normalize_exercise_name(ex)
            target = self.plan_targets.get(plan_name, max(y + [0]) + 1)

            ax.set_ylim(0, target)
            ax.set_yticks(range(0, target + 1, 3))        

            ax.set_xticks(x)  

            ax.set_title(f"{ex} (Target: {target} sec)")
            ax.set_xlabel("Session")
            ax.set_ylabel("Seconds")
            ax.legend()
            ax.grid(True)

            canvas = FigureCanvas(fig)
            canvas.setMinimumSize(1000, 700)
            canvas.draw()

            self.line_charts_layout.addWidget(canvas, row, col)

            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1



    def create_accuracy_bar_chart(self):
        """
        Bar chart showing accuracy % for ALL exercises
        Rep → correct/total
        Time → hold/target
        With:
        - Red < 60%
        - Green ≥ 60%
        - Fixed order
        """

        rates = self.calculate_success_rates()

        # ----- ORDER -----
        order = [
            "Jumping Jack",
            "Push-up",
            "Plank",
            "Crunches",
            "Squat",
            "Cobra Stretch"
        ]

        exercises = []
        values = []

        for ex in order:
            acc = rates.get(ex, 0)
            acc = min(100, round(acc, 1)) 
            exercises.append(ex)
            values.append(acc)

        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)

        # ----- COLOR LOGIC -----
        colors = ["green" if v >= 60 else "red" for v in values]

        ax.bar(exercises, values, color=colors, width=0.3)

        ax.set_title("Exercise Accuracy %")
        ax.set_ylabel("Accuracy")
        ax.set_ylim(0, 100)

        ax.grid(axis="y")

        # Show % labels
        for i, v in enumerate(values):
            ax.text(i, v + 1, f"{v}%", ha="center", fontsize=9)

        ax.set_xticks(range(len(exercises)))
        ax.set_xticklabels(exercises, rotation=20)

        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(520)
        canvas.setMaximumHeight(600)

        return canvas

            
    
    def update_session_tracker(self, completed_sessions):
        completed_sessions = min(completed_sessions, 60)

        for i, label in enumerate(self.session_marks):
            if i < completed_sessions:
                # MARK COMPLETED
                label.setStyleSheet("""
                QLabel {
                background-color: #667eea;
                border-radius: 25px;
                color: white;
                font-weight: bold;
                }
        """)
            else:
                # NOT COMPLETED
                label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255,255,255,0.08);
                        border-radius: 12px;
                    }
                """)
                
    def get_next_plan(self, current_plan):
        from backend.models.data_manager import get_next_plan_same_index
        return get_next_plan_same_index(current_plan)
    
    def normalize_exercise_name(self, name):
        name_map = {
            "Jumping Jack": "Jumping Jacks",
            "Push-up": "Push Ups",
            "Squat": "Squats",
            "Crunches": "Crunches",
            "Plank": "Plank",
            "Cobra Stretch": "Cobra Stretch"
        }
        return name_map.get(name, name)


    def _create_item(self, text, alignment=Qt.AlignmentFlag.AlignCenter, color=None):
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
        if color:
            item.setForeground(QColor(color))
        return item
    
    
    def on_profile_clicked(self):
        """Notify main window to show profile"""
        main_win = self.window()
        if hasattr(main_win, "show_profile"):
            main_win.show_profile()
