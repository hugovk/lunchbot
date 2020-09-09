#!/usr/bin/env python
"""
Check what's for lunch at local restaurants and post to Slack

Prerequisites for posting to Slack:
pip install slacker-cli
Get a Slack token and save it in LUNCHBOT_TOKEN the environment variable
See: https://github.com/juanpabloaj/slacker-cli#tokens
"""
import argparse
import calendar
import datetime
import hashlib
import json
import os
import random
import traceback
import urllib
from pprint import pprint  # noqa: F401

from bs4 import BeautifulSoup  # pip install BeautifulSoup4 lxml
from requests_html import HTMLSession  # pip install requests-html

KAARTI_URL = "http://www.ravintolakaarti.fi/lounas"
KUUKUU_URL = "https://www.kuukuu.fi/fi/lounas"
LOUNAAT_URL = "https://www.lounaat.info/kasarmikatu-42-00130-helsinki"
LOUNAAT_PASILA_URLS = {
    "Viherlatva": "https://www.lounaat.info/lounas/amica-viherlatva/helsinki",
    "Antell Akavatalo": "https://www.lounaat.info/lounas/antell-akavatalo/helsinki",
    "Factory Vallila": "https://www.lounaat.info/lounas/factory-vallila/helsinki",
    "Savor Vallila": "https://www.lounaat.info/lounas/savor-vallila/helsinki",
}

SAVEL_URL = "http://toolonsavel.fi/menu/?lang=fi#lounas"
SOGNO_URL = "http://www.trattoriasogno.fi/lounas"

KASSU = [
    "bank",
    "block-by-dylan",
    "cock",
    "factory-aleksi",
    "paisano",
    "pompier",
    "presto",
]
PASILA = [
    "antell-akavatalo",
    "factory-vallila",
    "savor-vallila",
    "viherlatva",
]
RESTAURANTS = KASSU + PASILA

EMOJI = [
    ":fork_and_knife:",
    ":pizza:",
    ":hamburger:",
    ":fries:",
    ":poultry_leg:",
    ":meat_on_bone:",
    ":spaghetti:",
    ":curry:",
    ":fried_shrimp:",
    ":bento:",
    ":sushi:",
    ":fish_cake:",
    ":rice_ball:",
    ":rice_cracker:",
    ":rice:",
    ":ramen:",
    ":stew:",
    ":oden:",
    ":dango:",
    ":egg:",
    ":bread:",
    ":doughnut:",
    ":custard:",
    ":icecream:",
    ":ice_cream:",
    ":shaved_ice:",
    ":birthday:",
    ":cake:",
    ":cookie:",
    ":chocolate_bar:",
    ":candy:",
    ":lollipop:",
    ":honey_pot:",
    ":apple:",
    ":green_apple:",
    ":tangerine:",
    ":lemon:",
    ":cherries:",
    ":grapes:",
    ":watermelon:",
    ":strawberry:",
    ":peach:",
    ":melon:",
    ":banana:",
    ":pear:",
    ":pineapple:",
    ":sweet_potato:",
    ":eggplant:",
    ":tomato:",
    ":corn:",
]

LOUNAAT_RESPONSE = None


def pause(reopen_date):
    """Return true if before this yyyy-mm-dd date"""
    reopen_date = datetime.datetime.strptime(reopen_date, "%Y-%m-%d")
    now = datetime.datetime.now()
    return now.date() < reopen_date.date()


def day_name_fi(day_number):
    """Return the Finnish day name for this day number"""
    # Could use locale, but it's a bit fiddly depending on Mac/Windows
    # and we only have one language
    if day_number == 0:
        return "maanantai"
    elif day_number == 1:
        return "tiistai"
    elif day_number == 2:
        return "keskiviikko"
    elif day_number == 3:
        return "torstai"
    elif day_number == 4:
        return "perjantai"
    elif day_number == 5:
        return "lauantai"
    elif day_number == 6:
        return "sunnuntai"


def dopplr(name):
    """
    Take the MD5 digest of a name,
    convert it to hex and take the
    first 6 characters as an RGB value.
    """
    return "#" + hashlib.sha224(name.encode()).hexdigest()[:6]


def squeeze(char, text):
    """Replace repeated characters with a single one
    https://stackoverflow.com/a/3878698/724176
    """
    while char * 2 in text:
        text = text.replace(char * 2, char)
    return text


def day_name_en(day_number):
    """Return the English day name for this day number"""
    return calendar.day_name[day_number]


def get_soup(url):
    """Not that kind"""
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page.read(), "lxml")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    # pprint(soup)
    return soup


def get_submenu(children, start, end):
    """Given a list of HTML,
    go through each element,
    start grabbing from the one containing start text,
    and stop at the one with end text
    """
    submenu = []
    started = False
    for child in children:

        child_text = child.get_text()

        if "Lounas maanantaista perjantaihin" in child_text:
            # Ignore this bit
            continue

        if child_text:
            if start.lower() in child_text.lower():
                started = True
            if started and end.lower() in child_text.lower():
                break

            if started:
                if not submenu or submenu[-1] != child_text:  # No duplicates
                    submenu.append(child_text)

    return submenu


def lunch_bank():
    return lunch_lounaat("Bank Lunch Club")


def lunch_block_by_dylan():
    return lunch_lounaat("Block by Dylan")


def lunch_cock():
    if pause("2019-08-12"):
        return None
    return lunch_lounaat("The Cock")


def lunch_factory_aleksi():
    return lunch_lounaat("Factory Aleksi")


def lunch_kaarti():
    """
    Get the lunch menu from Kaarti
    """
    title = "Kaarti"
    emoji = ":kaarti:"
    url = KAARTI_URL
    soup = get_soup(url)

    # Weekly menu is in <div id="column1Content"><div class>
    weekly_menu = soup.find("div", id="column1Content")
    children = weekly_menu.findAll("p")
    todays_menu = []

    # Get today's menu
    kaarti_menu = get_submenu(children, today_fi, tomorrow_fi)

    # Switch SHOUTY ALL CAPS to Sentence case
    kaarti_menu = [line.capitalize() for line in kaarti_menu]

    todays_menu.extend(kaarti_menu)

    return title, emoji, "\n".join(todays_menu), url


def lunch_kuukuu():
    """
    Get the lunch menu from KuuKuu
    """
    title = "KuuKuu"
    emoji = ":kuukuu:"
    url = KUUKUU_URL
    soup = get_soup(url)

    # Weekly menu is in the second <section>
    weekly_menu = soup.findAll("section")[1]

    children = weekly_menu.findAll("p")
    todays_menu = []

    # Get today's menu
    todays_menu.extend(get_submenu(children, today_fi, tomorrow_fi))

    return title, emoji, "\n".join(todays_menu), url


def lunch_paisano():
    """
    Get the lunch menu from Paisano
    """
    return lunch_lounaat("Paisano")


def lunch_savel():
    """
    Get the lunch menu from Sävel
    """
    title = "Sävel"
    emoji = ":savel:"
    url = SAVEL_URL
    soup = get_soup(url)

    # Weekly menu is in <div id="cL">
    weekly_menu = soup.find("div", class_="menu-box")
    weekly_menu = weekly_menu.find("div", class_="wysiwyg")
    children = weekly_menu.findChildren()
    todays_menu = []

    # Get the stuff before Monday: weekly burger
    todays_menu.extend(get_submenu(children, "viikon burgerit:", monday))
    todays_menu.append("")

    # Get today's menu
    todays_menu.extend(get_submenu(children, today_fi, tomorrow_fi))

    return title, emoji, "\n".join(todays_menu), url


def lunch_sogno():
    """
    Get the lunch menu from Sogno
    """
    title = "Sogno"
    emoji = ":sogno:"
    url = SOGNO_URL
    soup = get_soup(url)

    # Weekly menu is in <div class="mainTextWidgetContent">
    weekly_menu = soup.find("div", class_="mainTextWidgetContent")
    children = weekly_menu.findAll("p")
    todays_menu = []

    # Get today's menu
    todays_menu.extend(get_submenu(children, today_fi, tomorrow_fi))

    return title, emoji, "\n".join(todays_menu), url


def lunch_pompier():
    return lunch_lounaat("Pompier Espa")


def lunch_presto():
    if pause("2019-07-01"):
        return None
    return lunch_lounaat("Presto")


def lunch_lounaat(restaurant):
    """
    :param restaurant
    :return: lunch menu
    Get the lunch for a restaurant from Lounaat.info
    """
    global LOUNAAT_RESPONSE

    if not LOUNAAT_RESPONSE:
        # Requests-HTML is easier than Requests + Beautiful Soup
        session = HTMLSession()
        LOUNAAT_RESPONSE = session.get(LOUNAAT_URL)

    element = LOUNAAT_RESPONSE.html.find("div.menu", containing=restaurant, first=True)

    path = element.find("h3 a")[0].attrs["href"]  # eg. '/lounas/presto/helsinki'
    url = f"https://www.lounaat.info{path}"

    emoji = f':{restaurant.replace(" ", "")}:'
    title = restaurant

    todays_menu = []
    opening_hours = element.find("p.lunch", first=True).text
    item_body = element.find("div.item-body", first=True).text
    item_footer = element.find("div.item-footer", first=True).text
    todays_menu.append(item_body)
    todays_menu.append(opening_hours + " " + item_footer)

    return title, emoji, "\n".join(todays_menu), url


# Pasila
def lunch_factory_vallila():
    return lunch_pasila("Factory Vallila")


def lunch_viherlatva():
    return lunch_pasila("Viherlatva")


def lunch_savor_vallila():
    return lunch_pasila("Savor Vallila")


def lunch_antell_akavatalo():
    return lunch_pasila("Antell Akavatalo")


def lunch_pasila(restaurant):
    PASILA_LOUNAAT_RESPONSE = None

    url = LOUNAAT_PASILA_URLS[restaurant]

    if not PASILA_LOUNAAT_RESPONSE:
        # Requests-HTML is easier than Requests + Beautiful Soup
        session = HTMLSession()
        PASILA_LOUNAAT_RESPONSE = session.get(url)

    today_number = datetime.datetime.today().weekday()
    element = PASILA_LOUNAAT_RESPONSE.html.find(
        "div.item", containing=day_name_fi(today_number), first=True
    )

    emoji = f':{restaurant.replace(" ", "")}:'
    title = restaurant

    todays_menu = []
    opening_hours = PASILA_LOUNAAT_RESPONSE.html.find(
        "div.tile", containing="ma-", first=True
    ).text
    item_body = element.find("div.item-body", first=True).text
    item_footer = element.find("div.item-footer", first=True).text
    todays_menu.append(item_body)
    todays_menu.append(opening_hours + " " + item_footer)

    return title, emoji, "\n".join(todays_menu), url


def do_restaurant(restaurant_name, restaurant_function, dry_run, target):
    """Get the menu for a restaurant and post to Slack"""
    output = {}
    try:
        ret = restaurant_function()
        if ret is None:
            print("Skip", restaurant_function.__name__)
            return
        title, emoji, menu, url = ret
    except AttributeError:
        print(restaurant_function.__name__)
        traceback.print_exc()
        return

    # Remove &nbsp; chars
    menu = menu.replace("\xa0", "")
    # Squeeze out repeated newlines
    menu = squeeze("\n", menu)

    output["title"] = title
    output["menu"] = menu
    output["url"] = url

    # Escape ' like in "Pasta all'amatriciana" by
    # replacing ' with '"'"'
    # https://stackoverflow.com/a/1250279/724176
    menu = menu.replace("'", "'\"'\"'")

    menu += f"\n{url}"
    print(emoji, title)
    print(menu)
    print()

    colour = dopplr(restaurant_name)
    attachment = [
        {"color": colour, "fields": [{"title": f"{emoji} {title}", "value": menu}]}
    ]
    attachments = f"attachments='{json.dumps(attachment)}'"

    if not dry_run:

        slacker_cmd = ("slacker -t $LUNCHBOT_TOKEN -n LunchBot -i {} {} {}").format(
            random.choice(EMOJI), target, attachments
        )
        # print(slacker_cmd)

        cmd = f"echo '' | {slacker_cmd}"
        # print(cmd.encode("utf8"))
        os.system(cmd)

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Post what's for lunch at local restaurants to Slack",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-r",
        "--restaurants",
        choices=["all"] + RESTAURANTS,
        default=["all"],
        nargs="+",
        help="Which restaurants to check",
    )
    parser.add_argument(
        "--kassu", action="store_true", help="Shortcut for the restaurants near Kassu"
    )
    parser.add_argument(
        "--pasila", action="store_true", help="Shortcut for the restaurants in Pasila"
    )
    parser.add_argument(
        "-u", "--user", help="Send to this Slack user instead of #lunch"
    )
    parser.add_argument(
        "-c", "--channel", help="Send to this Slack channel instead of #lunch"
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Don't post to Slack"
    )
    parser.add_argument("-j", "--json", action="store_true", help="Save data as JSON")
    args = parser.parse_args()
    print(args)

    if args.kassu:
        args.restaurants = KASSU
    elif args.pasila:
        args.restaurants = PASILA

    # Get Monday, today and tomorrow in Finnish
    today_number = datetime.datetime.today().weekday()
    monday = day_name_fi(0)
    today_fi = day_name_fi(today_number)
    if today_number == 4:
        tomorrow_number = 0  # Monday
    else:
        tomorrow_number = today_number + 1
    tomorrow_fi = day_name_fi(tomorrow_number).lower()

    # Get today and tomorrow in English
    today_en = day_name_en(today_number)
    tomorrow_en = day_name_en(tomorrow_number)

    if args.restaurants == ["all"]:
        restaurants = RESTAURANTS
    else:
        restaurants = args.restaurants
    random.shuffle(restaurants)

    if args.user:
        target = f"-u {args.user}"
    if args.channel:
        target = f"-c {args.channel}"
    else:
        target = "-c lunch"

    all_output = {}
    all_output["menus"] = []
    for restaurant in restaurants:

        # Call function from a string
        function = "lunch_" + restaurant.replace("-", "_")
        # Like getting lunch_savel()
        restaurant_function = locals()[function]

        tries = 0
        while tries < 3:
            tries += 1
            try:
                output = do_restaurant(
                    restaurant, restaurant_function, args.dry_run, target
                )
                all_output["menus"].append(output)
                break
            except urllib.error.HTTPError as e:
                print(e)

    if args.json:
        all_output["updated"] = datetime.datetime.utcnow().strftime(
            "%A, %d %B %Y, %X UTC"
        )
        with open("lunch.json", "w") as outfile:
            json.dump(all_output, outfile)


# End of file
