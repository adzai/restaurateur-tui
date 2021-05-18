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


current_path = ""

and_params = ["Vegetarian", "Vegan", "Gluten free", "Takeaway"]
price_param = ["0-300", "300-600", "600-"]
cuisines_param = ["Czech", "International", "Italian", "English", "American", "Asian", "Indian", "Japanese", "Vietnamese",
                  "Spanish", "Mediterranean", "French", "Thai", "Balkan", "Brazil", "Russian", "Chinese", "Greek", "Arabic", "Korean"]
and_filters = []
cuisines = []
prices = []


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
    def __init__(self, data):
        # TODO: add these as constants for windows and use everywhere
        self.x = 2
        self.y = 1
        self.data = data
        self.current_y = self.y
        self.menu_items = []
        self.offset = 0

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

    def scroll_loop(self, stdscr, action, items=[]):
        if len(items) == 0:
            items = get_restaurant_names(self.data)
        self.render_menu(stdscr, items)
        while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
            win_max_y, _ = stdscr.getmaxyx()
            # max_y = number_of_restaurants - orig_y + 1
            max_y = len(items) + self.y - 1
            if c in (ord('j'), ord('J')):
                if self.current_y == win_max_y - 2 or self.current_y == max_y:
                    if self.offset + self.current_y < max_y:
                        self.offset += 1
                else:
                    self.current_y += 1
            elif c in (ord('k'), ord('K')):
                if self.current_y > self.y:
                    self.current_y -= 1
                elif self.offset > 0:
                    self.offset -= 1
            elif c in (10, ord('o'), ord('O')):
                if action is not None:
                    action(self, stdscr)
            elif c in (ord('f'), ord('F')):
                menu = filters_menu
                filters_menu.scroll_loop(stdscr, toggle_item, items=filters)
            elif c in (ord('r'), ord('R')):
                return True
            elif c == ord('?'):
                print_help_menu(stdscr)
            self.render_menu(stdscr, items)

    def get_currently_selected(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return self.data[i]

    def get_currently_selected_item(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return item


filters = and_params + ["Cuisines", "Prices"]
filters_menu = Menu(filters)
cuisines_menu = Menu(cuisines_param)
prices_menu = Menu(price_param)


def string_to_param(string):
    return string.replace(" ", "-").lower()


def toggle_item(menu, stdscr):
    item = menu.get_currently_selected_item()
    if item.string_content == "Cuisines":
        cuisines_menu.scroll_loop(stdscr, toggle_item, items=cuisines_param)
        return
    elif item.string_content == "Prices":
        prices_menu.scroll_loop(stdscr, toggle_item, items=price_param)
        return
    item.toggle_highlighted = not item.toggle_highlighted
    param_value = string_to_param(item.string_content)
    if item.toggle_highlighted:
        if item.string_content in and_params:
            and_filters.append(param_value + "=true")
        elif item.string_content in cuisines_param:
            cuisines.append(param_value)
        elif item.string_content in price_param:
            prices.append(param_value)
    else:
        if item.string_content in and_params:
            and_filters.remove(param_value + "=true")
        elif item.string_content in cuisines:
            cuisines.remove(param_value)
        elif item.string_content in prices:
            prices.remove(param_value)


def restaurant_items_loop(menu, stdscr):
    new_items = get_restaurant_info(
        menu.get_currently_selected())
    new_menu = Menu(new_items)
    new_menu.scroll_loop(stdscr, None, items=new_items)


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

# TODO handle resizing search_input


def render_home(stdscr, search_name="name", search_text=None):
    stdscr.clear()
    y, x = stdscr.getmaxyx()
    if y < 20 or x < 40:
        raise TerminalTooSmall(x, y)
    elif y > 20 and x > 60:
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
    main_box = curses.newwin(
        int(y*0.5), main_box_max_x, main_box_y, main_box_x)
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
    # TODO: Have a toggle key which will toggle between search name and search address
    search_string = "Search " + search_name + ": "
    print_keyword_string(stdscr, search_box_y, search_box_x, search_string +
                         search_text)


def print_nav_bar_items(stdscr, y, x, max_x):
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
        print_keyword_string(stdscr, y, x, text)
        x += len(text) + gap


def format_request_url(path):
    all_filters = []
    url = "http://localhost:8080/" + path + "?"
    if path == "restaurants":
        all_filters.append("radius=ignore")
    if len(and_filters) > 0:
        all_filters += and_filters
    if len(cuisines) > 0:
        all_filters.append("cuisine=" + ",".join(cuisines))
    if len(prices) > 0:
        all_filters.append("price-range=" + ",".join(prices))
    return url + "&".join(all_filters)


def get_data(stdscr, path):
    try:
        url = format_request_url(path)
        r = requests.get(url)
        data = json.loads(r.text)
        if data["Data"] is None:
            return [dict({"Name": "No restaurants found"})]
        return data["Data"]
    except Exception as e:
        stdscr.clear()
        stdscr.addstr("Couldn't connect to the server, press any key to exit")
        stdscr.getch()
        sys.exit(1)


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


def print_help_string(stdscr, y, x, max_x):
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
            stdscr.addch(y, x, char)
            x += 1


def print_keyword_string(stdscr, y, x, string):
    stdscr.addch(y + 1, x + 1, string[0], curses.color_pair(1) +
                 curses.A_UNDERLINE)
    stdscr.addstr(y + 1, x + 2, string[1:])


def get_user_input(stdscr, y, x, search_name="name", chars=None):
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
                render_home(stdscr, search_name=search_name, search_text=chars)
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
            elif code == 410:  # resize char
                chars = chars[:-1]
            elif isinstance(char, str):
                stdscr.addstr(y, x, char)
                x += 1
        render_home(stdscr, search_name=search_name, search_text=chars)
    return chars, False


def render_help_menu(stdscr):
    stdscr.clear()
    help_box = curses.newwin(0, 0)
    help_box.box()
    stdscr.refresh()
    help_box.refresh()
    stdscr.addstr(1, 1, "Esc : Exits current mode/window")
    stdscr.addstr(2, 1, "I, i: Enters insert mode")
    stdscr.addstr(3, 1, "P, p: Displays restaurants around Prague college")
    stdscr.addstr(4, 1, "S, s: Toggles between search name/address")
    stdscr.addstr(5, 1, "R, r: Displays register page")
    stdscr.addstr(6, 1, "L, l: Displays login page")
    stdscr.addstr(
        7, 1, "F, f: Displays filter page menu to search based on filters")
    stdscr.addstr(
        8, 1, "R, r: Refreshes restaurants page")


def print_help_menu(stdscr):
    render_help_menu(stdscr)
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        render_help_menu(stdscr)


def main(stdscr):
    stdscr.clear()
    curses.curs_set(0)  # Turn off cursor blinking
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_RED, -1)
    render_home(stdscr)
    user_input = ""
    search_name = "name"
    while (c := stdscr.getch()) != 27 and c not in (ord('q'), ord('Q')):
        if c in (ord('s'), ord('S')):
            search_name = "name" if search_name == "address" else "address"
        if c in (ord('i'), ord('I')):
            y, x = stdscr.getyx()
            stdscr.move(y, x)
            user_input, finished = get_user_input(
                stdscr, y, x, search_name=search_name, chars=user_input)
            if finished:
                # process input
                user_input = ""
                render_home(stdscr, search_text=user_input)
        elif c == ord('?'):
            print_help_menu(stdscr)
            render_home(stdscr, search_name=search_name,
                        search_text=user_input)
        elif c in (ord('p'), ord('P')):
            current_path = "prague-college/restaurants"
            cont = True
            while cont:
                data = get_data(stdscr, current_path)
                menu = Menu(data)
                cont = menu.scroll_loop(stdscr, restaurant_items_loop)
            # render_menu(stdscr)
        elif c in (ord('a'), ord('A')):
            current_path = "restaurants"
            cont = True
            while cont:
                data = get_data(stdscr, current_path)
                menu = Menu(data)
                cont = menu.scroll_loop(stdscr, restaurant_items_loop)
        elif c in (ord('f'), ord('F')):
            menu = filters_menu
            filters_menu.scroll_loop(stdscr, toggle_item, items=filters)
            # render_menu(stdscr)
        render_home(stdscr, search_name=search_name, search_text=user_input)


if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
