from tui import main_loop
import curses
import os


# TODO: adjust data from JSON to be more relevant
# TODO: Handle truncating of text in menus or r for reload
# TODO: add some vim key bindings
if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main_loop)
