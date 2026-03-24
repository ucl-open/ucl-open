from os import replace
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
import requests
import json
import sys
import re
from datetime import datetime, timezone
from urllib.parse import urlencode
import shlex
import tkinter.font as tkFont
from ttkbootstrap.widgets.tableview import Tableview
#from ttkbootstrap.utility import enable_high_dpi_awareness

class PyratAPI:
    # Class constants for color mappings
    COLOR_MAP_LIGHT = {
        'Blue': "#9CCDDD",
        'Green': "#75D475",
        'Pink': "#E797A3"}
    COLOR_MAP_DARK = {
        'Blue': '#214f7e',
        'Green': '#2e5d2f',
        'Pink': '#78334f'}

    BASE_FONT_KWARGS = {
        "family": "Helvetica",
        "size": 12,
        "weight": "normal"}

    def __init__(self, window):
        self.window = window
        self.window.title("PyRAT GUI")
        
        self.session = requests.Session()
        self.URL = "https://ucl.pyrat.cloud/api/v3"
        self.client_token = "1-9vBhAUJnGJZldlehOEKX08" 
        self.timeout = 20

    #Set up font
        self._init_base_font()
        self.apply_base_font()

    #dpi sacle
        dpi = self.window.winfo_fpixels('1i')
        self.window.tk.call('tk', 'scaling', dpi / 72.0)

        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)
        
        self.root = ttk.Frame(self.window)
        self.root.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=0)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=0)
        
    #Users
        with open("PyRAT_GUI/users.json", "r") as f:
            self.users = json.load(f)
        self.current_user = "Ryan"  #default user
        self.current = window.style.theme.name.lower()
        self.getlist()
        self.highlight_color = 'lightblue'
        self.selected_cage = None

    def _init_base_font(self):
        """Create the base tk font once the root window exists."""
        # tkFont.Font expects the root via the root keyword (not -master option)
        self.base_font = tkFont.Font(root=self.window, **self.BASE_FONT_KWARGS)

    def apply_base_font(self):
        """Apply BASE_FONT to common ttk and tk widgets."""
        self.window.option_add("*Font", self.base_font)

        style = ttk.Style(self.window)
        common_styles = [
            "TLabel",
            "TButton",
            "TEntry",
            "TCombobox",
            "TFrame",
            "Treeview",
            "Tableview"
        ]

        for stylename in common_styles:
            try:
                style.configure(stylename, font=self.base_font)
            except tk.TclError:
                print(f"Failed to apply font to {stylename}")
                pass

    def switch_theme(self):
        #switch between themes
        new_theme = "sandstone" if "cyborg" in window.style.theme.name.lower() else "cyborg"
        window.style.theme_use(new_theme)
        self.current = new_theme
        self.change_highlight_color()
        self.apply_base_font()
        self.manual_autofit_tableview(self.tv)
        self.configure_hidden_columns()

    def change_highlight_color(self, event=None):
        if "sandstone" in self.current:
            self.highlight_color = self.COLOR_MAP_LIGHT.get(self.color_combo.get(), "#9CCDDD") 
        elif "cyborg" in self.current:
            self.highlight_color = self.COLOR_MAP_DARK.get(self.color_combo.get(), "#214f7e")
        self.apply_highlight()

    def apply_highlight(self):
        for item in self.tv.view.get_children():
            self.tv.view.item(item, tags=())
        if self.selected_cage:
            for item in self.tv.view.get_children():
                values = self.tv.view.item(item, 'values')
                if len(values) > 10 and str(values[10]).strip() == str(self.selected_cage).strip():
                    self.tv.view.item(item, tags=('highlight',))
        self.tv.view.tag_configure('highlight', background=self.highlight_color)

    #this is for testing
    # def print_widget_widths(self):
        #print("WINDOW:", self.window.winfo_width())
        #print("ROOT:", self.root.winfo_width())
        # print("WEIGHT FRAME:", self.weight_frame.winfo_width())
        # print("COMMENT FRAME:", self.comment_frame.winfo_width())
        # print("USER FRAME:", self.user_box.winfo_width())
        # # print("CONNECTION LABEL:", self.connection.winfo_width())
        
    def autosize_window(self, window):
        window.update_idletasks()
        req_w = window.winfo_reqwidth()
        req_h = window.winfo_reqheight()
        window.geometry(f"{req_w}x{req_h}")
        window.minsize(req_w, req_h)

    def manual_autofit_tableview(self, tableview=None):
        """Manually autofit tableview since it doesn't support different font"""
        if not tableview:
            return
        f = self.base_font
        columns = tableview.view["columns"]
        col_widths = []
        for col in columns:
            head = tableview.view.heading(col)["text"]

            if col == "_index":
                col_widths.append(0)
                continue

            max_width = f.measure(head)

            for item in tableview.view.get_children():
                val = tableview.view.set(item, col)
                max_width = max(max_width, f.measure(str(val)))

            col_widths.append(max_width + 10)

        for col, width in zip(columns, col_widths):
            tableview.view.column(col, width=width)

    def connect(self):

        self.session = requests.Session()
        response = self.make_request('GET', 'credentials')
        data = response.json() if response else {}
        
        if data['client_valid'] and data['user_valid']:
            messagebox.showinfo("Success", "Login successful")
            self.enable_posting_features()
            self.close_login_window()
            return

        if data['client_valid'] and not data['user_valid']:
            messagebox.showwarning("Error", "Login failed. Invalid user token")
            return
            
    def getlist(self):
        params = {
            "k": [
                "eartag_or_id",
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
                "sex"
            ],
            "l": 2000
        }
        self.response = self.make_request('GET', 'animals', params=params)

        if not self.response:
            messagebox.showwarning("Error", "Failed to retrieve animal list. Please check connection")
            return None
        self.info = self.response.json()

        #rename and add fields
        for idx, animal in enumerate(self.info):
            muts = animal.get("mutations", [])
            animal["Confirmed Mutations"] = " | ".join(
                f"{m['mutationname']}-{m['mutationgrade'].upper() if m['mutationgrade'] in ['het', 'hom'] else m['mutationgrade']}"
                for m in muts
            )
            animal["Age(d)"] = animal.get("age_days", "")
            animal["Age(w)"] = animal.get("age_weeks", "")
            animal["Room"] = animal.get("room_name", "")
            animal["Eartag/Id"] = animal.get("eartag_or_id", "")
            animal["Cage Number"] = animal.get("cagenumber", "")
            animal["Cage Type"] = animal.get("cagetype", "")
            animal["Responsible"] = animal.get("responsible_fullname", "")
            animal["Sex"] = animal.get("sex", "").capitalize()
            animal["_index"] = idx   # hidden index for locating row

    #top top frame
        toptop_frame = ttk.Frame(self.root, border=1, relief= "sunken")
        toptop_frame.grid(row=0, column=0,sticky = "nsew")

        ttk.Button(toptop_frame, text= "Theme", command= lambda:self.switch_theme()).grid(row=0, column=0, sticky="w")

        ttk.Button(toptop_frame, text="Help", command=lambda: self.get_help()).grid(row=0, column=1, padx=5, sticky="w")
        self.status = ttk.Label(toptop_frame, text=(f"No connection"), border= 1, relief="raised", anchor='center', foreground="red")
        self.status.grid(row=0, column=2, padx=5,sticky="w")

        self.login_button = ttk.Button(toptop_frame, text="Login", command=lambda: self.toggle_login_logout(), bootstyle='warning')
        self.login_button.grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(toptop_frame, text="Highlight Color:").grid(row=0, column=4, sticky="w", padx=(10,5))
        self.color_combo = ttk.Combobox(toptop_frame, values=['Blue', 'Green', 'Pink'], state="readonly", width=8)
        self.color_combo.grid(row=0, column=5, sticky="w", padx=5)
        self.color_combo.set('Blue')
        self.color_combo.bind('<<ComboboxSelected>>', self.change_highlight_color)

    #top frame
        self.top_frame = ttk.Frame(self.root, border=1, relief="sunken")
        self.top_frame.grid(row=1, column=0, sticky="nsew")

        self.filter_button = ttk.Label(self.top_frame, text="Filter")
        self.filter_button.grid(row=1, column=0, sticky="w")

        self.filter_entry = ttk.Entry(self.top_frame)
        self.filter_entry.grid(row=1, column=1, sticky="w", padx=5)
        self.filter_entry.bind('<Return>', lambda event: self.multi_filters(text = self.filter_entry.get()))

        ttk.Label(self.top_frame, text = "Preset Filters:").grid(row=1, column=2, sticky="w", padx=(0,5))

        self.mymice = ttk.Button(self.top_frame, text="My Mice", command = lambda: self.preset_filters(text= 'responsible'))
        self.mymice.grid(row=1, column=3, sticky="w", padx=5)

        self.WRmice = ttk.Button(self.top_frame, text="Water Restriction Mice",state= 'disabled',command = lambda: self.preset_filters(text= 'Water Restriction Mice'))
        self.WRmice.grid(row=1, column=4, sticky="w", padx=5)

        self.breeding = ttk.Button(self.top_frame, text="Breeding Mice", command = lambda: self.preset_filters(text= 'Breeding'))
        self.breeding.grid(row=1, column=5, sticky="w", padx=5)

        self.stockmice = ttk.Button(self.top_frame, text="Stock Mice", command = lambda: self.preset_filters(text= 'Stock'))
        self.stockmice.grid(row=1, column=6, sticky="w", padx=5)
        
        self.experimice = ttk.Button(self.top_frame, text="Experimental Mice", command = lambda: self.preset_filters(text= 'Experiment'))
        self.experimice.grid(row=1, column=7, sticky="w", padx=5)

        self.rest = ttk.Button(self.top_frame, text="Reset", command = lambda: self.preset_filters(text= ''))
        self.rest.grid(row=1, column=8, sticky="w", padx=5)

    #middle frame
        middleframe = ttk.Frame(self.root, border=1, relief="sunken")
        middleframe.grid(row=2, column=0, sticky="nsew") 
        middleframe.rowconfigure(0, weight=1) 
        middleframe.columnconfigure(0, weight=1)

        keys = [
            "_index",             # hidden
            "Eartag/Id",
            "weight",
            "Sex",
            "strain_name_with_id",
            "Responsible",
            "Age(w)",
            "Room",
            "Confirmed Mutations",
            "Cage Type",
            "Cage Number"
        ]

        info_filtered = [
            {k: animal.get(k, "") for k in keys}
            for animal in self.info
        ]

        self.columns = list(info_filtered[0].keys())
        self.rows = [[animal[col] for col in self.columns] for animal in info_filtered]

        #build table
        self.coldata = []
        for col in self.columns:
            if col == "_index":
                self.coldata.append({"text": "", "width": 0, "stretch": False})
            else:
                self.coldata.append({"text": col.replace("_", " ").title()})

        self.tv = Tableview(
            master=middleframe,
            coldata=self.coldata,
            rowdata=self.rows,
            bootstyle="primary",
            autofit=True,
            height=20,
            autoalign=True,
            on_select=self.showinfo,
            yscrollbar=True
        )

        self.tv.grid(row=0, column=0, sticky="nsew")
        self.manual_autofit_tableview(self.tv)
        self.configure_hidden_columns()

    #bottom frame
        self.bottomframe = ttk.Frame(self.root, border=1, relief="sunken")
        self.bottomframe.grid(row=3, column=0, sticky="nsew")
        # comment frame takes 2/3 of width, action frame takes 1/3 of width
        # uniform keeps proportions stable across theme changes
        self.bottomframe.columnconfigure(0, weight=2, uniform="bottom")  # comment frame - 2/3 width
        self.bottomframe.columnconfigure(1, weight=1, uniform="bottom")  # action frame - 1/3 width
        self.bottomframe.rowconfigure(1, weight=1)

        #comment frame
        self.comment_frame = ttk.Frame(self.bottomframe, border=1, relief="sunken")
        self.comment_frame.grid(row=1, column=0, sticky="nsew")
        # Let the detail row keep minimal height; give the comment table the growth space
        self.comment_frame.rowconfigure(0, weight =0)
        self.comment_frame.rowconfigure(1, weight =3)
        self.comment_frame.columnconfigure(0, weight=1)

        self.build_detail_and_comment_views()

        #posting frame
        self.post_frame = ttk.Frame(self.bottomframe,border=1, relief="sunken")
        self.post_frame.grid(row=1, column=1, sticky="nsew")
        self.post_frame.columnconfigure(0, weight=1)

        ttk.Label(self.post_frame, text="Actions (Login required)", 
          font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0,10))
    
    #frequest used function
        frq_used = ttk.Frame(self.post_frame)
        frq_used.grid(row=1, column=0, sticky="ew")
        frq_used.columnconfigure(0, weight=1)
        frq_used.columnconfigure(1, weight=1)
        # frq_used.columnconfigure(2, weight=1)
        frq_used.rowconfigure(0, weight=1)
        frq_used.rowconfigure(1, weight=1)
        frq_used.rowconfigure(2, weight=1)

        self.bw = ttkb.Label(frq_used, text="Weight", style="secondary.Inverse.TLabel")
        self.bw.grid(row=0, column=0, sticky="ew", padx=3)
        self.weight_entry = ttk.Entry(frq_used)
        self.weight_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.weight_entry.bind('<Return>', lambda event: self.submit_post(text = "weight"))

        self.cmt = ttkb.Label(frq_used, text="Comment",  style="secondary.Inverse.TLabel")
        self.cmt.grid(row=1, column=0, sticky="ew", padx=3)
        self.comment_entry = ttk.Entry(frq_used)
        self.comment_entry.grid(row=1, column=1, sticky= "ew",padx=5)
        self.comment_entry.bind('<Return>', lambda event: self.submit_post(text = "comment"))

        self.waterdelivery = ttkb.Label(frq_used, text="Water Delivery",  style="secondary.Inverse.TLabel")
        self.waterdelivery.grid(row=2, column=0, sticky="ew", padx=3)
        self.waterdelivery_entry = ttk.Entry(frq_used)
        self.waterdelivery_entry.grid(row=2, column=1, sticky= "ew", padx=5)
        self.waterdelivery_entry.bind('<Return>', lambda event: self.submit_post(text = "waterdelivery"))

        for i in (self.bw, self.cmt, self.waterdelivery, self.weight_entry, self.comment_entry, self.waterdelivery_entry):
            i.configure(state="disabled")
    
    #rare used function
        self.toggle_rare_button = ttk.Button(self.post_frame, text="Show Rare Used Actions", command=self.toggle_rare_actions)
        self.toggle_rare_button.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        self.rare_used = ttk.Frame(self.post_frame)
        self.rare_used.grid(row=3, column=0, sticky="ew", pady = 7)
        self.rare_used.columnconfigure(0, weight=1)
        self.rare_used.columnconfigure(1, weight=1)

        self.refbw = ttk.Label(self.rare_used, text="Ref Weight", style = "secondary.Inverse.TLabel")
        self.refbw.grid(row=0, column=0, sticky="ew", padx=3)
        self.refbw_entry = ttk.Entry(self.rare_used)
        self.refbw_entry.grid(row=0, column =1, sticky ="ew", padx=5)
        self.refbw_entry.bind('<Return>', lambda event: self.submit_post(text = "refbw"))

        self.implantweight = ttk.Label(self.rare_used, text="Implant Weight", style="secondary.Inverse.TLabel")
        self.implantweight.grid(row=1, column=0, sticky="ew", padx=3)
        self.implantweight_entry = ttk.Entry(self.rare_used)
        self.implantweight_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.implantweight_entry.bind('<Return>', lambda event: self.submit_post(text = "implantweight"))

        for i in (self.refbw, self.implantweight, self.refbw_entry, self.implantweight_entry):
            i.configure(state="disabled")
    
        self.rare_used.grid_remove()

    def toggle_rare_actions(self):
        """Toggle the visibility of the advanced actions frame."""
        if self.rare_used.winfo_ismapped():
            self.rare_used.grid_remove()
            self.toggle_rare_button.config(text="Show Rare Used Actions")
        else:
            self.rare_used.grid()
            self.toggle_rare_button.config(text="Hide Rare Used Actions")

    def _rebuild_table(self, filtered_rows):
        """Helper method to rebuild the table with filtered data"""
        middleframe = self.tv.master
        self.tv.destroy()
        
        self.tv = Tableview(
            master=middleframe,
            coldata=self.coldata,
            rowdata=filtered_rows,
            bootstyle="primary",
            autofit=True,
            height=20,
            autoalign=True,
            on_select=self.showinfo,
            yscrollbar=True
        )
        
        self.tv.grid(row=0, column=0, sticky="nsew")

        self.manual_autofit_tableview(self.tv)
        self.configure_hidden_columns()
        self.apply_highlight()

    def multi_filters(self, text=None):
        if not text or text.strip() == "":
            self.preset_filters(text='')
            return
        
        # Split by comma and strip whitespace from each keyword
        keywords = [keyword.strip() for keyword in text.split(",")]
        
        # Filter rows that contain ALL keywords
        filtered_row = [row for row in self.rows
                        if all(any(keyword.lower() in str(cell).lower() for cell in row) 
                               for keyword in keywords)]
        
        self._rebuild_table(filtered_row)

    def preset_filters(self, text=None):
        if text == 'responsible':
            text = self.current_user
        filtered_row = [row for row in self.rows
                        if any(text in str(cell) for cell in row)]
        
        self._rebuild_table(filtered_row)

    def configure_hidden_columns(self):
        """Helper to configure hidden columns - call after build_table_data"""
        self.tv.view.column(0, width=0, stretch=False)

    def submit_post(self, text=None):
        # Get selection
        selection = self.tv.view.selection()

        row_values = self.tv.view.item(selection[0])["values"]
        idx = int(row_values[0])
        animal_id = self.info[idx]["eartag_or_id"]

        # Dynamically get the entry widget based on text
        entry_name = f"{text}_entry"
        entry_widget = getattr(self, entry_name, None)
        
        if not entry_widget:
            messagebox.showerror("Error", f"Entry widget not found for {text}")
            return

        # Get text from entry widget (handle both Entry and Text widgets)
        if isinstance(entry_widget, tk.Text):
            entry_text = entry_widget.get("1.0", "end").strip()
        else:
            entry_text = entry_widget.get().strip()

        has_changes = False

        # Post weight
        if text == "weight" and entry_text:
            try:
                weight_value = float(entry_text)
            except ValueError:
                messagebox.showwarning("Error", "Invalid weight value.")
                return

            self.update_animal_weight(animal_id, weight_value)
            has_changes = True

        # Post comment or other text
        elif entry_text:
            self.post_comment(animal_id, entry_text)
            has_changes = True

        if not has_changes:
            messagebox.showwarning("Warning", "Nothing to submit.")
            return

        # Success - clear the entry widget
        if isinstance(entry_widget, tk.Text):
            entry_widget.delete("1.0", tk.END)
        else:
            entry_widget.delete(0, tk.END)

        # Refresh detail panel
        self.showinfo() 

    def build_detail_and_comment_views(self):
        """Create (once) the detail tree and comment table. Do NOT recreate on each selection."""

        self.detail_cols = ["Age(d)", "responsible_id", "Cage Number"]

        self.detail_tv = ttk.Treeview(self.comment_frame, show="headings", height=1)
        self.detail_tv.grid(row=0, column=0, sticky="ew")
        self.detail_tv["columns"] = self.detail_cols

        for col in self.detail_cols:
            title = col.replace("_", " ").title()
            self.detail_tv.heading(col, text=title)
            self.detail_tv.column(col, anchor="center", stretch=False, width=140)

        self.comment_tv = Tableview(
            master=self.comment_frame,
            coldata=[
                {"text": "Date", "stretch": False},
                {"text": "Content", "stretch": True},
            ],
            rowdata=[],          # start empty
            autofit=True,
            height=8,
            bootstyle="info",
            yscrollbar=True,
        )
        self.comment_tv.grid(row=1, column=0, sticky="nsew")

        self.comment_frame.rowconfigure(1, weight=3)

        self._showinfo_job = None

    def showinfo(self, event=None):
        """Selection callback from table 1. Debounced to avoid heavy work per arrow keypress."""
        if getattr(self, "_showinfo_job", None) is not None:
            try:
                self.root.after_cancel(self._showinfo_job)
            except Exception:
                pass
        self._showinfo_job = self.root.after_idle(self.showinfo_update)

    def showinfo_update(self):
        self._showinfo_job = None

        if not hasattr(self, "tv") or not hasattr(self, "detail_tv") or not hasattr(self, "comment_tv"):
            return

        sel = self.tv.view.selection()
        if not sel:
            return

        row_values = self.tv.view.item(sel[0]).get("values", [])
        if not row_values:
            return

        try:
            original_index = int(row_values[0])
        except Exception:
            return

        if original_index < 0 or original_index >= len(self.info):
            return

        animal_selected = self.info[original_index]

        try:
            self.selected_cage = row_values[10]
        except Exception:
            self.selected_cage = animal_selected.get("Cage Number", "")

        detail_values = [
            animal_selected.get("Age(d)", ""),
            animal_selected.get("responsible_id", ""),
            animal_selected.get("Cage Number", ""),
        ]

        for iid in self.detail_tv.get_children():
            self.detail_tv.delete(iid)
        self.detail_tv.insert("", "end", values=detail_values)

        comments = animal_selected.get("comments", [])

        comment_rows = []
        for c in comments:
            date = (c.get("created", "") or "")[:10]
            content = c.get("content", "") or ""
            comment_rows.append([date, content])

        view = self.comment_tv.view
        for iid in view.get_children():
            view.delete(iid)

        for r in comment_rows:
            view.insert("", "end", values=r)

        if hasattr(self, "apply_highlight"):
            self.apply_highlight()

        try:
            self.tv.view.focus_set()
        except Exception:
            pass
        
    def get_help(self):

        """Display usage instructions in a new window"""
        self.helpwindow = tk.Toplevel(self.window)
        self.helpwindow.title("Help")
        self.helpwindow.geometry("650x600")
        
        frame = ttk.Frame(self.helpwindow)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        #scrollbar
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        #text widget
        text_widget = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        #configure scrollbar
        scrollbar.config(command=text_widget.yview)
        
        help_text = """
        PyRAT GUI User Guide
        ======================================

        This application allows you to interact with the PyRAT API to manage animal data.
        The connection is made with the default user Pip. To switch user, click login button and enter your PIN.
        You will be logged in if PIN matches your PIN. If PIN matches another user, you will be prompted to switch user.

        ======================================

        Main Features:

        -Multiple filter: enter the keyword you want in the entry box next to Filter, separate keywords by ",", no space needed. For example, Ryan,cdh23. Press enter to apply the filter.
        
        -Preset filters: some filters are preset for some situations. Reset button will clear all filters. 
        
        -Animal list & Details: Click on an animal in the Animal list (middle) to view detailed information and comments (bottom left).  
        
        -Actions: You would need to login with your PIN to post any information to PyRAT.

        ======================================

        Note:

        -For work requests, please use PyRAT. This GUI only provides quick overview and few posting capabilities.

        """
        text_widget.insert(tk.END, help_text.strip())
        text_widget.config(state=tk.DISABLED)  #read-only

        #close button
        close_button = ttk.Button(self.helpwindow, text="Close", command=self.helpwindow.destroy)
        close_button.pack(pady=5)

        self.autosize_window(self.helpwindow)
        self.helpwindow.grab_set()
        self.helpwindow.wait_window()

    def toggle_login_logout(self):
        if self.login_button["text"] == "Login":
            self.login()
        else:
            self.logout()

    def login(self):
        self.loginwindow = tk.Toplevel(self.window)
        self.loginwindow.title("Login")

        frame = ttk.Frame(self.loginwindow)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Please login to post", font= ("tkdefaultfont", 11, "bold")).grid(row=0, column=0, sticky="w")

        ttk.Label(frame, text="Pin", font= ("tkdefaultfont", 10)).grid(row=1, column=0, sticky="w")

        self.login_entry = ttk.Entry(frame, width=10)
        self.login_entry.grid(row=1, column=1, sticky="w")
        ttk.Button(frame, text="Submit", command=lambda: self.compare_PIN()).grid(row=1, column=2, sticky="w")
        self.autosize_window(self.loginwindow)

        self.loginwindow.bind('<Return>', lambda event: self.compare_PIN())
        self.loginwindow.grab_set()
        self.loginwindow.wait_window()

    def _set_posting_widget_states(self, state, style):
        """Helper to set state and style for all posting widgets"""
        # Set entry states
        for entry in [self.weight_entry, self.comment_entry, self.waterdelivery_entry, 
                      self.refbw_entry, self.implantweight_entry]:
            entry['state'] = state
        
        # Set label states and styles
        for label in [self.refbw, self.implantweight, self.bw, self.cmt, self.waterdelivery]:
            label['state'] = state
            label.configure(style=style)

    def enable_posting_features(self):
        self._set_posting_widget_states("normal", "info.Inverse.TLabel")
        self.status['text'] = (f"Connected-{self.current_user}")
        self.status['foreground'] = "green"
        
    def close_login_window(self):
        """Close the login window and update button state"""
        self.login_entry.delete(0, tk.END)
        self.login_entry.master.destroy()
        self.loginwindow.destroy()
        self.login_button.configure(bootstyle="success")
        self.login_button["text"] = "Log out"

    def compare_PIN(self):
        pin = self.login_entry.get()
        selected_user = self.current_user

        user_info = self.users.get(selected_user, {})
        correct_pin = user_info.get("PIN", "")

        if pin == correct_pin:
            self.connect()
                
        else:
            matched_user = None
            for username, user_data in self.users.items():
                if user_data.get("PIN") == pin:
                    matched_user = username
                    break
            
            if matched_user:
                response = messagebox.askyesno("Warning", f"PIN matched with {matched_user}. Do you want to switch?")
                if response:
                    self.current_user = matched_user
                    self.connect()
            else:
                messagebox.showwarning("Error", "Invalid PIN")

    def logout(self):
        self._set_posting_widget_states("disabled", "secondary.Inverse.TLabel")
        self.status['text'] = "No connection"
        self.login_button.configure(bootstyle="warning")
        self.login_button["text"] = "Login"
        messagebox.showinfo("Info", "Logged out successfully")

    def make_request(self, method, endpoint, **kwargs):
        """Make a request with consistent error handling"""
        url = f"{self.URL}/{endpoint.lstrip('/')}"
        kwargs.setdefault('timeout', self.timeout)

        #attach auth tuple using the currently connected user's token (if any)
        token = ""
        if self.current_user and self.current_user in self.users:
            token = self.users[self.current_user].get("token", "")
        kwargs['auth'] = (self.client_token, token)

        try:
            #prefer using the session so headers/cookies persist
            if method.upper() == 'GET':
                response = self.session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = self.session.post(url, **kwargs)
            elif method.upper() == 'PUT':
                response = self.session.put(url, **kwargs)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.Timeout:
            print(f"Request timed out after {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Connection error - check network/VPN")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    def calculate_water_requirement(self, weight_g):
        """Calculate water requirement: 40ml/kg/day"""
        if weight_g <= 0:
            return 0
        
        weight_kg = weight_g / 1000.0
        water_ml = weight_kg * 40.0
        
        return round(water_ml, 2)
    
    def update_animal_weight(self, animal_id, weight_g, weight_time=None):
        """Update an animal's weight via API"""
        if weight_time is None:
            weight_time = datetime.now(timezone.utc).isoformat() + 'Z'
        
        data = {
            "weight": float(weight_g),
            "weight_time": weight_time
        }
        
        response = self.make_request('POST', f'animals/{animal_id}/weight', json=data)
        info = response.json() if response else {}
        print(info)
        print(response.status_code)

        if response and response.status_code in [200, 201, 204]:
            messagebox.showinfo("Success", "Weight updated successfully!")
            return True
        elif response:
            messagebox.showerror("Error", f"Response: {response.text[:500]}")
            return False
        else:
            messagebox.showerror("Error", f"Failed to update weight: Status {response.status_code if response else 'No response'}")
            return False
           
    def post_comment(self, animal_id, comment_text):
        """Post a comment to an animal"""
       
        data = {'comment': comment_text}
        response = self.make_request('POST', f'animals/{animal_id}/comments', json=data)
        
        if response and response.status_code == 200:
            messagebox.showinfo("Success", "Comment posted successfully!")
            return True
        elif response:
            messagebox.showerror("Error", f"Response: {response.text[:200]}")
            return False
        else:
            messagebox.showerror("Error", f"Failed: Status {response.status_code if response else 'No response'}")
            return False

if __name__ == "__main__":
    window = ttkb.Window(themename= "sandstone")
    app = PyratAPI(window)

    window.mainloop()