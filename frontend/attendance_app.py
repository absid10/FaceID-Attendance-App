"""Tkinter application with navigation-focused UI for face attendance."""

from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.attendance_core import (
    delete_user_profile,
    load_attendance,
    load_user_details,
    load_user_records,
    run_recognition,
)
from backend.requests_core import add_request, load_requests, update_request_status

TITLE_FONT = ('Bahnschrift', 18, 'bold')
BODY_FONT = ('Bahnschrift', 11)
BG_COLOR = '#0f172a'
SIDEBAR_COLOR = '#020617'
CARD_COLOR = '#1e293b'
ACCENT_COLOR = '#22d3ee'
HIGHLIGHT_COLOR = '#38bdf8'
DATA_DIR = ROOT_DIR / 'data'
DATASET_DIR = DATA_DIR / 'dataset'
SCRIPTS_DIR = ROOT_DIR / 'scripts'


class AttendanceViewer(tk.Toplevel):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title('Attendance Log')
        self.configure(bg=BG_COLOR)
        self.geometry('680x460')
        self.minsize(620, 420)
        self.resizable(True, True)
        self._build_widgets()
        self.refresh()

    def _build_widgets(self) -> None:
        header = tk.Label(self, text='Logged Attendance', font=TITLE_FONT,
                          fg='white', bg=BG_COLOR)
        header.pack(pady=(16, 8))

        columns = ('Id', 'Name', 'Date', 'Time')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=16)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center', width=110)
        self.tree.pack(fill='both', padx=16, pady=8, expand=True)

        btn_row = tk.Frame(self, bg=BG_COLOR)
        btn_row.pack(pady=(0, 16))

        refresh_btn = ttk.Button(btn_row, text='Refresh Log', style='Accent.TButton',
                                 width=18, command=self.refresh)
        refresh_btn.grid(row=0, column=0, padx=6)

        close_btn = ttk.Button(btn_row, text='Close', style='Secondary.TButton',
                               width=12, command=self.destroy)
        close_btn.grid(row=0, column=1, padx=6)

    def refresh(self) -> None:
        df = load_attendance()
        for row in self.tree.get_children():
            self.tree.delete(row)
        if df.empty:
            return
        for _, record in df.sort_values(['Date', 'Time']).iterrows():
            self.tree.insert('', 'end', values=(record['Id'], record['Name'],
                                                record['Date'], record['Time']))


class AttendanceApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title('Face Attendance Console')
        self.configure(bg=BG_COLOR)
        self.geometry('880x540')
        self.minsize(840, 520)

        self.status_var = tk.StringVar(value='Idle — ready to capture.')
        self.last_log_var = tk.StringVar(value='No entries yet.')
        self.today_total_var = tk.StringVar(value='0 logs captured today')
        self.unique_students_var = tk.StringVar(value='0 unique faces today')
        self.registered_var = tk.StringVar(value='0 registered users')
        self.pending_requests_var = tk.StringVar(value='No pending requests.')

        self.capture_thread: threading.Thread | None = None
        self.timeline_trees: list[ttk.Treeview] = []

        self._configure_style()
        self._build_layout()
        self._refresh_data()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Accent.TButton', font=BODY_FONT, padding=8,
                        background=ACCENT_COLOR, foreground='#041421')
        style.map('Accent.TButton', background=[('active', '#0ea5e9')])
        style.configure('Secondary.TButton', font=BODY_FONT, padding=6,
                        background='#1f2937', foreground='white')
        style.configure('Card.TFrame', background=CARD_COLOR)

    def _build_layout(self) -> None:
        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill='both', expand=True)

        self.sidebar = tk.Frame(container, bg=SIDEBAR_COLOR, width=210)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        self.content_area = tk.Frame(container, bg=BG_COLOR)
        self.content_area.pack(side='right', fill='both', expand=True)

        self._build_sidebar()
        self._build_views()

    def _build_sidebar(self) -> None:
        title = tk.Label(self.sidebar, text='Face Attendance', font=TITLE_FONT,
                         fg='white', bg=SIDEBAR_COLOR)
        title.pack(pady=(24, 6))

        subtitle = tk.Label(self.sidebar, text='Smart capture console',
                            font=('Bahnschrift', 12), fg='#94a3b8', bg=SIDEBAR_COLOR)
        subtitle.pack()

        nav_wrapper = tk.Frame(self.sidebar, bg=SIDEBAR_COLOR)
        nav_wrapper.pack(pady=(30, 10), fill='x')

        self.current_view = tk.StringVar(value='landing')

        home_btn = ttk.Button(nav_wrapper, text='Home',
                      style='Secondary.TButton', width=20,
                      command=lambda: self.switch_view('landing'))
        home_btn.pack(pady=6)

        admin_btn = ttk.Button(nav_wrapper, text='Admin Console',
                    style='Accent.TButton', width=20,
                    command=lambda: self.switch_view('admin'))
        admin_btn.pack(pady=6)

        user_btn = ttk.Button(nav_wrapper, text='User Dashboard',
                       style='Secondary.TButton', width=20,
                       command=lambda: self.switch_view('user'))
        user_btn.pack(pady=6)

        tk.Label(self.sidebar, text='Session Status', font=('Bahnschrift', 12, 'bold'),
                 fg='white', bg=SIDEBAR_COLOR).pack(pady=(40, 6))
        status_label = tk.Label(self.sidebar, textvariable=self.status_var,
                                font=BODY_FONT, fg='#e2e8f0', bg=SIDEBAR_COLOR,
                                wraplength=180, justify='left')
        status_label.pack(padx=10)

        tk.Label(self.sidebar, textvariable=self.last_log_var, font=BODY_FONT,
                 fg=HIGHLIGHT_COLOR, bg=SIDEBAR_COLOR, wraplength=180,
                 justify='left').pack(padx=10, pady=(10, 0))

        capture_btn = ttk.Button(self.sidebar, text='Launch Capture',
                                 style='Accent.TButton', width=20,
                                 command=self.start_capture)
        capture_btn.pack(pady=(40, 10))

        view_log_btn = ttk.Button(self.sidebar, text='Open Log Viewer',
                                  style='Secondary.TButton', width=20,
                                  command=self.open_log_viewer)
        view_log_btn.pack()

    def _build_views(self) -> None:
        self.views: dict[str, tk.Frame] = {}
        landing_view = tk.Frame(self.content_area, bg=BG_COLOR)
        admin_view = tk.Frame(self.content_area, bg=BG_COLOR)
        user_view = tk.Frame(self.content_area, bg=BG_COLOR)
        for frame in (landing_view, admin_view, user_view):
            frame.grid(row=0, column=0, sticky='nsew')
        self.views['landing'] = landing_view
        self.views['admin'] = admin_view
        self.views['user'] = user_view

        self._build_landing_view(landing_view)
        self._build_admin_view(admin_view)
        self._build_user_view(user_view)
        self.switch_view('landing')

    def _build_landing_view(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        welcome_card = self._create_card(parent, 'Welcome',
                                         'Choose Admin or User to access the right tools. Capture, enrollment, and management are now separated for clarity.')
        welcome_card.grid(row=0, column=0, padx=40, pady=60, sticky='nsew')
        tk.Label(welcome_card, text='• Admins: manage users, review requests, run capture, and retrain the model.'
                 '\n• Users: log attendance or submit an enrollment request.'
                 '\nUse the sidebar buttons anytime to change areas.',
                 font=BODY_FONT, fg='#e2e8f0', bg=CARD_COLOR, justify='left',
                 wraplength=520).pack(anchor='w')

    def _build_admin_view(self, parent: tk.Frame) -> None:
        parent.columnconfigure((0, 1), weight=1)

        quick_card = self._create_card(parent, 'Admin Quick Actions',
                           'Access daily admin workflows.')
        quick_card.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='nsew')
        ttk.Button(quick_card, text='Log Attendance Session', style='Accent.TButton',
                   command=self.start_capture).pack(fill='x', pady=4)
        ttk.Button(quick_card, text='View Enrollment Requests',
                   style='Secondary.TButton', command=self.open_request_viewer).pack(fill='x', pady=4)
        ttk.Button(quick_card, text='Enroll New Face', style='Accent.TButton',
                   command=self.launch_enrollment).pack(fill='x', pady=4)
        ttk.Button(quick_card, text='Manage Users', style='Secondary.TButton',
               command=self.open_user_manager).pack(fill='x', pady=4)
        ttk.Button(quick_card, text='Train Recognition Model', style='Accent.TButton',
               command=self.train_model).pack(fill='x', pady=4)
        ttk.Button(quick_card, text='Open Attendance Log', style='Secondary.TButton',
                   command=self.open_log_viewer).pack(fill='x', pady=4)

        insights_card = self._create_card(parent, 'Model Insights',
                                          'Health of today’s attendance pipeline.')
        insights_card.grid(row=0, column=1, padx=16, pady=(16, 8), sticky='nsew')
        tk.Label(insights_card, textvariable=self.today_total_var, font=BODY_FONT,
                 fg='white', bg=CARD_COLOR).pack(anchor='w', pady=4)
        tk.Label(insights_card, textvariable=self.unique_students_var, font=BODY_FONT,
                 fg='white', bg=CARD_COLOR).pack(anchor='w', pady=4)
        tk.Label(insights_card, textvariable=self.registered_var, font=BODY_FONT,
                 fg='white', bg=CARD_COLOR).pack(anchor='w', pady=4)
        tk.Label(insights_card, textvariable=self.pending_requests_var,
                 font=BODY_FONT, fg=HIGHLIGHT_COLOR, bg=CARD_COLOR,
                 wraplength=260, justify='left').pack(anchor='w', pady=10)

        timeline_card = self._create_card(parent, 'Recent Attendance',
                                          'Latest captured faces across all classes.')
        timeline_card.grid(row=1, column=0, columnspan=2,
                           padx=16, pady=(8, 16), sticky='nsew')

        timeline_body = tk.Frame(timeline_card, bg=CARD_COLOR)
        timeline_body.pack(fill='both', expand=True)
        timeline_body.columnconfigure(0, weight=1)

        tree = ttk.Treeview(timeline_body, columns=('Name', 'Date', 'Time'),
                            show='headings', height=8)
        for col in ('Name', 'Date', 'Time'):
            tree.heading(col, text=col)
            tree.column(col, width=150 if col == 'Name' else 100, anchor='center')
        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(timeline_body, orient='vertical', command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns', padx=(6, 0))
        tree.configure(yscrollcommand=scrollbar.set)
        self.timeline_trees.append(tree)

    def _build_user_view(self, parent: tk.Frame) -> None:
        parent.columnconfigure((0, 1), weight=1)

        action_card = self._create_card(parent, 'User Dashboard',
                        'Log your attendance or request onboarding.')
        action_card.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='nsew')
        ttk.Button(action_card, text='Log Today’s Attendance', style='Accent.TButton',
                   command=self.start_capture).pack(fill='x', pady=6)
        ttk.Button(action_card, text='Request Enrollment', style='Secondary.TButton',
                   command=self.launch_request_form).pack(fill='x', pady=6)

        info_card = self._create_card(parent, 'Need help?',
                                      'If you are not recognized, request enrollment and notify your admin.')
        info_card.grid(row=0, column=1, padx=16, pady=(16, 8), sticky='nsew')
        tk.Label(info_card, text='Tips:'
                 '\n• Ensure good lighting'
                 '\n• Face the camera squarely'
                 '\n• Remove hats/masks if possible',
                 font=BODY_FONT, fg='#cbd5f5', bg=CARD_COLOR, justify='left').pack(anchor='w')

        timeline_card = self._create_card(parent, 'Live Attendance Feed',
                                          'Showing the latest capture activity.')
        timeline_card.grid(row=1, column=0, columnspan=2,
                           padx=16, pady=(8, 16), sticky='nsew')
        tree = ttk.Treeview(timeline_card, columns=('Name', 'Date', 'Time'),
                            show='headings', height=8)
        for col in ('Name', 'Date', 'Time'):
            tree.heading(col, text=col)
            tree.column(col, width=150 if col == 'Name' else 100, anchor='center')
        tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(timeline_card, orient='vertical', command=tree.yview)
        scrollbar.pack(side='right', fill='y', padx=(6, 0))
        tree.configure(yscrollcommand=scrollbar.set)
        self.timeline_trees.append(tree)

    def _create_card(self, parent: tk.Frame, title: str, subtitle: str) -> tk.Frame:
        card = tk.Frame(parent, bg=CARD_COLOR, bd=0, highlightthickness=0,
                        relief='flat', padx=18, pady=12)
        tk.Label(card, text=title, font=('Bahnschrift', 15, 'bold'),
                 fg='white', bg=CARD_COLOR).pack(anchor='w')
        tk.Label(card, text=subtitle, font=BODY_FONT, fg='#94a3b8',
                 bg=CARD_COLOR, wraplength=320, justify='left').pack(anchor='w', pady=(0, 10))
        return card

    def switch_view(self, view_name: str) -> None:
        frame = self.views.get(view_name)
        if not frame:
            return
        frame.tkraise()
        self.current_view.set(view_name)

    def _refresh_data(self) -> None:
        df = load_attendance()
        if df is None or getattr(df, 'empty', True):
            df = pd.DataFrame(columns=['Id', 'Name', 'Date', 'Time'])

        recent = df.sort_values(['Date', 'Time'], ascending=False).head(10) if not df.empty else pd.DataFrame()
        for tree in self.timeline_trees:
            tree.delete(*tree.get_children())
            if recent.empty:
                continue
            for _, record in recent.iterrows():
                tree.insert('', 'end', values=(record['Name'], record['Date'], record['Time']))

        today = datetime.now().strftime('%Y-%m-%d')
        today_df = df[df['Date'] == today] if 'Date' in df.columns else pd.DataFrame()
        self.today_total_var.set(f"{len(today_df)} logs captured today")
        unique_faces = today_df['Id'].nunique() if 'Id' in today_df else 0
        self.unique_students_var.set(f"{unique_faces} unique faces today")

        try:
            user_map = load_user_details()
            self.registered_var.set(f"{len(user_map)} registered users")
        except Exception:
            self.registered_var.set('No registered users detected')

        pending_df = load_requests()
        if pending_df is None or getattr(pending_df, 'empty', True):
            total_pending = 0
        else:
            status_series = pending_df['Status'] if 'Status' in pending_df.columns else None
            if status_series is not None:
                total_pending = status_series.str.contains('Pending', case=False, na=False).sum()
            else:
                total_pending = len(pending_df)
        if total_pending:
            self.pending_requests_var.set(f"{total_pending} pending enrollment requests awaiting review.")
        else:
            self.pending_requests_var.set('No pending enrollment requests.')

        self.after(60000, self._refresh_data)

    def start_capture(self) -> None:
        if self.capture_thread and self.capture_thread.is_alive():
            messagebox.showinfo('Capture Running',
                                'A capture session is already active.')
            return

        self.status_var.set('Spinning up camera...')
        self.capture_thread = threading.Thread(
            target=self._run_capture_session,
            daemon=True,
        )
        self.capture_thread.start()

    def _run_capture_session(self) -> None:
        def thread_safe_update(var: tk.StringVar, value: str) -> None:
            self.after(0, lambda: var.set(value))

        def handle_status(message: str) -> None:
            thread_safe_update(self.status_var, message)

        def handle_log(name: str, time_str: str) -> None:
            thread_safe_update(self.last_log_var, f'Last log • {name} @ {time_str}')

        try:
            run_recognition(
                session_seconds=90,
                status_callback=handle_status,
                log_callback=handle_log,
                display_window=True,
            )
        except Exception as exc:
            self.after(0, lambda err=exc: messagebox.showerror('Capture Error', str(err)))
        finally:
            thread_safe_update(self.status_var, 'Idle — ready to capture.')

    def open_log_viewer(self) -> None:
        AttendanceViewer(self)

    def launch_enrollment(self, prefill_id: int | None = None,
                          prefill_name: str | None = None) -> None:
        script_path = SCRIPTS_DIR / '01_create_dataset.py'
        if not script_path.exists():
            messagebox.showerror('Script Missing',
                                 'Cannot find 01_create_dataset.py in this folder.')
            return

        self.status_var.set('Launching enrollment window...')
        try:
            cmd = [sys.executable, str(script_path)]
            if prefill_id is not None:
                cmd.extend(['--id', str(prefill_id)])
            if prefill_name:
                cmd.extend(['--name', prefill_name])
            subprocess.Popen(['cmd.exe', '/c', 'start', '', *cmd])
            messagebox.showinfo(
                'Enrollment Started',
                'A new console window opened. Complete the capture and retrain the model.',
            )
        except Exception as exc:
            messagebox.showerror('Enrollment Error', str(exc))
        finally:
            self.status_var.set('Idle — ready to capture.')

    def train_model(self) -> None:
        script_path = SCRIPTS_DIR / '02_train_model.py'
        if not script_path.exists():
            messagebox.showerror('Script Missing',
                                 'Cannot find 02_train_model.py in this folder.')
            return

        self.status_var.set('Training model in separate console...')
        try:
            subprocess.Popen(['cmd.exe', '/c', 'start', '', sys.executable, str(script_path)])
            messagebox.showinfo(
                'Training Launched',
                'A console window is running 02_train_model.py. Wait for it to finish before the next capture.',
            )
        except Exception as exc:
            messagebox.showerror('Training Error', str(exc))
        finally:
            self.status_var.set('Idle — ready to capture.')

    def open_request_viewer(self) -> None:
        RequestViewer(self)

    def launch_request_form(self) -> None:
        EnrollmentRequestForm(self)

    def open_user_manager(self) -> None:
        UserManager(self)


class RequestViewer(tk.Toplevel):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title('Enrollment Requests')
        self.configure(bg=BG_COLOR)
        self.geometry('680x460')
        self.minsize(620, 420)
        self.resizable(True, True)
        self._rows: dict[str, dict] = {}
        self._build_widgets()
        self.refresh()

    def _build_widgets(self) -> None:
        header = tk.Label(self, text='Pending Requests', font=TITLE_FONT,
                          fg='white', bg=BG_COLOR)
        header.pack(pady=(14, 8))

        cols = ('RequestId', 'Name', 'Contact', 'Message', 'Timestamp', 'Status')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=14)
        for col in cols:
            self.tree.heading(col, text=col)
            width = 80 if col == 'RequestId' else 110
            self.tree.column(col, anchor='center', width=width)
        self.tree.pack(fill='both', padx=16, pady=8, expand=True)

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(pady=(0, 12))

        accept_btn = ttk.Button(btn_frame, text='Accept & Enroll', style='Accent.TButton',
                                width=18, command=self.accept_request)
        accept_btn.grid(row=0, column=0, padx=6)

        reject_btn = ttk.Button(btn_frame, text='Reject', style='Secondary.TButton',
                                width=12, command=self.reject_request)
        reject_btn.grid(row=0, column=1, padx=6)

        refresh_btn = ttk.Button(btn_frame, text='Refresh', style='Secondary.TButton',
                                 width=10, command=self.refresh)
        refresh_btn.grid(row=0, column=2, padx=6)

        close_btn = ttk.Button(btn_frame, text='Close', style='Secondary.TButton',
                               width=10, command=self.destroy)
        close_btn.grid(row=0, column=3, padx=6)

    def refresh(self) -> None:
        df = load_requests()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._rows.clear()
        if df.empty:
            return
        for _, record in df.iterrows():
            item = self.tree.insert('', 'end', values=(
                record['RequestId'], record['Name'], record['Contact'],
                record['Message'], record['Timestamp'], record['Status'],
            ))
            self._rows[item] = record.to_dict()

    def _get_selected_request(self) -> dict | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo('No Selection', 'Select a request first.')
            return None
        return self._rows.get(selection[0])

    def accept_request(self) -> None:
        record = self._get_selected_request()
        if not record:
            return
        if str(record.get('Status', '')).lower().startswith('approved'):
            messagebox.showinfo('Already Approved', 'This request was already approved.')
            return
        name = record['Name']
        request_id = int(record['RequestId'])
        face_id = simpledialog.askinteger('Assign User ID',
                                          f'Enter numeric ID for {name}:',
                                          minvalue=1)
        if face_id is None:
            return
        if isinstance(self.master, AttendanceApp):
            self.master.launch_enrollment(prefill_id=face_id, prefill_name=name)
        else:
            messagebox.showerror('Action Unavailable',
                                 'Cannot launch enrollment from this window.')
            return
        update_request_status(request_id, f'Approved (ID {face_id})')
        messagebox.showinfo('Request Approved',
                            'Capture window launched. Remember to retrain after capture.')
        self.refresh()

    def reject_request(self) -> None:
        record = self._get_selected_request()
        if not record:
            return
        request_id = int(record['RequestId'])
        update_request_status(request_id, 'Rejected')
        self.refresh()


class EnrollmentRequestForm(tk.Toplevel):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title('Request Enrollment')
        self.configure(bg=BG_COLOR)
        self.geometry('420x360')
        self.resizable(False, False)
        self.name_var = tk.StringVar()
        self.contact_var = tk.StringVar()
        self._build()

    def _build(self) -> None:
        tk.Label(self, text='Need to be added to attendance?', font=TITLE_FONT,
                 fg='white', bg=BG_COLOR).pack(pady=(16, 6))

        form = tk.Frame(self, bg=BG_COLOR)
        form.pack(padx=20, pady=10, fill='x')

        tk.Label(form, text='Your Name', font=BODY_FONT,
                 fg='white', bg=BG_COLOR).pack(anchor='w')
        tk.Entry(form, textvariable=self.name_var).pack(fill='x', pady=(0, 8))

        tk.Label(form, text='Contact Info (email/phone)', font=BODY_FONT,
                 fg='white', bg=BG_COLOR).pack(anchor='w')
        tk.Entry(form, textvariable=self.contact_var).pack(fill='x', pady=(0, 8))

        tk.Label(form, text='Message to admin', font=BODY_FONT,
                 fg='white', bg=BG_COLOR).pack(anchor='w')
        self.message_box = tk.Text(form, height=5)
        self.message_box.pack(fill='x')

        submit_btn = ttk.Button(self, text='Send Request',
                                style='Accent.TButton', command=self.submit)
        submit_btn.pack(pady=12)

    def submit(self) -> None:
        try:
            add_request(
                self.name_var.get(),
                self.contact_var.get(),
                self.message_box.get('1.0', 'end').strip(),
            )
        except ValueError as exc:
            messagebox.showerror('Invalid Request', str(exc))
            return
        messagebox.showinfo('Request Sent',
                    'Your request was sent to the admin for approval.')
        self.destroy()


class UserManager(tk.Toplevel):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title('Manage Users')
        self.configure(bg=BG_COLOR)
        self.geometry('580x420')
        self.resizable(False, False)
        self.status_var = tk.StringVar(value='Loading users...')
        self._build_widgets()
        self.refresh()

    def _build_widgets(self) -> None:
        header = tk.Label(self, text='Registered Users', font=TITLE_FONT,
                          fg='white', bg=BG_COLOR)
        header.pack(pady=(14, 4))

        sub = tk.Label(self, text='Delete stale profiles before retraining the model.',
                       font=BODY_FONT, fg='#94a3b8', bg=BG_COLOR)
        sub.pack()

        cols = ('Id', 'Name', 'Samples')
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.pack(fill='both', expand=True, padx=16, pady=10)

        self.tree = ttk.Treeview(frame, columns=cols, show='headings', height=10)
        for col in cols:
            heading = 'Sample Count' if col == 'Samples' else col
            self.tree.heading(col, text=heading)
            width = 90 if col in ('Id', 'Samples') else 260
            self.tree.column(col, anchor='center' if col != 'Name' else 'w', width=width)
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(pady=(4, 10))

        delete_btn = ttk.Button(btn_frame, text='Delete Selected', style='Accent.TButton',
                                width=18, command=self.delete_selected_user)
        delete_btn.grid(row=0, column=0, padx=6)

        refresh_btn = ttk.Button(btn_frame, text='Refresh', style='Secondary.TButton',
                                 width=12, command=self.refresh)
        refresh_btn.grid(row=0, column=1, padx=6)

        close_btn = ttk.Button(btn_frame, text='Close', style='Secondary.TButton',
                               width=12, command=self.destroy)
        close_btn.grid(row=0, column=2, padx=6)

        reminder = tk.Label(
            self,
            text='Reminder: Run 02_train_model.py after deleting users to keep the model in sync.',
            font=('Bahnschrift', 10), fg=HIGHLIGHT_COLOR, bg=BG_COLOR,
        )
        reminder.pack(pady=(0, 4))

        status_label = tk.Label(self, textvariable=self.status_var, font=BODY_FONT,
                                fg='#e2e8f0', bg=BG_COLOR)
        status_label.pack()

    def refresh(self) -> None:
        df = load_user_records()
        self.tree.delete(*self.tree.get_children())
        if df.empty:
            self.status_var.set('No registered users yet.')
            return

        dataset_dir = DATASET_DIR
        for _, row in df.iterrows():
            user_id = int(row['Id'])
            samples = self._count_samples(dataset_dir, user_id)
            self.tree.insert('', 'end', values=(user_id, row['Name'], samples))

        self.status_var.set(f'{len(df)} user(s) loaded.')

    def delete_selected_user(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo('Select User', 'Choose a user row first.')
            return

        item_id = selection[0]
        values = self.tree.item(item_id, 'values')
        user_id = int(values[0])
        user_name = values[1]

        confirm = messagebox.askyesno(
            'Delete User',
            f"This removes {user_name} (ID {user_id}) from the roster and deletes their dataset images. Continue?",
        )
        if not confirm:
            return

        try:
            summary = delete_user_profile(user_id)
        except Exception as exc:
            messagebox.showerror('Delete Failed', str(exc))
            return

        self.refresh()
        messagebox.showinfo(
            'User Deleted',
            f"Removed {user_name}. Deleted {summary.get('samples_removed', 0)} sample images. Remember to retrain (02_train_model.py).",
        )
        parent_status = getattr(self.master, 'status_var', None)
        if isinstance(parent_status, tk.StringVar):
            parent_status.set('User removed. Retrain model before next capture session.')

    @staticmethod
    def _count_samples(dataset_dir: Path, user_id: int) -> int:
        if not dataset_dir.exists():
            return 0
        return sum(1 for _ in dataset_dir.glob(f'User.{user_id}.*.jpg'))


def main() -> None:
    app = AttendanceApp()
    app.mainloop()


if __name__ == '__main__':
    main()
