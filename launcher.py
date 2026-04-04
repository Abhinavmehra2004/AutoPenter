import sys
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from backend import app

def run_backend():
    # Start the Flask backend on port 5000
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

class AutoPentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AutoPent · AI Agentic Pentest Framework')
        self.resize(1280, 800)
        
        # Create the web view and point it to the Vite dev server
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://localhost:8080"))
        
        self.setCentralWidget(self.browser)

if __name__ == '__main__':
    # 1. Start backend thread
    print("[*] Starting Backend API...")
    t = threading.Thread(target=run_backend, daemon=True)
    t.start()

    # 2. Start PyQt5 GUI
    print("[*] Launching AutoPent Desktop UI (PyQt5)...")
    qt_app = QApplication(sys.argv)
    
    # Optional: Set a dark theme/style if desired
    qt_app.setStyle("Fusion")
    
    window = AutoPentWindow()
    window.show()
    
    sys.exit(qt_app.exec_())
