![Restaurateur TUI](https://github.com/adzai/restaurateur-tui/actions/workflows/restaurateur-tui.yml/badge.svg)
# Restaurateur TUI

Terminal frontend for [Restaurateur API](https://github.com/AgiliaErnis/restaurateur/tree/main/backend) 
written in python curses.

![tui-main-menu](https://user-images.githubusercontent.com/39188731/119695960-ff024f00-be4e-11eb-9214-6e5c1caa28bd.png)

![tui-pc-menu](https://user-images.githubusercontent.com/39188731/119696621-ae3f2600-be4f-11eb-8a77-cb810113523a.png)

![tui-filters](https://user-images.githubusercontent.com/39188731/119697157-31f91280-be50-11eb-8b4a-5e6c25064cae.png)

## Requirements

## Linux

* Python 3.8+

## Windows

* Python 3.8+
* `$ python -m pip install windows-curses`

## Run

`$ python restaurateur-tui.py`

If you want to specify your own backend (local build), you can use
`$ python restaurateur-tui.py --host "http://localhost:8080"`

## Functionality

* Search for a restaurant in Prague by name
* Search for a restaurant in Prague by address
* Search for all restaurants in Prague
* Search for restaurants around Prague college
* Apply various filters to your searches such as cuisines, vegetarian, vegan, price range etc.
* Adapts display on terminal resizing

## User manual

You can navigate the TUI via keyboard controls. If you are unsure
of the controls, you can press '?' at any point, which will bring up the 
keybinds.

If you want to reload your page to either reload new content
after changing your filter preferences or because of a visual
bug, you can pres 'r' at any time.

On the bottom of your screen there is a small status line
explaining what is happening on the screen.

To quit the current window (go back) you can press 'q' or 'esc'.

### Main menu

All of the keyboard shortcuts are highlighted in yellow and 
underlined. If you press the highlighted key (upper or lower case)
the described action will take place. 

If you press 'f', a list with filters will appear. Those are the
options you can toggle on or off (highlighted by changing the 
color to red) which will be applied to your restaurant search.
You can toggle the filters by pressing 'o' or 'enter'. If there
are subfilters behind the selected filter, like 'Cuisines', 
you will enter the cuisines filter where you can toggle the
individual items.


By pressing 's' you can toggle between searching based on a name, or based
on an address. If you'd like to type in the name or address,
you'll have to enter insert mode by pressing 'i'. After you are
done typing, you can press 'enter' to submit the search or 
'esc' to abort.

To search for restaurants around Prague college with
currently applied filters, press 'p'. You can do the same
for all restaurants around Prague by pressing 'a'.

### Menus

Once you are in a menu, you can scroll through the items with
'j' and 'k' or with your arrow keys. To open a selected item, 
press 'o' or 'enter' and additional content will be displayed,
if there's any. If you see '...' at the end of the line, it 
means that the text had to be truncated to fit on the line. 
You can display the rest by pressing 'o' or 'enter'. 
If you see '...' after resizing and the text didn't expand 
back to original, press 'r' to reload. When in the restaurants
scroll menu, you can apply/remove filters by pressing 'f' and
reload the restaurants based on new preferences by pressing 'r'.


## Disclaimers

* This is just a demo showcasing a possibility of using different frontends for the [Restaurateur API](https://github.com/AgiliaErnis/restaurateur/tree/main/backend) and as such offers limited functionality and isn't very polished
* The user experience may be affected by your terminal and terminal font of choice
