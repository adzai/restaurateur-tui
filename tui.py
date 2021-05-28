import requests
import curses
import json
from user import User
from menus import Menu
import utils

and_params = ["Vegetarian", "Vegan", "Gluten free",
              "Takeaway", "Has menu", "Sort by"]
price_param = ["0-300", "300-600", "600-"]
cuisines_param = ["Czech", "International", "Italian", "English", "American",
                  "Asian", "Indian", "Japanese", "Vietnamese",
                  "Spanish", "Mediterranean", "French", "Thai", "Balkan",
                  "Brazil", "Russian", "Chinese", "Greek", "Arabic", "Korean"]

sort_param = ["Rating", "Price desc", "Price asc"]

logo_big = r"""
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
        self.cuisines_menu = Menu("Cuisines", user)
        self.prices_menu = Menu("Prices", user)
        self.filters_menu = Menu("Filters", user)
        self.sort_menu = Menu("Sort by", user, strict_toggle=True)
        self.filters_menu_on = False
        self.status = "Main menu"
        self.displaying_error = False
        self.get_restaurants = False
        self.highlight_parent = False

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
            original_status = self.status
            while self.home_y < 12 or self.home_x < 30:
                self.status = "Terminal too small"
                self.stdscr.erase()
                self.stdscr.refresh()
                self.render_status_line()
                self.stdscr.getch()
                self.home_y, self.home_x = self.stdscr.getmaxyx()
            self.status = original_status
            if self.home_y < 15 or self.home_x < 40:
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
        self.status_box = curses.newwin(3, 30, max_y - 1, 1)
        self.status_box.addstr(self.status)
        self.status_box.refresh()

    def scroll_loop(self, menu, action, items_func=None):
        if menu == self.filters_menu:
            self.filters_menu_on = True
        if items_func is None:

            def items_func():
                menu.set_data(self.get_data(self.user))
                return utils.get_restaurant_names(menu.raw_data)
        items = items_func()
        self.stdscr.erase()
        self.render_status_line()
        original_status = menu.name
        self.status = original_status
        menu.render_menu(self.stdscr, items, self.render_status_line)
        # Making window bigger doesn't resize
        while (c := menu.window.getch()) != 27 \
                and c not in (ord('q'), ord('Q')):
            win_max_y, max_x = menu.window.getmaxyx()
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
                                     self.toggle_item,
                                     items_func=lambda: self.filters)
            elif c in (ord('r'), ord('R')):
                if menu != self.filters_menu:
                    items = items_func()
                    menu.refresh_items = True
            elif c == ord('?'):
                self.print_help_menu()
            elif c == curses.KEY_RESIZE:
                self.stdscr.erase()
                self.stdscr.refresh()

            self.status = original_status
            menu.render_menu(self.stdscr, items, self.render_status_line)
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
            if resized:
                self.search_box.move(1, x)
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
        self.help_box.addstr(2, 1, "I, i: Enters insert mode")
        self.help_box.addstr(
            3, 1, "P, p: Displays restaurants around Prague college")
        self.help_box.addstr(
            4, 1, "A, a: Displays all restaurants in Prague")
        self.help_box.addstr(5, 1, "S, s: Toggles between search name/address")
        self.help_box.addstr(
            6, 1, "F, f: Displays filter page menu to search based on filters")
        self.help_box.addstr(
            7, 1, "R, r: Refreshes current page")
        self.help_box.refresh()

    def get_data(self, user):
        self.status = "Loading"
        self.render_status_line()
        try:
            url = user.format_request_url()
            r = requests.get(url)
            data = json.loads(r.text)
            return data["data"]
        except Exception:
            self.stdscr.erase()
            self.status = "Couldn't connect to the server"
            self.displaying_error = True

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
                     cuisines_text]
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
        elements you can use the key that is highlighted in yellow and
        underlined. Access insert mode with "I" or "i", exit it with escape.
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
        def data_func(): return utils.get_restaurant_info(
            menu.get_currently_selected())
        new_menu = Menu("Restaurant info", self.user)
        new_menu.raw_data = data_func()
        self.scroll_loop(new_menu, action=self.display_truncated,
                         items_func=data_func)

    def display_truncated(self, menu):
        item, pos = menu.get_currently_selected_item()
        if item.string_content[:-4:-1] == "...":
            key = item.string_content.split(":")[0]
            values = menu.raw_data[pos].replace(key + ": ", "")  # [key]
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
            except Exception:
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
            new_menu = Menu("Item info", self.user)
            self.scroll_loop(new_menu, action=None, items_func=lambda: items)

    def toggle_item(self, menu):
        item, _ = menu.get_currently_selected_item()
        if item.string_content == "Cuisines":
            self.scroll_loop(self.cuisines_menu, action=self.toggle_item,
                             items_func=lambda: cuisines_param)

            if self.highlight_parent:
                item.toggle_highlighted = not item.toggle_highlighted
            return
        elif item.string_content == "Prices":
            self.scroll_loop(self.prices_menu,
                             action=self.toggle_item,
                             items_func=lambda: price_param)
            if self.highlight_parent:
                item.toggle_highlighted = not item.toggle_highlighted
            return
        elif item.string_content == "Sort by":
            self.scroll_loop(self.sort_menu,
                             action=self.toggle_item,
                             items_func=lambda: sort_param)
            if self.highlight_parent:
                item.toggle_highlighted = not item.toggle_highlighted
            return
        item.toggle_highlighted = not item.toggle_highlighted
        if menu.strict_toggle:
            menu.remove_other_toggles(item.string_content)
            # menu.render_menu(self.stdscr, menu.menu_items,
            #                  self.render_status_line)
            # remove from params
            self.user.sort = ""
        param_value = utils.string_to_param(item.string_content)
        if item.toggle_highlighted:
            if item.string_content in and_params:
                self.user.and_filters.append(param_value + "=true")
            elif item.string_content in cuisines_param:
                self.user.cuisines.append(param_value)
            elif item.string_content in price_param:
                self.user.prices.append(param_value)
            elif item.string_content in sort_param:
                self.user.sort_method = param_value
        else:
            if item.string_content in and_params:
                menu.user.and_filters.remove(param_value + "=true")
            elif item.string_content in cuisines_param:
                self.user.cuisines.remove(param_value)
            elif item.string_content in price_param:
                self.user.prices.remove(param_value)
            elif item.string_content in sort_param:
                self.user.sort_method = ""
        self.highlight_parent = menu.isHighlighted()


def main_loop(stdscr):
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
                user.prague_college = False
                user.search_param = "search-" + tui.search_name + \
                    "=" + tui.search_text
                menu_name = "Restaurants"
                tui.get_restaurants = True
                tui.search_submitted = False
                tui.search_text = None
        elif c == ord('?'):
            tui.print_help_menu()
            re_render = True
        elif c in (ord('p'), ord('P')):
            user.prague_college = True
            menu_name = "Prague college restaurants"
            tui.get_restaurants = True
        elif c in (ord('a'), ord('A')):
            user.prague_college = False
            tui.get_restaurants = True
            menu_name = "Restaurants"
        elif c in (ord('f'), ord('F')):
            tui.scroll_loop(tui.filters_menu, action=tui.toggle_item,
                            items_func=lambda: tui.filters)
            re_render = True
        elif c == curses.KEY_RESIZE:
            re_render = True
        if tui.displaying_error:
            tui.displaying_error = False
        else:
            tui.status = "Main menu"
        if tui.get_restaurants:
            menu = Menu(menu_name, user)
            tui.scroll_loop(menu, action=tui.restaurant_items_loop)
            re_render = True
            tui.get_restaurants = False
            user.search_param = None

        tui.render_home(render_all=re_render)
