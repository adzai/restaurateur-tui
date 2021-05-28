import argparse

parser = argparse.ArgumentParser(
    description='Restaurateur TUI')
parser.add_argument('--host', help="Provide restaurateur API host URL")
args = parser.parse_args()

BASE_URL = args.host if args.host else "https://api.restaurateur.tech"


class User:
    def __init__(self):
        self.and_filters = []
        self.search_param = None
        self.cuisines = []
        self.prices = []
        self.sort_method = ""
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
        if self.sort_method != "":
            all_filters.append("sort=" + self.sort_method)
        return url + "&".join(all_filters)
