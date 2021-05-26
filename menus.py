import curses


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
    def __init__(self, name, data, user, filters_menu=None):
        self.name = name
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

    def render_menu(self, stdscr, items, render_status_line):
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
        render_status_line()
        self.window.refresh()

    def get_currently_selected(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return self.data[i]

    def get_currently_selected_item(self):
        for i, item in enumerate(self.menu_items):
            if item.y == self.current_y + self.offset:
                return item, i
