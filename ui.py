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
cuisines_param = ["Czech", "International", "Italian", "English", "American",
                  "Asian", "Indian", "Japanese", "Vietnamese",
                  "Spanish", "Mediterranean", "French", "Thai", "Balkan",
                  "Brazil", "Russian", "Chinese", "Greek", "Arabic", "Korean"]


# TODO: add some vim key bindings

class User:
    def __init__(self):
        self.and_filters = []
        self.search_param = None
        self.cuisines = []
        self.prices = []
        self.prague_college = False

    def format_request_url(self):
        all_filters = []
        url = BASE_URL + "/restaurants?"
        if self.prague_college:
            all_filters.append("lat=50.0785714")
            all_filters.append("lon=14.4400922")
        else:
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
        self.home_main_box = None
        self.nav_bar = None
        self.search_box = None
        self.status_box = None
        self.help_box = None
        self.search_name = "name"
        self.user = user
        self.search_text = None
        self.search_submitted = False
        self.filters = and_params + ["Cuisines", "Prices"]
        self.cuisines_menu = Menu(cuisines_param, user)
        self.prices_menu = Menu(price_param, user)
        self.filters_menu = Menu(self.filters, user)
        self.filters_menu_on = False
        self.status = "Normal mode"
        self.home_max_x = None
        self.home_max_y = None

    def render_home_main_box(self):
        home_main_box_x = 5
        home_main_box_max_x = self.home_x-10
        if self.home_y > 25:
            home_main_box_y = int(self.home_y*0.35)
            self.home_main_box = curses.newwin(
                int(self.home_y*0.5), home_main_box_max_x, home_main_box_y,
                home_main_box_x)
        else:
            home_main_box_y = int(self.home_y*0.50)
            self.home_main_box = curses.newwin(
                max(int(self.home_y*0.20), 3),
                home_main_box_max_x, home_main_box_y, home_main_box_x)
        self.home_main_box.box()
        self.print_help_string()
        self.home_main_box.refresh()

    def render_search_box(self):
        if self.home_y > 25:
            search_box_y = int(self.home_y*0.87)
        else:
            search_box_y = int(self.home_y*0.75)
        search_box_x = 5
        self.search_box = curses.newwin(
            3, self.home_x-10, search_box_y, search_box_x)
        self.search_box.box()
        self.search_box.refresh()
        self.search_text = "" if self.search_text is None else self.search_text
        search_string = "Search " + self.search_name + ": "
        self.print_keyword_string(1, self.search_box,
                                  search_string + self.search_text)

    def render_nav_bar(self):
        if self.home_y > 25:
            nav_bar_y = int(self.home_y*0.20)
        else:
            nav_bar_y = int(self.home_y*0.30)
        nav_bar_x = 5
        nav_bar_max_x = self.home_x-10
        self.nav_bar = curses.newwin(
            3, nav_bar_max_x, nav_bar_y, nav_bar_x)
        self.nav_bar.box()
        self.render_home_main_box()
        self.nav_bar.refresh()
        self.print_nav_bar_items()

    def render_home(self, render_all=False):
        self.home_y, self.home_x = self.stdscr.getmaxyx()
        if render_all:
            self.stdscr.erase()
            if self.home_y < 12 or self.home_x < 30:
                raise TerminalTooSmall(self.home_x, self.home_y)
            elif self.home_y < 15 or self.home_x < 40:
                self.stdscr.addstr("Restaurateur TUI")
            elif self.home_y > 30 and self.home_x > 65:
                self.stdscr.addstr(logo_big)
            else:
                self.stdscr.addstr(1, 0, logo_small)
            self.stdscr.refresh()
            self.render_nav_bar()
            self.render_search_box()
            self.render_status_line()
            return
        self.render_status_line()
        self.render_search_box()

    def render_status_line(self):
        max_y, _ = self.stdscr.getmaxyx()
        self.status_box = curses.newwin(3, 20, max_y - 1, 1)
        self.status_box.addstr("Status: " + self.status)
        self.status_box.refresh()

    def scroll_loop(self, menu, action, items=[]):
        if menu == self.filters_menu:
            self.filters_menu_on = True
        if len(items) == 0:
            items = get_restaurant_names(menu.data)
        self.stdscr.erase()
        self.render_status_line()
        menu.render_menu(self.stdscr, items)
        # Making window bigger doesn't resize
        while (c := menu.window.getch()) != 27 and c not in (ord('q'), ord('Q')):
            win_max_y, max_x = menu.window.getmaxyx()
            # max_y = number_of_restaurants - orig_y + 1
            max_y = len(items) + menu.y - 1
            if c in (ord('j'), ord('J'), curses.KEY_DOWN):
                if menu.current_y == win_max_y - 2 or menu.current_y == max_y:
                    if menu.offset + menu.current_y < max_y:
                        menu.offset += 1
                    else:
                        continue
                else:
                    menu.current_y += 1
            elif c in (ord('k'), ord('K'), curses.KEY_UP):
                if menu.current_y > menu.y:
                    menu.current_y -= 1
                elif menu.offset > 0:
                    menu.offset -= 1
                else:
                    continue
            elif c in (10, ord('o'), ord('O')):
                if action is not None:
                    action(menu)
            elif c in (ord('f'), ord('F')):
                if not self.filters_menu_on:
                    self.scroll_loop(self.filters_menu,
                                     self.toggle_item, items=self.filters)
            elif c in (ord('r'), ord('R')):
                if menu != self.filters_menu:
                    return True
            elif c == ord('?'):
                self.print_help_menu()
            elif c == curses.KEY_RESIZE:
                self.stdscr.erase()
                self.stdscr.refresh()

            menu.render_menu(self.stdscr, items)
        if menu == self.filters_menu:
            self.filters_menu_on = False

    def get_user_input(self):
        chars = "" if self.search_text is None else self.search_text
        orig_x = len("Search " + self.search_name + ": ") + 1 + len(chars)
        x = orig_x
        self.search_box.move(1, x)
        curses.curs_set(1)
        offset = 0
        while True:
            char = self.search_box.get_wch()
            _, max_x = self.search_box.getmaxyx()
            max_x -= 3
            chars += char if isinstance(char, str) else chr(char)
            code = ord(char) if isinstance(char, str) else char
            resized = False
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
                    self.search_text = ""
                    self.render_home()
                    return
                elif chars[-1] == "\n":
                    curses.curs_set(0)
                    self.search_submitted = True
                    self.search_text = chars[:-1]
                    return
                elif code == curses.KEY_RESIZE:
                    chars = ""
                    self.search_text = chars
                    x = orig_x
                    offset = 0
                    resized = True
                elif isinstance(char, str):
                    if x > max_x:
                        offset += 1
                        self.search_text = chars[offset:]
                    else:
                        x += 1
                        self.search_text = chars

            curses.curs_set(0)  # Prevent cursor flashing on re-render
            self.render_home(render_all=resized)
            curses.curs_set(1)

    def print_help_menu(self):
        self.stdscr.erase()
        self.stdscr.refresh()
        self.render_help_menu()
        while (c := self.stdscr.getch()) != 27 and \
                c not in (ord('q'), ord('Q')):
            self.render_help_menu()
        self.help_box.erase()
        self.help_box.refresh()
        self.render_status_line()

    def render_help_menu(self):
        self.help_box = curses.newwin(0, 0)
        self.help_box.box()
        self.help_box.addstr(1, 1, "Esc : Exits current status/window")
        self.help_box.addstr(2, 1, "I, i: Enters insert status")
        self.help_box.addstr(
            3, 1, "P, p: Displays restaurants around Prague college")
        self.help_box.addstr(
            4, 1, "A, a: Displays all restaurants in Prague")
        self.help_box.addstr(5, 1, "S, s: Toggles between search name/address")
        self.help_box.addstr(
            6, 1, "F, f: Displays filter page menu to search based on filters")
        self.help_box.addstr(
            7, 1, "R, r: Refreshes restaurants page")
        self.help_box.refresh()

    def get_data(self, user):
        self.status = "Loading"
        self.render_status_line()
        try:
            url = user.format_request_url()
            r = requests.get(url)
            data = json.loads(r.text)
            if data["Data"] is None:
                return [dict({"Name": "No restaurants found"})]
            self.status = "Normal mode"
            return data["Data"]
        except Exception as e:
            self.stdscr.erase()
            self.stdscr.addstr("Exception: " + str(e) + "\n")
            self.stdscr.addstr(
                "Couldn't connect to the server, press any key to exit")
            self.stdscr.getch()
            sys.exit(1)

    def print_keyword_string(self, x, box, string):
        box.addstr(1, x, string[0], curses.color_pair(1) +
                   curses.A_UNDERLINE)
        box.addstr(1, x + 1, string[1:])
        box.refresh()

    def print_nav_bar_items(self):
        max_y, max_x = self.nav_bar.getmaxyx()
        max_len = max_x - 1
        x = 1
        space = max_len - x
        pc_text = "Prague College"
        restaurants_text = "All restaurants"
        cuisines_text = "Filters"
        text_list = [pc_text, restaurants_text,
                     cuisines_text]  # , login_text, sign_in_text]
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
            self.print_keyword_string(x, self.nav_bar, text)
            x += len(text) + gap

    def print_help_string(self):
        help_text = """Welcome to restaurateur TUI!
        This interface is controlled via keyboard shortcuts. To access specific
        elements you can use the key that is highlighted in yellow and underlined. Access insert status with "I" or "i", exit it with escape.
        If you need help with any of the commands press '?'"""
        max_y, max_x = self.home_main_box.getmaxyx()
        max_len = max_x - 2
        x = 1
        if max_x < 45 or max_y < 12:
            help_text = "Press ? for help"
        count = x
        orig_x = x
        y = 1
        for word in help_text.split():
            word += " "
            count += len(word)
            if count + orig_x >= max_len:
                y += 1
                x = orig_x
                count = x
            for char in word:
                if x == orig_x and char == " ":
                    continue
                self.home_main_box.addch(y, x, char)
                x += 1
                if x == max_len:
                    y += 1
                    x = orig_x
                    count = x

    def restaurant_items_loop(self, menu):
        new_items = get_restaurant_info(
            menu.get_currently_selected())
        new_menu = Menu(new_items, self.user)
        self.scroll_loop(new_menu, self.display_truncated, items=new_items)

    def display_truncated(self, menu):
        item, pos = menu.get_currently_selected_item()
        if item.string_content[:-4:-1] == "...":
            # Do something when string
            # Do something when list
            # Do something when dict
            key = item.string_content.split(":")[0]
            values = menu.data[pos].replace(key + ": ", "")  # [key]
            items = []
            _, max_x = self.stdscr.getmaxyx()
            max_x -= 6
            try:
                d = json.loads(values)
                # TODO function wrap_text
                for k, v in d.items():
                    x = 0
                    items.append(str(k))
                    chars = ""
                    for char in str(v):
                        if x == max_x:
                            items.append(chars)
                            chars = ""
                            x = 0
                        chars += char
                        x += 1
                    items.append(chars)
                    items.append("")
                items = items[:-1]
            except:
                x = 0
                chars = ""
                for char in str(values):
                    if x == max_x:
                        items.append(chars)
                        chars = ""
                        x = 0
                    chars += char
                    x += 1
                items.append(chars)
            new_menu = Menu(items, self.user)
            self.scroll_loop(new_menu, None, items=items)  # Use menu.data?

    def toggle_item(self, menu):
        item, _ = menu.get_currently_selected_item()
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
                self.user.and_filters.append(param_value + "=true")
            elif item.string_content in cuisines_param:
                self.user.cuisines.append(param_value)
            elif item.string_content in price_param:
                self.user.prices.append(param_value)
        else:
            if item.string_content in and_params:
                menu.user.and_filters.remove(param_value + "=true")
            elif item.string_content in cuisines_param:
                self.user.cuisines.remove(param_value)
            elif item.string_content in price_param:
                self.user.prices.remove(param_value)


class TerminalTooSmall(Exception):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.message = f"Terminal too small! (x: {self.x}, y: {self.y})"
        super().__init__(self.message)


class MenuItem:
    def __init__(self, x, y, content, highlighted=False):
        self.x = x
        self.y = y
        self.string_content = content
        self.highlighted = highlighted
        self.toggle_highlighted = False
        self.max_x = 0

    def update_max(self, max_x):
        self.max_x = max_x
        self.string_content = self.string_content if self.x + \
            len(self.string_content) < max_x - 1 else \
            self.string_content[:max_x-self.x-4] + "..."


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
        self.window = None

    def add_items(self, items):
        max_x, max_y = self.window.getmaxyx()
        y = self.y
        for item in items:
            highlighted = True if y == self.current_y + self.offset else False
            self.menu_items.append(MenuItem(self.x, y, item, highlighted))
            y += 1

    def update_items(self):
        max_x, max_y = self.window.getmaxyx()
        y = self.y
        for item in self.menu_items:
            item.highlighted = True if y == self.current_y + \
                self.offset else False
            y += 1

    def render_menu(self, stdscr, items):
        max_y, max_x = stdscr.getmaxyx()
        self.window = curses.newwin(max_y - 1, max_x - 1)
        self.window.keypad(True)
        if len(self.menu_items) == 0:
            self.menu_items = []
            self.add_items(items)
        else:
            self.update_items()
        self.window.erase()
        max_y, max_x = self.window.getmaxyx()
        max_y -= 1
        y = self.y
        menu_items = self.menu_items[self.offset:]
        for item in menu_items:
            if y >= max_y:
                break
            item.update_max(max_x)
            if item.toggle_highlighted and item.highlighted:
                self.window.attron(curses.color_pair(2))
                self.window.addstr(y, item.x, item.string_content)
                self.window.attroff(curses.color_pair(2))
            elif item.toggle_highlighted:
                self.window.attron(curses.color_pair(3))
                self.window.addstr(y, item.x, item.string_content)
                self.window.attroff(curses.color_pair(3))
            elif item.highlighted:
                self.window.addstr(y, item.x, item.string_content,
                                   curses.A_STANDOUT)
            else:
                self.window.addstr(y, item.x, item.string_content)
            y += 1

        self.window.box()
        self.window.refresh()

    def get_currently_selected(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return self.data[i]

    def get_currently_selected_item(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return item, i


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


def main(stdscr):
    stdscr.erase()
    curses.curs_set(0)  # Turn off cursor blinking
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_RED, -1)
    user = User()
    tui = TUI(stdscr, user)
    tui.render_home(render_all=True)
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        re_render = False
        if c in (ord('s'), ord('S')):
            tui.search_name = "name" if tui.search_name == "address" \
                else "address"
        if c in (ord('i'), ord('I')):
            tui.status = "Insert mode"
            tui.render_status_line()
            tui.get_user_input()
            if tui.search_submitted:
                # process input
                user.prague_college = False
                user.search_param = "search-" + tui.search_name + \
                    "=" + tui.search_text
                cont = True
                while cont:
                    data = tui.get_data(tui.user)
                    menu = Menu(data, user)
                    cont = tui.scroll_loop(menu, tui.restaurant_items_loop)
                tui.search_submitted = False
                tui.search_text = None
                user.search_param = None
            re_render = True
        elif c == ord('?'):
            tui.print_help_menu()
            re_render = True
        elif c in (ord('p'), ord('P')):
            user.prague_college = True
            cont = True
            while cont:
                data = tui.get_data(tui.user)
                menu = Menu(data, user)
                cont = tui.scroll_loop(menu, tui.restaurant_items_loop)
            re_render = True
        elif c in (ord('a'), ord('A')):
            user.prague_college = False
            cont = True
            while cont:
                data = tui.get_data(tui.user)
                menu = Menu(data, user)
                cont = tui.scroll_loop(menu, tui.restaurant_items_loop)
            re_render = True
        elif c in (ord('f'), ord('F')):
            tui.scroll_loop(tui.filters_menu, tui.toggle_item,
                            items=tui.filters)
            re_render = True
        elif c == curses.KEY_RESIZE:
            re_render = True
        tui.status = "Normal mode"
        tui.render_home(render_all=re_render)


# TODO: Handle truncating of text in menus
if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
