import curses
import os
import requests
import json

logo_big = """
                 _                        _
   _ __ ___  ___| |_ __ _ _   _ _ __ __ _| |_ ___ _   _ _ __
  | '__/ _ \/ __| __/ _` | | | | '__/ _` | __/ _ \ | | | '__|
  | | |  __/\__ \ || (_| | |_| | | | (_| | ||  __/ |_| | |
  |_|  \___||___/\__\__,_|\__,_|_|  \__,_|\__\___|\__,_|_|
"""[1:]

logo_small = """
  ┬─┐┌─┐┌─┐┌┬┐┌─┐┬ ┬┬─┐┌─┐┌┬┐┌─┐┬ ┬┬─┐
  ├┬┘├┤ └─┐ │ ├─┤│ │├┬┘├─┤ │ ├┤ │ │├┬┘
  ┴└─└─┘└─┘ ┴ ┴ ┴└─┘┴└─┴ ┴ ┴ └─┘└─┘┴└─
"""[1:]

class TerminalTooSmall(Exception):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.message = f"Terminal too small! (x: {self.x}, y: {self.y})"
        super().__init__(self.message)


# TODO rerender only on change?
# TODO handle resizing search_input
def render_home(stdscr, search_text=None):
    stdscr.clear()
    y, x = stdscr.getmaxyx()
    if y < 21 or x < 57:
        raise TerminalTooSmall(x, y)
    elif y > 30 and x > 60:
        stdscr.addstr(logo_big)
    else:
        stdscr.addstr(1, 0, logo_small)
    nav_bar_y = int(y*0.25)
    nav_bar_x = 5
    search_box_y = int(y*0.9)
    search_box_x = 5
    main_box_y = int(y*0.4)
    main_box_x = 5
    main_box_max_x = x-10
    nav_bar_max_x = x-10
    nav_bar = curses.newwin(3, nav_bar_max_x, nav_bar_y, nav_bar_x)
    nav_bar.box()
    main_box = curses.newwin(int(y*0.5), main_box_max_x, main_box_y, main_box_x)
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
    print_nav_bar_items(stdscr, nav_bar_y, nav_bar_x, nav_bar_max_x)
    print_keyword_string(stdscr, search_box_y, search_box_x, "Search: " +
                         search_text)

def print_nav_bar_items(stdscr, y, x, max_x):
    max_len = max_x
    x += 3
    space = max_len - x
    pc_text = "Prague College"
    cuisines_text = "Filters"
    login_text = "Login"
    sign_in_text = "Sign up"
    text_list = [pc_text, cuisines_text, login_text, sign_in_text]
    total_len = sum(map(len, text_list))
    space_total = space - total_len
    gap = space_total // (len(text_list) - 1)
    for text in text_list:
        print_keyword_string(stdscr, y, x, text)
        x += len(text) + gap

def render_menu(stdscr):
    r = requests.get("http://localhost:8080/prague-college/restaurants")
    data = json.loads(r.text)
    stdscr.clear()
    y, x = stdscr.getyx()
    if data["Status"] == 200:
        dat = data["Data"]
        orig_y = y + 1
    else:
        stdscr.addstr(y + 1, x, "Couldn't fetch restaurants")
        return
    number_of_restaurants = len(dat)
    user_y = orig_y
    display_restaurants(stdscr, dat, orig_y, x, user_y)
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        max_y, max_x = stdscr.getmaxyx()
        max_y = number_of_restaurants - orig_y + 1
        if c in (ord('j'), ord('J')):
            if user_y < max_y:
                user_y += 1
        elif c in (ord('k'), ord('K')):
            if user_y > orig_y:
                user_y -= 1
        elif c == 10:
            display_restaurant_info(stdscr, dat[user_y - orig_y])
        display_restaurants(stdscr, dat, orig_y, x, user_y)

def display_restaurant_info(stdscr, restaurant):
    stdscr.clear()
    y, x = stdscr.getyx()
    main_box = curses.newwin(y, x)
    main_box.box()
    stdscr.refresh()
    main_box.refresh()
    x += 1
    for key, value in restaurant.items():
        y += 1
        if value is None or key == 'Images':
            y -= 1
            pass
        elif key == 'OpeningHours':
            y += 1
            stdscr.addstr(y, x, "**Opening hours**")
            y += 1
            for k, v in value.items():
                orig_x = x
                stdscr.addstr(y, x, k + ":")
                x += len(k) + 2
                stdscr.addstr(y, x, v)
                x = orig_x
                y += 1
        else:
            orig_x = x
            stdscr.addstr(y, x, key + ":")
            x += len(key) + 2
            stdscr.addstr(y, x, str(value))
            x = orig_x
    stdscr.getch()


def display_restaurants(stdscr, restaurants, y, x, user_y):
    stdscr.clear()
    win_y, win_x = stdscr.getyx()
    main_box = curses.newwin(win_y, win_x)
    main_box.box()
    stdscr.refresh()
    main_box.refresh()
    x += 1
    for restaurant in restaurants:
        if y == user_y:
            stdscr.addstr(y, x, restaurant["Name"], curses.A_STANDOUT)
        else:
            stdscr.addstr(y, x, restaurant["Name"])
        y += 1
    stdscr.refresh()

def print_help_string(stdscr, y, x, max_x):
    help_text = """Welcome to restaurateur TUI!
    This interface is controlled via keyboard shortcuts. To access specific
    elements you can use the key that is highlighted in yellow and underlined,
    eg: to enter the search box press 'S' or 's'. To leave any window/mode press escape.
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

def render_help_menu(stdscr):
    stdscr.clear()
    help_box = curses.newwin(0, 0)
    help_box.box()
    stdscr.refresh()
    help_box.refresh()
    stdscr.addstr(1, 1, "Esc : Exits current mode/window")
    stdscr.addstr(2, 1, "S, s: Enter search input box")
    stdscr.addstr(3, 1, "P, p: Displays restaurants around Prague college")
    stdscr.addstr(4, 1, "L, l: Displays log in page")
    stdscr.addstr(5, 1, "S, S: Displays sign up page")
    stdscr.addstr(6, 1, "F, f: Displays filter page menu to search based on filters")

def print_help_menu(stdscr):
    render_help_menu(stdscr)
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        render_help_menu(stdscr)


def main(stdscr):
    stdscr.clear()
    curses.curs_set(0) # Turn off cursor blinking
    curses.start_color()
    curses.use_default_colors();
    curses.init_pair(1, curses.COLOR_YELLOW, -1)
    render_home(stdscr)
    user_input = ""
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        if c in (ord('s'), ord('S')):
            y, x = stdscr.getyx()
            stdscr.move(y, x)
            user_input, finished = get_user_input(stdscr, y, x, chars=user_input)
            if finished:
                # process input
                user_input = ""
                render_home(stdscr, search_text=user_input)
        elif c == ord('?'):
            print_help_menu(stdscr)
            render_home(stdscr, search_text=user_input)
        elif c in (ord('p'), ord('P')):
            render_menu(stdscr)
        render_home(stdscr, search_text=user_input)


if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
