import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import subprocess
import re
import math
import shutil
import datetime
import webbrowser

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
    paths = [m.group(1) or m.group(2) for m in re.finditer(r'\{([^}]+)\}|(\S+)', raw)]
    return [p for p in paths if os.path.isfile(p) or os.path.isdir(p)]

def _lerp_hex(c1, c2, t):
    r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

def _arc_pts(cx, cy, r, start_deg, end_deg, steps):
    pts = []
    for i in range(steps + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts += [cx + r * math.cos(a), cy - r * math.sin(a)]
    return pts

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

DATE_FORMATS = ["none", "YYMMDD", "DDMMYY", "YYYYMM"]

# ── ToolTip ───────────────────────────────────────────────────────────────────
class ToolTip:
    def __init__(self, widget, text):
        self.widget  = widget
        self.text    = text
        self.tw      = None
        self._ids    = {}   # name → after-id
        self.show_count = 0
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")

    def _cancel(self, *names):
        for n in names:
            if self._ids.get(n):
                self.widget.after_cancel(self._ids.pop(n))

    def _enter(self, _=None):
        if self.show_count < 3:
            self._cancel("show")
            self._ids["show"] = self.widget.after(500, self._show)

    def _leave(self, _=None):
        self._cancel("show", "wait", "fade")
        self._hide()

    def _show(self, _=None):
        self.show_count += 1
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tw = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-alpha", 1.0)
        tk.Label(tw, text=self.text, justify=tk.LEFT,
                 background=SURFACE2, foreground=FG,
                 relief=tk.SOLID, borderwidth=1,
                 font=("Consolas", 8)).pack(ipadx=4, ipady=2)
        self._ids["wait"] = self.widget.after(1000, self._fade)

    def _fade(self, alpha=1.0):
        if not self.tw: return
        alpha -= 0.08
        if alpha > 0:
            self.tw.attributes("-alpha", alpha)
            self._ids["fade"] = self.widget.after(40, lambda: self._fade(alpha))
        else:
            self._hide()

    def _hide(self):
        if self.tw:
            self.tw.destroy()
            self.tw = None

# ── Icon painter ──────────────────────────────────────────────────────────────
def draw_icon(canvas, kind, color, bg):
    canvas.delete("all")
    c, b = color, bg
    if kind == "rename":
        canvas.create_polygon(3,12, 5,12, 13,4, 11,2, fill=c, outline="")
        canvas.create_polygon(3,12, 5,12, 4,14, fill=c, outline="")
        canvas.create_line(11,2, 13,4, fill=b, width=1)
    elif kind == "reset":
        pts = _arc_pts(8, 8, 5, -30, 270, 18)
        if len(pts) >= 4: canvas.create_line(pts, fill=c, width=2)
        canvas.create_polygon(12,3, 14,7, 10,6, fill=c, outline="")
    elif kind == "files":
        for ox, oy in [(3,1),(2,0),(1,1)]:
            canvas.create_rectangle(ox+1,oy+3, ox+9,oy+12, outline=c, width=1)
        canvas.create_rectangle(2,4, 12,13, fill=bg, outline=c, width=1)
        for y in (7, 9, 11): canvas.create_line(5,y, 9,y, fill=c, width=1)
    elif kind == "add":
        canvas.create_oval(1,1,13,13, outline=c, width=1.5)
        canvas.create_line(7,4, 7,10, fill=c, width=2)
        canvas.create_line(4,7, 10,7, fill=c, width=2)
    elif kind == "remove":
        canvas.create_oval(1,1,13,13, outline=c, width=1.5)
        canvas.create_line(4,7, 10,7, fill=c, width=2)
    elif kind == "folder":
        canvas.create_polygon(1,5, 1,13, 13,13, 13,6, 6,6, 5,5, fill=c, outline="")
        canvas.create_rectangle(1,6, 13,13, fill=c, outline="")
    elif kind == "file":
        canvas.create_polygon(2,1, 9,1, 12,4, 12,13, 2,13, fill=c, outline="")
        canvas.create_polygon(9,1, 9,4, 12,4, fill=b, outline="")
        for y in (6, 8): canvas.create_line(4,y, 10,y, fill=b, width=1)
        canvas.create_line(4,10, 9,10, fill=b, width=1)
    elif kind == "export":
        canvas.create_line(7,4, 13,4, fill=c, width=2)
        canvas.create_line(13,4, 10,1, fill=c, width=2)
        canvas.create_line(13,4, 10,7, fill=c, width=2)
    elif kind == "github":
        canvas.create_oval(4,3,12,10, fill=c, outline="")
        canvas.create_oval(5,7,11,14, fill=c, outline="")
        canvas.create_polygon(4,5,5,2,7,5,   fill=b, outline="")
        canvas.create_polygon(9,5,11,2,12,5, fill=b, outline="")
        canvas.create_oval(5,4,7,6, fill=b, outline="")
        canvas.create_oval(9,4,11,6, fill=b, outline="")


class BatchRenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Renamer v1.7")

        w, h = 470, 350
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        root.resizable(False, False)
        root.configure(bg=BG)
        root.attributes("-alpha", 0.0)

        self.files          = []
        self.rename_to_dir  = None
        self._hover_fade_id = None
        self._toast_job     = None

        self._setup_styles()
        self._create_widgets()
        root.update_idletasks()
        root.after(50, self._fade_in)

    # ── Fade-in ───────────────────────────────────────────────────────────────
    def _fade_in(self, alpha=0.0):
        alpha = min(alpha + 0.05, 1.0)
        self.root.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.root.after(30, lambda: self._fade_in(alpha))

    # ── Styles ────────────────────────────────────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        base = dict(background=BG, foreground=FG, fieldbackground=INPUT_BG,
                    bordercolor=BORDER, darkcolor=SURFACE, lightcolor=SURFACE,
                    troughcolor=SURFACE, font=("Consolas", 9))
        s.configure(".", **base)
        s.configure("TLabel",      background=BG,      foreground=FG,       font=("Consolas", 9))
        s.configure("TFrame",      background=BG)
        s.configure("TEntry",      fieldbackground=INPUT_BG, foreground=FG,
                    insertcolor=NEON_BLUE, bordercolor=BORDER, font=("Consolas", 9))
        s.map("TEntry",       bordercolor=[("focus", NEON_BLUE)])
        s.configure("TCheckbutton", background=BG, foreground=FG, font=("Consolas", 9),
                    indicatorcolor=SURFACE2, indicatorrelief="flat")
        s.map("TCheckbutton", indicatorcolor=[("selected", NEON_BLUE)],
                              foreground=[("active", NEON_BLUE)])
        s.configure("TRadiobutton", background=BG, foreground=FG, font=("Consolas", 9),
                    indicatorcolor=SURFACE2, indicatorrelief="flat")
        s.map("TRadiobutton", indicatorcolor=[("selected", NEON_CYAN)],
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
        s.map("Treeview", background=[("selected", NEON_BLUE)],
                          foreground=[("selected", BG)])
        s.configure("Vertical.TScrollbar", background=SURFACE2, troughcolor=SURFACE,
                    arrowcolor=FG_DIM, bordercolor=BORDER)

    # ── Helper: hoverable icon button ─────────────────────────────────────────
    def _icon_btn(self, parent, icon_kind, label, command,
                  fg=FG, bg=SURFACE2, hover=NEON_BLUE,
                  bold=False, side="left", padx=(6, 0)):
        frame = tk.Frame(parent, bg=bg, cursor="hand2")
        frame.pack(side=side, padx=padx, pady=4)
        ic = tk.Canvas(frame, width=14, height=14, bg=bg,
                       highlightthickness=0, cursor="hand2")
        ic.pack(side="left", padx=(6, 3))
        draw_icon(ic, icon_kind, fg, bg)
        lbl = tk.Label(frame, text=label, fg=fg, bg=bg, cursor="hand2",
                       font=("Consolas", 11, "bold") if bold else ("Consolas", 11),
                       padx=4, pady=2)
        lbl.pack(side="left", padx=(0, 6))

        def _enter(_=None):
            frame.config(bg=hover); ic.config(bg=hover)
            lbl.config(bg=hover, fg=BG); draw_icon(ic, icon_kind, BG, hover)
        def _leave(_=None):
            frame.config(bg=bg); ic.config(bg=bg)
            lbl.config(bg=bg, fg=fg); draw_icon(ic, icon_kind, fg, bg)
        for w in (frame, ic, lbl):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
        return frame

    # ── Helper: bind hover color swap to a set of widgets ────────────────────
    @staticmethod
    def _bind_hover(widgets, normal_bg, hover_bg, *extra_pairs):
        """extra_pairs: (widget, normal_fg, hover_fg) for label color flips."""
        def _enter(_=None):
            for w in widgets: w.config(bg=hover_bg)
            for w, _, hfg in extra_pairs: w.config(fg=hfg)
        def _leave(_=None):
            for w in widgets: w.config(bg=normal_bg)
            for w, nfg, _ in extra_pairs: w.config(fg=nfg)
        for w in widgets:
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

    # ── Helper: center a Toplevel over root ───────────────────────────────────
    def _center_dlg(self, dlg, dw, dh):
        self.root.update_idletasks()
        rx, ry = self.root.winfo_x(), self.root.winfo_y()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        dlg.geometry(f"{dw}x{dh}+{rx+(rw-dw)//2}+{ry+(rh-dh)//2}")

    # ── Widgets ───────────────────────────────────────────────────────────────
    def _create_widgets(self):
        self.root.grid_columnconfigure(0, weight=1)

        # ── Top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg=BG)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(12, 6))

        # "Rename to..." button
        self.renameto_btn = tk.Frame(top, bg=SURFACE2, cursor="hand2")
        self.renameto_btn.pack(side="left", padx=(0, 6))
        self.renameto_ic = tk.Canvas(self.renameto_btn, width=14, height=14,
                                     bg=SURFACE2, highlightthickness=0, cursor="hand2")
        self.renameto_ic.pack(side="left", padx=(6, 3), pady=4)
        draw_icon(self.renameto_ic, "export", NEON_PURP, SURFACE2)
        self.renameto_lbl = tk.Label(self.renameto_btn, text="Rename to...",
                                     fg=FG, bg=SURFACE2, font=("Consolas", 9),
                                     padx=6, pady=3, cursor="hand2")
        self.renameto_lbl.pack(side="left")
        def rt_enter(_=None):
            col = NEON_PURP if self.rename_to_dir is None else NEON_GRN
            self.renameto_btn.config(bg=col); self.renameto_ic.config(bg=col)
            self.renameto_lbl.config(bg=col, fg=BG)
            draw_icon(self.renameto_ic, "export", BG, col)
        for w in (self.renameto_btn, self.renameto_ic, self.renameto_lbl):
            w.bind("<Button-1>", lambda e: self.pick_rename_to_dir())
            w.bind("<Enter>", rt_enter)
            w.bind("<Leave>", lambda e: self._update_renameto_btn())

        # "View files" button (hidden until files added)
        self.files_btn = tk.Frame(top, bg=SURFACE2, cursor="hand2")
        self.files_btn_ic = tk.Canvas(self.files_btn, width=14, height=14,
                                      bg=SURFACE2, highlightthickness=0, cursor="hand2")
        self.files_btn_ic.pack(side="left", padx=(6, 3), pady=3)
        draw_icon(self.files_btn_ic, "files", NEON_CYAN, SURFACE2)
        self.files_btn_lbl = tk.Label(self.files_btn, text="File list",
                                      fg=NEON_CYAN, bg=SURFACE2,
                                      font=("Consolas", 9), padx=4, pady=2, cursor="hand2")
        self.files_btn_lbl.pack(side="left", padx=(0, 6))
        def fb_enter(_=None):
            self.files_btn.config(bg=NEON_CYAN); self.files_btn_ic.config(bg=NEON_CYAN)
            self.files_btn_lbl.config(bg=NEON_CYAN, fg=BG)
            draw_icon(self.files_btn_ic, "files", BG, NEON_CYAN)
        def fb_leave(_=None):
            self.files_btn.config(bg=SURFACE2); self.files_btn_ic.config(bg=SURFACE2)
            self.files_btn_lbl.config(bg=SURFACE2, fg=NEON_CYAN)
            draw_icon(self.files_btn_ic, "files", NEON_CYAN, SURFACE2)
        for w in (self.files_btn, self.files_btn_ic, self.files_btn_lbl):
            w.bind("<Button-1>", lambda e: self.open_files_manager())
            w.bind("<Enter>", fb_enter)
            w.bind("<Leave>", fb_leave)

        # GitHub link
        gh = tk.Frame(top, bg=BG, cursor="hand2")
        gh.pack(side="right", padx=(4, 0))
        gh_ic = tk.Canvas(gh, width=14, height=14, bg=BG,
                          highlightthickness=0, cursor="hand2")
        gh_ic.pack(side="left", padx=(0, 4))
        draw_icon(gh_ic, "github", NEON_BLUE, BG)
        gh_lbl = tk.Label(gh, text="buonber", fg=NEON_BLUE, bg=BG,
                          font=("Consolas", 8), cursor="hand2")
        gh_lbl.pack(side="left")
        for w in (gh, gh_ic, gh_lbl):
            w.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/buonber/simple_rename"))
            w.bind("<Enter>",    lambda e: gh_lbl.config(fg=NEON_CYAN))
            w.bind("<Leave>",    lambda e: gh_lbl.config(fg=NEON_BLUE))

        # ── Drop zone ─────────────────────────────────────────────────────────
        drop_wrap = tk.Frame(self.root, bg=BG)
        drop_wrap.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))
        drop_wrap.grid_columnconfigure(0, weight=1)

        self.drop_canvas = tk.Canvas(drop_wrap, height=77, bg=SURFACE2,
                                     highlightthickness=1, highlightbackground=BORDER,
                                     cursor="hand2")
        self.drop_canvas.grid(row=0, column=0, sticky="ew")
        self.drop_canvas.bind("<Configure>", lambda e: self._draw_drop_zone(False))
        self.drop_canvas.bind("<Button-1>",  lambda e: self.select_files())
        self.drop_canvas.bind("<Enter>",     lambda e: self._dz_hover_enter())
        self.drop_canvas.bind("<Leave>",     lambda e: self._dz_hover_leave())
        if DND_AVAILABLE:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<DropEnter>>", lambda e: self._draw_drop_zone(True))
            self.drop_canvas.dnd_bind("<<DropLeave>>", lambda e: self._draw_drop_zone(False))
            self.drop_canvas.dnd_bind("<<Drop>>",      self._on_drop)

        # ── Rename Options header ─────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG)
        hdr.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 2))
        tk.Label(hdr, text="●", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 8, "bold")).pack(side="left", padx=(0, 5))
        tk.Label(hdr, text="Rename Options", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 9, "bold")).pack(side="left")

        self.case_var  = tk.StringVar(value="")
        self._prev_case = ""

        def _toggle_case(val):
            if self._prev_case == val:
                self.case_var.set(""); self._prev_case = ""
            else:
                self.case_var.set(val); self._prev_case = val

        for val, txt, px in [("lower", "lowercase", (4, 0)), ("upper", "UPPERCASE", (8, 0))]:
            ttk.Checkbutton(hdr, text=txt, variable=self.case_var,
                            onvalue=val, offvalue="",
                            command=lambda v=val: _toggle_case(v)
                            ).pack(side="right", padx=px)

        # ── Options grid ──────────────────────────────────────────────────────
        opt = tk.Frame(self.root, bg=BG)
        opt.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 2))
        opt.grid_columnconfigure(1, weight=1)
        opt.grid_columnconfigure(3, weight=1)

        vcmd = (self.root.register(lambda P: P.isdigit() or P == ""), "%P")
        self.del_left_var  = tk.StringVar(value="0")
        self.del_right_var = tk.StringVar(value="0")

        def _enforce_zero(var):
            if not var.get().strip(): var.set("0")

        def _make_date_combo(parent, entry):
            fv = tk.StringVar(value="none")
            entry._date_var    = fv
            entry._use_mtime   = None
            entry._date_active = False
            cb = ttk.Combobox(parent, values=DATE_FORMATS, textvariable=fv,
                              width=7, state="readonly", font=("Consolas", 8))
            def _sel(*_):
                cb.selection_clear()
                val = fv.get()
                if val == "none":
                    entry._use_mtime = None
                    if entry._date_active:
                        entry.delete(0, tk.END)
                        entry._date_active = False
                else:
                    entry._use_mtime   = val
                    entry._date_active = True
            cb.bind("<<ComboboxSelected>>", _sel)
            cb.bind("<FocusIn>", lambda e: cb.selection_clear())
            ToolTip(cb, "Append creation/modified date")
            return cb

        def _opt_row(row, label_txt, var_attr, del_attr, del_var, del_tip):
            row_f = tk.Frame(opt, bg=BG)
            row_f.grid(row=row, column=0, columnspan=4, sticky="ew", pady=3)
            row_f.grid_columnconfigure(1, weight=1)
            tk.Label(row_f, text=label_txt, fg=FG_DIM, bg=BG,
                     font=("Consolas", 9)).grid(row=0, column=0, sticky="w", padx=(0, 4))
            entry = ttk.Entry(row_f)
            entry.grid(row=0, column=1, sticky="ew")
            tk.Label(row_f, text="🕐", fg=FG_DIM, bg=BG,
                     font=("Consolas", 9)).grid(row=0, column=2, padx=(6, 2))
            _make_date_combo(row_f, entry).grid(row=0, column=3, sticky="w")
            tk.Label(row_f, text=f" {del_attr}:", fg=FG_DIM, bg=BG,
                     font=("Consolas", 9)).grid(row=0, column=4, padx=(4, 2))
            sp = ttk.Spinbox(row_f, from_=0, to=999, width=3,
                             textvariable=del_var, validate="all", validatecommand=vcmd)
            sp.grid(row=0, column=5, sticky="w")
            sp.bind("<FocusOut>", lambda e: _enforce_zero(del_var))
            ToolTip(sp, del_tip)
            setattr(self, var_attr, entry)
            setattr(self, f"del_{del_attr.lower()}_sp", sp)
            return entry

        self.prefix_entry = _opt_row(0, "Prefix:", "prefix_entry", "Del L",
                                     self.del_left_var,  "Remove N characters from the Left")
        self.suffix_entry = _opt_row(1, "Suffix:", "suffix_entry", "Del R",
                                     self.del_right_var, "Remove N characters from the Right")

        # Find & Replace
        tk.Label(opt, text="Find:",    fg=FG_DIM, bg=BG, font=("Consolas", 9)
                 ).grid(row=2, column=0, sticky="w", padx=(0, 4), pady=1)
        self.find_entry = ttk.Entry(opt)
        self.find_entry.grid(row=2, column=1, sticky="ew", pady=3)
        tk.Label(opt, text="Replace:", fg=FG_DIM, bg=BG, font=("Consolas", 9)
                 ).grid(row=2, column=2, sticky="w", padx=(0, 4), pady=1)
        self.replace_entry = ttk.Entry(opt)
        self.replace_entry.grid(row=2, column=3, sticky="ew", pady=3)

        def _check_find(*_):
            ft = self.find_entry.get()
            if ft and self.files:
                names = [os.path.splitext(os.path.basename(p))[0] for p in self.files]
                if not any(ft in n for n in names):
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

        for txt, attr, default, w_ in [("Start:", "start_number", "1", 5),
                                        ("Pad:",   "padding_number", "3", 5)]:
            tk.Label(num_row, text=txt, fg=FG_DIM, bg=BG,
                     font=("Consolas", 9)).pack(side="left", padx=(8, 2))
            sp = ttk.Spinbox(num_row, from_=0, to=9999, width=w_)
            sp.set(default); sp.pack(side="left")
            sp.config(state="disabled")
            setattr(self, attr, sp)

        tk.Label(num_row, text="Pos:", fg=FG_DIM, bg=BG,
                 font=("Consolas", 9)).pack(side="left", padx=(8, 2))
        self.number_position = ttk.Combobox(num_row, values=["Start", "End"],
                                            width=5, state="readonly")
        self.number_position.set("End"); self.number_position.pack(side="left")
        self.number_position.config(state="disabled")

        def _numbering_disabled_click(e):
            if not self.number_var.get(): self._show_toast("Numbering is disabled")
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
        sep_f = tk.Frame(custom_row, bg=BG)
        sep_f.pack(side="left")
        for val, txt in [("_", "_ "), (".", ". "), ("-", "- "), ("", "none")]:
            ttk.Radiobutton(sep_f, text=txt, variable=self.separator_var,
                            value=val).pack(side="left", padx=(0, 2))

        # ── Action bar ────────────────────────────────────────────────────────
        bar = tk.Frame(self.root, bg=SURFACE, height=43)
        bar.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        bar.grid_propagate(False)

        self._icon_btn(bar, "reset", "Reset", self.reset_fields)

        self.toast_label = tk.Label(bar, text="", fg=NEON_RED, bg=SURFACE,
                                    font=("Consolas", 9), padx=4)
        self.toast_label.pack(side="left", padx=(8, 0))

        # Rename button
        rb = tk.Frame(bar, bg=NEON_PURP, cursor="hand2")
        rb.pack(side="right", padx=(0, 8), pady=4)
        rb_ic = tk.Canvas(rb, width=14, height=14, bg=NEON_PURP,
                          highlightthickness=0, cursor="hand2")
        rb_ic.pack(side="left", padx=(8, 3))
        draw_icon(rb_ic, "rename", BG, NEON_PURP)
        rb_lbl = tk.Label(rb, text="Rename", fg=BG, bg=NEON_PURP,
                          font=("Consolas", 11, "bold"), padx=4, pady=2, cursor="hand2")
        rb_lbl.pack(side="left", padx=(0, 8))
        def rb_enter(_=None):
            rb.config(bg=NEON_BLUE); rb_ic.config(bg=NEON_BLUE)
            rb_lbl.config(bg=NEON_BLUE); draw_icon(rb_ic, "rename", BG, NEON_BLUE)
        def rb_leave(_=None):
            rb.config(bg=NEON_PURP); rb_ic.config(bg=NEON_PURP)
            rb_lbl.config(bg=NEON_PURP); draw_icon(rb_ic, "rename", BG, NEON_PURP)
        for w in (rb, rb_ic, rb_lbl):
            w.bind("<Button-1>", lambda e: self.execute_rename())
            w.bind("<Enter>", rb_enter)
            w.bind("<Leave>", rb_leave)

    # ── Drop zone drawing ─────────────────────────────────────────────────────
    def _dz_border(self, c, w, h, color):
        d = (4, 3)
        c.create_line(5,3,   w-5,3,   dash=d, fill=color)
        c.create_line(w-3,5, w-3,h-5, dash=d, fill=color)
        c.create_line(w-5,h-3, 5,h-3, dash=d, fill=color)
        c.create_line(3,h-5, 3,5,     dash=d, fill=color)

    def _draw_drop_zone(self, active):
        c = self.drop_canvas
        c.delete("all")
        w = c.winfo_width() or 480
        h = c.winfo_height() or 72
        bg = "#1e2d3d" if active else SURFACE2
        bd = NEON_CYAN if active else BORDER
        tx = NEON_CYAN if active else FG_DIM
        c.configure(bg=bg, highlightbackground=bd)
        self._dz_border(c, w, h, bd)
        msg = "Release to add" if active else (
              "Drag & drop files / folders here" if DND_AVAILABLE
              else "Click to browse files / folders")
        icon_w, gap = 12, 6
        x0 = w // 2 - (icon_w + gap + int(len(msg) * 6.5)) // 2
        iy = h // 2
        ix = x0 + icon_w // 2
        c.create_polygon(ix,iy-6, ix-5,iy, ix-2,iy, ix-2,iy+5,
                         ix+2,iy+5, ix+2,iy, ix+5,iy, fill=tx, outline="")
        c.create_rectangle(ix-5, iy+7, ix+5, iy+8, fill=tx, outline="")
        c.create_text(x0 + icon_w + gap, iy, text=msg,
                      font=("Consolas", 9), fill=tx, anchor="w")

    def _draw_drop_zone_selected(self):
        c = self.drop_canvas
        c.delete("all")
        w = c.winfo_width() or 480
        h = c.winfo_height() or 72
        c.configure(bg=SURFACE2, highlightbackground=NEON_GRN)
        self._dz_border(c, w, h, NEON_GRN)
        n_folders = sum(1 for p in self.files if os.path.isdir(p))
        n_files   = len(self.files) - n_folders
        parts = ([f"{n_folders} folder(s)"] if n_folders else []) + \
                ([f"{n_files} file(s)"]    if n_files   else [])
        summary = " + ".join(parts) + " ready to rename"
        cx, cy = w // 2, h // 2 - 4
        c.create_line(cx-10, cy,   cx-4,  cy+7,  fill=NEON_GRN, width=2)
        c.create_line(cx-4,  cy+7, cx+10, cy-8,  fill=NEON_GRN, width=2)
        c.create_text(w // 2, h // 2 + 12, text=summary,
                      font=("Consolas", 9, "bold"), fill=NEON_GRN, anchor="center")

    def _draw_drop_zone_color(self, bg, bd, tx):
        c = self.drop_canvas
        c.delete("all")
        w = c.winfo_width() or 480
        h = c.winfo_height() or 72
        c.configure(bg=bg, highlightbackground=bd)
        self._dz_border(c, w, h, bd)
        msg = "Drag & drop files / folders here" if DND_AVAILABLE \
              else "Click to browse files / folders"
        icon_w, gap = 12, 6
        x0 = w // 2 - (icon_w + gap + int(len(msg) * 6.5)) // 2
        iy = h // 2
        ix = x0 + icon_w // 2
        c.create_polygon(ix,iy-6, ix-5,iy, ix-2,iy, ix-2,iy+5,
                         ix+2,iy+5, ix+2,iy, ix+5,iy, fill=tx, outline="")
        c.create_rectangle(ix-5, iy+7, ix+5, iy+8, fill=tx, outline="")
        c.create_text(x0 + icon_w + gap, iy, text=msg,
                      font=("Consolas", 9), fill=tx, anchor="w")

    def _dz_hover_enter(self):
        if self.files: return
        if self._hover_fade_id:
            self.drop_canvas.after_cancel(self._hover_fade_id)
            self._hover_fade_id = None
        self._draw_drop_zone_color("#1a2535", NEON_CYAN, NEON_CYAN)
        self._hover_fade_id = self.drop_canvas.after(300, self._dz_fade_out)

    def _dz_fade_out(self, step=0):
        STEPS = 8
        t = step / STEPS
        self._draw_drop_zone_color(
            _lerp_hex("#1a2535", SURFACE2,  t),
            _lerp_hex(NEON_CYAN, BORDER,    t),
            _lerp_hex(NEON_CYAN, FG_DIM,    t))
        if step < STEPS:
            self._hover_fade_id = self.drop_canvas.after(
                30, lambda: self._dz_fade_out(step + 1))
        else:
            self._hover_fade_id = None

    def _dz_hover_leave(self):
        if self.files: return
        if self._hover_fade_id:
            self.drop_canvas.after_cancel(self._hover_fade_id)
            self._hover_fade_id = None
        self._draw_drop_zone(False)

    def _on_drop(self, e):
        self._draw_drop_zone(False)
        dropped = _parse_dnd_paths(e.data)
        if not dropped:
            messagebox.showwarning("Warning", "No valid files or folders dropped.")
            return
        existing = set(self.files)
        self.files.extend(p for p in dropped if p not in existing)
        self._refresh_drop()

    # ── File list refresh ─────────────────────────────────────────────────────
    def _refresh_drop(self):
        if self.files:
            self._draw_drop_zone_selected()
            self.files_btn.pack(side="left", padx=(6, 0))
        else:
            self._draw_drop_zone(False)
            self.files_btn.pack_forget()

    # ── Files manager dialog ──────────────────────────────────────────────────
    def open_files_manager(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("File List")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        self._center_dlg(dlg, 480, 380)

        tk.Label(dlg, text="● Manage Files", fg=NEON_BLUE, bg=BG,
                 font=("Consolas", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        lf = tk.Frame(dlg, bg=SURFACE)
        lf.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        list_cv = tk.Canvas(lf, bg=SURFACE, highlightthickness=0)
        vsb = ttk.Scrollbar(lf, orient="vertical", command=list_cv.yview)
        list_cv.configure(yscrollcommand=vsb.set)
        list_cv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        inner = tk.Frame(list_cv, bg=SURFACE)
        inner_id = list_cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: list_cv.configure(scrollregion=list_cv.bbox("all")))
        list_cv.bind("<Configure>",
                     lambda e: list_cv.itemconfig(inner_id, width=e.width))

        selected_rows = set()
        row_widgets   = []   # (frame, canvas, label)

        def _repaint():
            for i, (fr, ic, lbl) in enumerate(row_widgets):
                sel   = i in selected_rows
                bg_   = NEON_BLUE if sel else SURFACE
                fg_   = BG        if sel else FG
                is_dir = os.path.isdir(self.files[i])
                ic_col = BG if sel else (NEON_PURP if is_dir else NEON_CYAN)
                fr.config(bg=bg_); ic.config(bg=bg_); lbl.config(bg=bg_, fg=fg_)
                draw_icon(ic, "folder" if is_dir else "file", ic_col, bg_)

        def _select(idx, event=None):
            ctrl  = event and (event.state & 0x4)
            shift = event and (event.state & 0x1)
            if ctrl:
                selected_rows.discard(idx) if idx in selected_rows else selected_rows.add(idx)
            elif shift and selected_rows:
                lo, hi = min(max(selected_rows), idx), max(max(selected_rows), idx)
                selected_rows.update(range(lo, hi + 1))
            else:
                selected_rows.clear(); selected_rows.add(idx)
            _repaint()

        def refresh_lb():
            for w in inner.winfo_children(): w.destroy()
            row_widgets.clear(); selected_rows.clear()
            for i, fp in enumerate(self.files):
                is_dir = os.path.isdir(fp)
                fr  = tk.Frame(inner, bg=SURFACE, cursor="hand2")
                fr.pack(fill="x")
                ic  = tk.Canvas(fr, width=14, height=14, bg=SURFACE,
                                highlightthickness=0, cursor="hand2")
                ic.pack(side="left", padx=(6, 3), pady=4)
                draw_icon(ic, "folder" if is_dir else "file",
                          NEON_PURP if is_dir else NEON_CYAN, SURFACE)
                lbl = tk.Label(fr, text=os.path.basename(fp), fg=FG, bg=SURFACE,
                               font=("Consolas", 9), anchor="w", cursor="hand2")
                lbl.pack(side="left", fill="x", expand=True, pady=2)
                row_widgets.append((fr, ic, lbl))
                for w in (fr, ic, lbl):
                    w.bind("<Button-1>", lambda e, i=i: _select(i, e))

        refresh_lb()

        def move_up():
            sel = sorted(selected_rows)
            if not sel or sel[0] == 0: return
            for i in sel:
                if i > 0: self.files[i-1], self.files[i] = self.files[i], self.files[i-1]
            new = {i-1 for i in sel if i > 0}
            selected_rows.clear(); selected_rows.update(new)
            refresh_lb(); selected_rows.update(new); _repaint()

        def move_down():
            sel = sorted(selected_rows)
            if not sel or sel[-1] == len(self.files)-1: return
            for i in reversed(sel):
                if i < len(self.files)-1:
                    self.files[i], self.files[i+1] = self.files[i+1], self.files[i]
            new = {i+1 for i in sel if i < len(self.files)-1}
            selected_rows.clear(); selected_rows.update(new)
            refresh_lb(); selected_rows.update(new); _repaint()

        def add_files():
            paths = filedialog.askopenfilenames(title="Add files", parent=dlg)
            if paths:
                existing = set(self.files)
                self.files.extend(p for p in paths if p not in existing)
                refresh_lb(); self._refresh_drop()

        def remove_selected():
            sel = sorted(selected_rows, reverse=True)
            if not sel:
                messagebox.showwarning("Warning", "Select items to remove.", parent=dlg)
                return
            for i in sel: del self.files[i]
            refresh_lb(); self._refresh_drop()

        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        # Build dialog buttons via helper
        def _dlg_btn(parent, text, fg_col, cmd, side_="left", padx_=(0, 0)):
            f   = tk.Frame(parent, bg=SURFACE2, cursor="hand2")
            f.pack(side=side_, padx=padx_, pady=2)
            lbl = tk.Label(f, text=text, fg=fg_col, bg=SURFACE2,
                           font=("Consolas", 9), padx=8, pady=4, cursor="hand2")
            lbl.pack()
            def _e(_): f.config(bg=fg_col); lbl.config(bg=fg_col, fg=BG)
            def _l(_): f.config(bg=SURFACE2); lbl.config(bg=SURFACE2, fg=fg_col)
            for w in (f, lbl):
                w.bind("<Button-1>", lambda e: cmd())
                w.bind("<Enter>", _e); w.bind("<Leave>", _l)

        # Add files with icon
        add_f = tk.Frame(btn_row, bg=SURFACE2, cursor="hand2")
        add_f.pack(side="left", pady=2)
        add_ic = tk.Canvas(add_f, width=14, height=14, bg=SURFACE2,
                           highlightthickness=0, cursor="hand2")
        add_ic.pack(side="left", padx=(6, 3))
        draw_icon(add_ic, "add", NEON_GRN, SURFACE2)
        add_lbl = tk.Label(add_f, text="Add files", fg=NEON_GRN, bg=SURFACE2,
                           font=("Consolas", 9), padx=4, pady=4, cursor="hand2")
        add_lbl.pack(side="left", padx=(0, 6))
        def ae(_): add_f.config(bg=NEON_GRN); add_ic.config(bg=NEON_GRN); add_lbl.config(bg=NEON_GRN, fg=BG); draw_icon(add_ic,"add",BG,NEON_GRN)
        def al(_): add_f.config(bg=SURFACE2); add_ic.config(bg=SURFACE2); add_lbl.config(bg=SURFACE2, fg=NEON_GRN); draw_icon(add_ic,"add",NEON_GRN,SURFACE2)
        for w in (add_f, add_ic, add_lbl):
            w.bind("<Button-1>", lambda e: add_files())
            w.bind("<Enter>", ae); w.bind("<Leave>", al)

        # Remove with icon
        rem_f = tk.Frame(btn_row, bg=SURFACE2, cursor="hand2")
        rem_f.pack(side="left", padx=(8, 0), pady=2)
        rem_ic = tk.Canvas(rem_f, width=14, height=14, bg=SURFACE2,
                           highlightthickness=0, cursor="hand2")
        rem_ic.pack(side="left", padx=(6, 3))
        draw_icon(rem_ic, "remove", NEON_RED, SURFACE2)
        rem_lbl = tk.Label(rem_f, text="Remove", fg=NEON_RED, bg=SURFACE2,
                           font=("Consolas", 9), padx=4, pady=4, cursor="hand2")
        rem_lbl.pack(side="left", padx=(0, 6))
        def re_(_): rem_f.config(bg=NEON_RED); rem_ic.config(bg=NEON_RED); rem_lbl.config(bg=NEON_RED, fg=BG); draw_icon(rem_ic,"remove",BG,NEON_RED)
        def rl(_):  rem_f.config(bg=SURFACE2); rem_ic.config(bg=SURFACE2); rem_lbl.config(bg=SURFACE2, fg=NEON_RED); draw_icon(rem_ic,"remove",NEON_RED,SURFACE2)
        for w in (rem_f, rem_ic, rem_lbl):
            w.bind("<Button-1>", lambda e: remove_selected())
            w.bind("<Enter>", re_); w.bind("<Leave>", rl)

        def _arrow_btn(txt, cmd, px):
            f = tk.Frame(btn_row, bg=SURFACE2, cursor="hand2")
            f.pack(side="left", padx=px, pady=2)
            lbl_ = tk.Label(f, text=txt, fg=NEON_CYAN, bg=SURFACE2,
                            font=("Consolas", 9, "bold"), padx=8, pady=4, cursor="hand2")
            lbl_.pack()
            def _e(_): f.config(bg=NEON_CYAN); lbl_.config(bg=NEON_CYAN, fg=BG)
            def _l(_): f.config(bg=SURFACE2);  lbl_.config(bg=SURFACE2,  fg=NEON_CYAN)
            for w in (f, lbl_):
                w.bind("<Button-1>", lambda e, c=cmd: c())
                w.bind("<Enter>", _e); w.bind("<Leave>", _l)

        _arrow_btn("▲ Up",   move_up,   (8, 0))
        _arrow_btn("▼ Down", move_down, (4, 0))

        done_f = tk.Frame(btn_row, bg=NEON_BLUE, cursor="hand2")
        done_f.pack(side="right", pady=2)
        done_lbl = tk.Label(done_f, text="Done", fg=BG, bg=NEON_BLUE,
                            font=("Consolas", 9, "bold"), padx=14, pady=4, cursor="hand2")
        done_lbl.pack()
        def de(_): done_f.config(bg=NEON_CYAN); done_lbl.config(bg=NEON_CYAN)
        def dl_(_): done_f.config(bg=NEON_BLUE); done_lbl.config(bg=NEON_BLUE)
        for w in (done_f, done_lbl):
            w.bind("<Button-1>", lambda e: dlg.destroy())
            w.bind("<Enter>", de); w.bind("<Leave>", dl_)

    # ── Toast notification ────────────────────────────────────────────────────
    def _show_toast(self, msg, color=NEON_RED):
        if self._toast_job:
            self.root.after_cancel(self._toast_job)
            self._toast_job = None
        self.toast_label.config(text=msg, fg=color)
        STEPS = ["#d4738a","#b05a6e","#8c4255","#6c3040","#4e2030","#341220","#1a0810",SURFACE]
        def _fade(i=0):
            if i < len(STEPS):
                self.toast_label.config(fg=STEPS[i])
                self._toast_job = self.root.after(80, lambda: _fade(i + 1))
            else:
                self.toast_label.config(text="", fg=NEON_RED)
                self._toast_job = None
        self._toast_job = self.root.after(1000, _fade)

    # ── Numbering toggle ──────────────────────────────────────────────────────
    def toggle_number_options(self):
        st = "normal" if self.number_var.get() else "disabled"
        for w in (self.start_number, self.padding_number,
                  self.number_position, self.custom_name_entry):
            w.config(state=st)

    # ── Rename-to button state ────────────────────────────────────────────────
    def _update_renameto_btn(self):
        if self.rename_to_dir:
            short = os.path.basename(self.rename_to_dir) or self.rename_to_dir
            if len(short) > 18:
                short = short[:16] + "…"
            self.renameto_lbl.config(text=f"...\\{short}", fg=NEON_GRN, bg=SURFACE2)
            draw_icon(self.renameto_ic, "export", NEON_GRN, SURFACE2)
        else:
            self.renameto_lbl.config(text="Rename to...", fg=FG, bg=SURFACE2)
            draw_icon(self.renameto_ic, "export", NEON_PURP, SURFACE2)
        self.renameto_btn.config(bg=SURFACE2)
        self.renameto_ic.config(bg=SURFACE2)

    def pick_rename_to_dir(self):
        if self.rename_to_dir:
            self.rename_to_dir = None
            self._update_renameto_btn()
            self._show_toast("Destination cleared — renaming in-place", NEON_CYAN)
            return
        folder = filedialog.askdirectory(title="Copy renamed files to...", mustexist=True)
        if folder:
            self.rename_to_dir = folder
            self._update_renameto_btn()
            self._show_toast(f"Destination: {os.path.basename(folder) or folder}", NEON_GRN)

    def select_files(self):
        paths = filedialog.askopenfilenames(title="Select files to rename")
        if paths:
            existing = set(self.files)
            self.files.extend(p for p in paths if p not in existing)
            self._refresh_drop()

    # ── Name generation ───────────────────────────────────────────────────────
    def generate_new_name(self, filename, index):
        fp = self.files[index] if index < len(self.files) else None
        if fp and os.path.isdir(fp):
            name, ext = filename, ""
        else:
            name, ext = os.path.splitext(filename)

        sep = self.separator_var.get()

        def _int(var, default=0):
            try: return int(var.get() or default)
            except ValueError: return default

        dl = _int(self.del_left_var)
        dr = _int(self.del_right_var)
        if dl: name = name[dl:]
        if dr and name: name = name[:-dr]

        def _resolve_date(entry, is_prefix):
            fmt  = getattr(entry, "_use_mtime", None)
            text = entry.get()
            if not fmt: return text
            ts = os.path.getmtime(fp) if fp else None
            dt = datetime.datetime.fromtimestamp(ts) if ts else datetime.datetime.now()
            d_str = dt.strftime({"YYMMDD":"%y%m%d","DDMMYY":"%d%m%y","YYYYMM":"%Y%m"}.get(fmt, "%y%m%d"))
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
                num = str(_int(self.start_number, 1) + index).zfill(_int(self.padding_number, 3))
                name = f"{num}{sep}{name}" if self.number_position.get() == "Start" \
                       else f"{name}{sep}{num}"
            except ValueError:
                pass

        prefix = _resolve_date(self.prefix_entry, True)
        suffix = _resolve_date(self.suffix_entry, False)
        if prefix: prefix += sep
        if suffix: suffix  = sep + suffix

        full = f"{prefix}{name}{suffix}"
        case = self.case_var.get()
        if case == "upper": return f"{full.upper()}{ext}"
        if case == "lower": return f"{full.lower()}{ext.lower()}"
        return f"{full}{ext}"

    # ── Execute rename ────────────────────────────────────────────────────────
    def execute_rename(self):
        if not self.files:
            messagebox.showwarning("Warning", "No files/folders to rename!"); return

        for v in (self.del_left_var, self.del_right_var):
            if not v.get().strip(): v.set("0")

        dl = int(self.del_left_var.get() or 0)
        dr = int(self.del_right_var.get() or 0)
        for fp in self.files:
            base = os.path.basename(fp) if os.path.isdir(fp) \
                   else os.path.splitext(os.path.basename(fp))[0]
            if (dl + dr) > len(base):
                self._show_toast("Trim length exceeds filename"); return

        pairs = [(fp, os.path.basename(fp),
                  self.generate_new_name(os.path.basename(fp), i))
                 for i, fp in enumerate(self.files)]

        # Preview dialog
        dlg = tk.Toplevel(self.root)
        dlg.title("Preview & Confirm")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dw, dh = 580, min(80 + len(pairs) * 20 + 70, 480)
        self._center_dlg(dlg, dw, dh)

        tk.Label(dlg, text=f"● Preview — {len(pairs)} item(s) will be renamed",
                 fg=NEON_CYAN, bg=BG, font=("Consolas", 9, "bold")
                 ).pack(anchor="w", padx=12, pady=(10, 4))

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
        vsb.grid(row=0,  column=1, sticky="ns")

        for _, fn, nn in pairs:
            tree.insert("", "end", values=(fn, "→", nn),
                        tags=("changed" if fn != nn else "same",))
        tree.tag_configure("changed", foreground=NEON_GRN)
        tree.tag_configure("same",    foreground=FG_DIM)

        btn_row   = tk.Frame(dlg, bg=BG)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        confirmed = [False]

        cancel_btn = tk.Frame(btn_row, bg=SURFACE2, cursor="hand2")
        cancel_btn.pack(side="left", pady=2)
        cancel_lbl = tk.Label(cancel_btn, text="Cancel", fg=FG, bg=SURFACE2,
                              font=("Consolas", 9), padx=10, pady=4, cursor="hand2")
        cancel_lbl.pack()
        def ce(_): cancel_btn.config(bg=BORDER); cancel_lbl.config(bg=BORDER)
        def cl(_): cancel_btn.config(bg=SURFACE2); cancel_lbl.config(bg=SURFACE2)
        for w in (cancel_btn, cancel_lbl):
            w.bind("<Button-1>", lambda e: dlg.destroy())
            w.bind("<Enter>", ce); w.bind("<Leave>", cl)

        confirm_btn = tk.Frame(btn_row, bg=NEON_PURP, cursor="hand2")
        confirm_btn.pack(side="right", pady=2)
        confirm_ic  = tk.Canvas(confirm_btn, width=14, height=14, bg=NEON_PURP,
                                highlightthickness=0, cursor="hand2")
        confirm_ic.pack(side="left", padx=(8, 3))
        draw_icon(confirm_ic, "rename", BG, NEON_PURP)
        confirm_lbl = tk.Label(confirm_btn, text="Confirm Rename", fg=BG, bg=NEON_PURP,
                               font=("Consolas", 9, "bold"), padx=4, pady=4, cursor="hand2")
        confirm_lbl.pack(side="left", padx=(0, 8))
        def cfe(_):
            confirm_btn.config(bg=NEON_BLUE); confirm_ic.config(bg=NEON_BLUE)
            confirm_lbl.config(bg=NEON_BLUE); draw_icon(confirm_ic, "rename", BG, NEON_BLUE)
        def cfl(_):
            confirm_btn.config(bg=NEON_PURP); confirm_ic.config(bg=NEON_PURP)
            confirm_lbl.config(bg=NEON_PURP); draw_icon(confirm_ic, "rename", BG, NEON_PURP)
        for w in (confirm_btn, confirm_ic, confirm_lbl):
            w.bind("<Button-1>", lambda e: [confirmed.__setitem__(0, True), dlg.destroy()])
            w.bind("<Enter>", cfe); w.bind("<Leave>", cfl)

        dlg.wait_window()
        if not confirmed[0]: return

        ok = err = 0
        errors    = []
        dest_root = self.rename_to_dir
        for fp, fn, nn in pairs:
            try:
                if dest_root:
                    np_ = os.path.join(dest_root, nn)
                    if os.path.exists(np_) and os.path.normcase(fp) != os.path.normcase(np_):
                        errors.append(f"{fn} → already exists in destination"); err += 1
                    else:
                        (shutil.copytree if os.path.isdir(fp) else shutil.copy2)(fp, np_)
                        ok += 1
                else:
                    np_ = os.path.join(os.path.dirname(fp), nn)
                    if os.path.exists(np_) and os.path.normcase(fp) != os.path.normcase(np_):
                        errors.append(f"{fn} → already exists"); err += 1
                    else:
                        os.rename(fp, np_); ok += 1
            except Exception as ex:
                errors.append(f"{fn}: {ex}"); err += 1

        prefix_ = "Copied & renamed" if dest_root else "Renamed"
        msg = f"{prefix_}: {ok}  |  Failed: {err}"
        if errors: msg += "\n\n" + "\n".join(errors[:10])
        (messagebox.showwarning if err else messagebox.showinfo)("Result", msg)
        self.files = []
        self._refresh_drop()

    # ── Reset all fields ──────────────────────────────────────────────────────
    def reset_fields(self):
        self.files         = []
        self.rename_to_dir = None
        self._refresh_drop()
        self._update_renameto_btn()

        for e in (self.prefix_entry, self.suffix_entry,
                  self.find_entry,   self.replace_entry):
            e.delete(0, tk.END)

        for e in (self.prefix_entry, self.suffix_entry):
            e._use_mtime   = None
            e._date_var.set("none")
            e._date_active = False

        self.del_left_var.set("0")
        self.del_right_var.set("0")
        self.custom_name_entry.config(state="normal")
        self.custom_name_entry.delete(0, tk.END)
        self.number_var.set(False)
        self.case_var.set(""); self._prev_case = ""
        self.start_number.set("1")
        self.padding_number.set("3")
        self.number_position.set("End")
        self.separator_var.set("_")
        self.toggle_number_options()


if __name__ == "__main__":
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    root.attributes("-alpha", 0.0)
    try:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        root.iconbitmap(os.path.join(base, "app.ico"))
    except Exception:
        pass
    BatchRenameApp(root)
    root.mainloop()
