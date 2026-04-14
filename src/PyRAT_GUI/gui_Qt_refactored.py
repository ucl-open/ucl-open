import subprocess
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional
from matplotlib import ticker

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import requests
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ucl_open.pyrat.models import PyRatSubject
from ucl_open.pyrat.session import SessionConfig


class APIAuthManager:
    """Handles API communication and user authentication with the PyRAT backend."""

    def __init__(self, main_window: "PyratAPI", url: str, client_token: str, users: dict, timeout: int = 20):
        self.main_window = main_window
        self.url = url
        self.client_token = client_token
        self.users = users
        self.timeout = timeout
        self.session = requests.Session()
        self.current_user = "Ryan"
        self.current_token = ""

    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make a request with consistent error handling."""
        url = f"{self.url}/{endpoint.lstrip('/') }"
        kwargs.setdefault("timeout", self.timeout)

        # Attach auth tuple using the currently connected user's token (if any)
        token = ""
        if self.current_user and self.current_user in self.users:
            user_info = self.users.get(self.current_user, {})
            token = user_info.get("Token", user_info.get("token", ""))
        kwargs["auth"] = (self.client_token, token)

        try:
            resp = self.session.request(method.upper(), url, **kwargs)
            return resp
        except requests.exceptions.Timeout:
            QMessageBox.warning(self.main_window, "Timeout", "The request timed out.")
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self.main_window, "Connection Error", "Unable to connect to the API.")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Unexpected error: {e}")
        return None

    def verify_credentials(self) -> dict:
        """Verify user credentials with the API."""
        response = self.make_request("GET", "credentials")
        return response.json() if response else {}

    def fetch_animal_list(self) -> Optional[List[dict]]:
        """Fetch the list of animals from the API."""
        params = {
            "k": [
                "eartag_or_id", "labid", "room_name", "age_days", "age_weeks",
                "strain_name_with_id", "responsible_fullname", "responsible_id",
                "mutations", "weight", "comments", "date_last_comment",
                "cagenumber", "cagetype", "requests", "sex",
            ],
            "l": 2000,
        }
        response = self.make_request("GET", "animals", params=params)
        return response.json() if response else None

    def update_weight(self, animal_id: str, weight_g: float, weight_time: Optional[str] = None) -> bool:
        """Update an animal's weight via API."""
        if weight_time is None:
            weight_time = datetime.now(timezone.utc).isoformat()
        data = {"weight": float(weight_g), "weight_time": weight_time}
        response = self.make_request("POST", f"animals/{animal_id}/weights", json=data)
        if response is None:
            QMessageBox.warning(self.main_window, "Error", "No response from API. Check your connection and token.")
            return False
        if response.status_code in [200, 201, 204]:
            return True
        else:
            QMessageBox.warning(self.main_window, "Error", f"API returned status {response.status_code}. {response.text if response.text else 'No details provided.'}")
            return False

    def post_comment(self, animal_id: str, comment_text: str) -> bool:
        """Post a comment to an animal record."""
        data = {"comment": f"#{comment_text}"}
        response = self.make_request("POST", f"animals/{animal_id}/comments", json=data)
        return bool(response and response.status_code == 200)

    def login(self):
        """Show PIN entry dialog for authentication."""
        dlg = QDialog(self.main_window)
        dlg.setWindowTitle("Login")
        grid = QGridLayout(dlg)
        grid.addWidget(QLabel("Please login to post"), 0, 0, 1, 2)
        grid.addWidget(QLabel("Pin"), 1, 0)
        login_entry = QLineEdit()
        login_entry.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(login_entry, 1, 1)
        submit = QPushButton("Submit")
        grid.addWidget(submit, 1, 2)
        submit.clicked.connect(lambda: self.compare_pin(login_entry.text().strip(), dlg))
        self.login_dialog = dlg
        dlg.adjustSize()
        dlg.exec()

    def compare_pin(self, pin: str, dialog: QDialog):
        """Verify entered PIN against user database."""
        user_info = self.users.get(self.current_user, {})
        correct_pin = user_info.get("PIN", "")
        if pin == correct_pin:
            self.verify_and_authenticate(dialog)
        else:
            QMessageBox.warning(self.main_window, "Error", "Invalid PIN")

    def verify_and_authenticate(self, dialog: QDialog):
        """Authenticate with the API."""
        user_info = self.users.get(self.current_user, {})
        token = user_info.get("Token", user_info.get("token", ""))
        self.current_token = token
        
        data = self.verify_credentials()

        if data.get("client_valid") and data.get("user_valid"):
            QMessageBox.information(self.main_window, "Success", "Login successful")
            self.enable_posting_features()
            dialog.accept()
            return

        if data.get("client_valid") and not data.get("user_valid"):
            QMessageBox.warning(self.main_window, "Error", "Login failed. Invalid user token")
            return

        QMessageBox.warning(self.main_window, "Error", "Failed to authenticate")

    def enable_posting_features(self):
        """Enable posting features after successful login."""
        self.main_window.ui_manager.set_posting_widget_states(True)
        self.main_window.status_label.setText(f"Connected-{self.current_user}")
        self.main_window.status_label.setStyleSheet("color: green;")
        self.main_window.login_button.setText("Log out")

    def logout(self):
        """Log out the current user."""
        self.main_window.ui_manager.set_posting_widget_states(False)
        self.main_window.status_label.setText("No connection")
        self.main_window.status_label.setStyleSheet("color: red;")
        self.main_window.login_button.setText("Login")
        self.current_token = ""
        QMessageBox.information(self.main_window, "Info", "Logged out successfully")

    def get_indiv_mouse_weight(self, animal_id: str) -> Optional[List[dict]]:
        """Fetch weight history for a specific animal."""
        response = self.make_request("GET", f"animals/{animal_id}/weights")
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
        elif response and response.status_code == 404:
            QMessageBox.warning(self.main_window, "Not Found", "Animal not found for weight retrieval.")
        elif response and response.status_code == 422:
            QMessageBox.warning(self.main_window, "Error", "Validation error, check your token.")
        return None

class UIManager:
    """Manages GUI building, styling, and theme management."""

    COLOR_MAP_LIGHT = {
        "Blue": "#9CCDDD",
        "Green": "#75D475",
        "Pink": "#E797A3",
    }
    COLOR_MAP_DARK = {
        "Blue": "#0055aa",
        "Green": "#00A703",
        "Pink": "#af0247",
    }
    COLOR_MAP_SELECTED_LIGHT = {
        "Blue": "#52BEE2",
        "Green": "#28A428",
        "Pink": "#E04B6D",
    }
    COLOR_MAP_SELECTED_DARK = {
        "Blue": "#003663",
        "Green": "#006602",
        "Pink": "#630027",
    }
    BASE_FONT_KWARGS = {
        "family": "Helvetica",
        "size": 13,
        "weight": QFont.Weight.Normal,
    }

    def __init__(self, main_window: "PyratAPI"):
        self.main_window = main_window
        self.base_font = QFont(
            self.BASE_FONT_KWARGS["family"],
            self.BASE_FONT_KWARGS["size"],
        )
        self.current_theme = "light"
        self.highlight_color = "#9CCDDD"
        self.selection_color = "#52BEE2"
        self.red_bg = QColor("#ffcccc")

    def setup_ui(self):
        """Set up the user interface layout and widgets."""
        outer = QVBoxLayout(self.main_window.central_widget)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setStretch(2, 5)

        # Top-top frame (theme, help, status, login, highlight color)
        toptop = QHBoxLayout()

        self.main_window.status_label = QLabel("No connection")
        self.main_window.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_window.status_label.setStyleSheet("color: red;")
        toptop.addWidget(self.main_window.status_label)

        self.main_window.login_button = QPushButton("Login")
        self.main_window.login_button.clicked.connect(self.main_window.toggle_login_logout)
        toptop.addWidget(self.main_window.login_button)

        self.main_window.theme_btn = QPushButton("Theme")
        self.main_window.theme_btn.clicked.connect(self.switch_theme)
        toptop.addWidget(self.main_window.theme_btn)

        self.main_window.help_btn = QPushButton("Help")
        self.main_window.help_btn.clicked.connect(self.main_window.get_help)
        toptop.addWidget(self.main_window.help_btn)

        highlight_label = QLabel("Highlight Color:")
        highlight_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        toptop.addWidget(highlight_label)

        self.main_window.color_combo = QComboBox()
        self.main_window.color_combo.addItems(["Blue", "Green", "Pink"])
        self.main_window.color_combo.currentIndexChanged.connect(self.change_highlight_color)
        toptop.addWidget(self.main_window.color_combo)

        outer.addLayout(toptop, 0)

        # Top frame (filters)
        top = QHBoxLayout()
        top.addWidget(QLabel("Filter:"))
        self.main_window.filter_entry = QLineEdit()
        self.main_window.filter_entry.setPlaceholderText("Use \",\" separate keywords")
        self.main_window.filter_entry.returnPressed.connect(lambda: self.main_window.multi_filters(text=self.main_window.filter_entry.text()))
        top.addWidget(self.main_window.filter_entry)

        top.addWidget(QLabel("Preset Filters:"))

        self.main_window.mymice = QPushButton("My Mice")
        self.main_window.mymice.clicked.connect(lambda: self.main_window.preset_filters(text="responsible"))
        top.addWidget(self.main_window.mymice)

        self.main_window.WRmice = QPushButton("Water Restriction Mice")
        self.main_window.WRmice.setEnabled(False)
        self.main_window.WRmice.clicked.connect(lambda: self.main_window.preset_filters(text="Water Restriction Mice"))
        top.addWidget(self.main_window.WRmice)

        self.main_window.breeding = QPushButton("Breeding Mice")
        self.main_window.breeding.clicked.connect(lambda: self.main_window.preset_filters(text="Breeding"))
        top.addWidget(self.main_window.breeding)

        self.main_window.stockmice = QPushButton("Stock Mice")
        self.main_window.stockmice.clicked.connect(lambda: self.main_window.preset_filters(text="Stock"))
        top.addWidget(self.main_window.stockmice)

        self.main_window.experimice = QPushButton("Experimental Mice")
        self.main_window.experimice.clicked.connect(lambda: self.main_window.preset_filters(text="Experiment"))
        top.addWidget(self.main_window.experimice)

        self.main_window.rest = QPushButton("Reset")
        self.main_window.rest.clicked.connect(lambda: self.main_window.preset_filters(text=""))
        top.addWidget(self.main_window.rest)

        outer.addLayout(top, 1)

        # Middle frame (main table)
        middle = QVBoxLayout()
        self.main_window.table = QTableWidget()
        self.main_window.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.main_window.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.main_window.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.main_window.table.setSortingEnabled(True)
        self.main_window.table.setWordWrap(True)
        self.main_window.table.itemSelectionChanged.connect(self.main_window.showinfo)
        middle.addWidget(self.main_window.table)
        outer.addLayout(middle, 5)

        # Bottom frame (details/comments left, actions right)
        bottom = QHBoxLayout()

        # Comment/Detail frame (left)
        left = QVBoxLayout()

        # Comment table
        self.main_window.comment_tv = QTableWidget(0, 2)
        self.main_window.comment_tv.setHorizontalHeaderLabels(["Date", "Content"])
        hdr = self.main_window.comment_tv.horizontalHeader()
        assert hdr is not None
        hdr.setStretchLastSection(True)
        vhdr = self.main_window.comment_tv.verticalHeader()
        assert vhdr is not None
        vhdr.setVisible(False)
        self.main_window.comment_tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        left.addWidget(self.main_window.comment_tv, stretch=3)

        # Actions frame (right)
        right = QVBoxLayout()
        actionlabel = QLabel("Actions (Login required)")
        actionlabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        actionlabel.setFont(QFont(self.base_font.family(), self.base_font.pointSize(), QFont.Weight.Bold))
        right.addWidget(actionlabel)

        frq_used = QGridLayout()

        self.main_window.weightplot_button = QPushButton("Weight History")
        self.main_window.weightplot_button.clicked.connect(lambda: self.main_window.plot_weight_history())
        frq_used.addWidget(self.main_window.weightplot_button, 0, 0)

        self.main_window.bw_label = QLabel("Weight (g)")
        self.main_window.bw_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        frq_used.addWidget(self.main_window.bw_label, 1, 0)
        self.main_window.weight_entry = QLineEdit()
        self.main_window.weight_entry.setPlaceholderText("Please enter weight (float)")
        self.main_window.weight_entry.returnPressed.connect(lambda: self.main_window.submit_post(text="weight"))
        frq_used.addWidget(self.main_window.weight_entry, 1, 1)


        self.main_window.water_label = QLabel("Water Delivery (ml)")
        self.main_window.water_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        frq_used.addWidget(self.main_window.water_label, 2, 0)
        self.main_window.waterdelivery_entry = QLineEdit()
        self.main_window.waterdelivery_entry.setPlaceholderText("Please enter water delivery (float)")
        self.main_window.waterdelivery_entry.returnPressed.connect(lambda: self.main_window.submit_post(text="waterdelivery"))
        frq_used.addWidget(self.main_window.waterdelivery_entry, 2, 1)
        self.main_window.cmt_label = QLabel("Comment")
        self.main_window.cmt_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        frq_used.addWidget(self.main_window.cmt_label, 3, 0)
        self.main_window.comment_entry = QLineEdit()
        self.main_window.comment_entry.setPlaceholderText("Please enter comment")
        self.main_window.comment_entry.returnPressed.connect(lambda: self.main_window.submit_post(text="comment"))
        frq_used.addWidget(self.main_window.comment_entry, 3, 1)

        right.addLayout(frq_used)

        self.main_window.toggle_rare_button = QPushButton("Show Rarely Used Actions")
        self.main_window.toggle_rare_button.clicked.connect(self.main_window.toggle_rare_actions)
        right.addWidget(self.main_window.toggle_rare_button)

        self.main_window.rare_group = QGroupBox()
        rare_layout = QGridLayout(self.main_window.rare_group)
        self.main_window.refbw_label = QLabel("Ref Weight")
        rare_layout.addWidget(self.main_window.refbw_label, 0, 0)
        self.main_window.refbw_entry = QLineEdit()
        self.main_window.refbw_entry.setPlaceholderText("Please enter reference body weight")
        self.main_window.refbw_entry.returnPressed.connect(lambda: self.main_window.submit_post(text="refbw"))
        rare_layout.addWidget(self.main_window.refbw_entry, 0, 1)

        self.main_window.implant_label = QLabel("Implant Weight")
        rare_layout.addWidget(self.main_window.implant_label, 1, 0)
        self.main_window.implantweight_entry = QLineEdit()
        self.main_window.implantweight_entry.setPlaceholderText("Please enter implant weight")
        self.main_window.implantweight_entry.returnPressed.connect(lambda: self.main_window.submit_post(text="implantweight"))
        rare_layout.addWidget(self.main_window.implantweight_entry, 1, 1)

        self.main_window.rare_group.setVisible(False)
        right.addWidget(self.main_window.rare_group)
        
        right.addWidget(self.build_launch_panel())
        right.addStretch()

        bottom.addLayout(left, stretch=2)
        bottom.addLayout(right, stretch=1)
        outer.addLayout(bottom, 3)

        self.set_posting_widget_states(False)

    def build_launch_panel(self) -> QGroupBox:
        """Build the Launch Session group box."""
        group = QGroupBox("Launch Session")
        layout = QGridLayout(group)

        layout.addWidget(QLabel("Mouse:"), 0, 0)
        self.main_window.launch_mouse_combo = QComboBox()
        layout.addWidget(self.main_window.launch_mouse_combo, 0, 1, 1, 2)

        layout.addWidget(QLabel("Bonsai exe:"), 1, 0)
        self.main_window.bonsai_exe_edit = QLineEdit()
        self.main_window.bonsai_exe_edit.setPlaceholderText("Path to Bonsai.exe")
        layout.addWidget(self.main_window.bonsai_exe_edit, 1, 1)
        bonsai_browse_btn = QPushButton("Browse…")
        bonsai_browse_btn.clicked.connect(self.main_window.browse_bonsai_exe)
        layout.addWidget(bonsai_browse_btn, 1, 2)

        layout.addWidget(QLabel("Workflow:"), 2, 0)
        self.main_window.workflow_edit = QLineEdit()
        self.main_window.workflow_edit.setPlaceholderText("Path to .bonsai workflow")
        layout.addWidget(self.main_window.workflow_edit, 2, 1)
        workflow_browse_btn = QPushButton("Browse…")
        workflow_browse_btn.clicked.connect(self.main_window.browse_workflow)
        layout.addWidget(workflow_browse_btn, 2, 2)

        self.main_window.start_session_btn = QPushButton("Start Session")
        self.main_window.start_session_btn.clicked.connect(self.main_window.start_session)
        layout.addWidget(self.main_window.start_session_btn, 3, 0, 1, 2)

        self.main_window.session_status_label = QLabel("")
        layout.addWidget(self.main_window.session_status_label, 3, 2)

        return group

    def apply_theme(self):
        """Apply the current theme stylesheet."""
        font_family = self.base_font.family()
        font_size = self.base_font.pointSize()
        
        if self.current_theme == "light":
            stylesheet = f"""
                QMainWindow {{
                    background-color: #f5f5f2;
                    color: #202020;
                    font-family: '{font_family}';
                    font-size: {font_size}pt;
                }}
                
                QWidget {{
                    background-color: #f5f5f2;
                    color: #202020;
                    font-family: '{font_family}';
                    font-size: {font_size}pt;
                }}
                
                QPushButton {{
                    background-color: #e8e8e5;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    padding: 5px 15px;
                    color: #202020;
                }}
                
                QPushButton:hover {{
                    background-color: #d0d0cd;
                }}
                
                QPushButton:pressed {{
                    background-color: #b8b8b5;
                }}
                
                QPushButton:disabled {{
                    background-color: #f0f0ed;
                    color: #a0a0a0;
                }}
                
                QLineEdit, QTextEdit {{
                    background-color: #ffffff;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    padding: 3px;
                    color: #202020;
                    selection-background-color: #9CCDDD;
                }}
                
                QLineEdit:disabled, QTextEdit:disabled {{
                    background-color: #f0f0ed;
                    color: #a0a0a0;
                }}
                
                QComboBox {{
                    background-color: #ffffff;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    padding: 3px;
                    color: #202020;
                }}
                
                QComboBox:hover {{
                    border: 1px solid #9CCDDD;
                }}
                
                QComboBox::drop-down {{
                    border: none;
                }}
                
                QLabel {{
                    color: #202020;
                }}
                
                QTableWidget {{
                    background-color: #ffffff;
                    alternate-background-color: #f9f9f9;
                    gridline-color: #d0d0d0;
                    color: #202020;
                    border: 1px solid #c0c0c0;
                }}
                
                QTableWidget::item {{
                    padding: 3px;
                }}
                
                QHeaderView::section {{
                    background-color: #e8e8e5;
                    color: #202020;
                    padding: 5px;
                    border: 1px solid #c0c0c0;
                    font-weight: bold;
                }}
                
                QGroupBox {{
                    border: 1px solid #c0c0c0;
                    border-radius: 5px;
                    margin-top: 10px;
                    font-weight: bold;
                }}
                
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                }}
            """
        else:
            stylesheet = f"""
                QMainWindow {{
                    background-color: #1e1e1e;
                    color: #dddddd;
                    font-family: '{font_family}';
                    font-size: {font_size}pt;
                }}
                
                QWidget {{
                    background-color: #1e1e1e;
                    color: #dddddd;
                    font-family: '{font_family}';
                    font-size: {font_size}pt;
                }}
                
                QPushButton {{
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    padding: 5px 15px;
                    color: #dddddd;
                }}
                
                QPushButton:hover {{
                    background-color: #3d3d3d;
                }}
                
                QPushButton:pressed {{
                    background-color: #4d4d4d;
                }}
                
                QPushButton:disabled {{
                    background-color: #252525;
                    color: #666666;
                }}
                
                QLineEdit, QTextEdit {{
                    background-color: #2a2a2a;
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    padding: 3px;
                    color: #ffffff;
                    selection-background-color: #214f7e;
                }}
                
                QLineEdit:disabled, QTextEdit:disabled {{
                    background-color: #252525;
                    color: #666666;
                }}
                
                QComboBox {{
                    background-color: #2a2a2a;
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    padding: 3px;
                    color: #dddddd;
                }}
                
                QComboBox:hover {{
                    border: 1px solid #214f7e;
                }}
                
                QComboBox::drop-down {{
                    border: none;
                }}
                
                QLabel {{
                    color: #dddddd;
                }}
                
                QTableWidget {{
                    background-color: #2a2a2a;
                    alternate-background-color: #252525;
                    gridline-color: #3d3d3d;
                    color: #dddddd;
                    border: 1px solid #3d3d3d;
                }}
                
                QTableWidget::item {{
                    padding: 3px;
                }}
                
                QHeaderView::section {{
                    background-color: #2d2d2d;
                    color: #dddddd;
                    padding: 5px;
                    border: 1px solid #3d3d3d;
                    font-weight: bold;
                }}
                
                QGroupBox {{
                    border: 1px solid #3d3d3d;
                    border-radius: 5px;
                    margin-top: 10px;
                    font-weight: bold;
                    color: #dddddd;
                }}
                
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                }}
            """
        
        self.main_window.setStyleSheet(stylesheet)

    def switch_theme(self):
        """Toggle between light and dark themes."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme()
        self.change_highlight_color()
        self.wt_highlight_color_on()
        self.configure_hidden_columns()

    def change_highlight_color(self, event: Optional[int] = None):
        """Update highlight color based on current theme and selected color."""
        color_choice = self.main_window.color_combo.currentText()
        if self.current_theme == "light":
            self.highlight_color = self.COLOR_MAP_LIGHT.get(color_choice, "#9CCDDD")
            self.selection_color = self.COLOR_MAP_SELECTED_LIGHT.get(color_choice, "#52BEE2")
            self.red_bg = QColor("#ffcccc")
        else:
            self.highlight_color = self.COLOR_MAP_DARK.get(color_choice, "#0055aa")
            self.selection_color = self.COLOR_MAP_SELECTED_DARK.get(color_choice, "#003663")
            self.red_bg = QColor("#8b0000")
        self.apply_cagematch_highlight()
        self.apply_selection_highlight()

    def apply_selection_highlight(self):
        """Highlight the currently selected row."""
        row = self.main_window.table.currentRow()
        row_color = QColor(self.selection_color)
        for c in range(self.main_window.table.columnCount()):
            item = self.main_window.table.item(row, c)
            if item:
                current_bg = item.background().color()
                if current_bg != self.red_bg:
                    item.setBackground(row_color)

    def apply_cagematch_highlight(self):
        """Apply highlight to rows matching the selected cage."""
        for r in range(self.main_window.table.rowCount()):
            for c in range(self.main_window.table.columnCount()):
                item = self.main_window.table.item(r, c)
                if item:
                    current_bg = item.background().color()
                    if current_bg != self.red_bg:
                        item.setBackground(QColor(Qt.GlobalColor.transparent))
        
        try:
            cage_col = self.main_window.columns.index("Cage Number")
        except ValueError:
            cage_col = None

        for r in range(self.main_window.table.rowCount()):
            is_cage_match = False
            if cage_col is not None and self.main_window.selected_cage:
                cage_item = self.main_window.table.item(r, cage_col)
                is_cage_match = cage_item and str(cage_item.text()).strip() == str(self.main_window.selected_cage).strip()
            
            if is_cage_match:
                row_color = QColor(self.highlight_color)
            else:
                continue
            
            for c in range(self.main_window.table.columnCount()):
                item = self.main_window.table.item(r, c)
                if item:
                    current_bg = item.background().color()
                    if current_bg != self.red_bg:
                        item.setBackground(row_color)

    def wt_highlight_color_on(self):
        """Highlight 'wt' entries in Confirmed Mutations column with red background."""
        try:
            mut_col = self.main_window.columns.index("Confirmed Mutations")
        except ValueError:
            return
        
        for r in range(self.main_window.table.rowCount()):
            item = self.main_window.table.item(r, mut_col)
            if item and "wt" in item.text().lower():
                item.setBackground(self.red_bg)

    def configure_hidden_columns(self):
        """Hide the helper index column."""
        if self.main_window.table.columnCount() > 0:
            self.main_window.table.setColumnHidden(0, True)

    def set_posting_widget_states(self, enabled: bool):
        """Enable or disable posting widgets."""
        for w in [
            self.main_window.weight_entry,
            self.main_window.comment_entry,
            self.main_window.waterdelivery_entry,
            self.main_window.refbw_entry,
            self.main_window.implantweight_entry,
        ]:
            w.setEnabled(enabled)
        for lbl in [
            self.main_window.refbw_label,
            self.main_window.implant_label,
            self.main_window.bw_label,
            self.main_window.cmt_label,
            self.main_window.water_label,
        ]:
            lbl.setEnabled(enabled)

class DataManager:
    """Handles data transformation, filtering, and table population."""

    def __init__(self, main_window: "PyratAPI"):
        self.main_window = main_window

    def transform_animal_data(self, animals: List[dict]) -> tuple[List[str], List[List[Any]]]:
        """Transform raw API data into table rows and columns."""
        for idx, animal in enumerate(animals):
            muts = animal.get("mutations", [])
            animal["Confirmed Mutations"] = " | ".join(
                f"{m.get('mutationname','')}-{m.get('mutationgrade','').upper() if m.get('mutationgrade') in ['het','hom'] else m.get('mutationgrade','')}"
                for m in muts
            )
            animal["Age(d)"] = animal.get("age_days", "")
            animal["Age(w)"] = animal.get("age_weeks", "")
            animal["Room"] = animal.get("room_name", "")
            animal["Eartag/Id"] = animal.get("eartag_or_id", "")
            animal["Weight"] = animal.get("weight", "")
            animal["Cage Number"] = animal.get("cagenumber", "")
            animal["Cage Type"] = animal.get("cagetype", "")
            animal["Responsible"] = animal.get("responsible_fullname", "")
            animal["Sex"] = str(animal.get("sex", "")).capitalize()
            animal["_index"] = idx
            animal["Lab ID"] = animal.get("labid", "")
            animal["Strain Name"] = animal.get("strain_name_with_id", "")

        keys = [
            "_index", "Eartag/Id", "Lab ID", "Weight", "Sex", "Strain Name",
            "Responsible", "Age(w)", "Room", "Confirmed Mutations",
            "Cage Type", "Cage Number",
        ]

        info_filtered = [{k: a.get(k, "") for k in keys} for a in animals]
        columns = list(info_filtered[0].keys()) if info_filtered else keys
        rows = [[animal[col] for col in columns] for animal in info_filtered]
        return columns, rows

    def format_genotype(self, text: str) -> str:
        """Format genotype string to show each mutation on a new line."""
        s = str(text or "")
        if "|" in s:
            parts = [p.strip() for p in s.split("|")]
            return "\n".join(parts)
        for token in ("wt", "het", "hom"):
            s = s.replace(token, token + "\n")
            s = s.replace(token.upper(), token.upper() + "\n")
        return "\n".join(line.strip() for line in s.splitlines() if line.strip())

    def populate_table(self, rowdata: List[List[Any]]):
        """Build or refresh the main table with provided rows."""
        self.main_window.table.setSortingEnabled(False)
        
        self.main_window.table.clear()
        self.main_window.table.setColumnCount(len(self.main_window.columns))
        self.main_window.table.setRowCount(len(rowdata))
        self.main_window.table.setHorizontalHeaderLabels(self.main_window.columns)

        for r, row in enumerate(rowdata):
            for c, val in enumerate(row):
                if c < len(self.main_window.columns) and self.main_window.columns[c] == "Confirmed Mutations":
                    item = QTableWidgetItem(self.format_genotype(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item = QTableWidgetItem(str(val))
                item.setFont(self.main_window.ui_manager.base_font)
                if isinstance(val, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_window.table.setItem(r, c, item)

        self.main_window.table.resizeColumnsToContents()
        self.main_window.table.resizeRowsToContents()
        self.main_window.ui_manager.configure_hidden_columns()
        
        self.main_window.table.setSortingEnabled(True)
        self.main_window.ui_manager.wt_highlight_color_on()

    def rebuild_table(self, filtered_rows: List[List[Any]]):
        """Rebuild the table with filtered data."""
        self.populate_table(filtered_rows)
        if hasattr(self.main_window, 'original_index'):
            for r in range(self.main_window.table.rowCount()):
                idx_item = self.main_window.table.item(r, 0)
                if idx_item and str(idx_item.text()) == str(self.main_window.original_index):
                    self.main_window.table.selectRow(r)
                    return

    def apply_multi_filters(self, text: str):
        """Apply multiple keyword filters."""
        if not text or text.strip() == "":
            QMessageBox.information(self.main_window, "Info", "No filter keywords provided.")
            return
        keywords = [k.strip() for k in text.split(",")]
        filtered_rows = [
            row for row in self.main_window.rows
            if all(any(k.lower() in str(cell).lower() for cell in row) for k in keywords)
        ]
        self.rebuild_table(filtered_rows)
        self.main_window.filter_entry.clear()

    def apply_preset_filter(self, text: str):
        """Apply a preset filter."""
        if text == "responsible":
            text = self.main_window.api_auth_manager.current_user
        if text == "":
            self.main_window.load_data()
        else:
            filtered_rows = [row for row in self.main_window.rows if any(str(text) in str(cell) for cell in row)]
            self.rebuild_table(filtered_rows)

    def format_weight_history(self, animal_id: str) -> Optional[tuple[list, list]]:
        """Format weight history data to (date, weight) tuples."""
        weight_history_data = self.main_window.api_auth_manager.get_indiv_mouse_weight(animal_id)
        if not weight_history_data:
            return None
        all_weight = []
        all_date = []
        for record in weight_history_data:
            weight = record.get("weight")
            weight_time = record.get("weight_time")
            if weight is not None and weight_time is not None:
                try:
                    time_obj = datetime.fromisoformat(weight_time.replace("Z", "+00:00"))
                    all_date.append(time_obj.strftime("%Y-%m-%d"))
                    all_weight.append(weight)
                except (ValueError, AttributeError):
                    continue
        return (all_date, all_weight) if (all_weight and all_date) else None

    def get_ref_bw(self):
        """Get reference body weight for the selected animal.
        
        First looks for a comment starting with #refbw (format: #refbw: 40).
        If not found, uses the oldest weight record as reference body weight.
        """
        sel_ranges = self.main_window.table.selectedRanges()
        r = sel_ranges[0].topRow()
        idx_item = self.main_window.table.item(r, 0)
        if idx_item:
            idx = int(idx_item.text())
            animal_info = self.main_window.info[idx]
            ref_bw_cmt = animal_info.get("comments") or []
            try:
                for cmt in ref_bw_cmt:
                    content = cmt.get("content", "")
                    if content and "refbw" in content:
                        ref_bw_str = content.split(":", 1)[1].strip()
                        try:
                            ref_bw = float(ref_bw_str)
                            return ref_bw
                        except ValueError:
                            continue
            except Exception:
                pass
        return None
class PyratAPI(QMainWindow):
    """
    PyQt6 GUI for PyRAT API interaction.
    
    Coordinates between multiple manager classes:
    - APIAuthManager: handles API communication and authentication
    - UIManager: handles GUI building and styling
    - DataManager: handles data transformation and filtering
    """

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyRAT GUI")
        self.setMinimumSize(1700, 800)
        
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Configuration
        self.timeout = 20
        config = self.load_config()
        self.URL = config["url"]
        self.client_token = config["client_token"]
        self.users = config["users"]

        # Initialize managers
        self.api_auth_manager = APIAuthManager(self, self.URL, self.client_token, self.users, self.timeout)
        self.ui_manager = UIManager(self)
        self.data_manager = DataManager(self)
    

        # Data/table state
        self.info: List[dict[str, Any]] = []
        self.columns: List[str] = []
        self.rows: List[List[Any]] = []
        self.original_index = int(0)
        self.selected_cage: Optional[str] = None
        # Debounce flag
        self.showinfo_job_active = False

        # Session launcher
        self.bonsai_proc: Optional[subprocess.Popen] = None
        self.session_json_path: Optional[Path] = None
        self.session_output_json_path: Optional[Path] = None

        # UI widgets — assigned by UIManager.setup_ui(); declared here for static analysis
        self.status_label: QLabel
        self.login_button: QPushButton
        self.theme_btn: QPushButton
        self.help_btn: QPushButton
        self.color_combo: QComboBox
        self.filter_entry: QLineEdit
        self.mymice: QPushButton
        self.WRmice: QPushButton
        self.breeding: QPushButton
        self.stockmice: QPushButton
        self.experimice: QPushButton
        self.rest: QPushButton
        self.table: QTableWidget
        self.comment_tv: QTableWidget
        self.weightplot_button: QPushButton
        self.bw_label: QLabel
        self.weight_entry: QLineEdit
        self.water_label: QLabel
        self.waterdelivery_entry: QLineEdit
        self.cmt_label: QLabel
        self.comment_entry: QLineEdit
        self.toggle_rare_button: QPushButton
        self.rare_group: QGroupBox
        self.refbw_label: QLabel
        self.refbw_entry: QLineEdit
        self.implant_label: QLabel
        self.implantweight_entry: QLineEdit
        self.launch_mouse_combo: QComboBox
        self.bonsai_exe_edit: QLineEdit
        self.workflow_edit: QLineEdit
        self.start_session_btn: QPushButton
        self.session_status_label: QLabel

        # Build UI and load initial data
        self.ui_manager.setup_ui()
        self.ui_manager.apply_theme()

        # Persisted launcher paths
        settings = QSettings("UCL", "PyRATGUI")
        saved_exe = settings.value("bonsai_exe_path", "")
        if saved_exe:
            self.bonsai_exe_edit.setText(saved_exe)
        saved_workflow = settings.value("workflow_path", "")
        if saved_workflow:
            self.workflow_edit.setText(saved_workflow)

        self.load_data()

    def load_config(self) -> dict:
        """Load server URL from pyrat_server.yaml and credentials from users.json."""
        import yaml

        try:
            with open("src/PyRAT_GUI/pyrat_server.yaml", "r", encoding="utf-8") as f:
                server = yaml.safe_load(f)
            url = server.get("url", "")
        except Exception as e:
            QMessageBox.warning(None, "Warning", f"Could not load pyrat_server.yaml: {e}")
            url = ""

        try:
            with open("src/PyRAT_GUI/users.json", "r", encoding="utf-8") as f:
                creds = json.load(f)
            client_token = creds.get("client_token", "")
            users = creds.get("users", {})
        except Exception as e:
            QMessageBox.warning(None, "Warning", f"Could not load users.json: {e}")
            client_token = ""
            users = {}

        return {"url": url, "client_token": client_token, "users": users}

    def load_data(self):
        """Load animal data from API and populate table."""
        animals = self.api_auth_manager.fetch_animal_list()
        if not animals:
            QMessageBox.warning(self, "Error", "Failed to retrieve animal list. Please check connection")
            return
        
        self.info = animals
        self.columns, self.rows = self.data_manager.transform_animal_data(self.info)
        if self.rows:
            self.data_manager.populate_table(self.rows)
        self.populate_launch_mouse_combo()

    def toggle_login_logout(self):
        """Toggle login/logout."""
        if self.login_button.text() == "Login":
            self.api_auth_manager.login()
        else:
            self.api_auth_manager.logout()

    def get_help(self):
        """Display usage instructions in a help dialog."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Help")
        dlg.setMinimumSize(1000, 650)
        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        help_text = (
            "PyRAT GUI User Guide\n"
            "======================================\n\n"
            "This application allows you to interact with the PyRAT API to manage animal data.\n\n"
            "The connection is made with the default user Pip. To switch user, click login button and enter your PIN.\n\n"
            "You will be logged in if PIN matches your PIN. If PIN matches another user, you will be prompted to switch user.\n\n"
            "======================================\n\n"
            "Main Features:\n\n"
            "- Highlight: animal with same cage number as selected are highlighted. You can choose the highlight color on the top right dropdown list\n\n"
            "- Multiple filter: enter keywords separated by commas in the filter box. e.g., Ryan,cdh23. Press Enter.\n\n"
            "- Preset filters: quick buttons for common filters. Reset clears.\n\n"
            "- Sorting: click column headers to sort ascending/descending.\n\n"
            "- Animal list & Details: Select an animal to view details and comments.\n\n"
            "- Actions: all posting actions are disabled until login with PIN.\n\n"
            "======================================\n\n"
            "Note:\n\n"
            "- For work requests, please use PyRAT. This GUI provides quick overview and limited posting capabilities.\n"
        )
        text.setText(help_text)
        layout.addWidget(text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.adjustSize()
        dlg.exec()

    def toggle_rare_actions(self):
        """Toggle the visibility of the advanced actions frame."""
        if self.rare_group.isVisible():
            self.rare_group.setVisible(False)
            self.toggle_rare_button.setText("Show Rare Used Actions")
        else:
            self.rare_group.setVisible(True)
            self.toggle_rare_button.setText("Hide Rare Used Actions")

    def showinfo(self):
        """Debounced selection callback from table."""
        if self.showinfo_job_active:
            return
        self.showinfo_job_active = True
        QTimer.singleShot(0, self.showinfo_update)

    def showinfo_update(self):
        """Update details panel for selected animal."""
        self.showinfo_job_active = False
        sel_ranges = self.table.selectedRanges()
        if not sel_ranges:
            return
        r = sel_ranges[0].topRow()
        idx_item = self.table.item(r, 0)
        if not idx_item:
            return
        try:
            self.original_index = int(idx_item.text())
        except Exception:
            return
        if self.original_index < 0 or self.original_index >= len(self.info):
            return

        animal_selected = self.info[self.original_index]
        if "Cage Number" in self.columns:
            cage_item = self.table.item(r, self.columns.index("Cage Number"))
            self.selected_cage = cage_item.text().strip() if cage_item is not None else ""
        else:
            self.selected_cage = animal_selected.get("Cage Number", "").strip()

        comments = animal_selected.get("comments", []) or []
        self.comment_tv.setRowCount(0)
        for cmt in comments:
            date = (cmt.get("created", "") or "")[:10]
            content = cmt.get("content", "") or ""
            row = self.comment_tv.rowCount()
            self.comment_tv.insertRow(row)
            date_item = QTableWidgetItem(date)
            date_item.setFont(self.ui_manager.base_font)
            content_item = QTableWidgetItem(content)
            content_item.setFont(self.ui_manager.base_font)
            self.comment_tv.setItem(row, 0, date_item)
            self.comment_tv.setItem(row, 1, content_item)

        self.comment_tv.resizeColumnsToContents()

        self.ui_manager.apply_cagematch_highlight()
        self.ui_manager.apply_selection_highlight()

    def multi_filters(self, text: Optional[str] = None):
        """Apply multiple keyword filters."""
        self.data_manager.apply_multi_filters(text or "")

    def preset_filters(self, text: Optional[str] = None):
        """Apply a preset filter."""
        self.data_manager.apply_preset_filter(text or "")

    def submit_post(self, text: Optional[str] = None):
        """Submit data to API based on selected action type."""
        sel_ranges = self.table.selectedRanges()
        if not sel_ranges:
            QMessageBox.warning(self, "Warning", "Select a row first.")
            return
        r = sel_ranges[0].topRow()
        idx_item = self.table.item(r, 0)
        if not idx_item:
            QMessageBox.warning(self, "Error", "Index not found for selection.")
            return
        idx = int(idx_item.text())
        animal_id = self.info[idx].get("eartag_or_id", "")

        entry_widget = {
            "weight": self.weight_entry,
            "comment": self.comment_entry,
            "waterdelivery": self.waterdelivery_entry,
            "refbw": self.refbw_entry,
            "implantweight": self.implantweight_entry,
        }.get(text or "", None)

        if not entry_widget:
            QMessageBox.critical(self, "Error", f"Entry widget not found for {text}")
            return
        entry_text = entry_widget.text().strip()
        has_changes = False
        if entry_text:
            if text == "weight":
                try:
                    weight_value = float(entry_text)
                except ValueError:
                    QMessageBox.warning(self, "Error", "Weight must be a number")
                    return
                if weight_value >= 50 or weight_value <= 15:
                    QMessageBox.warning(self, "Warning", "Weight value seems unusual. Please verify.")
                    return
                success = self.api_auth_manager.update_weight(animal_id, weight_value)
                if success:
                    QMessageBox.information(self, "Success", "Weight updated successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to update weight")
                has_changes = True

            elif text == "waterdelivery":
                try:
                    water_value = float(entry_text)
                except ValueError:
                    QMessageBox.warning(self, "Error", "Water delivery must be a number")
                    return
                if water_value < 0 or water_value > 3:
                    QMessageBox.warning(self, "Warning", "Water delivery value seems unusual. Please verify.")
                    return
                entry_text = f"{text}: {water_value}ml"
                success = self.api_auth_manager.post_comment(animal_id, entry_text)
                if success:
                    QMessageBox.information(self, "Success", "Comment posted successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to post comment")
                has_changes = True

            else:
                entry_text = f"{text}: {entry_text}"
                success = self.api_auth_manager.post_comment(animal_id, entry_text)
                if success:
                    QMessageBox.information(self, "Success", "Comment posted successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to post comment")
                has_changes = True

        if not has_changes:
            QMessageBox.warning(self, "Warning", "Nothing to submit.")
            return

        if has_changes:
            self.load_data()

        entry_widget.clear()
        self.showinfo_update()

    def calculate_water_requirement(self, weight_g: float) -> float:
        """Calculate water requirement: 40ml/kg/day."""
        if weight_g <= 0:
            raise ValueError("Weight must be positive")
        weight_kg = weight_g / 1000.0
        water_ml = weight_kg * 40.0
        return round(water_ml, 2)

    def plot_weight_history(self):
        """Plot weight history for the selected animal."""
        sel_ranges = self.table.selectedRanges()
        if not sel_ranges:
            QMessageBox.warning(self, "Warning", "Select a row first.")
            return
        r = sel_ranges[0].topRow()
        idx_item = self.table.item(r, 0)
        if not idx_item:
            QMessageBox.warning(self, "Error", "Index not found for selection.")
            return
        idx = int(idx_item.text())
        animal_id = self.info[idx].get("eartag_or_id", "")
        result = self.data_manager.format_weight_history(animal_id)
        if result is None:
            QMessageBox.information(self, "No Data", "No weight history found for this animal.")
            return
        date, weight = result

        date = date[::-1]
        weights = weight[::-1]
        refbw = self.data_manager.get_ref_bw()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Weight History - {animal_id}")
        dlg.setMinimumSize(900, 600)
        layout = QVBoxLayout(dlg)
        
        fig = Figure(figsize=(7, 7
                              ), tight_layout=True)
        ax = fig.add_subplot()
        ax.plot(date, weights, marker='o', linestyle='-', linewidth=2, markersize=6)
        ax.set_title(f"Weight history for mice {animal_id}", fontsize=14, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Weight (g)", fontsize=12)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
        ax.tick_params(axis='x', rotation=45)

        if refbw is not None:
            lower_bound_bw =refbw * 0.8
            monitoring_threshold_bw = refbw * 0.85
            ax.axhline(y=refbw, color='blue', linestyle='--', label='Reference BW')
            ax.axhline(y=lower_bound_bw, color='red', linestyle='--', label='80% of Ref BW')
            ax.axhline(y=monitoring_threshold_bw, color='orange', linestyle='--', label='85% of Ref BW')
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.3), fancybox=True, shadow=True, ncol=5)
            for i, w in enumerate(weights):
                if w < lower_bound_bw:
                    ax.axvspan(i-0.5, i+0.5, color='red', alpha=0.3)
                elif w < monitoring_threshold_bw:
                    ax.axvspan(i-0.5, i+0.5, color='orange', alpha=0.3)
                else:
                    ax.axvspan(i-0.5, i+0.5, color='green', alpha=0.3)
        
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        
        dlg.exec()


    def populate_launch_mouse_combo(self):
        """Populate the Launch Session mouse dropdown from loaded animal data."""
        combo = self.launch_mouse_combo
        combo.clear()
        for animal in self.info:
            eartag = animal.get("eartag_or_id", "")
            labid = animal.get("labid", "")
            label = eartag + (f" ({labid})" if labid else "")
            combo.addItem(label, userData=eartag)

    def browse_bonsai_exe(self):
        """Open file browser to select Bonsai.exe."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Bonsai.exe", "", "Executables (*.exe)")
        if path:
            self.bonsai_exe_edit.setText(path)
            QSettings("UCL", "PyRATGUI").setValue("bonsai_exe_path", path)

    def browse_workflow(self):
        """Open file browser to select a .bonsai workflow file."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Bonsai Workflow", "", "Bonsai Workflows (*.bonsai)")
        if path:
            self.workflow_edit.setText(path)
            QSettings("UCL", "PyRATGUI").setValue("workflow_path", path)

    def start_session(self):
        """Build session JSON and launch Bonsai subprocess."""
        eartag = self.launch_mouse_combo.currentData()
        idx = self.launch_mouse_combo.currentIndex()
        workflow = self.workflow_edit.text().strip()
        bonsai_exe = self.bonsai_exe_edit.text().strip()

        if not eartag:
            QMessageBox.warning(self, "Warning", "Select a mouse first.")
            return
        if not workflow or not Path(workflow).exists():
            QMessageBox.warning(self, "Warning", "Select a valid .bonsai workflow file.")
            return
        if not bonsai_exe or not Path(bonsai_exe).exists():
            QMessageBox.warning(self, "Warning", "Select a valid Bonsai.exe path.")
            return

        session = SessionConfig(
            subject=PyRatSubject.model_validate(self.info[idx]),
            session_start=datetime.now(timezone.utc),
            workflow=workflow,
        )
        sessions_dir = Path(__file__).parent / "sessions"
        sessions_dir.mkdir(exist_ok=True)
        timestamp = session.session_start.strftime("%Y%m%d_%H%M%S")
        json_path = sessions_dir / f"{eartag}_{timestamp}.json"
        json_path.write_text(session.model_dump_json(indent=2, by_alias=True))
        start_str = session.session_start.strftime("%Y-%m-%d %H:%M:%S UTC")
        self.api_auth_manager.post_comment(eartag, f"sessionstart: {Path(workflow).stem} [{start_str}]")

        out_path = json_path.with_stem(json_path.stem + "_out")
        self.session_json_path = json_path
        self.session_output_json_path = out_path
        self.bonsai_proc = subprocess.Popen(
            [
                bonsai_exe, workflow,
                "--property", f"PyRatInputPath={json_path}",
                "--property", f"PyRatOutputPath={out_path}",
            ],
            stderr=subprocess.PIPE, # Capture stderr to show in case of Bonsai errors
        )
        self.start_session_btn.setEnabled(False)
        self.session_status_label.setText("Session running…")
        QTimer.singleShot(500, self.poll_bonsai) # Start polling after a short delay (500ms) to allow Bonsai to initialize

    def poll_bonsai(self):
        """Check if Bonsai has exited; if so, trigger the post-session dialog."""
        if self.bonsai_proc and self.bonsai_proc.poll() is not None:
            returncode = self.bonsai_proc.returncode
            _, stderr_bytes = self.bonsai_proc.communicate()
            self.bonsai_proc = None
            self.session_status_label.setText("Session ended.")
            self.start_session_btn.setEnabled(True)
            if returncode != 0:
                stderr_text = stderr_bytes.decode(errors="replace").strip() if stderr_bytes else ""
                msg = f"Bonsai exited with code {returncode}."
                if stderr_text:
                    msg += f"\n\n{stderr_text}"
                QMessageBox.warning(self, "Bonsai Error", msg)
                return
            self.post_session_dialog()
        elif self.bonsai_proc:
            QTimer.singleShot(500, self.poll_bonsai)

    def post_session_dialog(self):
        """Read output session JSON (written by Bonsai), pre-populate dialog, then post to PyRAT."""
        out_path = self.session_output_json_path
        read_path = out_path if (out_path and out_path.exists()) else self.session_json_path # Could be either the original or output path
        if not read_path or not read_path.exists():
            return

        session = SessionConfig.model_validate_json(read_path.read_text())
        eartag = session.subject.eartag_or_id
        session_water = session.water_delivered_ml or 0.0

        dlg = QDialog(self)
        dlg.setWindowTitle("Post Session")
        layout = QGridLayout(dlg)

        layout.addWidget(QLabel("Water in session (ml):"), 0, 0)
        layout.addWidget(QLabel(f"{session_water:.2f}"), 0, 1)

        layout.addWidget(QLabel("Additional water (ml):"), 1, 0)
        water_spin = QDoubleSpinBox()
        water_spin.setRange(0.0, 100.0)
        water_spin.setDecimals(3) # Allow up to 3 decimal places (ul precision)
        water_spin.setSingleStep(0.003) # 3ul step
        water_spin.setValue(0.0)
        layout.addWidget(water_spin, 1, 1)

        layout.addWidget(QLabel("Comment (optional):"), 2, 0)
        comment_edit = QLineEdit()
        comment_edit.setText(session.comment or "")
        layout.addWidget(comment_edit, 2, 1)

        submit_btn = QPushButton("Post to PyRAT")
        layout.addWidget(submit_btn, 3, 0, 1, 2)

        def _submit():
            additional = water_spin.value()
            comment = comment_edit.text().strip()
            total_water = session_water + additional
            session.water_delivered_ml = total_water or None
            session.comment = comment or None
            session.session_end = session.session_end or datetime.now(timezone.utc)
            read_path.write_text(session.model_dump_json(indent=2, by_alias=True))
            end_str = session.session_end.strftime("%Y-%m-%d %H:%M:%S UTC")
            self.api_auth_manager.post_comment(eartag, f"sessionend: {Path(session.workflow).stem} [{end_str}]")
            if total_water > 0:
                end_str = session.session_end.strftime("%Y-%m-%d %H:%M:%S UTC")
                success = self.api_auth_manager.post_comment(
                    eartag, f"waterdelivery: {total_water}ml [{end_str}]"
                )
                if not success:
                    QMessageBox.warning(self, "Warning", "Failed to post water delivery.")
            if comment:
                self.api_auth_manager.post_comment(eartag, comment)
            for c in session.comments:
                ts = c.created.strftime("%Y-%m-%d %H:%M:%S UTC") if c.created else ""
                text = f"{c.content} [{ts}]" if ts else c.content
                self.api_auth_manager.post_comment(eartag, text)
            dlg.accept()

        submit_btn.clicked.connect(_submit)
        dlg.adjustSize()
        dlg.exec()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("PyRAT GUI")
    app.setOrganizationName("UCL")
    
    window = PyratAPI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
