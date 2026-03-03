# =========================================
# workout_session.py  (FULLY CORRECTED + TOAST OVER CAMERA FIX)
# =========================================
"""
Workout Session UI with live camera feedback and guided workflow.

✅ Features:
- Beep when target time reached for Plank / Cobra Stretch
- Show NON-BLOCKING toast/banner at bottom-right (no OK button)
- Timer continues even after target reached
- Toast stays until user clicks Stop
- Toast border will NOT hide under the camera section (QVideoWidget native overlay fix)
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QTime, QUrl, QSize
from PyQt6.QtGui import QFont, QMovie, QIcon, QPixmap
from PyQt6.QtMultimedia import (
    QCamera, QMediaCaptureSession, QAudioOutput, QMediaPlayer, QSoundEffect
)
from PyQt6.QtMultimediaWidgets import QVideoWidget


class WorkoutSession(QWidget):
    """Real-time workout session page with camera monitoring"""

    sessionEnded = pyqtSignal()
    nextWorkoutRequested = pyqtSignal(int)

    # Exercise name → media file mapping
    GIF_MAP = {
        "squats": "Squats.mp4",
        "push ups": "Push ups.mp4",
        "crunches": "Crunches.mp4",
        "jumping jacks": "Jumping jacks.mp4",
        "plank": "Plank.mp4",
        "cobra stretch": "Cobra stretch.mp4"
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_workout = None
        self.current_index = -1   # workout_id
        self.camera_permission_granted = False
        self.camera_active = False
        self.movie = None

        self.camera = QCamera()
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setCamera(self.camera)

        self.stopwatch_timer = QTimer(self)
        self.stopwatch_timer.timeout.connect(self.update_stopwatch)
        self.session_time = QTime(0, 0)

        self.target_seconds = None
        self.target_reached = False

        self.demo_player = QMediaPlayer(self)
        self.demo_audio = QAudioOutput(self)
        self.demo_audio.setVolume(0.0)
        self.demo_player.setAudioOutput(self.demo_audio)
        self.demo_player.errorOccurred.connect(self.on_demo_media_error)
        self.demo_player.setLoops(QMediaPlayer.Loops.Infinite)

        # Beep sound (reliable)
        self.beep_sound = QSoundEffect(self)
        beep_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "beep.wav")
        )
        if os.path.exists(beep_path):
            self.beep_sound.setSource(QUrl.fromLocalFile(beep_path))
            self.beep_sound.setVolume(0.8)

        self.init_ui()

    # ---------------- UI ----------------
    def init_ui(self):
        self.setStyleSheet("background-color: #0f0c29;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.target_toast = QFrame(self)
        self.target_toast.setVisible(False)
        self.target_toast.setStyleSheet("""
        QFrame {
            background: rgba(10, 20, 40, 220);
            border: 2px solid #10b981;
            border-radius: 14px;
        }
        """)
        self.target_toast.setMinimumWidth(420)
        self.target_toast.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        toast_layout = QHBoxLayout(self.target_toast)
        toast_layout.setContentsMargins(16, 12, 16, 12)
        toast_layout.setSpacing(10)

        self.target_toast_label = QLabel("")
        self.target_toast_label.setWordWrap(True)
        self.target_toast_label.setStyleSheet("""
        QLabel {
            color: white;
            font-weight: 700;
            font-size: 16px;
            border: none;
            background: transparent;
            padding: 0px;
            line-height: 22px;
        }
        """)
        self.target_toast_label.setMinimumHeight(48)
        self.target_toast_label.setFixedWidth(380)
        toast_layout.addWidget(self.target_toast_label)

        # Make sure toast overlays on top of the UI
        self.target_toast.raise_()

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
                background: transparent;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.4);
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
        self.dash_btn.setStyleSheet(
            btn_style.replace("transparent", "rgba(102, 126, 234, 0.8)")
                     .replace("1px solid rgba(255, 255, 255, 0.4)", "none")
        )
        self.dash_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dash_btn.clicked.connect(lambda: self.sessionEnded.emit())

        self.analytics_btn = QPushButton("Dashboard")
        self.analytics_btn.setStyleSheet(btn_style)
        self.analytics_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analytics_btn.clicked.connect(self.on_analytics_clicked)

        self.profile_btn = QPushButton("Profile")
        self.profile_btn.setStyleSheet(btn_style)
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_btn.clicked.connect(self.on_profile_clicked)

        nav_layout.addWidget(self.dash_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.analytics_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.profile_btn)

        main_layout.addWidget(nav_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(50, 20, 50, 40)
        content_layout.setSpacing(15)

        header_layout = QHBoxLayout()

        self.workout_label = QLabel("Workout Name")
        self.workout_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.workout_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(self.workout_label)

        header_layout.addStretch()

        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("color: #667eea; background: transparent;")
        header_layout.addWidget(self.timer_label)

        content_layout.addLayout(header_layout)

        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)
        self.split_layout = split_layout

        self.demo_container = QFrame()
        self.demo_container.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.05);
            }
        """)
        self.demo_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.demo_container.setFixedHeight(500)

        demo_main_layout = QVBoxLayout(self.demo_container)
        demo_main_layout.setContentsMargins(10, 10, 10, 15)
        demo_main_layout.setSpacing(10)

        demo_header = QHBoxLayout()
        demo_header.addStretch()

        self.close_demo_btn = QPushButton()
        self.close_demo_btn.setFixedSize(30, 30)
        self.close_demo_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "cancel_icon.png"))
        if os.path.exists(icon_path):
            self.close_demo_btn.setIcon(QIcon(icon_path))
            self.close_demo_btn.setIconSize(QSize(24, 24))
        else:
            self.close_demo_btn.setText("✕")

        self.close_demo_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }
        """)
        self.close_demo_btn.clicked.connect(self.close_demo_pane)
        demo_header.addWidget(self.close_demo_btn)
        demo_main_layout.addLayout(demo_header)

        # Demo (GIF/Image) widget
        self.demo_widget = QLabel("Demo Video")
        self.demo_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.demo_widget.setStyleSheet("color: #666; font-size: 14px; border: none; background: transparent;")
        self.demo_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.demo_widget.setScaledContents(True)
        demo_main_layout.addWidget(self.demo_widget, stretch=1)

        # Demo (MP4) widget
        self.demo_video_widget = QVideoWidget()
        self.demo_video_widget.setMinimumHeight(240)
        self.demo_video_widget.setStyleSheet("background: transparent;")
        self.demo_video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.demo_video_widget.setVisible(False)
        self.demo_player.setVideoOutput(self.demo_video_widget)
        demo_main_layout.addWidget(self.demo_video_widget, stretch=1)

        self.tutorial_btn = QPushButton("Tutorial")
        self.tutorial_btn.setFixedHeight(40)
        self.tutorial_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tutorial_btn.setStyleSheet("""
            QPushButton {
                background: rgba(102, 126, 234, 0.1);
                color: #667eea;
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.2);
            }
        """)
        self.tutorial_btn.clicked.connect(self.open_tutorial)
        demo_main_layout.addWidget(self.tutorial_btn)

        self.video_container = QFrame()
        self.video_container.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.05);
            }
        """)
        self.video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.video_container.setFixedHeight(500)

        # ✅ FIX: prevent native window stacking issues so toast can overlay above camera
        self.video_container.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        self.video_container.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, False)

        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget()

        # ✅ FIX: allow overlay widgets (toast) to appear above the video
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, False)

        self.video_widget.setStyleSheet("background: transparent; border-radius: 18px;")
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.capture_session.setVideoOutput(self.video_widget)
        video_layout.addWidget(self.video_widget)

        split_layout.addWidget(self.demo_container, 40)
        split_layout.addWidget(self.video_container, 60)

        content_layout.addLayout(split_layout)

        footer_layout = QHBoxLayout()

        self.open_demo_btn = QPushButton("Demo")
        self.open_demo_btn.setFixedSize(100, 55)
        self.open_demo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_demo_btn.setStyleSheet("""
            QPushButton {
                background: #2d3748;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                border: 1px solid rgba(255,255,255,0.1);
            }
            QPushButton:hover {
                background: #4a5568;
            }
        """)
        self.open_demo_btn.setVisible(False)
        self.open_demo_btn.clicked.connect(self.open_demo_pane)
        footer_layout.addWidget(self.open_demo_btn)

        self.control_btn = QPushButton("Start")
        self.control_btn.setFixedSize(200, 55)
        self.control_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_start_style()
        self.control_btn.clicked.connect(self.toggle_session)
        footer_layout.addWidget(self.control_btn)

        footer_layout.addStretch()

        self.next_btn = QPushButton("Next Workout")
        self.next_btn.setFixedSize(180, 50)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        self.next_btn.setVisible(False)
        self.next_btn.clicked.connect(self.on_next_clicked)
        footer_layout.addWidget(self.next_btn)

        content_layout.addLayout(footer_layout)
        main_layout.addWidget(content)

        # ✅ Ensure toast is always above everything after UI is built
        self.target_toast.raise_()

    # ---------------- Target toast helpers ----------------
    def _position_target_toast(self):
        """Place toast at bottom-right of this screen (non-blocking overlay)."""
        margin_x = 28
        margin_y = 28
        self.target_toast.adjustSize()

        w = self.target_toast.width()
        h = self.target_toast.height()
        x = max(0, self.width() - w - margin_x)
        y = max(0, self.height() - h - margin_y)

        self.target_toast.move(x, y)
        self.target_toast.raise_()

    def show_target_toast(self, text: str):
        self.target_toast_label.setText(text)
        self.target_toast_label.adjustSize()
        self.target_toast.adjustSize()
        self.target_toast.setVisible(True)
        self._position_target_toast()

    def hide_target_toast(self):
        self.target_toast.setVisible(False)
        self.target_toast_label.setText("")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.target_toast.isVisible():
            self._position_target_toast()

    # ---------------- Tutorial navigation ----------------
    def open_tutorial(self):
        """Tutorial button -> open WorkoutDemo screen for the current workout_id."""
        if self.camera_active:
            self.stop_session()

        if self.demo_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.demo_player.pause()
        if self.movie and self.movie.state() == QMovie.MovieState.Running:
            self.movie.setPaused(True)

        workout_id = self.current_index
        if workout_id is None or workout_id == -1:
            return

        main_win = self.window()
        if hasattr(main_win, "show_workout_demo"):
            main_win.show_workout_demo(workout_id)

    # ---------------- Demo Pane ----------------
    def close_demo_pane(self):
        """Hide demo pane, pause media, and expand camera"""
        self.demo_container.hide()
        self.open_demo_btn.setVisible(True)

        if self.demo_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.demo_player.pause()

        if self.movie and self.movie.state() == QMovie.MovieState.Running:
            self.movie.setPaused(True)

        self.split_layout.setStretch(0, 0)
        self.split_layout.setStretch(1, 1)

    def open_demo_pane(self):
        """Show demo pane, resume media, and restore split"""
        self.demo_container.show()
        self.open_demo_btn.setVisible(False)

        self.split_layout.setStretch(0, 40)
        self.split_layout.setStretch(1, 60)

        if self.demo_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.demo_player.play()

        if self.movie and self.movie.state() == QMovie.MovieState.Paused:
            self.movie.setPaused(False)

    # ---------------- Workout Flow ----------------
    def on_next_clicked(self):
        self.nextWorkoutRequested.emit(self.current_index)

    def set_workout(self, workout: dict, index: int):
        self.current_workout = workout
        self.current_index = index

        name = workout.get("name", "Unknown Workout")
        self.workout_label.setText(name)
        self.preview_gif(name)

        # Store target seconds for timed workouts
        target_val = workout.get("target")
        try:
            self.target_seconds = int(target_val) if target_val is not None else None
        except Exception:
            self.target_seconds = None

        self.target_reached = False
        self.hide_target_toast()
        self.reset_session()

    # ---------------- Demo Media ----------------
    def on_demo_media_error(self, error, error_string):
        self.demo_player.stop()
        self.demo_video_widget.setVisible(False)
        self.demo_widget.setVisible(True)
        self.demo_widget.setText(
            "Video preview unavailable on this PC.\n"
            "Tip: Install a media codec pack / Qt multimedia backend,\n"
            "or replace MP4 previews with GIFs."
        )

    def preview_gif(self, workout_name: str):
        key = workout_name.strip().lower()
        media_file = self.GIF_MAP.get(key)

        if not media_file:
            self.demo_widget.setText("No Preview Available")
            self.demo_widget.setVisible(True)
            self.demo_video_widget.setVisible(False)
            return

        self.load_media(media_file)

    def load_media(self, filename: str):
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        media_path = os.path.join(frontend_dir, "assets", filename)

        if not os.path.exists(media_path):
            self.demo_widget.setText(f"File Not Found:\n{filename}")
            self.demo_widget.setVisible(True)
            self.demo_video_widget.setVisible(False)
            return

        if self.movie:
            self.movie.stop()
            self.movie = None
        self.demo_player.stop()

        ext = os.path.splitext(filename)[1].lower()
        self.demo_audio.setVolume(0.0)

        if ext in [".mp4", ".avi", ".mov", ".mkv"]:
            self.demo_widget.setVisible(False)
            self.demo_video_widget.setVisible(True)
            self.demo_player.setSource(QUrl.fromLocalFile(media_path))
            self.demo_player.play()
        else:
            self.demo_video_widget.setVisible(False)
            self.demo_widget.setVisible(True)

            if ext == ".gif":
                self.movie = QMovie(media_path)
                self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
                self.demo_widget.setMovie(self.movie)
                self.movie.start()
            else:
                pixmap = QPixmap(media_path)
                if pixmap.isNull():
                    self.demo_widget.setText("Preview not supported")
                else:
                    self.demo_widget.setPixmap(pixmap)

            self.demo_widget.setScaledContents(True)

    # ---------------- Session Controls ----------------
    def set_start_style(self):
        self.control_btn.setText("Start")
        self.control_btn.setStyleSheet("""
            QPushButton {
                background: #48bb78;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background: #38a169;
            }
        """)

    def set_stop_style(self):
        self.control_btn.setText("Stop")
        self.control_btn.setStyleSheet("""
            QPushButton {
                background: #f56565;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background: #e53e3e;
            }
        """)

    def toggle_session(self):
        if not self.camera_active:
            self.start_session()
        else:
            self.stop_session()

    def ask_camera_permission_once(self) -> bool:
        if self.camera_permission_granted:
            return True

        dialog = QDialog(self)
        dialog.setWindowTitle("Camera Permission")
        dialog.setFixedSize(420, 190)

        dialog.setStyleSheet("""
            QDialog { background-color: #0f0f10; border: 1px solid #2a2a2a; border-radius: 10px; }
            QLabel { color: white; font-size: 14px; }
            QPushButton {
                background: transparent; color: white; font-size: 14px; font-weight: 600;
                min-width: 80px; min-height: 32px; border: 1px solid rgba(255,255,255,0.75);
                border-radius: 8px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.12); }
            QPushButton:pressed { background: rgba(255,255,255,0.20); }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        label = QLabel("This workout requires access to your camera.\nDo you want to allow camera access?")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        yes_btn = QPushButton("Yes")
        no_btn = QPushButton("No")

        btn_row.addStretch()
        btn_row.addWidget(yes_btn)
        btn_row.addWidget(no_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        def on_yes():
            self.camera_permission_granted = True
            dialog.accept()

        def on_no():
            dialog.reject()

        yes_btn.clicked.connect(on_yes)
        no_btn.clicked.connect(on_no)

        return dialog.exec() == QDialog.DialogCode.Accepted

    def start_session(self):
        if not self.ask_camera_permission_once():
            self.set_start_style()
            self.next_btn.setVisible(False)
            return

        self.camera.start()
        self.camera_active = True
        self.stopwatch_timer.start(1000)
        self.set_stop_style()
        self.next_btn.setVisible(False)

    def stop_session(self):
        # Hide toast when user stops
        self.hide_target_toast()

        self.camera.stop()
        self.camera_active = False
        self.stopwatch_timer.stop()
        self.set_start_style()
        self.next_btn.setVisible(True)

    def reset_session(self):
        if self.camera_active:
            self.camera.stop()
            self.camera_active = False

        self.stopwatch_timer.stop()
        self.set_start_style()
        self.next_btn.setVisible(False)

        self.session_time = QTime(0, 0)

        # Do NOT clear target_seconds here
        self.target_reached = False

        self.timer_label.setText("00:00")
        self.hide_target_toast()

    def update_stopwatch(self):
        self.session_time = self.session_time.addSecs(1)
        self.timer_label.setText(self.session_time.toString("mm:ss"))

        workout_name = (self.current_workout or {}).get("name", "").strip().lower()
        is_timed = ("plank" in workout_name) or ("cobra" in workout_name)

        if is_timed and self.target_seconds and not self.target_reached:
            elapsed = self.session_time.minute() * 60 + self.session_time.second()
            if elapsed >= int(self.target_seconds):
                self.target_reached = True

                # Beep once
                try:
                    if self.beep_sound.source().isValid():
                        self.beep_sound.play()
                    else:
                        QApplication.beep()
                except Exception:
                    QApplication.beep()

                # Non-blocking toast (no OK)
                self.show_target_toast("Target time reached!")

    # ---------------- Navigation Buttons ----------------
    def on_analytics_clicked(self):
        main_win = self.window()
        if hasattr(main_win, "show_analytics"):
            main_win.show_analytics()

    def on_profile_clicked(self):
        main_win = self.window()
        if hasattr(main_win, "show_profile"):
            main_win.show_profile()
