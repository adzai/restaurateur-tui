import argparse
import curses
import json
import os
import re
import requests
import sys

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

parser = argparse.ArgumentParser(
    description='Restaurateur TUI')
parser.add_argument('--host', help="Provide restaurateur API host URL")
args = parser.parse_args()


BASE_URL = args.host if args.host else "https://api.restaurateur.tech"


and_params = ["Vegetarian", "Vegan", "Gluten free", "Takeaway", "Has menu"]
price_param = ["0-300", "300-600", "600-"]
cuisines_param = ["Czech", "International", "Italian", "English", "American", "Asian", "Indian", "Japanese", "Vietnamese",
                  "Spanish", "Mediterranean", "French", "Thai", "Balkan", "Brazil", "Russian", "Chinese", "Greek", "Arabic", "Korean"]


# TODO: add some vim key bindings

class User:
    def __init__(self):
        self.current_path = ""
        self.and_filters = []
        self.search_param = None
        self.cuisines = []
        self.prices = []

    def format_request_url(self):
        all_filters = []
        url = BASE_URL + "/" + self.current_path + "?"
        if self.current_path == "restaurants":
            all_filters.append("radius=ignore")
        if self.search_param is not None:
            all_filters.append(self.search_param)
        if len(self.and_filters) > 0:
            all_filters += self.and_filters
        if len(self.cuisines) > 0:
            all_filters.append("cuisine=" + ",".join(self.cuisines))
        if len(self.prices) > 0:
            all_filters.append("price-range=" + ",".join(self.prices))
        return url + "&".join(all_filters)


class TUI:
    def __init__(self, stdscr, user):
        self.stdscr = stdscr
        self.search_name = "name"
        self.user = user
        self.search_text = None
        self.search_submitted = False
        self.filters = and_params + ["Cuisines", "Prices"]
        self.cuisines_menu = Menu(cuisines_param, user)
        self.prices_menu = Menu(price_param, user)
        self.filters_menu = Menu(self.filters, user)

    def render_home(self):
        self.stdscr.clear()
        y, x = self.stdscr.getmaxyx()
        if y < 20 or x < 40:
            raise TerminalTooSmall(x, y)
        elif y > 20 and x > 60:
            self.stdscr.addstr(logo_big)
        else:
            self.stdscr.addstr(1, 0, logo_small)
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
        main_box = curses.newwin(
            int(y*0.5), main_box_max_x, main_box_y, main_box_x)
        main_box.box()
        search_box = curses.newwin(3, x-10, search_box_y, search_box_x)
        search_box.box()
        self.stdscr.refresh()
        nav_bar.refresh()
        main_box.refresh()
        search_box.refresh()
        self.search_text = "" if self.search_text is None else self.search_text
        _, max_x = main_box.getmaxyx()
        self.print_help_string(main_box_y, main_box_x,
                               main_box_max_x - main_box_x)
        self.print_nav_bar_items(
            nav_bar_y, nav_bar_x, nav_bar_max_x)
        search_string = "Search " + self.search_name + ": "
        self.print_keyword_string(search_box_y,
                                  search_box_x, search_string + self.search_text)

    def scroll_loop(self, menu, action, items=[]):
        if len(items) == 0:
            items = get_restaurant_names(menu.data)
        menu.render_menu(self.stdscr, items)
        while (c := self.stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
            win_max_y, _ = self.stdscr.getmaxyx()
            # max_y = number_of_restaurants - orig_y + 1
            max_y = len(items) + menu.y - 1
            if c in (ord('j'), ord('J')):
                if menu.current_y == win_max_y - 2 or menu.current_y == max_y:
                    if menu.offset + menu.current_y < max_y:
                        menu.offset += 1
                else:
                    menu.current_y += 1
            elif c in (ord('k'), ord('K')):
                if menu.current_y > menu.y:
                    menu.current_y -= 1
                elif menu.offset > 0:
                    menu.offset -= 1
            elif c in (10, ord('o'), ord('O')):
                if action is not None:
                    action(menu)
            elif c in (ord('f'), ord('F')):
                self.scroll_loop(self.filters_menu,
                                 self.toggle_item, items=self.filters)
            elif c in (ord('r'), ord('R')):
                return True
            elif c == ord('?'):
                print_help_menu()
            menu.render_menu(self.stdscr, items)

    def get_user_input(self, y, x):
        chars = "" if self.search_text is None else self.search_text
        orig_x = x if chars == "" else x - len(chars)
        curses.curs_set(1)
        offset = 0
        while True:
            char = self.stdscr.get_wch()
            _, max_x = self.stdscr.getmaxyx()
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
                    if offset > 0:
                        offset -= 1
                    else:
                        x = max(orig_x, x - 1)
                    self.search_text = chars[offset:]
                elif code == 27:
                    curses.curs_set(0)
                    self.search_text = chars[:-1]
                    self.render_home()
                    return
                # elif x == max_:
                #     chars = chars[offset:-1]
                elif chars[-1] == "\n":
                    curses.curs_set(0)
                    # stdscr.clear()
                    # stdscr.addstr(3, 3, chars[:-1])
                    # stdscr.getch()
                    self.search_submitted = True
                    self.search_text = chars[:-1]
                    return
                # escape
                elif code == 410:  # resize char
                    chars = ""
                    self.search_text = chars
                    x = orig_x
                    offset = 0
                elif isinstance(char, str):
                    if x > max_x:
                        offset += 1
                        self.search_text = chars[offset:]
                    else:
                        x += 1
                        self.search_text = chars
            self.render_home()
        self.search_text = chars

    def print_help_menu(self):
        render_help_menu()
        while (c := self.stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
            render_help_menu()

    def render_help_menu(self):
        self.stdscr.clear()
        help_box = curses.newwin(0, 0)
        help_box.box()
        self.stdscr.refresh()
        help_box.refresh()
        self.stdscr.addstr(1, 1, "Esc : Exits current mode/window")
        self.stdscr.addstr(2, 1, "I, i: Enters insert mode")
        self.stdscr.addstr(
            3, 1, "P, p: Displays restaurants around Prague college")
        self.stdscr.addstr(4, 1, "S, s: Toggles between search name/address")
        self.stdscr.addstr(5, 1, "R, r: Displays register page")
        self.stdscr.addstr(6, 1, "L, l: Displays login page")
        self.stdscr.addstr(
            7, 1, "F, f: Displays filter page menu to search based on filters")
        self.stdscr.addstr(
            8, 1, "R, r: Refreshes restaurants page")

    def get_data(self, user):
        try:
            url = user.format_request_url()
            r = requests.get(url)
            data = json.loads(r.text)
            if data["Data"] is None:
                return [dict({"Name": "No restaurants found"})]
            return data["Data"]
        except Exception as e:
            self.stdscr.clear()
            self.stdscr.addstr(str(e))
            self.stdscr.addstr(
                "Couldn't connect to the server, press any key to exit")
            self.stdscr.getch()
            sys.exit(1)

    def print_keyword_string(self, y, x, string):
        self.stdscr.addch(y + 1, x + 1, string[0], curses.color_pair(1) +
                          curses.A_UNDERLINE)
        self.stdscr.addstr(y + 1, x + 2, string[1:])

    def print_nav_bar_items(self, y, x, max_x):
        max_len = max_x
        x += 3
        space = max_len - x
        pc_text = "Prague College"
        restaurants_text = "All restaurants"
        cuisines_text = "Filters"
        login_text = "Login"
        sign_in_text = "Register"
        text_list = [pc_text, restaurants_text,
                     cuisines_text, login_text, sign_in_text]
        updated = len(text_list) - 1
        while len(" ".join(text_list)) >= max_x - x:
            text_list[updated] = text_list[updated][0] + "..."
            if updated == 0:
                break
            updated -= 1
        total_len = sum(map(len, text_list))
        space_total = space - total_len
        gap = space_total // (len(text_list) - 1)
        for text in text_list:
            self.print_keyword_string(y, x, text)
            x += len(text) + gap

    def print_help_string(self, y, x, max_x):
        help_text = """Welcome to restaurateur TUI!
        This interface is controlled via keyboard shortcuts. To access specific
        elements you can use the key that is highlighted in yellow and underlined. Access insert mode with "I" or "i", exit it with escape.
        If you need help with any of the commands press '?'"""
        max_len = max_x - 2
        x += 2
        if max_x < 45:
            help_text = "Press ? for help"
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
                self.stdscr.addch(y, x, char)
                x += 1

    def restaurant_items_loop(self, menu):
        new_items = get_restaurant_info(
            menu.get_currently_selected())
        new_menu = Menu(new_items, self.user)
        self.scroll_loop(new_menu, None, items=new_items)

    def toggle_item(self, menu):
        item = menu.get_currently_selected_item()
        if item.string_content == "Cuisines":
            self.scroll_loop(self.cuisines_menu, self.toggle_item,
                             items=cuisines_param)
            return
        elif item.string_content == "Prices":
            self.scroll_loop(self.prices_menu,
                             self.toggle_item, items=price_param)
            return
        item.toggle_highlighted = not item.toggle_highlighted
        param_value = string_to_param(item.string_content)
        if item.toggle_highlighted:
            if item.string_content in and_params:
                menu.user.and_filters.append(param_value + "=true")
            elif item.string_content in cuisines_param:
                menu.user.cuisines.append(param_value)
            elif item.string_content in price_param:
                menu.user.prices.append(param_value)
        else:
            if item.string_content in and_params:
                menu.user.and_filters.remove(param_value + "=true")
            elif item.string_content in cuisines:
                menu.user.cuisines.remove(param_value)
            elif item.string_content in prices:
                menu.user.prices.remove(param_value)


class TerminalTooSmall(Exception):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.message = f"Terminal too small! (x: {self.x}, y: {self.y})"
        super().__init__(self.message)


class MenuItem:
    def __init__(self, x, y, string_content, highlighted=False):
        self.x = x
        self.y = y
        self.string_content = string_content
        self.highlighted = highlighted
        self.toggle_highlighted = False
        self.max_x = 0

    def update_max(self, max_x):
        self.max_x = max_x
        self.string_content = self.string_content if self.x + \
            len(self.string_content) < max_x - 1 else self.string_content[:max_x-self.x-4] + "..."


class Menu:
    def __init__(self, data, user, filters_menu=None):
        # TODO: add these as constants for windows and use everywhere
        self.x = 2
        self.y = 1
        self.data = data
        self.current_y = self.y
        self.menu_items = []
        self.offset = 0
        self.user = user

    def add_items(self, stdscr, items):
        max_x, max_y = stdscr.getmaxyx()
        y = self.y
        for item in items:
            highlighted = True if y == self.current_y + self.offset else False
            self.menu_items.append(MenuItem(self.x, y, item, highlighted))
            y += 1

    def update_items(self, stdscr):
        max_x, max_y = stdscr.getmaxyx()
        y = self.y
        for item in self.menu_items:
            item.highlighted = True if y == self.current_y + self.offset else False
            y += 1

    def render_menu(self, stdscr, items):
        if len(self.menu_items) == 0:
            self.menu_items = []
            self.add_items(stdscr, items)
        else:
            self.update_items(stdscr)
        stdscr.clear()
        win_y, win_x = stdscr.getyx()
        main_box = curses.newwin(win_y, win_x)
        main_box.box()
        stdscr.refresh()
        main_box.refresh()
        max_y, max_x = stdscr.getmaxyx()
        max_y -= 1
        y = self.y
        menu_items = self.menu_items[self.offset:]
        for item in menu_items:
            if y >= max_y:
                break
            item.update_max(max_x)
            if item.toggle_highlighted and item.highlighted:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(y, item.x, item.string_content)
                stdscr.attroff(curses.color_pair(2))
            elif item.toggle_highlighted:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, item.x, item.string_content)
                stdscr.attroff(curses.color_pair(3))
            elif item.highlighted:
                stdscr.addstr(y, item.x, item.string_content,
                              curses.A_STANDOUT)
            else:
                stdscr.addstr(y, item.x, item.string_content)
            y += 1
        stdscr.refresh()

    def get_currently_selected(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return self.data[i]

    def get_currently_selected_item(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return item


def string_to_param(string):
    return string.replace(" ", "-").lower()


def get_restaurant_info(restaurant):
    try:
        restaurant["URL"] = re.match(
            r"^.+?[^\/:](?=[?\/]|$)", restaurant["URL"]).group(0)
    except:
        pass
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"]
    items = []
    for key, value in restaurant.items():
        if value in (None, "", "null") or key in ('Images', "ID"):
            continue
        elif key == 'OpeningHours':
            sorted_days = dict()
            for day in days_of_week:
                sorted_days[day] = json.loads(value)[day]
            items.append("**Opening hours**")
            for k, v in sorted_days.items():
                items.append(k)
                items.append(v)
        else:
            start = key + ": "
            if isinstance(value, list):
                v = ", ".join(value)
                items.append(start + v)
            else:
                items.append(start + str(value))
    return items


def get_restaurant_names(data):
    return [restaurant["Name"] for restaurant in data]


def render_menu(stdscr):
    # TODO handle errors
    stdscr.clear()
    y, x = stdscr.getyx()
    if data["Status"] == 200:
        dat = data["Data"]
        orig_y = y + 1
    else:
        stdscr.addstr(y + 1, x, "Couldn't fetch restaurants")
        return
    user_y = orig_y
    offset = 0
    number_of_restaurants = display_restaurants(
        stdscr, dat, orig_y, x, user_y, offset)
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        max_y, max_x = stdscr.getmaxyx()
        max_y = number_of_restaurants - orig_y + 1
        if c in (ord('j'), ord('J')):
            if user_y + offset < max_y:
                win_y, win_x = stdscr.getmaxyx()
                if user_y == win_y - 2:
                    offset += 1
                else:
                    user_y += 1
        elif c in (ord('k'), ord('K')):
            if user_y > orig_y:
                user_y -= 1
            elif offset > 0:
                offset -= 1
        elif c in (10, ord('o'), ord('O')):
            display_restaurant_info(stdscr, dat[user_y - orig_y])
        display_restaurants(stdscr, dat, orig_y, x, user_y, offset)


def display_restaurant_info(stdscr, restaurant):
    stdscr.clear()
    # Clean up URL
    try:
        restaurant["URL"] = re.match(
            r"^.+?[^\/:](?=[?\/]|$)", restaurant["URL"]).group(0)
    except:
        pass
    y, x = stdscr.getyx()
    main_box = curses.newwin(y, x)
    main_box.box()
    stdscr.refresh()
    main_box.refresh()
    x += 1
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"]
    max_y, max_x = stdscr.getmaxyx()
    max_len = max_x - 2
    orig_x = x
    for key, value in restaurant.items():
        y += 1
        if y >= max_y - 1:
            break
        if value in (None, "", "null") or key in ('Images', "ID"):
            y -= 1
            continue
        elif key == 'OpeningHours':
            sorted_days = dict()
            for day in days_of_week:
                sorted_days[day] = json.loads(value)[day]
            y += 1
            stdscr.addstr(y, x, "**Opening hours**")
            y += 1
            for k, v in sorted_days.items():
                orig_x = x
                stdscr.addstr(y, x, k + ":")
                x += len(k) + 2
                stdscr.addstr(y, x, v)
                x = orig_x
                y += 1
                if y >= max_y - 1:
                    stdscr.getch()
                    return
        else:
            stdscr.addstr(y, x, key + ":")
            x += len(key) + 2
            if isinstance(value, list):
                value = ", ".join(value)
            if isinstance(value, str):
                for word in value.split():
                    word_len = len(word)
                    if x + word_len + 1 >= max_len:
                        y += 1
                        if y >= max_y - 1:
                            stdscr.getch()
                            return
                        x = orig_x
                    stdscr.addstr(y, x, str(word))
                    x += word_len
                    stdscr.addstr(y, x, " ")
                    x += 1
            else:
                stdscr.addstr(y, x, str(value))
            x = orig_x
    stdscr.getch()


def display_restaurants(stdscr, restaurants, y, x, user_y, offset):
    stdscr.clear()
    win_y, win_x = stdscr.getyx()
    main_box = curses.newwin(win_y, win_x)
    main_box.box()
    stdscr.refresh()
    main_box.refresh()
    max_y, max_x = stdscr.getmaxyx()
    x += 1
    number_of_restaurants = len(restaurants)
    free_space = max_y - y - 1
    # For user_y
    if number_of_restaurants > free_space:
        max_num = number_of_restaurants - free_space
    else:
        max_num = 0
    restaurants = restaurants[offset:]
    for restaurant in restaurants:
        if y == max_y - 1:
            break
        elif y == user_y:
            stdscr.addstr(y, x, restaurant["Name"], curses.A_STANDOUT)
        else:
            stdscr.addstr(y, x, restaurant["Name"])
        y += 1
    stdscr.refresh()
    return number_of_restaurants


# FIXME


def main(stdscr):
    stdscr.clear()
    curses.curs_set(0)  # Turn off cursor blinking
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_RED, -1)
    user = User()
    tui = TUI(stdscr, user)
    tui.render_home()
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        if c in (ord('s'), ord('S')):
            tui.search_name = "name" if tui.search_name == "address" else "address"
        if c in (ord('i'), ord('I')):
            y, x = tui.stdscr.getyx()
            tui.stdscr.move(y, x)
            tui.get_user_input(y, x)
            if tui.search_submitted:
                # process input
                user.search_param = "search-" + tui.search_name + "=" + tui.search_text
                user.current_path = "restaurants"
                cont = True
                while cont:
                    data = tui.get_data(tui.user)
                    menu = Menu(data, user)
                    cont = tui.scroll_loop(menu, tui.restaurant_items_loop)
                tui.search_submitted = False
                tui.search_text = None
                user.search_param = None
                tui.render_home()
        elif c == ord('?'):
            tui.print_help_menu()
            tui.render_home()
        elif c in (ord('p'), ord('P')):
            user.current_path = "prague-college/restaurants"
            cont = True
            while cont:
                data = tui.get_data(tui.user)
                menu = Menu(data, user)
                cont = tui.scroll_loop(menu, tui.restaurant_items_loop)
            # render_menu(stdscr)
        elif c in (ord('a'), ord('A')):
            user.current_path = "restaurants"
            cont = True
            while cont:
                data = tui.get_data(tui.user)
                menu = Menu(data, user)
                cont = tui.scroll_loop(menu, tui.restaurant_items_loop)
        elif c in (ord('f'), ord('F')):
            tui.scroll_loop(tui.filters_menu, tui.toggle_item,
                            items=tui.filters)
            # render_menu(stdscr)
        tui.render_home()


# TODO: Add status line
if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
