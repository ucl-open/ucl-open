import sys
import json
from datetime import datetime, timezone
from typing import Any, List, Optional

import requests

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QFontMetrics, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
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


class PyratAPI(QMainWindow):
    """
    PyQt6 GUI for PyRAT API interaction.
    
    Inherits from QMainWindow for proper Qt window management.
    Provides animal data viewing, filtering, and basic CRUD operations.
    """

    #constants for highlight colors
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

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyRAT GUI")
        self.setMinimumSize(1700, 800)
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Networking/API
        self.session = requests.Session()
        # self.URL = "https://ucl.pyrat.cloud/api/v3" #normal pyrat url
        self.URL = "https://ucl-uat.pyrat.cloud/api/v3" #UAT pyrat url
    #Normal Pyrat token
        self.client_token = "1-9vBhAUJnGJZldlehOEKX08"
        #user token = 18-b8adbe51a796a5841e321d64c88387bd69155408a495
        #19-777ad49d25f6f73c6655f533008e2c5188989c920c91
    #UAT PyRAT token
        #user token= 21-3b4a224b3fea344cd4029f5edd488fde37a03dc52e8d


        #20-5894606171ac87acce75646dd27c62d0e31cf25fe05a
        #
        #self.client_token = "1-0551cc75b1b0c60b96d321857ac2bfd331e950e3f3c7"
        self.timeout = 20   

        # User management
        self.users = self._load_users()
        self.current_user = "Ryan"

        # Theme state
        self.current_theme = "light"
        self.highlight_color = "#9CCDDD"
        self.selection_color = "#52BEE2"
        self.selected_cage: Optional[str] = None
        
        # Data/table state
        self.info: List[dict[str, Any]] = []
        self.columns: List[str] = []
        self.rows: List[List[Any]] = []
        self.original_index = int(0)

        # Debounce flag
        self._showinfo_job_active = False

        # Build UI
        self._init_base_font()
        self._setup_ui()
        self._apply_theme()

        # Load initial data
        self._load_data()

    def _load_users(self) -> dict:
        """Load user configuration from JSON file."""
        try:
            with open("PyRAT_GUI/users.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.warning(None, "Warning", f"Could not load users.json: {e}")
            return {}

    def _init_base_font(self):
        """Initialize the application base font."""
        self.base_font = QFont(
            self.BASE_FONT_KWARGS["family"],
            self.BASE_FONT_KWARGS["size"],
        )
        self.setFont(self.base_font)

    def _setup_ui(self):
        """Set up the user interface layout and widgets."""
        outer = QVBoxLayout(self.central_widget)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setStretch(2, 5)

        # Top-top frame (theme, help, status, login, highlight color)
        toptop = QHBoxLayout()

        self.status_label = QLabel("No connection")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        toptop.addWidget(self.status_label)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.toggle_login_logout)
        toptop.addWidget(self.login_button)

        self.theme_btn = QPushButton("Theme")
        self.theme_btn.clicked.connect(self.switch_theme)
        toptop.addWidget(self.theme_btn)

        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.get_help)
        toptop.addWidget(self.help_btn)

        highlight_label = QLabel("Highlight Color:")
        highlight_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        toptop.addWidget(highlight_label)

        self.color_combo = QComboBox()
        self.color_combo.addItems(["Blue", "Green", "Pink"])
        self.color_combo.currentIndexChanged.connect(self.change_highlight_color)
        toptop.addWidget(self.color_combo)

        outer.addLayout(toptop, 0)

        # Top frame (filters)
        top = QHBoxLayout()
        top.addWidget(QLabel("Filter:"))
        self.filter_entry = QLineEdit()
        self.filter_entry.setPlaceholderText("Use \",\" separate keywords")
        self.filter_entry.returnPressed.connect(lambda: self.multi_filters(text=self.filter_entry.text()))
        top.addWidget(self.filter_entry)

        top.addWidget(QLabel("Preset Filters:"))

        self.mymice = QPushButton("My Mice")
        self.mymice.clicked.connect(lambda: self.preset_filters(text="responsible"))
        top.addWidget(self.mymice)

        self.WRmice = QPushButton("Water Restriction Mice")
        self.WRmice.setEnabled(False)
        self.WRmice.clicked.connect(lambda: self.preset_filters(text="Water Restriction Mice"))
        top.addWidget(self.WRmice)

        self.breeding = QPushButton("Breeding Mice")
        self.breeding.clicked.connect(lambda: self.preset_filters(text="Breeding"))
        top.addWidget(self.breeding)

        self.stockmice = QPushButton("Stock Mice")
        self.stockmice.clicked.connect(lambda: self.preset_filters(text="Stock"))
        top.addWidget(self.stockmice)

        self.experimice = QPushButton("Experimental Mice")
        self.experimice.clicked.connect(lambda: self.preset_filters(text="Experiment"))
        top.addWidget(self.experimice)

        self.rest = QPushButton("Reset")
        self.rest.clicked.connect(lambda: self.preset_filters(text=""))
        top.addWidget(self.rest)

        outer.addLayout(top, 1)

        # Middle frame (main table)
        middle = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setWordWrap(True)
        self.table.itemSelectionChanged.connect(self.showinfo)
        # self.table.itemSelectionChanged.connect(self.apply_selection_highlight)
        middle.addWidget(self.table)
        outer.addLayout(middle, 5)

        # Bottom frame (details/comments left, actions right)
        bottom = QHBoxLayout()

        # Comment/Detail frame (left)
        left = QVBoxLayout()

        # Comment tableW
        self.comment_tv = QTableWidget(0, 2)
        self.comment_tv.setHorizontalHeaderLabels(["Date", "Content"])
        self.comment_tv.horizontalHeader().setStretchLastSection(True)
        self.comment_tv.verticalHeader().setVisible(False)
        self.comment_tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        left.addWidget(self.comment_tv, stretch=3)  # Takes remaining space

        # Actions frame (right)
        right = QVBoxLayout()
        actionlabel = QLabel("Actions (Login required)")
        actionlabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        actionlabel.setFont(QFont(self.base_font.family(), self.base_font.pointSize(), QFont.Weight.Bold))
        right.addWidget(actionlabel)

        frq_used = QGridLayout()
        self.bw_label = QLabel("Weight (g)")
        self.bw_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        frq_used.addWidget(self.bw_label, 0, 0)
        self.weight_entry = QLineEdit()
        self.weight_entry.setPlaceholderText("Please enter weight (float)")
        self.weight_entry.returnPressed.connect(lambda: self.submit_post(text="weight"))
        frq_used.addWidget(self.weight_entry, 0, 1)

        self.water_label = QLabel("Water Delivery (ml)")
        self.water_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        frq_used.addWidget(self.water_label, 1, 0)
        self.waterdelivery_entry = QLineEdit()
        self.waterdelivery_entry.setPlaceholderText("Please enter water delivery (float)")
        self.waterdelivery_entry.returnPressed.connect(lambda: self.submit_post(text="waterdelivery"))
        frq_used.addWidget(self.waterdelivery_entry, 1, 1)

        self.cmt_label = QLabel("Comment")
        self.cmt_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        frq_used.addWidget(self.cmt_label, 2, 0)
        self.comment_entry = QLineEdit()
        self.comment_entry.setPlaceholderText("Please enter comment")
        self.comment_entry.returnPressed.connect(lambda: self.submit_post(text="comment"))
        frq_used.addWidget(self.comment_entry, 2, 1)

        right.addLayout(frq_used)

        self.toggle_rare_button = QPushButton("Show Rarely Used Actions")
        self.toggle_rare_button.clicked.connect(self.toggle_rare_actions)
        right.addWidget(self.toggle_rare_button)

        self.rare_group = QGroupBox()
        rare_layout = QGridLayout(self.rare_group)
        self.refbw_label = QLabel("Ref Weight")
        rare_layout.addWidget(self.refbw_label, 0, 0)
        self.refbw_entry = QLineEdit()
        self.refbw_entry.setPlaceholderText("Please enter reference body weight")
        self.refbw_entry.returnPressed.connect(lambda: self.submit_post(text="refbw"))
        rare_layout.addWidget(self.refbw_entry, 0, 1)

        self.implant_label = QLabel("Implant Weight")
        rare_layout.addWidget(self.implant_label, 1, 0)
        self.implantweight_entry = QLineEdit()
        self.implantweight_entry.setPlaceholderText("Please enter implant weight")
        self.implantweight_entry.returnPressed.connect(lambda: self.submit_post(text="implantweight"))
        rare_layout.addWidget(self.implantweight_entry, 1, 1)

        self.rare_group.setVisible(False)
        right.addWidget(self.rare_group)
        
        right.addStretch()  # Push everything to top

        bottom.addLayout(left, stretch=2)
        bottom.addLayout(right, stretch=1)
        outer.addLayout(bottom, 3)

        # Disabled until login
        self._set_posting_widget_states(False)

    def _apply_theme(self):
        """Apply the current theme stylesheet with PyQt6 compatible syntax."""
        font_family = self.base_font.family()
        font_size = self.base_font.pointSize()
        
        if self.current_theme == "light":
            # Light theme
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
            # Dark theme
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
        
        self.setStyleSheet(stylesheet)

    def _load_data(self):
        """Load animal data from API and populate table."""
        self.getlist()
        if self.rows:
            self._populate_table(self.rows)

    def switch_theme(self):
        """Toggle between light and dark themes."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()
        self.change_highlight_color()
        self.wt_highlight_color_on()
        self.configure_hidden_columns()

    def change_highlight_color(self, event: Optional[int] = None):
        """Update highlight color based on current theme and selected color."""
        color_choice = self.color_combo.currentText()
        if self.current_theme == "light":
            self.highlight_color = self.COLOR_MAP_LIGHT.get(color_choice, "#9CCDDD")
            self.selection_color = self.COLOR_MAP_SELECTED_LIGHT.get(color_choice, "#52BEE2")
        else:
            self.highlight_color = self.COLOR_MAP_DARK.get(color_choice, "#0055aa")
            self.selection_color = self.COLOR_MAP_SELECTED_DARK.get(color_choice, "#003663")
        self.apply_cagematch_highlight()
        self.apply_selection_highlight()

    def apply_selection_highlight(self):
        row = self.table.currentRow()
        row_color = QColor(self.selection_color)
        for c in range(self.table.columnCount()):
            item = self.table.item(row, c)
            if item:
                current_bg = item.background().color()
                if current_bg != self.red_bg:
                    item.setBackground(row_color)

    def apply_cagematch_highlight(self):
        """Apply highlight to rows matching the selected cage (Modified for PyQt6)."""
        # Clear all backgrounds except red
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    current_bg = item.background().color()
                    if current_bg != self.red_bg:
                        item.setBackground(QColor(Qt.GlobalColor.transparent))
        # Find column index of "Cage Number"
        try:
            cage_col = self.columns.index("Cage Number")
        except ValueError:
            cage_col = None

        # Apply highlighting
        for r in range(self.table.rowCount()):
            is_cage_match = False
            if cage_col is not None and self.selected_cage:
                cage_item = self.table.item(r, cage_col)
                is_cage_match = cage_item and str(cage_item.text()).strip() == str(self.selected_cage).strip()
            
            if is_cage_match:
                row_color = QColor(self.highlight_color)
                # print(r,"row")
                # print(self.original_index,"original index")
            else:
                continue  # No highlight neededs
            
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    current_bg = item.background().color()
                    if current_bg != self.red_bg:
                        item.setBackground(row_color)

    def wt_highlight_color_on(self):
        """Highlight Confirmed Mutations cells containing 'wt' with red background."""
        try:
            mut_col = self.columns.index("Confirmed Mutations")
        except ValueError:
            return
        self.red_bg = QColor("#ffcccc") if self.current_theme == "light" else QColor("#8b0000")
        for r in range(self.table.rowCount()):
            item = self.table.item(r, mut_col)
            if item and "wt" in item.text().lower():
                item.setBackground(self.red_bg)

    def connect(self):
        """Authenticate with the PyRAT API."""
        response = self.make_request("GET", "credentials")
        data = response.json() if response else {}

        if data.get("client_valid") and data.get("user_valid"):
            QMessageBox.information(self, "Success", "Login successful")
            self.enable_posting_features()
            self.close_login_window()
            return

        if data.get("client_valid") and not data.get("user_valid"):
            QMessageBox.warning(self, "Error", "Login failed. Invalid user token")
            return

        QMessageBox.warning(self, "Error", "Failed to authenticate")

    def format_genotype(self, text: str) -> str:
        """Format genotype string to show each mutation on a new line.
        
        Preferred: split on '|' separators; fallback: insert line breaks after
        'wt', 'het', 'hom' tokens case-insensitively.
        """
        s = str(text or "")
        if "|" in s:
            parts = [p.strip() for p in s.split("|")]
            return "\n".join(parts)
        for token in ("wt", "het", "hom"):
            s = s.replace(token, token + "\n")
            s = s.replace(token.upper(), token.upper() + "\n")
        # Normalize whitespace and remove empty lines
        return "\n".join(line.strip() for line in s.splitlines() if line.strip())

    def getlist(self):
        """Fetch animal list and transform fields for table display."""
        params = {
            "k": [
                "eartag_or_id",
                "labid",
                "room_name",
                "age_days",
                "age_weeks",
                "strain_name_with_id",
                "responsible_fullname",
                "responsible_id",
                "mutations",
                "weight",
                "comments",
                "date_last_comment",
                "cagenumber",
                "cagetype",
                "requests",
                "sex",
            ],
            "l": 2000,
        }

        response = self.make_request("GET", "animals", params=params)
        if not response:
            QMessageBox.warning(self, "Error", "Failed to retrieve animal list. Please check connection")
            return
        self.info = response.json() or []

        for idx, animal in enumerate(self.info):
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
            "_index",
            "Eartag/Id",
            "Lab ID",
            "Weight",
            "Sex",
            "Strain Name",
            "Responsible",
            "Age(w)",
            "Room",
            "Confirmed Mutations",
            "Cage Type",
            "Cage Number",
        ]

        info_filtered = [{k: a.get(k, "") for k in keys} for a in self.info]
        self.columns = list(info_filtered[0].keys()) if info_filtered else keys
        self.rows = [[animal[col] for col in self.columns] for animal in info_filtered]

    def _populate_table(self, rowdata: List[List[Any]]):
        """Initial build or refresh of the main table with provided rows."""
        # CRITICAL: Disable sorting before modifying table to prevent None items
        self.table.setSortingEnabled(False)
        
        self.table.clear()
        self.table.setColumnCount(len(self.columns))
        self.table.setRowCount(len(rowdata))
        self.table.setHorizontalHeaderLabels(self.columns)

        for r, row in enumerate(rowdata):
            for c, val in enumerate(row):
                # Multi-line formatting for Confirmed Mutations column
                if c < len(self.columns) and self.columns[c] == "Confirmed Mutations":
                    item = QTableWidgetItem(self.format_genotype(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item = QTableWidgetItem(str(val))
                item.setFont(self.base_font)
                # Align non-text numerics centered for readability
                if isinstance(val, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.configure_hidden_columns()
        
        # Re-enable sorting after all items are set
        self.table.setSortingEnabled(True)
        self.wt_highlight_color_on()

    def _rebuild_table(self, filtered_rows: List[List[Any]]):
        """Helper method to rebuild the table with filtered data."""
        self._populate_table(filtered_rows)
        # Try to preserve the previous selection if the selected animal is in the filtered data
        if hasattr(self, 'original_index') and self.original_index is not None:
            for r in range(self.table.rowCount()):
                idx_item = self.table.item(r, 0)
                if idx_item and str(idx_item.text()) == str(self.original_index):
                    self.table.selectRow(r)
                    # showinfo will be triggered, applying highlights
                    return
        # If no selection preserved, no highlights

    def multi_filters(self, text: Optional[str] = None):
        if not text or text.strip() == "":
            QMessageBox.information(self, "Info", "No filter keywords provided.")
            return
        keywords = [k.strip() for k in text.split(",")]
        filtered_row = [
            row for row in self.rows
            if all(any(k.lower() in str(cell).lower() for cell in row) for k in keywords)
        ]
        self._rebuild_table(filtered_row)
        self.filter_entry.clear()

    def preset_filters(self, text: Optional[str] = None):
        if text == "responsible":
            text = self.current_user
        if text == "":
            self._rebuild_table(self.rows)
        else:
            filtered_row = [row for row in self.rows if any(str(text) in str(cell) for cell in row)]
            self._rebuild_table(filtered_row)

    def configure_hidden_columns(self):
        """Hide the helper index column (column 0)."""
        if self.table.columnCount() > 0:
            self.table.setColumnHidden(0, True)

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
                self.update_animal_weight(animal_id, weight_value)
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
                self.post_comment(animal_id, entry_text)
                has_changes = True

            else:
                entry_text = f"{text}: {entry_text}"
                self.post_comment(animal_id, entry_text)
                has_changes = True


        if not has_changes:
            QMessageBox.warning(self, "Warning", "Nothing to submit.")
            return

        entry_widget.clear()
        self.showinfo_update()

    def toggle_rare_actions(self):
        """Toggle the visibility of the advanced actions frame."""
        if self.rare_group.isVisible():
            self.rare_group.setVisible(False)
            self.toggle_rare_button.setText("Show Rare Used Actions")
        else:
            self.rare_group.setVisible(True)
            self.toggle_rare_button.setText("Hide Rare Used Actions")

    def showinfo(self):
        """Debounced selection callback from table (Modified for PyQt6)."""
        if self._showinfo_job_active:
            return
        self._showinfo_job_active = True
        QTimer.singleShot(0, self.showinfo_update)

    def showinfo_update(self):
        self._showinfo_job_active = False
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

        self.animal_selected = self.info[self.original_index]
        self.selected_cage = str(self.table.item(r, self.columns.index("Cage Number")).text()).strip() if "Cage Number" in self.columns else self.animal_selected.get("Cage Number", "").strip()

        comments = self.animal_selected.get("comments", []) or []
        self.comment_tv.setRowCount(0)
        for cmt in comments:
            date = (cmt.get("created", "") or "")[:10]
            content = cmt.get("content", "") or ""
            row = self.comment_tv.rowCount()
            self.comment_tv.insertRow(row)
            date_item = QTableWidgetItem(date)
            date_item.setFont(self.base_font)
            content_item = QTableWidgetItem(content)
            content_item.setFont(self.base_font)
            self.comment_tv.setItem(row, 0, date_item)
            self.comment_tv.setItem(row, 1, content_item)

        self.comment_tv.resizeColumnsToContents()

        self.apply_cagematch_highlight()
        self.apply_selection_highlight()

    def get_help(self):
        """Display usage instructions in a help dialog."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Help")
        dlg.setMinimumSize(1000,650)
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

    def toggle_login_logout(self):
        """Toggle login/logout."""
        if self.login_button.text() == "Login":
            self.login()
        else:
            self.logout()

    def login(self):
        """Show PIN entry dialog for authentication."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Login")
        grid = QGridLayout(dlg)
        grid.addWidget(QLabel("Please login to post"), 0, 0, 1, 2)
        grid.addWidget(QLabel("Pin"), 1, 0)
        self.login_entry = QLineEdit()
        self.login_entry.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(self.login_entry, 1, 1)
        submit = QPushButton("Submit")
        grid.addWidget(submit, 1, 2)
        submit.clicked.connect(self.compare_PIN)
        self._login_dialog = dlg
        dlg.adjustSize()
        dlg.exec()

    def _set_posting_widget_states(self, enabled: bool):
        """Enable or disable posting widgets based on login state."""
        for w in [
            self.weight_entry,
            self.comment_entry,
            self.waterdelivery_entry,
            self.refbw_entry,
            self.implantweight_entry,
        ]:
            w.setEnabled(enabled)
        for l in [
            self.refbw_label,
            self.implant_label,
            self.bw_label,
            self.cmt_label,
            self.water_label,
        ]:
            l.setEnabled(enabled)

    def enable_posting_features(self):
        """Enable posting features after successful login."""
        self._set_posting_widget_states(True)
        self.status_label.setText(f"Connected-{self.current_user}")
        self.status_label.setStyleSheet("color: green;")
        self.login_button.setText("Log out")

    def close_login_window(self):
        """Close the login dialog and update button state."""
        try:
            if hasattr(self, "_login_dialog") and self._login_dialog is not None:
                self._login_dialog.accept()
        except Exception:
            pass
        self.login_button.setText("Log out")

    def compare_PIN(self):
        """Verify entered PIN against user database."""
        pin = self.login_entry.text().strip() if hasattr(self, "login_entry") else ""
        selected_user = self.current_user
        user_info = self.users.get(selected_user, {})
        correct_pin = user_info.get("PIN", "")
        if pin == correct_pin:
            self.connect()
        else:
            QMessageBox.warning(self, "Error", "Invalid PIN")

    def logout(self):
        self._set_posting_widget_states(False)
        self.status_label.setText("No connection")
        self.status_label.setStyleSheet("color: red;")
        self.login_button.setText("Login")
        QMessageBox.information(self, "Info", "Logged out successfully")

    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make a request with consistent error handling."""
        url = f"{self.URL}/{endpoint.lstrip('/') }"
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
            QMessageBox.warning(self, "Timeout", "The request timed out.")
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self, "Connection Error", "Unable to connect to the API.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")
        return None

    def calculate_water_requirement(self, weight_g: float) -> float:
        """Calculate water requirement: 40ml/kg/day."""
        if weight_g <= 0:
            raise ValueError("Weight must be positive")
        weight_kg = weight_g / 1000.0
        water_ml = weight_kg * 40.0
        return round(water_ml, 2)

    def update_animal_weight(self, animal_id: str, weight_g: float, weight_time: Optional[str] = None):
        """Update an animal's weight via API."""
        if weight_time is None:
            weight_time = datetime.now(timezone.utc).isoformat()
        data = {"weight": float(weight_g), "weight_time": weight_time}
        response = self.make_request("POST", f"animals/{animal_id}/weight", json=data)
        info = response.json() if response else {}
        if response and response.status_code in [200, 201, 204]:
            QMessageBox.information(self, "Success", "Weight updated successfully")
        elif response:
            QMessageBox.warning(self, "Error", f"Failed to update weight: {info}")
        else:
            QMessageBox.warning(self, "Error", "No response from server")

    def post_comment(self, animal_id: str, comment_text: str):
        """Post a comment to an animal record."""
        data = {"comment": f"#{comment_text}"}
        response = self.make_request("POST", f"animals/{animal_id}/comments", json=data)
        if response and response.status_code == 200:
            QMessageBox.information(self, "Success", "Comment posted successfully")
        elif response:
            QMessageBox.warning(self, "Error", f"Failed to post comment: {response.text}")
        else:
            QMessageBox.warning(self, "Error", "No response from server")


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
