#!/usr/bin/env python
# encoding: utf-8
"""
Check what's for lunch at local restaurants and post to Slack

Prerequisites for posting to Slack:
pip install slacker-cli
Get a Slack token and save it in LUNCHBOT_TOKEN the environment variable
See: https://github.com/juanpabloaj/slacker-cli#tokens
"""
from __future__ import print_function, unicode_literals
from bs4 import BeautifulSoup  # pip install BeautifulSoup4 lxml
import argparse
import datetime
import os
import random
try:
    # Python 2
    from urllib2 import urlopen
except ImportError:
    # Python 3
    from urllib.request import urlopen

# from pprint import pprint


KAARTI_URL = "http://www.ravintolakaarti.fi/lounas"
SAVEL_URL = "http://toolonsavel.fi/index.php?page=lounas&lang=fi"
SOGNO_URL = "http://www.trattoriasogno.fi/lounas"

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


def day_name(day_number):
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


def get_soup(url):
    """Not that kind"""
    page = urlopen(url)
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

        if child_text:
            if start in child_text.lower():
                started = True
            if started and end in child_text.lower():
                break

            if started:
                submenu.append(child_text)

    return submenu


def lunch_kaarti():
    """
    Get the lunch menu from Kaarti
    """
    url = KAARTI_URL
    soup = get_soup(url)

    # Weekly menu is in <div id="column1Content"><div class>
    weekly_menu = soup.find("div", id="column1Content")
    children = weekly_menu.findAll("p")
    todays_menu = ["", ":kaarti: Kaarti {}".format(url), ""]

    # Get today's menu
    kaarti_menu = get_submenu(children, today, tomorrow)

    # Switch SHOUTY ALL CAPS to Sentence case
    kaarti_menu = [line.capitalize() for line in kaarti_menu]

    todays_menu.extend(kaarti_menu)

    return "\n".join(todays_menu)


def lunch_savel():
    """
    Get the lunch menu from Sävel
    """
    url = SAVEL_URL
    soup = get_soup(url)

    # Weekly menu is in <div id="cL">
    weekly_menu = soup.find("div", id="cL")
    children = weekly_menu.findChildren()
    todays_menu = ["", ":savel: Sävel {}".format(url), ""]

    # Get the stuff before Monday: weekly burger
    todays_menu.extend(get_submenu(children, "viikon burgerit", monday+":"))
    todays_menu.append("")

    # Get today's menu
    todays_menu.extend(get_submenu(children, today+":", tomorrow+":"))

    return "\n".join(todays_menu)


def lunch_sogno():
    """
    Get the lunch menu from Sogno
    """
    url = SOGNO_URL
    soup = get_soup(url)

    # Weekly menu is in <div class="mainTextWidgetContent">
    weekly_menu = soup.find("div", class_="mainTextWidgetContent")
    children = weekly_menu.findAll("p")
    todays_menu = ["", ":sogno: Sogno {}".format(url), ""]

    # Get today's menu
    todays_menu.extend(get_submenu(children, today, tomorrow))

    return "\n".join(todays_menu)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Post what's for lunch at local restaurants to Slack",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-u", "--user",
        help="Send to this Slack user instead of the lunch channel")
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Don't post to Slack")
    args = parser.parse_args()

    # Get Monday, today and tomorrow in Finnish
    today_number = datetime.datetime.today().weekday()
    monday = day_name(0)
    today = day_name(today_number)
    if today_number == 4:
        tomorrow_number = 0  # Monday
    else:
        tomorrow_number = today_number + 1
    tomorrow = day_name(tomorrow_number).lower()

    restaurants = ["kaarti", "savel", "sogno"]
    random.shuffle(restaurants)

    for restaurant in restaurants:

        if restaurant == "kaarti":
            menu = lunch_kaarti()
        elif restaurant == "savel":
            menu = lunch_savel()
        elif restaurant == "sogno":
            menu = lunch_sogno()

        print(menu.encode("utf8"))

        # Escape ' like in "Pasta all'amatriciana" by
        # replacing ' with '"'"'
        # https://stackoverflow.com/a/1250279/724176
        menu = menu.replace("'", "'\"'\"'")

        if not args.dry_run:

            if args.user:
                target = "-u {}".format(args.user)
            else:
                target = "-c lunch"

            slacker_cmd = (
                "slacker -t $LUNCHBOT_TOKEN -n LunchBot -i {} {}"
                ).format(random.choice(EMOJI), target)
            # print(slacker_cmd)

            cmd = "echo '{}' | {}".format(menu, slacker_cmd)
            # print(cmd.encode("utf8"))
            os.system(cmd.encode("utf8"))

# End of file
