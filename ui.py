import curses
import os


logo = """
 _ __ ___  ___| |_ __ _ _   _ _ __ __ _| |_ ___ _   _ _ __
| '__/ _ \/ __| __/ _` | | | | '__/ _` | __/ _ \ | | | '__|
| | |  __/\__ \ || (_| | |_| | | | (_| | ||  __/ |_| | |
|_|  \___||___/\__\__,_|\__,_|_|  \__,_|\__\___|\__,_|_|
"""

# TODO rerender only on change?
# TODO handle resizing search_input
def render_home(stdscr, search_text=None):
    stdscr.clear()
    stdscr.addstr(logo)
    y, x = stdscr.getmaxyx()
    nav_bar_y = int(y*0.2)
    nav_bar_x = 5
    search_box_y = int(y*0.9)
    search_box_x = 5
    main_box_y = int(y*0.3)
    main_box_x = 5
    main_box_max_x = x-10
    nav_bar = curses.newwin(3, x-10, nav_bar_y, nav_bar_x)
    nav_bar.box()
    main_box = curses.newwin(int(y*0.6), main_box_max_x, main_box_y, main_box_x)
    main_box.box()
    search_box = curses.newwin(3, x-10, search_box_y, search_box_x)
    search_box.box()
    stdscr.refresh()
    nav_bar.refresh()
    main_box.refresh()
    search_box.refresh()
    search_text = "" if search_text is None else search_text
    _, max_x = main_box.getmaxyx()
    print_help_string(stdscr, main_box_y, main_box_x,
                      main_box_max_x - main_box_x)
    print_keyword_string(stdscr, search_box_y, search_box_x, "Search: " +
                         search_text)

def print_help_string(stdscr, y, x, max_x):
    help_text = """Welcome to restaurateur TUI!
    This interface is controlled via keyboard shortcuts. To access specific
    elements you can use the key that is in yellow and underlined, eg: to enter
    the search box press 'S' or 's'. To leave any window/mode press escape.
    If you need help with any of the commands press '?'"""
    max_len = max_x - 2
    x += 2
    count = x
    orig_x = x
    y += 1
    for word in help_text.split():
        word += " "
        count += len(word)
        if count + orig_x >= max_len:
            y += 1
            x = orig_x
            count = x
        for char in word:
            stdscr.addch(y, x, char)
            x += 1

def print_keyword_string(stdscr, y, x, string):
    stdscr.addch(y + 1, x + 1, string[0], curses.color_pair(1) +
                 curses.A_UNDERLINE)
    stdscr.addstr(y + 1, x + 2, string[1:])

def get_user_input(stdscr, y, x, chars=None):
    chars = "" if chars is None else chars
    orig_x = x if chars == "" else x - len(chars)
    curses.curs_set(1)
    while True:
        char = stdscr.get_wch()
        _, max_x = stdscr.getmaxyx()
        max_x -= orig_x
        chars += char if isinstance(char, str) else chr(char)
        code = ord(char) if isinstance(char, str) else char
        # chars += str(code)
        # x += len(str(code))
        # scroll search bar when char limit reached?
        if len(chars) > 0:
            # backspace
            if code == 263 or code == 127 or code == 8:
                chars = chars[:-2]
                x = max(orig_x, x - 1)
                stdscr.addstr(y, x, " ")
                stdscr.addstr(y, x, "")
            elif code == 27:
                curses.curs_set(0)
                chars = chars[:-1]
                render_home(stdscr, search_text=chars)
                return chars, False
            elif x > max_x:
                diff = max_x - x - 1
                x = max_x
                chars = chars[:diff]
            elif x == max_x:
                chars = chars[:-1]
            elif chars[-1] == "\n":
                curses.curs_set(0)
                return chars[:-1], True
            # escape
            elif code == 410: # resize char
                chars = chars[:-1]
            elif isinstance(char, str):
                stdscr.addstr(y, x, char)
                x += 1
        render_home(stdscr, search_text=chars)
    return chars, False

def main(stdscr):
    stdscr.clear()
    curses.curs_set(0) # Turn off cursor blinking
    curses.start_color()
    curses.use_default_colors();
    curses.init_pair(1, curses.COLOR_YELLOW, -1)
    render_home(stdscr)
    user_input = ""
    while (c := stdscr.getch()) != 27:
        render_home(stdscr, search_text=user_input)
        if c == ord('s') or c == ord('S'):
            y, x = stdscr.getyx()
            stdscr.move(y, x)
            user_input, finished = get_user_input(stdscr, y, x, chars=user_input)
            if finished:
                # process input
                user_input = ""
                render_home(stdscr, search_text=user_input)


if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
