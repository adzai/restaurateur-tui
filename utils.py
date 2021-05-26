import json
import re


def string_to_param(string):
    return string.replace(" ", "-").lower()


def get_restaurant_info(restaurant):
    try:
        restaurant["url"] = re.match(
            r"^.+?[^\/:](?=[?\/]|$)", restaurant["url"]).group(0)
    except Exception:
        pass
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"]
    items = []
    for key, value in restaurant.items():
        if value in (None, "", "null") or key in ('images', "id"):
            continue
        elif key == 'openingHours':
            sorted_days = dict()
            for day in days_of_week:
                sorted_days[day] = json.loads(value)[day]
            items.append("**Opening hours**")
            for k, v in sorted_days.items():
                items.append(k)
                items.append(v)
        else:
            # TODO: normalize keys
            start = key + ": "
            if isinstance(value, list):
                v = ", ".join(value)
                items.append(start + v)
            else:
                items.append(start + str(value))
    return items


def get_restaurant_names(data):
    return [restaurant["name"] for restaurant in data]
