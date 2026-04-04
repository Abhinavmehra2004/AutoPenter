import sys
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QFrame, QGraphicsDropShadowEffect, QSizePolicy, QProgressBar,
    QScrollArea, QStackedWidget
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, Qt, QPropertyAnimation, QEasingCurve,
    QTimer, QRect, QSize, QPoint
)
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient,
    QFont, QFontDatabase, QPalette, QTextCursor, QIcon, QPixmap,
    QConicalGradient, QRadialGradient
)

# ─────────────────────────────────────────────
#  THEME / TOKENS
# ─────────────────────────────────────────────
BG_DEEP    = "#050A0F"
BG_PANEL   = "#0B1520"
BG_CARD    = "#0F1E2E"
ACCENT     = "#00D4FF"
ACCENT2    = "#FF3C6E"
SUCCESS    = "#00FFB2"
WARNING    = "#FFB800"
TEXT_PRI   = "#E8F4FD"
TEXT_SEC   = "#5A8CA8"
TEXT_DIM   = "#2A4A5E"
BORDER     = "#1A3A4F"
BORDER_LIT = "#00D4FF"

FONT_MONO  = "Courier New"
FONT_UI    = "Segoe UI"


# ─────────────────────────────────────────────
#  ANIMATED SCAN LINE WIDGET
# ─────────────────────────────────────────────
class ScanlineWidget(QWidget):
    """Draws animated horizontal scanlines over its parent for atmosphere."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._offset = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def _tick(self):
        self._offset = (self._offset + 1) % 6
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(0, 212, 255, 8))
        pen.setWidth(1)
        p.setPen(pen)
        y = self._offset
        while y < self.height():
            p.drawLine(0, y, self.width(), y)
            y += 6
        p.end()


# ─────────────────────────────────────────────
#  ANIMATED SPINNER
# ─────────────────────────────────────────────
class SpinnerWidget(QWidget):
    def __init__(self, parent=None, size=36):
        super().__init__(parent)
        self._sz = size
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._active = False

    def start(self):
        self._active = True
        self._timer.start(16)
        self.show()

    def stop(self):
        self._active = False
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, e):
        if not self._active:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self._sz / 2, self._sz / 2)

        # Outer ring (dim)
        pen = QPen(QColor(BORDER), 3)
        p.setPen(pen)
        p.drawEllipse(-self._sz // 2 + 4, -self._sz // 2 + 4,
                      self._sz - 8, self._sz - 8)

        # Arc sweep
        grad = QConicalGradient(0, 0, -self._angle)
        grad.setColorAt(0,   QColor(ACCENT))
        grad.setColorAt(0.5, QColor(ACCENT2))
        grad.setColorAt(1,   QColor(ACCENT))
        pen2 = QPen(QBrush(grad), 3)
        pen2.setCapStyle(Qt.RoundCap)
        p.setPen(pen2)
        r = self._sz // 2 - 4
        p.drawArc(-r, -r, r * 2, r * 2,
                  -self._angle * 16, -270 * 16)
        p.end()


# ─────────────────────────────────────────────
#  PHASE BADGE
# ─────────────────────────────────────────────
class PhaseBadge(QLabel):
    COLORS = {
        "idle":    (TEXT_DIM,  BG_CARD),
        "active":  (ACCENT,    "#0A2030"),
        "done":    (SUCCESS,   "#0A2520"),
        "error":   (ACCENT2,   "#2A0A10"),
    }

    def __init__(self, number, title, parent=None):
        super().__init__(parent)
        self._number = number
        self._title  = title
        self._state  = "idle"
        self._update_style()
        self.setFixedHeight(38)

    def set_state(self, state: str):
        self._state = state
        self._update_style()

    def _update_style(self):
        fg, bg = self.COLORS.get(self._state, (TEXT_DIM, BG_CARD))
        icon = {"idle": "○", "active": "◉", "done": "✓", "error": "✕"}.get(self._state, "○")
        self.setText(f"  {icon}  PHASE {self._number}  ·  {self._title}  ")
        self.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background: {bg};
                border: 1px solid {fg if self._state != 'idle' else BORDER};
                border-radius: 4px;
                font-family: '{FONT_MONO}';
                font-size: 11px;
                font-weight: bold;
                padding: 2px 6px;
                letter-spacing: 1px;
            }}
        """)


# ─────────────────────────────────────────────
#  GLOW BUTTON
# ─────────────────────────────────────────────
class GlowButton(QPushButton):
    def __init__(self, text, color=ACCENT, parent=None):
        super().__init__(text, parent)
        self._color = QColor(color)
        self._base_color = color
        self._setup()

    def _setup(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(self._color)
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        self._apply_style(False)
        self.setCursor(Qt.PointingHandCursor)

    def _apply_style(self, hovered):
        alpha = "CC" if hovered else "88"
        bg    = f"{self._base_color}{alpha}"
        self.setStyleSheet(f"""
            QPushButton {{
                color: {BG_DEEP};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self._base_color}, stop:1 {ACCENT2});
                border: none;
                border-radius: 6px;
                font-family: '{FONT_MONO}';
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 12px 28px;
                text-transform: uppercase;
            }}
            QPushButton:disabled {{
                background: {BG_CARD};
                color: {TEXT_DIM};
                border: 1px solid {BORDER};
            }}
            QPushButton:pressed {{
                padding: 13px 26px 11px 30px;
            }}
        """)

    def enterEvent(self, e):
        self._apply_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply_style(False)
        super().leaveEvent(e)


# ─────────────────────────────────────────────
#  GHOST BUTTON (secondary)
# ─────────────────────────────────────────────
class GhostButton(QPushButton):
    def __init__(self, text, color=ACCENT, parent=None):
        super().__init__(text, parent)
        self._color = color
        self._apply_style(False)
        self.setCursor(Qt.PointingHandCursor)

    def _apply_style(self, hovered):
        bg = f"{self._color}18" if hovered else "transparent"
        self.setStyleSheet(f"""
            QPushButton {{
                color: {self._color};
                background: {bg};
                border: 1px solid {self._color};
                border-radius: 6px;
                font-family: '{FONT_MONO}';
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 10px 22px;
            }}
            QPushButton:disabled {{
                color: {TEXT_DIM};
                border-color: {BORDER};
            }}
        """)

    def enterEvent(self, e):
        self._apply_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply_style(False)
        super().leaveEvent(e)


# ─────────────────────────────────────────────
#  WORKER THREAD  (unchanged logic)
# ─────────────────────────────────────────────
class PentestWorker(QThread):
    update_signal  = pyqtSignal(str)
    phase_signal   = pyqtSignal(int, str)   # phase_number, state
    finished_signal = pyqtSignal(str)

    def __init__(self, target_url):
        super().__init__()
        self.target_url = target_url

    def log(self, text):
        self.update_signal.emit(text + "\n")

    def run(self):
        try:
            from recon        import run_recon
            from orchestrator import run_agentic_pipeline
            from exploitation import run_exploit
            from ai_engine    import ai_chain_vulnerabilities
            from reporting    import generate_security_report
        except ImportError as err:
            self.log(f"[!] Import error: {err}")
            self.finished_signal.emit("")
            return

        self.log(f"[*] Initialising AI Agentic Engine → {self.target_url}")

        self.phase_signal.emit(1, "active")
        self.log("[+] PHASE 1 · Zero-API Reconnaissance …")
        recon_data = run_recon(self.target_url)
        self.log(f"    IP Resolved: {recon_data.get('IP_Resolution', {}).get('ip')}")
        self.phase_signal.emit(1, "done")

        self.phase_signal.emit(2, "active")
        self.log("\n[+] PHASE 2 · Gemini AI Orchestrator + Fuzzing …")
        vuln_data = run_agentic_pipeline(self.target_url, recon_data, self.log)
        self.log(f"    {len(vuln_data.get('AI_Fuzzer', []))} dynamic vulnerabilities found.")
        self.phase_signal.emit(2, "done")

        self.phase_signal.emit(3, "active")
        self.log("\n[+] PHASE 3 · AI Vulnerability Chaining …")
        ai_chained_report = ai_chain_vulnerabilities(vuln_data)
        self.log("    Exploit chaining logic mapped.")
        self.phase_signal.emit(3, "done")

        self.phase_signal.emit(4, "active")
        self.log("\n[+] PHASE 4 · Metasploit RPC Exploitation …")
        exploit_data = run_exploit(self.target_url, recon_data, vuln_data)
        self.log(f"    Status: {exploit_data.get('message', 'Completed')}")
        self.phase_signal.emit(4, "done")

        self.phase_signal.emit(5, "active")
        self.log("\n[+] PHASE 5 · Compiling DevSecOps PDF Report …")
        report_path = generate_security_report(
            self.target_url, recon_data, vuln_data, exploit_data, ai_chained_report
        )

        if report_path:
            self.log(f"\n✅  Report saved → {report_path}")
            self.phase_signal.emit(5, "done")
            self.finished_signal.emit(report_path)
        else:
            self.log("\n❌  Failed to generate report.")
            self.phase_signal.emit(5, "error")
            self.finished_signal.emit("")


# ─────────────────────────────────────────────
#  HEADER WIDGET
# ─────────────────────────────────────────────
class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self._setup()

    def _setup(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)

        # Logo block
        logo_block = QVBoxLayout()
        logo_block.setSpacing(2)

        brand = QLabel("AUTOPENT")
        brand.setStyleSheet(f"""
            color: {ACCENT};
            font-family: '{FONT_MONO}';
            font-size: 22px;
            font-weight: 900;
            letter-spacing: 6px;
        """)

        tagline = QLabel("AI · AGENTIC · PENTEST FRAMEWORK")
        tagline.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-family: '{FONT_MONO}';
            font-size: 9px;
            letter-spacing: 4px;
        """)

        logo_block.addWidget(brand)
        logo_block.addWidget(tagline)
        lay.addLayout(logo_block)
        lay.addStretch()

        # Status pill
        self._status_pill = QLabel("● IDLE")
        self._status_pill.setStyleSheet(f"""
            color: {TEXT_DIM};
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
            font-family: '{FONT_MONO}';
            font-size: 11px;
            padding: 4px 14px;
        """)
        lay.addWidget(self._status_pill)

    def set_status(self, text, color=TEXT_DIM):
        self._status_pill.setText(text)
        self._status_pill.setStyleSheet(f"""
            color: {color};
            background: {color}18;
            border: 1px solid {color};
            border-radius: 12px;
            font-family: '{FONT_MONO}';
            font-size: 11px;
            padding: 4px 14px;
        """)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Bottom border line
        pen = QPen(QColor(BORDER_LIT), 1)
        p.setPen(pen)
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

        # Accent glow under the line
        grad = QLinearGradient(0, self.height(), self.width(), self.height())
        grad.setColorAt(0,   QColor(0, 212, 255, 0))
        grad.setColorAt(0.5, QColor(0, 212, 255, 60))
        grad.setColorAt(1,   QColor(0, 212, 255, 0))
        pen2 = QPen(QBrush(grad), 4)
        p.setPen(pen2)
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


# ─────────────────────────────────────────────
#  MAIN GUI
# ─────────────────────────────────────────────
class AutoPentGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.report_path = None
        self._phases: list[PhaseBadge] = []
        self._setup_window()
        self._build_ui()
        self._apply_global_stylesheet()

    # ── Window chrome ──────────────────────────
    def _setup_window(self):
        self.setWindowTitle("AutoPent · AI Agentic Pentesting Framework")
        self.setMinimumSize(960, 680)
        self.resize(1120, 740)
        self.setWindowFlags(Qt.Window)

    # ── Global QSS ────────────────────────────
    def _apply_global_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {BG_DEEP};
                color: {TEXT_PRI};
                font-family: '{FONT_UI}';
            }}
            QScrollBar:vertical {{
                background: {BG_PANEL};
                width: 6px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER_LIT};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QToolTip {{
                background: {BG_CARD};
                color: {TEXT_PRI};
                border: 1px solid {BORDER_LIT};
                font-family: '{FONT_MONO}';
                font-size: 11px;
                padding: 4px 8px;
            }}
        """)

    # ── Build UI ──────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self._header = HeaderWidget(self)
        root.addWidget(self._header)

        # Body
        body = QHBoxLayout()
        body.setContentsMargins(20, 20, 20, 20)
        body.setSpacing(16)
        root.addLayout(body)

        body.addWidget(self._build_left_panel(), stretch=1)
        body.addWidget(self._build_right_panel(), stretch=2)

        # Scanline overlay (cosmetic)
        self._scanlines = ScanlineWidget(self)
        self._scanlines.setAttribute(Qt.WA_TransparentForMouseEvents)

    def resizeEvent(self, e):
        if hasattr(self, '_scanlines'):
            self._scanlines.setGeometry(self.rect())
        super().resizeEvent(e)

    # ── Left Panel ────────────────────────────
    def _build_left_panel(self):
        panel = QFrame()
        panel.setObjectName("leftPanel")
        panel.setStyleSheet(f"""
            QFrame#leftPanel {{
                background: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        panel.setFixedWidth(300)

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # ─ Target section ─
        sec_label = QLabel("TARGET")
        sec_label.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-family: '{FONT_MONO}';
            font-size: 10px;
            letter-spacing: 3px;
        """)
        lay.addWidget(sec_label)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("http://target-app:5000")
        self._url_input.setMinimumHeight(42)
        self._url_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_CARD};
                color: {ACCENT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-family: '{FONT_MONO}';
                font-size: 13px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
                background: #0D2030;
            }}
        """)
        lay.addWidget(self._url_input)

        # ─ Divider ─
        lay.addWidget(self._divider())

        # ─ Phase tracker ─
        phase_lbl = QLabel("PIPELINE PHASES")
        phase_lbl.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-family: '{FONT_MONO}';
            font-size: 10px;
            letter-spacing: 3px;
        """)
        lay.addWidget(phase_lbl)

        phases_info = [
            (1, "RECON"),
            (2, "FUZZING"),
            (3, "CHAINING"),
            (4, "EXPLOIT"),
            (5, "REPORT"),
        ]
        self._phases = []
        for num, title in phases_info:
            badge = PhaseBadge(num, title)
            lay.addWidget(badge)
            self._phases.append(badge)

        # ─ Divider ─
        lay.addWidget(self._divider())
        lay.addStretch()

        # ─ Spinner + Deploy button ─
        btn_row = QHBoxLayout()
        self._spinner = SpinnerWidget(size=32)
        self._spinner.hide()
        btn_row.addWidget(self._spinner)
        btn_row.addSpacing(6)

        self._deploy_btn = GlowButton("▶️  DEPLOY AGENT", color=ACCENT)
        self._deploy_btn.clicked.connect(self._on_deploy)
        btn_row.addWidget(self._deploy_btn, stretch=1)
        lay.addLayout(btn_row)

        # ─ Download button ─
        self._download_btn = GhostButton("⬇  EXPORT REPORT", color=SUCCESS)
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._on_download)
        lay.addWidget(self._download_btn)

        # ─ Clear button ─
        self._clear_btn = GhostButton("✕  CLEAR CONSOLE", color=TEXT_SEC)
        self._clear_btn.clicked.connect(lambda: self._console.clear())
        lay.addWidget(self._clear_btn)

        return panel

    # ── Right Panel ───────────────────────────
    def _build_right_panel(self):
        panel = QFrame()
        panel.setObjectName("rightPanel")
        panel.setStyleSheet(f"""
            QFrame#rightPanel {{
                background: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Console header bar
        bar = QWidget()
        bar.setFixedHeight(40)
        bar.setStyleSheet(f"""
            background: {BG_CARD};
            border-bottom: 1px solid {BORDER};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(16, 0, 16, 0)

        dots = QHBoxLayout()
        dots.setSpacing(6)
        for col in [ACCENT2, WARNING, SUCCESS]:
            d = QLabel("●")
            d.setStyleSheet(f"color: {col}; font-size: 10px;")
            dots.addWidget(d)
        bar_lay.addLayout(dots)
        bar_lay.addSpacing(10)

        console_label = QLabel("LIVE CONSOLE OUTPUT")
        console_label.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-family: '{FONT_MONO}';
            font-size: 10px;
            letter-spacing: 3px;
        """)
        bar_lay.addWidget(console_label)
        bar_lay.addStretch()

        # Line counter
        self._line_count_lbl = QLabel("0 lines")
        self._line_count_lbl.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-family: '{FONT_MONO}';
            font-size: 10px;
        """)
        bar_lay.addWidget(self._line_count_lbl)

        lay.addWidget(bar)

        # Console text area
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_DEEP};
                color: #B0E8D0;
                font-family: '{FONT_MONO}';
                font-size: 12px;
                border: none;
                padding: 16px;
                line-height: 1.6;
                selection-background-color: {ACCENT}44;
            }}
        """)
        lay.addWidget(self._console)

        # Bottom progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)       # indeterminate
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: {BG_CARD};
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:1 {ACCENT2});
                border-radius: 2px;
            }}
        """)
        self._progress.hide()
        lay.addWidget(self._progress)

        return panel

    # ── Helpers ───────────────────────────────
    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {BORDER}; margin: 2px 0;")
        return line

    def _reset_phases(self):
        for b in self._phases:
            b.set_state("idle")

    # ── Slots ─────────────────────────────────
    def _on_deploy(self):
        url = self._url_input.text().strip()
        if not url:
            self._append("[!] Please enter a target URL.", color=WARNING)
            return

        self._reset_phases()
        self._console.clear()
        self._deploy_btn.setEnabled(False)
        self._download_btn.setEnabled(False)
        self._spinner.start()
        self._progress.show()
        self._header.set_status("● SCANNING", ACCENT2)

        self._worker = PentestWorker(url)
        self._worker.update_signal.connect(self._append)
        self._worker.phase_signal.connect(self._on_phase_update)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    def _append(self, text, color=None):
        # Color-code lines by prefix
        if color:
            hex_col = color
        elif text.startswith("✅") or "SUCCESS" in text:
            hex_col = SUCCESS
        elif text.startswith("❌") or "Error" in text or "Failed" in text:
            hex_col = ACCENT2
        elif text.startswith("[+]"):
            hex_col = ACCENT
        elif text.startswith("[*]"):
            hex_col = WARNING
        elif text.startswith("[!]"):
            hex_col = ACCENT2
        else:
            hex_col = "#B0E8D0"

        cursor = self._console.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._console.setTextCursor(cursor)

        fmt = self._console.currentCharFormat()
        fmt.setForeground(QColor(hex_col))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)

        sb = self._console.verticalScrollBar()
        sb.setValue(sb.maximum())

        # Update line count
        lines = self._console.toPlainText().count('\n')
        self._line_count_lbl.setText(f"{lines} lines")

    def _on_phase_update(self, phase_num, state):
        idx = phase_num - 1
        if 0 <= idx < len(self._phases):
            self._phases[idx].set_state(state)

    def _on_finished(self, report_path):
        self._deploy_btn.setEnabled(True)
        self._spinner.stop()
        self._progress.hide()

        if report_path:
            self.report_path = report_path
            self._download_btn.setEnabled(True)
            self._header.set_status("● COMPLETE", SUCCESS)
        else:
            self._header.set_status("● FAILED", ACCENT2)

    def _on_download(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report", "security_report.pdf", "PDF Files (*.pdf)"
        )
        if save_path and self.report_path:
            try:
                shutil.copy(self.report_path, save_path)
                self._append(f"\n📁 Exported → {save_path}\n", color=SUCCESS)
            except Exception as ex:
                self._append(f"\n❌ Export failed: {ex}\n", color=ACCENT2)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark fusion palette base
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(BG_DEEP))
    pal.setColor(QPalette.WindowText,      QColor(TEXT_PRI))
    pal.setColor(QPalette.Base,            QColor(BG_PANEL))
    pal.setColor(QPalette.AlternateBase,   QColor(BG_CARD))
    pal.setColor(QPalette.ToolTipBase,     QColor(BG_CARD))
    pal.setColor(QPalette.ToolTipText,     QColor(TEXT_PRI))
    pal.setColor(QPalette.Text,            QColor(TEXT_PRI))
    pal.setColor(QPalette.Button,          QColor(BG_CARD))
    pal.setColor(QPalette.ButtonText,      QColor(TEXT_PRI))
    pal.setColor(QPalette.BrightText,      QColor(ACCENT))
    pal.setColor(QPalette.Link,            QColor(ACCENT))
    pal.setColor(QPalette.Highlight,       QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor(BG_DEEP))
    app.setPalette(pal)

    win = AutoPentGUI()
    win.show()
    sys.exit(app.exec_())
