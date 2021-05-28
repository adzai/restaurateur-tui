from tui import main_loop
import curses
import os


if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main_loop)
