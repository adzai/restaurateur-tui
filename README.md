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


## Disclaimers

* This is just a demo showcasing a possibility of using different frontends for the [Restaurateur API](https://github.com/AgiliaErnis/restaurateur/tree/main/backend) and as such offers limited functionality and isn't very polished
* The user experience may be affected by your terminal and terminal font of choice
