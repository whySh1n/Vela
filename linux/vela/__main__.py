import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from desk import main as desk_main
from tui import main as tui_main


def main():
    if "--desk" in sys.argv[1:]:
        desk_main()
    else:
        tui_main()


if __name__ == "__main__":
    main()
