import sys
from gui import DYDApp

def main():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dyd.desktop.assistant")
    print("=" * 50)
    print("      DYD // AI DESKTOP ASSISTANT ONLINE       ")
    print("=" * 50)
    app = DYDApp()
    app.mainloop()

if __name__ == "__main__":
    main()
