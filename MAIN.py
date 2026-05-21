import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import subprocess
import re
import math

# ── tkinterdnd2 ───────────────────────────────────────────────────────────────
DND_AVAILABLE = False
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "tkinterdnd2", "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        from tkinterdnd2 import TkinterDnD, DND_FILES
        DND_AVAILABLE = True
    except Exception:
        pass

def _parse_dnd_paths(raw):
    paths = []
    for m in re.finditer(r'\{([^}]+)\}|(\S+)', raw):
        paths.append(m.group(1) or m.group(2))
    return [p for p in paths if os.path.isfile(p)]

# ── Neon palette ──────────────────────────────────────────────────────────────
BG        = "#111318"
SURFACE   = "#1a1d24"
SURFACE2  = "#22262f"
INPUT_BG  = "#111317"
BORDER    = "#2e3340"
FG        = "#cdd6f4"
FG_DIM    = "#6c7086"
NEON_BLUE = "#89b4fa"
NEON_CYAN = "#89dceb"
NEON_GRN  = "#a6e3a1"
NEON_PURP = "#cba6f7"
NEON_RED  = "#f38ba8"

# ── ToolTip Class ─────────────────────────────────────────────────────────────
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.fade_id = None
        self.wait_id = None
        self.show_count = 0
        self.widget.bind("<Enter>", self.enter, add="+")
        self.widget.bind("<Leave>", self.leave, add="+")

    def enter(self, event=None):
        if self.show_count < 3:
            self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        if self.wait_id:
            self.widget.after_cancel(self.wait_id)
            self.wait_id = None
        if self.fade_id:
            self.widget.after_cancel(self.fade_id)
            self.fade_id = None

    def showtip(self, event=None):
        self.show_count += 1 
        
        x, y, cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        tw.attributes("-alpha", 1.0)
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#22262f", foreground="#cdd6f4",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Consolas", 8))
        label.pack(ipadx=4, ipady=2)
        
        self.wait_id = self.widget.after(1000, self.start_fade)

    def start_fade(self, alpha=1.0):
        if not self.tipwindow:
            return
            
        alpha -= 0.08
        if alpha > 0:
            self.tipwindow.attributes("-alpha", alpha)
            self.fade_id = self.widget.after(40, lambda: self.start_fade(alpha))
        else:
            self.hidetip()

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# ── Icon painter ──────────────────────────────────────────────────────────────
def draw_icon(canvas, kind, color, bg):
    canvas.delete("all")
    c, b = color, bg
    if kind == "rename":        # pencil
        canvas.create_polygon(3,12, 5,12, 13,4, 11,2, fill=c, outline="")
        canvas.create_polygon(3,12, 5,12, 4,14, fill=c, outline="")
        canvas.create_line(11,2, 13,4, fill=b, width=1)
    elif kind == "reset":       # circular arrow
        pts = _arc_pts(8,8,5, -30, 270, 18)
        if len(pts) >= 4: canvas.create_line(pts, fill=c, width=2)
        canvas.create_polygon(12,3, 14,7, 10,6, fill=c, outline="")
    elif kind == "files":       # stack of papers
        for ox, oy in [(3,1),(2,0),(1,1)]:
            canvas.create_rectangle(ox+1,oy+3, ox+9,oy+12, outline=c, width=1)
        canvas.create_rectangle(2,4, 12,13, fill=bg, outline=c, width=1)
        canvas.create_line(5,7,  9,7,  fill=c, width=1)
        canvas.create_line(5,9,  9,9,  fill=c, width=1)
        canvas.create_line(5,11, 9,11, fill=c, width=1)
    elif kind == "add":         # plus circle
        canvas.create_oval(1,1,13,13, outline=c, width=1.5)
        canvas.create_line(7,4,  7,10, fill=c, width=2)
        canvas.create_line(4,7,  10,7, fill=c, width=2)
    elif kind == "remove":      # minus circle
        canvas.create_oval(1,1,13,13, outline=c, width=1.5)
        canvas.create_line(4,7,  10,7, fill=c, width=2)
    elif kind == "github":
        canvas.create_oval(2,2,14,14, outline=c, width=1.5)
        canvas.create_oval(4,3,12,10, fill=c, outline="")
        canvas.create_oval(5,7,11,14, fill=c, outline="")
        canvas.create_polygon(4,5,5,2,7,5,   fill=b, outline="")
        canvas.create_polygon(9,5,11,2,12,5, fill=b, outline="")
        canvas.create_oval(5,4,7,6, fill=b, outline="")
        canvas.create_oval(9,4,11,6,fill=b, outline="")

def _arc_pts(cx, cy, r, start_deg, end_deg, steps):
    pts = []
    for i in range(steps+1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts += [cx + r*math.cos(a), cy - r*math.sin(a)]
    return pts


class BatchRenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Rename v1.6")
        
        # Set window dimensions
        window_width = 470
        window_height = 350
        
        # Calculate center coordinates
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Set geometry to the center of the screen
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        
        # Make transparent immediately to hide UI rendering
        self.root.attributes("-alpha", 0.0)
        
        self.files = []
        self.setup_styles()
        self.create_widgets()
        
        # Force Tkinter to calculate all widget sizes/positions now
        self.root.update_idletasks()
        
        # Delay fade-in slightly to ensure window is fully mapped by OS
        self.root.after(50, self.start_fade_in)

    def start_fade_in(self, alpha=0.0):
        alpha += 0.05  # Increase opacity
        if alpha <= 1.0:
            self.root.attributes("-alpha", alpha)
            # Re-call every 30ms for a smooth ~600ms fade
            self.root.after(30, lambda: self.start_fade_in(alpha))
        else:
            self.root.attributes("-alpha", 1.0) # Ensure full opacity

    # ── Styles ────────────────────────────────────────────────────────────────
    def setup_styles(self):
        s = ttk.Style()
        s.theme_use('clam')
        base = dict(background=BG, foreground=FG, fieldbackground=INPUT_BG,
                    bordercolor=BORDER, darkcolor=SURFACE, lightcolor=SURFACE,
                    troughcolor=SURFACE, font=("Consolas", 9))
        s.configure(".", **base)
        s.configure("TLabel",    background=BG, foreground=FG,    font=("Consolas", 9))
        s.configure("TFrame",    background=BG)
        
        s.configure("TEntry",    fieldbackground=INPUT_BG, foreground=FG,
                    insertcolor=NEON_BLUE, bordercolor=BORDER, font=("Consolas", 9))
        s.map("TEntry", bordercolor=[("focus", NEON_BLUE)])
        
        s.configure("TCheckbutton", background=BG, foreground=FG, font=("Consolas", 9),
                    indicatorcolor=SURFACE2, indicatorrelief="flat")
        s.map("TCheckbutton",
              indicatorcolor=[("selected", NEON_BLUE)],
              foreground=[("active", NEON_BLUE)])
              
        s.configure("TRadiobutton", background=BG, foreground=FG, font=("Consolas", 9),
                    indicatorcolor=SURFACE2, indicatorrelief="flat")
        s.map("TRadiobutton",
              indicatorcolor=[("selected", NEON_CYAN)],
              foreground=[("active", NEON_CYAN)])
              
        s.configure("TCombobox", fieldbackground=INPUT_BG, background=SURFACE2,
                    foreground=FG, arrowcolor=NEON_BLUE,
                    selectbackground=NEON_BLUE, selectforeground=BG, font=("Consolas", 9))
        s.map("TCombobox", fieldbackground=[("readonly", INPUT_BG)]) 
        
        s.configure("TSpinbox", fieldbackground=INPUT_BG, background=SURFACE2,
                    foreground=FG, arrowcolor=NEON_BLUE, insertcolor=NEON_BLUE,
                    font=("Consolas", 9))
        s.map("TSpinbox", fieldbackground=[("readonly", INPUT_BG), ("disabled", SURFACE)])
        
        s.configure("Treeview", background=SURFACE, foreground=FG,
                    fieldbackground=SURFACE, bordercolor=BORDER,
                    rowheight=20, font=("Consolas", 9))
        s.configure("Treeview.Heading", background=SURFACE2, foreground=NEON_CYAN,
                    bordercolor=BORDER, relief="flat", font=("Consolas", 9, "bold"))
        s.map("Treeview",
              background=[("selected", NEON_BLUE)],
              foreground=[("selected", BG)])
        s.configure("Vertical.TScrollbar",
                    background=SURFACE2, troughcolor=SURFACE,
                    arrowcolor=FG_DIM, bordercolor=BORDER)

    # ── Section label ─────────────────────────────────────────────────────────
    def _section(self, parent, text, row):
        hdr = tk.Frame(parent, bg=BG)
        hdr.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 2))
        tk.Label(hdr, text="●", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 8, "bold")).pack(side="left", padx=(0, 5))
        tk.Label(hdr, text=text, fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 9, "bold")).pack(side="left")
        return hdr

    # ── Flat icon button ──────────────────────────────────────────────────────
    def _icon_btn(self, parent, icon_kind, label, command,
                  fg=FG, bg=SURFACE2, bold=False, side="left", padx=(6,0)):
        frame = tk.Frame(parent, bg=bg, cursor="hand2")
        frame.pack(side=side, padx=padx, pady=4)
        ic = tk.Canvas(frame, width=14, height=14, bg=bg, highlightthickness=0, cursor="hand2")
        ic.pack(side="left", padx=(6, 3))
        draw_icon(ic, icon_kind, fg, bg)
        font_ = ("Consolas", 11, "bold") if bold else ("Consolas", 11)
        lbl = tk.Label(frame, text=label, fg=fg, bg=bg, font=font_,
                       padx=4, pady=2, cursor="hand2")
        lbl.pack(side="left", padx=(0, 6))

        hover_bg = NEON_BLUE
        def on_click(e=None): command()
        def on_enter(e=None):
            frame.config(bg=hover_bg); ic.config(bg=hover_bg)
            lbl.config(bg=hover_bg, fg=BG)
            draw_icon(ic, icon_kind, BG, hover_bg)
        def on_leave(e=None):
            frame.config(bg=bg); ic.config(bg=bg)
            lbl.config(bg=bg, fg=fg)
            draw_icon(ic, icon_kind, fg, bg)
        for w in (frame, ic, lbl):
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
        return frame

    # ── Widgets ───────────────────────────────────────────────────────────────
    def create_widgets(self):
        self.root.grid_columnconfigure(0, weight=1)

        # ── Header row ───────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG)
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        hdr.grid_columnconfigure(1, weight=1)

        tk.Label(hdr, text="● Select Files", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 9, "bold")).grid(row=0, column=0, sticky="w")

        gh_frame = tk.Frame(hdr, bg=BG, cursor="hand2")
        gh_frame.grid(row=0, column=2, sticky="e")
        gh_ic = tk.Canvas(gh_frame, width=14, height=14, bg=BG,
                          highlightthickness=0, cursor="hand2")
        gh_ic.pack(side="left", padx=(0, 4))
        draw_icon(gh_ic, "github", NEON_BLUE, BG)
        self.gh_lbl = tk.Label(gh_frame, text="buonber", fg=NEON_BLUE, bg=BG,
                               font=("Consolas", 8), cursor="hand2")
        self.gh_lbl.pack(side="left")
        for w in (gh_frame, gh_ic, self.gh_lbl):
            w.bind("<Button-1>", lambda e: self.open_github())
            w.bind("<Enter>",    lambda e: self.gh_lbl.config(fg=NEON_CYAN))
            w.bind("<Leave>",    lambda e: self.gh_lbl.config(fg=NEON_BLUE))

        # ── Drop zone ─────────────────────────────────────────────────────
        drop_wrap = tk.Frame(self.root, bg=BG)
        drop_wrap.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))
        drop_wrap.grid_columnconfigure(0, weight=1)

        self.drop_canvas = tk.Canvas(
            drop_wrap, height=65, bg=SURFACE2,
            highlightthickness=1, highlightbackground=BORDER, cursor="hand2")
        self.drop_canvas.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.drop_canvas.bind("<Configure>", lambda e: self._draw_drop_zone(False))

        # file count row
        fc_row = tk.Frame(drop_wrap, bg=BG)
        fc_row.grid(row=1, column=0, sticky="ew")
        self.file_label = tk.Label(fc_row, text="No files selected",
                                   fg=FG_DIM, bg=BG, font=("Consolas", 9))
        self.file_label.pack(side="left")

        # Files list button
        self.files_btn_frame = tk.Frame(fc_row, bg=SURFACE2, cursor="hand2")
        self.files_btn_ic = tk.Canvas(self.files_btn_frame, width=14, height=14,
                                      bg=SURFACE2, highlightthickness=0, cursor="hand2")
        self.files_btn_ic.pack(side="left", padx=(6,3), pady=3)
        draw_icon(self.files_btn_ic, "files", NEON_CYAN, SURFACE2)
        self.files_btn_lbl = tk.Label(self.files_btn_frame, text="View files",
                                      fg=NEON_CYAN, bg=SURFACE2,
                                      font=("Consolas", 9), padx=4, pady=2, cursor="hand2")
        self.files_btn_lbl.pack(side="left", padx=(0,6))
        def fb_enter(e):
            self.files_btn_frame.config(bg=NEON_CYAN)
            self.files_btn_ic.config(bg=NEON_CYAN)
            self.files_btn_lbl.config(bg=NEON_CYAN, fg=BG)
            draw_icon(self.files_btn_ic, "files", BG, NEON_CYAN)
        def fb_leave(e):
            self.files_btn_frame.config(bg=SURFACE2)
            self.files_btn_ic.config(bg=SURFACE2)
            self.files_btn_lbl.config(bg=SURFACE2, fg=NEON_CYAN)
            draw_icon(self.files_btn_ic, "files", NEON_CYAN, SURFACE2)
        for w in (self.files_btn_frame, self.files_btn_ic, self.files_btn_lbl):
            w.bind("<Button-1>", lambda e: self.open_files_manager())
            w.bind("<Enter>", fb_enter)
            w.bind("<Leave>", fb_leave)

        # Browse button
        browse_btn = tk.Frame(fc_row, bg=SURFACE2, cursor="hand2")
        browse_btn.pack(side="right")
        browse_ic = tk.Canvas(browse_btn, width=14, height=14, bg=SURFACE2,
                              highlightthickness=0, cursor="hand2")
        browse_ic.pack(side="left", padx=(6,3), pady=4)
        browse_ic.create_rectangle(1,5,13,13, fill=NEON_BLUE, outline="")
        browse_ic.create_polygon(1,5, 1,3, 5,3, 6,5, fill=NEON_BLUE, outline="")
        browse_ic.create_rectangle(2,6,12,12, fill=SURFACE2, outline="")
        browse_ic.create_line(2,8,12,8, fill=NEON_BLUE, width=1)
        browse_ic.create_line(2,10,12,10, fill=NEON_BLUE, width=1)
        browse_lbl = tk.Label(browse_btn, text="Browse", fg=FG, bg=SURFACE2,
                              font=("Consolas", 9), padx=6, pady=3, cursor="hand2")
        browse_lbl.pack(side="left")
        def br_enter(e): browse_btn.config(bg=NEON_BLUE); browse_lbl.config(bg=NEON_BLUE, fg=BG)
        def br_leave(e): browse_btn.config(bg=SURFACE2);  browse_lbl.config(bg=SURFACE2, fg=FG)
        for w in (browse_btn, browse_ic, browse_lbl):
            w.bind("<Button-1>", lambda e: self.select_files())
            w.bind("<Enter>", br_enter)
            w.bind("<Leave>", br_leave)

        if DND_AVAILABLE:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<DropEnter>>", self._on_drop_enter)
            self.drop_canvas.dnd_bind("<<DropLeave>>", self._on_drop_leave)
            self.drop_canvas.dnd_bind("<<Drop>>",      self._on_drop)
        else:
            self.drop_canvas.bind("<Button-1>", lambda e: self.select_files())

        # ── Rename Options ────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG)
        hdr.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 2))
        tk.Label(hdr, text="●", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 8, "bold")).pack(side="left", padx=(0, 5))
        tk.Label(hdr, text="Rename Options", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 9, "bold")).pack(side="left")

        self.case_var = tk.StringVar(value="")
        self._prev_case = ""

        def _toggle_case(val):
            if self._prev_case == val:
                self.case_var.set("")
                self._prev_case = ""
            else:
                self.case_var.set(val)
                self._prev_case = val

        ttk.Checkbutton(
            hdr, text="lowercase",
            variable=self.case_var, onvalue="lower", offvalue="",
            command=lambda: _toggle_case("lower")).pack(side="right", padx=(4, 0))
        ttk.Checkbutton(
            hdr, text="UPPERCASE",
            variable=self.case_var, onvalue="upper", offvalue="",
            command=lambda: _toggle_case("upper")).pack(side="right", padx=(8, 0))

        opt = tk.Frame(self.root, bg=BG)
        opt.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 2))

        def lbl(text, row, col):
            tk.Label(opt, text=text, fg=FG_DIM, bg=BG,
                     font=("Consolas", 9)).grid(row=row, column=col, sticky="w",
                                                padx=(0,4), pady=1)
        def ent(row, col, cs=1):
            e = ttk.Entry(opt)
            e.grid(row=row, column=col, columnspan=cs, sticky="ew", pady=3)
            return e

        DATE_FORMATS = ["none", "YYMMDD", "DDMMYY", "YYYYMM"]

        def _make_date_btn(parent, entry_widget):
            fmt_var = tk.StringVar(value="none")
            entry_widget._date_var = fmt_var
            entry_widget._use_mtime = None

            fmt_cb = ttk.Combobox(parent, values=DATE_FORMATS,
                                  textvariable=fmt_var, width=7, state="readonly",
                                  font=("Consolas", 8))

            def _on_select(*_):
                fmt_cb.selection_clear()
                val = fmt_var.get()
                if val == "none":
                    entry_widget._use_mtime = None
                    if getattr(entry_widget, "_date_active", False):
                        entry_widget.delete(0, tk.END)
                        entry_widget._date_active = False
                else:
                    entry_widget._use_mtime = val
                    entry_widget._date_active = True

            fmt_cb.bind("<<ComboboxSelected>>", _on_select)
            fmt_cb.bind("<FocusIn>", lambda e: fmt_cb.selection_clear())
            
            # Tooltip for Timestamp Combobox
            ToolTip(fmt_cb, "Append creation/modified date")
            return fmt_cb

        # Prevent empty values
        def _enforce_zero(var):
            if not var.get().strip():
                var.set("0")

        self.del_left_var = tk.StringVar(value="0")
        self.del_right_var = tk.StringVar(value="0")
        vcmd_num_only = (self.root.register(lambda P: P.isdigit() or P == ""), '%P')

        # Prefix row with Del L
        prefix_row = tk.Frame(opt, bg=BG)
        prefix_row.grid(row=0, column=0, columnspan=4, sticky="ew", pady=3)
        prefix_row.grid_columnconfigure(1, weight=1) 
        
        tk.Label(prefix_row, text="Prefix:", fg=FG_DIM, bg=BG, font=("Consolas", 9)).grid(row=0, column=0, sticky="w", padx=(0,4))
        self.prefix_entry = ttk.Entry(prefix_row)
        self.prefix_entry.grid(row=0, column=1, sticky="ew")
        
        tk.Label(prefix_row, text="🕐", fg=FG_DIM, bg=BG, font=("Consolas", 9)).grid(row=0, column=2, padx=(6,2))
        _make_date_btn(prefix_row, self.prefix_entry).grid(row=0, column=3, sticky="w")
        
        tk.Label(prefix_row, text=" Del L:", fg=FG_DIM, bg=BG, font=("Consolas", 9)).grid(row=0, column=4, padx=(4,2))
        self.del_left_sp = ttk.Spinbox(prefix_row, from_=0, to=999, width=3, textvariable=self.del_left_var, validate='all', validatecommand=vcmd_num_only)
        self.del_left_sp.grid(row=0, column=5, sticky="w")
        
        self.del_left_sp.bind("<FocusOut>", lambda e: _enforce_zero(self.del_left_var))
        ToolTip(self.del_left_sp, "Remove N characters from the Left")

        # Suffix row with Del R
        suffix_row = tk.Frame(opt, bg=BG)
        suffix_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=3)
        suffix_row.grid_columnconfigure(1, weight=1)
        
        tk.Label(suffix_row, text="Suffix:", fg=FG_DIM, bg=BG, font=("Consolas", 9)).grid(row=0, column=0, sticky="w", padx=(0,4))
        self.suffix_entry = ttk.Entry(suffix_row)
        self.suffix_entry.grid(row=0, column=1, sticky="ew")
        
        tk.Label(suffix_row, text="🕐", fg=FG_DIM, bg=BG, font=("Consolas", 9)).grid(row=0, column=2, padx=(6,2))
        _make_date_btn(suffix_row, self.suffix_entry).grid(row=0, column=3, sticky="w")
        
        tk.Label(suffix_row, text=" Del R:", fg=FG_DIM, bg=BG, font=("Consolas", 9)).grid(row=0, column=4, padx=(4,2))
        self.del_right_sp = ttk.Spinbox(suffix_row, from_=0, to=999, width=3, textvariable=self.del_right_var, validate='all', validatecommand=vcmd_num_only)
        self.del_right_sp.grid(row=0, column=5, sticky="w")

        self.del_right_sp.bind("<FocusOut>", lambda e: _enforce_zero(self.del_right_var))
        ToolTip(self.del_right_sp, "Remove N characters from the Right")

        # Find & Replace
        opt.grid_columnconfigure(1, weight=1)
        opt.grid_columnconfigure(3, weight=1)
        lbl("Find:",   2, 0); self.find_entry   = ent(2, 1)
        lbl("Replace:",2, 2); self.replace_entry = ent(2, 3)

        def _check_find(*args):
            ft = self.find_entry.get()
            if not ft:
                return
            names = [os.path.splitext(os.path.basename(p))[0] for p in self.files]
            if names and not any(ft in n for n in names):
                self._show_toast("No match found")
        self.find_entry.bind("<FocusOut>", _check_find)
        self.find_entry.bind("<Return>",   _check_find)

        # Numbering row
        num_row = tk.Frame(opt, bg=BG)
        num_row.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(5, 0))

        self.number_var = tk.BooleanVar()
        ttk.Checkbutton(num_row, text="Numbering",
                        variable=self.number_var,
                        command=self.toggle_number_options).pack(side="left")

        for txt, attr, default, w_ in [
            ("Start:", "start_number",   "1", 5),
            ("Pad:",   "padding_number", "3", 5),
        ]:
            tk.Label(num_row, text=txt, fg=FG_DIM, bg=BG,
                     font=("Consolas", 9)).pack(side="left", padx=(8, 2))
            sp = ttk.Spinbox(num_row, from_=0, to=9999, width=w_)
            sp.set(default); sp.pack(side="left")
            sp.config(state="disabled")
            setattr(self, attr, sp)

        tk.Label(num_row, text="Pos:", fg=FG_DIM, bg=BG,
                 font=("Consolas", 9)).pack(side="left", padx=(8, 2))
        self.number_position = ttk.Combobox(num_row, values=["Start","End"],
                                            width=5, state="readonly")
        self.number_position.set("End"); self.number_position.pack(side="left")
        self.number_position.config(state="disabled")

        def _numbering_disabled_click(e):
            if not self.number_var.get():
                self._show_toast("Numbering is disabled")
        for _w in (self.start_number, self.padding_number, self.number_position):
            _w.bind("<Button-1>", _numbering_disabled_click)

        # Custom name row
        custom_row = tk.Frame(opt, bg=BG)
        custom_row.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(4, 0))
        tk.Label(custom_row, text="Custom name:", fg=FG_DIM, bg=BG,
                 font=("Consolas", 9)).pack(side="left", padx=(0, 6))
        self.custom_name_entry = ttk.Entry(custom_row)
        self.custom_name_entry.pack(side="left", fill="x", expand=True)
        self.custom_name_entry.config(state="disabled")
        self.custom_name_entry.bind("<Button-1>", _numbering_disabled_click)
        tk.Label(custom_row, text="Sep:", fg=FG_DIM, bg=BG,
                 font=("Consolas", 9)).pack(side="left", padx=(10, 4))
        self.separator_var = tk.StringVar(value="_")
        sep_frame = tk.Frame(custom_row, bg=BG)
        sep_frame.pack(side="left")
        for sep_val, sep_txt in [("_", "_ "), (".", ". "), ("-", "- "), ("", "none")]:
            ttk.Radiobutton(sep_frame, text=sep_txt, variable=self.separator_var,
                            value=sep_val).pack(side="left", padx=(0, 2))


        # ── Action bar ────────────────────────────────────────────────────
        bar = tk.Frame(self.root, bg=SURFACE, height=43)
        bar.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        bar.grid_propagate(False)

        self._icon_btn(bar, "reset", "Reset", self.reset_fields)

        self.toast_label = tk.Label(bar, text="", fg=NEON_RED, bg=SURFACE,
                                    font=("Consolas", 9), padx=4)
        self.toast_label.pack(side="left", padx=(8, 0))
        self._toast_job = None

        rename_btn = tk.Frame(bar, bg=NEON_PURP, cursor="hand2")
        rename_btn.pack(side="right", padx=(0, 8), pady=4)
        rename_ic = tk.Canvas(rename_btn, width=14, height=14, bg=NEON_PURP,
                              highlightthickness=0, cursor="hand2")
        rename_ic.pack(side="left", padx=(8, 3))
        draw_icon(rename_ic, "rename", BG, NEON_PURP)
        rename_lbl = tk.Label(rename_btn, text="Rename", fg=BG, bg=NEON_PURP,
                              font=("Consolas", 11, "bold"), padx=4, pady=2, cursor="hand2")
        rename_lbl.pack(side="left", padx=(0, 8))
        def rn_enter(e):
            rename_btn.config(bg=NEON_BLUE); rename_ic.config(bg=NEON_BLUE)
            rename_lbl.config(bg=NEON_BLUE); draw_icon(rename_ic, "rename", BG, NEON_BLUE)
        def rn_leave(e):
            rename_btn.config(bg=NEON_PURP); rename_ic.config(bg=NEON_PURP)
            rename_lbl.config(bg=NEON_PURP); draw_icon(rename_ic, "rename", BG, NEON_PURP)
        for w in (rename_btn, rename_ic, rename_lbl):
            w.bind("<Button-1>", lambda e: self.execute_rename())
            w.bind("<Enter>", rn_enter)
            w.bind("<Leave>", rn_leave)

    # ── Drop zone drawing ─────────────────────────────────────────────────────
    def _draw_drop_zone(self, active):
        c = self.drop_canvas
        c.delete("all")
        w = c.winfo_width() or 480
        h = c.winfo_height() or 40
        bg = "#1e2d3d" if active else SURFACE2
        bd = NEON_CYAN if active else BORDER
        tx = NEON_CYAN if active else FG_DIM
        c.configure(bg=bg, highlightbackground=bd)
        dash = (4, 3)
        c.create_line(5,3,   w-5,3,   dash=dash, fill=bd)
        c.create_line(w-3,5, w-3,h-5, dash=dash, fill=bd)
        c.create_line(w-5,h-3, 5,h-3, dash=dash, fill=bd)
        c.create_line(3,h-5, 3,5,     dash=dash, fill=bd)
        ix = w//2 - 85
        iy = h//2
        c.create_polygon(ix,iy-6, ix-5,iy, ix-2,iy, ix-2,iy+5,
                         ix+2,iy+5, ix+2,iy, ix+5,iy, fill=tx, outline="")
        c.create_rectangle(ix-5,iy+7, ix+5,iy+8, fill=tx, outline="")
        msg = "Release to add files" if active else (
              "Drag & drop files here" if DND_AVAILABLE else "Click to browse")
        c.create_text(w//2 - 68, h//2, text=msg,
                      font=("Consolas", 9), fill=tx, anchor="w")

    def _on_drop_enter(self, e): self._draw_drop_zone(True)
    def _on_drop_leave(self, e): self._draw_drop_zone(False)
    def _on_drop(self, e):
        self._draw_drop_zone(False)
        dropped = _parse_dnd_paths(e.data)
        if not dropped:
            messagebox.showwarning("Warning", "No valid files dropped."); return
        existing = set(self.files)
        self.files.extend(p for p in dropped if p not in existing)
        self._refresh_file_label()

    def _refresh_file_label(self):
        n = len(self.files)
        self.file_label.config(
            text="No files selected" if n == 0 else f"{n} file(s) selected",
            fg=FG_DIM if n == 0 else NEON_GRN)
        if n > 0:
            self.files_btn_frame.pack(side="left", padx=(8, 0))
        else:
            self.files_btn_frame.pack_forget()

    def open_github(self):
        import webbrowser; webbrowser.open("https://github.com/buonber/simple_rename")

    # ── Files manager dialog ──────────────────────────────────────────────────
    def open_files_manager(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("File List")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        self.root.update_idletasks()
        rx, ry = self.root.winfo_x(), self.root.winfo_y()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        dw, dh = 480, 380
        dlg.geometry(f"{dw}x{dh}+{rx+(rw-dw)//2}+{ry+(rh-dh)//2}")

        tk.Label(dlg, text="● Manage Files", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        lf = tk.Frame(dlg, bg=SURFACE)
        lf.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        lb = tk.Listbox(lf, bg=SURFACE, fg=FG, selectbackground=NEON_BLUE,
                        selectforeground=BG, font=("Consolas", 9),
                        borderwidth=0, highlightthickness=0,
                        activestyle="none", selectmode="extended")
        vsb = ttk.Scrollbar(lf, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=vsb.set)
        lb.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def refresh_lb():
            lb.delete(0, tk.END)
            for fp in self.files:
                lb.insert(tk.END, os.path.basename(fp))

        refresh_lb()

        def move_up():
            sel = list(lb.curselection())
            if not sel or sel[0] == 0: return
            for i in sel:
                if i == 0: continue
                self.files[i-1], self.files[i] = self.files[i], self.files[i-1]
            refresh_lb()
            for i in sel: lb.selection_set(i - 1)

        def move_down():
            sel = list(lb.curselection())
            if not sel or sel[-1] == len(self.files) - 1: return
            for i in reversed(sel):
                if i == len(self.files) - 1: continue
                self.files[i], self.files[i+1] = self.files[i+1], self.files[i]
            refresh_lb()
            for i in sel: lb.selection_set(i + 1)

        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        def add_files():
            paths = filedialog.askopenfilenames(title="Add files", parent=dlg)
            if paths:
                existing = set(self.files)
                self.files.extend(p for p in paths if p not in existing)
                refresh_lb()
                self._refresh_file_label()

        def remove_selected():
            sel = list(lb.curselection())
            if not sel:
                messagebox.showwarning("Warning", "Select files to remove.", parent=dlg)
                return
            for i in sorted(sel, reverse=True):
                del self.files[i]
            refresh_lb()
            self._refresh_file_label()

        add_btn = tk.Frame(btn_row, bg=SURFACE2, cursor="hand2")
        add_btn.pack(side="left", pady=2)
        add_ic = tk.Canvas(add_btn, width=14, height=14, bg=SURFACE2,
                           highlightthickness=0, cursor="hand2")
        add_ic.pack(side="left", padx=(6, 3))
        draw_icon(add_ic, "add", NEON_GRN, SURFACE2)
        add_lbl = tk.Label(add_btn, text="Add files", fg=NEON_GRN, bg=SURFACE2,
                           font=("Consolas", 9), padx=4, pady=4, cursor="hand2")
        add_lbl.pack(side="left", padx=(0, 6))
        def ae(e): add_btn.config(bg=NEON_GRN); add_ic.config(bg=NEON_GRN); add_lbl.config(bg=NEON_GRN, fg=BG); draw_icon(add_ic,"add",BG,NEON_GRN)
        def al(e): add_btn.config(bg=SURFACE2); add_ic.config(bg=SURFACE2); add_lbl.config(bg=SURFACE2, fg=NEON_GRN); draw_icon(add_ic,"add",NEON_GRN,SURFACE2)
        for w in (add_btn, add_ic, add_lbl):
            w.bind("<Button-1>", lambda e: add_files())
            w.bind("<Enter>", ae); w.bind("<Leave>", al)

        rem_btn = tk.Frame(btn_row, bg=SURFACE2, cursor="hand2")
        rem_btn.pack(side="left", padx=(8, 0), pady=2)
        rem_ic = tk.Canvas(rem_btn, width=14, height=14, bg=SURFACE2,
                           highlightthickness=0, cursor="hand2")
        rem_ic.pack(side="left", padx=(6, 3))
        draw_icon(rem_ic, "remove", NEON_RED, SURFACE2)
        rem_lbl = tk.Label(rem_btn, text="Remove", fg=NEON_RED, bg=SURFACE2,
                           font=("Consolas", 9), padx=4, pady=4, cursor="hand2")
        rem_lbl.pack(side="left", padx=(0, 6))
        def re_(e): rem_btn.config(bg=NEON_RED); rem_ic.config(bg=NEON_RED); rem_lbl.config(bg=NEON_RED, fg=BG); draw_icon(rem_ic,"remove",BG,NEON_RED)
        def rl(e):  rem_btn.config(bg=SURFACE2); rem_ic.config(bg=SURFACE2); rem_lbl.config(bg=SURFACE2, fg=NEON_RED); draw_icon(rem_ic,"remove",NEON_RED,SURFACE2)
        for w in (rem_btn, rem_ic, rem_lbl):
            w.bind("<Button-1>", lambda e: remove_selected())
            w.bind("<Enter>", re_); w.bind("<Leave>", rl)

        def _make_arrow_btn(parent, text, cmd, side_pad):
            btn = tk.Frame(parent, bg=SURFACE2, cursor="hand2")
            btn.pack(side="left", padx=side_pad, pady=2)
            lbl_ = tk.Label(btn, text=text, fg=NEON_CYAN, bg=SURFACE2,
                            font=("Consolas", 9, "bold"), padx=8, pady=4, cursor="hand2")
            lbl_.pack()
            def _e(e): btn.config(bg=NEON_CYAN); lbl_.config(bg=NEON_CYAN, fg=BG)
            def _l(e): btn.config(bg=SURFACE2);  lbl_.config(bg=SURFACE2, fg=NEON_CYAN)
            for w in (btn, lbl_):
                w.bind("<Button-1>", lambda e, c=cmd: c())
                w.bind("<Enter>", _e); w.bind("<Leave>", _l)

        _make_arrow_btn(btn_row, "▲ Up",   move_up,   (8, 0))
        _make_arrow_btn(btn_row, "▼ Down", move_down, (4, 0))

        done_btn = tk.Frame(btn_row, bg=NEON_BLUE, cursor="hand2")
        done_btn.pack(side="right", pady=2)
        done_lbl = tk.Label(done_btn, text="Done", fg=BG, bg=NEON_BLUE,
                            font=("Consolas", 9, "bold"), padx=14, pady=4, cursor="hand2")
        done_lbl.pack()
        def de(e): done_btn.config(bg=NEON_CYAN); done_lbl.config(bg=NEON_CYAN)
        def dl_(e): done_btn.config(bg=NEON_BLUE); done_lbl.config(bg=NEON_BLUE)
        for w in (done_btn, done_lbl):
            w.bind("<Button-1>", lambda e: dlg.destroy())
            w.bind("<Enter>", de); w.bind("<Leave>", dl_)

    # ── Logic ─────────────────────────────────────────────────────────────────
    def _show_toast(self, msg, color=None):
        if color is None: color = NEON_RED
        if self._toast_job is not None:
            self.root.after_cancel(self._toast_job)
            self._toast_job = None
        self.toast_label.config(text=msg, fg=color)

        def _fade(alpha=10):
            steps = [NEON_RED, "#d4738a", "#b05a6e", "#8c4255", "#6c3040",
                     "#4e2030", "#341220", "#1a0810", SURFACE]
            idx = 10 - alpha
            if idx < len(steps):
                self.toast_label.config(fg=steps[idx])
                self._toast_job = self.root.after(80, lambda: _fade(alpha - 1))
            else:
                self.toast_label.config(text="", fg=NEON_RED)
                self._toast_job = None

        self._toast_job = self.root.after(1000, lambda: _fade(10))

    def toggle_number_options(self):
        st = "normal" if self.number_var.get() else "disabled"
        for w in (self.start_number, self.padding_number,
                  self.number_position, self.custom_name_entry):
            w.config(state=st)

    def select_files(self):
        paths = filedialog.askopenfilenames(title="Select files to rename")
        if paths:
            existing = set(self.files)
            self.files.extend(p for p in paths if p not in existing)
            self._refresh_file_label()

    def generate_new_name(self, filename, index):
        import datetime
        name, ext = os.path.splitext(filename)
        sep = self.separator_var.get()

        # Enforce zero if empty just in case user clicks Rename without unfocusing
        if not self.del_left_var.get().strip(): self.del_left_var.set("0")
        if not self.del_right_var.get().strip(): self.del_right_var.set("0")

        # Apply left/right trim to original filename
        try: dl = int(self.del_left_var.get() or 0)
        except ValueError: dl = 0
        try: dr = int(self.del_right_var.get() or 0)
        except ValueError: dr = 0

        if dl > 0:
            name = name[dl:]
        if dr > 0 and name:
            name = name[:-dr]

        def _resolve_date(entry, is_prefix=True):
            fmt = getattr(entry, "_use_mtime", None)
            text = entry.get()
            if not fmt: return text
            
            fp = self.files[index] if index < len(self.files) else None
            if fp:
                ts = os.path.getmtime(fp)
                dt = datetime.datetime.fromtimestamp(ts)
            else:
                dt = datetime.datetime.now()
                
            if fmt == "YYMMDD":  d_str = dt.strftime("%y%m%d")
            elif fmt == "DDMMYY":  d_str = dt.strftime("%d%m%y")
            elif fmt == "YYYYMM":  d_str = dt.strftime("%Y%m")
            else: d_str = dt.strftime("%y%m%d")
            
            if not text: return d_str
            return f"{text}{sep}{d_str}" if is_prefix else f"{d_str}{sep}{text}"

        custom = self.custom_name_entry.get().strip() if self.number_var.get() else ""
        if custom:
            name = custom
        else:
            ft = self.find_entry.get()
            if ft: name = name.replace(ft, self.replace_entry.get())
            
        if self.number_var.get():
            try:
                num = str(int(self.start_number.get()) + index).zfill(
                          int(self.padding_number.get()))
                name = f"{num}{sep}{name}" if self.number_position.get() == "Start" \
                       else f"{name}{sep}{num}"
            except ValueError: pass

        prefix = _resolve_date(self.prefix_entry, True)
        suffix = _resolve_date(self.suffix_entry, False)
        
        if prefix: prefix = prefix + sep
        if suffix: suffix = sep + suffix
        
        case = self.case_var.get()
        full = f"{prefix}{name}{suffix}"
        
        # Apply case formatting
        if case == "upper": 
            return f"{full.upper()}{ext}" # Keep extension unchanged
        elif case == "lower": 
            return f"{full.lower()}{ext.lower()}"
        
        return f"{full}{ext}"

    def execute_rename(self):
        if not self.files:
            messagebox.showwarning("Warning", "No files to rename!"); return

        if not self.del_left_var.get().strip(): self.del_left_var.set("0")
        if not self.del_right_var.get().strip(): self.del_right_var.set("0")

        # Validate if trim length exceeds filename
        try: dl = int(self.del_left_var.get() or 0)
        except ValueError: dl = 0
        try: dr = int(self.del_right_var.get() or 0)
        except ValueError: dr = 0

        for fp in self.files:
            base_name = os.path.splitext(os.path.basename(fp))[0]
            if (dl + dr) > len(base_name):
                self._show_toast("Trim length exceeds filename")
                return

        pairs = [(fp, os.path.basename(fp), self.generate_new_name(os.path.basename(fp), i))
                 for i, fp in enumerate(self.files)]

        # ── Preview dialog ────────────────────────────────────────────────
        dlg = tk.Toplevel(self.root)
        dlg.title("Preview & Confirm")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        self.root.update_idletasks()
        rx, ry = self.root.winfo_x(), self.root.winfo_y()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        dw = 580
        dh = min(80 + len(pairs) * 20 + 70, 480)
        dlg.geometry(f"{dw}x{dh}+{rx+(rw-dw)//2}+{ry+(rh-dh)//2}")

        tk.Label(dlg, text=f"● Preview — {len(pairs)} file(s) will be renamed",
                 fg=NEON_CYAN, bg=BG, font=("Consolas", 9, "bold")).pack(
                 anchor="w", padx=12, pady=(10, 4))

        frm = tk.Frame(dlg, bg=SURFACE)
        frm.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

        cols = ("original", "arrow", "new")
        tree = ttk.Treeview(frm, columns=cols, show="headings",
                            height=min(len(pairs), 16))
        tree.heading("original", text="Original Name")
        tree.heading("arrow",    text="")
        tree.heading("new",      text="New Name")
        tree.column("original", width=230, minwidth=80)
        tree.column("arrow",    width=28,  stretch=False, anchor="center")
        tree.column("new",      width=270, minwidth=80)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        for _, fn, nn in pairs:
            tag = "changed" if fn != nn else "same"
            tree.insert("", "end", values=(fn, "→", nn), tags=(tag,))
        tree.tag_configure("changed", foreground=NEON_GRN)
        tree.tag_configure("same",    foreground=FG_DIM)

        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        confirmed = [False]

        cancel_btn = tk.Frame(btn_row, bg=SURFACE2, cursor="hand2")
        cancel_btn.pack(side="left", pady=2)
        cancel_lbl = tk.Label(cancel_btn, text="Cancel", fg=FG, bg=SURFACE2,
                              font=("Consolas", 9), padx=10, pady=4, cursor="hand2")
        cancel_lbl.pack()
        def ce(e): cancel_btn.config(bg=BORDER); cancel_lbl.config(bg=BORDER)
        def cl(e): cancel_btn.config(bg=SURFACE2); cancel_lbl.config(bg=SURFACE2)
        for w in (cancel_btn, cancel_lbl):
            w.bind("<Button-1>", lambda e: dlg.destroy())
            w.bind("<Enter>", ce); w.bind("<Leave>", cl)

        confirm_btn = tk.Frame(btn_row, bg=NEON_PURP, cursor="hand2")
        confirm_btn.pack(side="right", pady=2)
        confirm_ic = tk.Canvas(confirm_btn, width=14, height=14, bg=NEON_PURP,
                               highlightthickness=0, cursor="hand2")
        confirm_ic.pack(side="left", padx=(8, 3))
        draw_icon(confirm_ic, "rename", BG, NEON_PURP)
        confirm_lbl = tk.Label(confirm_btn, text="Confirm Rename", fg=BG, bg=NEON_PURP,
                               font=("Consolas", 9, "bold"), padx=4, pady=4, cursor="hand2")
        confirm_lbl.pack(side="left", padx=(0, 8))
        def cfe(e):
            confirm_btn.config(bg=NEON_BLUE); confirm_ic.config(bg=NEON_BLUE)
            confirm_lbl.config(bg=NEON_BLUE); draw_icon(confirm_ic,"rename",BG,NEON_BLUE)
        def cfl(e):
            confirm_btn.config(bg=NEON_PURP); confirm_ic.config(bg=NEON_PURP)
            confirm_lbl.config(bg=NEON_PURP); draw_icon(confirm_ic,"rename",BG,NEON_PURP)
        for w in (confirm_btn, confirm_ic, confirm_lbl):
            w.bind("<Button-1>", lambda e: [confirmed.__setitem__(0,True), dlg.destroy()])
            w.bind("<Enter>", cfe); w.bind("<Leave>", cfl)

        dlg.wait_window()
        if not confirmed[0]: return

        ok = err = 0; errors = []
        for fp, fn, nn in pairs:
            np_ = os.path.join(os.path.dirname(fp), nn)
            try:
                same_path = os.path.normcase(fp) == os.path.normcase(np_)
                if os.path.exists(np_) and not same_path:
                    errors.append(f"{fn} → already exists"); err += 1
                else:
                    os.rename(fp, np_); ok += 1
            except Exception as ex:
                errors.append(f"{fn}: {ex}"); err += 1

        msg = f"Renamed: {ok}  |  Failed: {err}"
        if errors: msg += "\n\n" + "\n".join(errors[:10])
        (messagebox.showwarning if err else messagebox.showinfo)("Result", msg)
        self.files = []
        self._refresh_file_label()

    def reset_fields(self):
        for e in (self.prefix_entry, self.suffix_entry,
                  self.find_entry, self.replace_entry):
            e.delete(0, tk.END)
            
        self.prefix_entry._use_mtime = None
        self.prefix_entry._date_var.set("none")
        self.prefix_entry._date_active = False
        
        self.suffix_entry._use_mtime = None
        self.suffix_entry._date_var.set("none")
        self.suffix_entry._date_active = False
        
        self.del_left_var.set("0")
        self.del_right_var.set("0")
        
        self.custom_name_entry.config(state="normal")
        self.custom_name_entry.delete(0, tk.END)
        self.number_var.set(False)
        self.case_var.set("")
        self._prev_case = ""
        self.start_number.set("1")
        self.padding_number.set("3")
        self.number_position.set("End")
        self.separator_var.set("_")
        self.toggle_number_options()


if __name__ == "__main__":
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    
    # Hide window instantly before OS draws the white frame
    root.attributes("-alpha", 0.0) 
    
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        root.iconbitmap(os.path.join(base_path, "app.ico"))
    except Exception:
        pass
        
    app = BatchRenameApp(root)
    root.mainloop()