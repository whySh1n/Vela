import os
import sys

VERSION = "0.1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def main():
    args = sys.argv[1:]
    if "--version" in args or "-V" in args:
        print(f"vela {VERSION}")
        return 0
    if "--term" in args or "-t" in args:
        from tui import main as tui_main

        tui_main()
        return 0
    from gui import main as gui_main

    return gui_main()


if __name__ == "__main__":
    sys.exit(main() or 0)
