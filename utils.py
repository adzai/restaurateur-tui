import json
import re


def string_to_param(string):
    return string.replace(" ", "-").lower()


def key_to_words(key):
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', key)
    if key == "url":
        return "URL"
    if len(words) > 0:
        words[0] = words[0].capitalize()
        words[1:] = map(lambda word: word.lower(), words[1:])
    return " ".join(words)


def get_restaurant_info(restaurant):
    try:
        restaurant["url"] = re.match(
            r"^.+?[^\/:](?=[?\/]|$)", restaurant["url"]).group(0)
    except Exception:
        pass
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"]
    items = []
    keys_to_skip = ["images", "id", "menuValidUntil"]
    values_to_skip = [None, "", "null"]
    for key, value in restaurant.items():
        if value in values_to_skip or key in keys_to_skip:
            continue
        word_key = key_to_words(key)
        if key == 'openingHours':
            sorted_days = dict()
            for day in days_of_week:
                sorted_days[day] = json.loads(value)[day]
            items.append("**Opening hours**")
            for k, v in sorted_days.items():
                items.append(k)
                items.append(v)
        elif key == 'distance':
            if value != 0:
                items.append(
                    f"{word_key}: {round(value)}m from Prague College")
        else:
            start = word_key + ": "
            if isinstance(value, list):
                v = ", ".join(value)
                items.append(start + v)
            else:
                items.append(start + str(value))
    return items


def get_restaurant_names(data):
    return [restaurant["name"] for restaurant in data]
