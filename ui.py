import curses
import os


logo = """
 _ __ ___  ___| |_ __ _ _   _ _ __ __ _| |_ ___ _   _ _ __
| '__/ _ \/ __| __/ _` | | | | '__/ _` | __/ _ \ | | | '__|
| | |  __/\__ \ || (_| | |_| | | | (_| | ||  __/ |_| | |
|_|  \___||___/\__\__,_|\__,_|_|  \__,_|\__\___|\__,_|_|
"""

def render_home(stdscr, search_text=None):
    stdscr.clear()
    stdscr.addstr(logo)
    y, x = stdscr.getmaxyx()
    search_box_y = int(y*0.9)
    search_box_x = 5
    main_box = curses.newwin(int(y*0.6), x-10, int(y*0.2), 5)
    main_box.box()
    search_box = curses.newwin(int(y*0.1), x-10, search_box_y, search_box_x)
    search_box.box()
    stdscr.refresh()
    main_box.refresh()
    search_box.refresh()
    search_text = "" if search_text is None else search_text
    print_keyword_string(stdscr, search_box_y, search_box_x, "Search: " + search_text)

def print_keyword_string(stdscr, y, x, string):
    stdscr.addch(y + 1, x + 1, string[0], curses.color_pair(1) + curses.A_UNDERLINE)
    stdscr.addstr(y + 1, x + 2, string[1:])


def get_user_input(stdscr, y, x, chars=None):
    chars = "" if chars is None else chars
    orig_x = x if chars == "" else x - len(chars)
    curses.curs_set(1)
    while True:
        char = stdscr.get_wch()
        chars += char if isinstance(char, str) else chr(char)
        code = ord(char) if isinstance(char, str) else char
        if len(chars) > 0:
            if chars[-1] == "\n":
                curses.curs_set(0)
                return chars[:-1], True
            # backspace
            elif code == 263:
                chars = chars[:-2]
                x = max(orig_x, x - 1)
                stdscr.addstr(y, x, " ")
                stdscr.addstr(y, x, "")
            # escape
            elif code == 27:
                curses.curs_set(0)
                chars = chars[:-1]
                render_home(stdscr, search_text=chars)
                return chars, False
            elif chars != "":
                stdscr.addstr(y, x, chars[-1])
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
    # TODO For inserting text it should just set a flag
    # insert mode. get_user_input should collect just the
    # 1 char and update a var with user input
    # user input can be cleaned on enter and stored on esc
    user_input = ""
    while (c := stdscr.getch()) != 27:
        render_home(stdscr, search_text=user_input)
        if c == ord('s') or c == ord('S'):
            y, x = stdscr.getyx()
            stdscr.move(y, x)
            user_input, finished = get_user_input(stdscr, y, x, chars=user_input)
            if finished:
                # process
                user_input = ""
                render_home(stdscr, search_text=user_input)


if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
