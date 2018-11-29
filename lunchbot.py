#!/usr/bin/env python
# encoding: utf-8
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
import os
import random
import traceback
from urllib.request import urlopen

from bs4 import BeautifulSoup  # pip install BeautifulSoup4 lxml

# from pprint import pprint


BANK_URL = "http://www.ravintolabank.fi/en/lunch-club-en/"
KAARTI_URL = "http://www.ravintolakaarti.fi/lounas"
KUUKUU_URL = "https://www.kuukuu.fi/fi/lounas"
PIHKA_URL = "https://kasarmi.pihka.fi/en/"
SAVEL_URL = "http://toolonsavel.fi/menu/?lang=fi#lounas"
SOGNO_URL = "http://www.trattoriasogno.fi/lounas"

# RESTAURANTS = ["kaarti", "kuukuu", "savel", "sogno"]
RESTAURANTS = ["bank", "pihka"]

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


def day_name_en(day_number):
    """Return the English day name for this day number"""
    return calendar.day_name[day_number]


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
    """
    Get the lunch menu from Bank
    """
    url = BANK_URL
    soup = get_soup(url)

    # Weekly menu is in <div class="lunch-list">
    weekly_menu = soup.find("div", class_="lunch-list")

    # Daily menu is in <div class="lunch lunch_monday">
    today_class_name = f"lunch_{today_en.lower()}"
    todays_menu_div = weekly_menu.find("div", class_=today_class_name)

    # Remove empty newlines
    menu_text = todays_menu_div.get_text().strip().split("\n")
    menu_text = list(filter(None, menu_text))

    todays_menu = ["", f":ravintolabank: Bank {url}", ""]
    todays_menu.extend(menu_text)
    todays_menu.append("*Rush hour: 11:30*")

    return "\n".join(todays_menu)


def lunch_kaarti():
    """
    Get the lunch menu from Kaarti
    """
    url = KAARTI_URL
    soup = get_soup(url)

    # Weekly menu is in <div id="column1Content"><div class>
    weekly_menu = soup.find("div", id="column1Content")
    children = weekly_menu.findAll("p")
    todays_menu = ["", f":kaarti: Kaarti {url}", ""]

    # Get today's menu
    kaarti_menu = get_submenu(children, today_fi, tomorrow_fi)

    # Switch SHOUTY ALL CAPS to Sentence case
    kaarti_menu = [line.capitalize() for line in kaarti_menu]

    todays_menu.extend(kaarti_menu)

    return "\n".join(todays_menu)


def lunch_kuukuu():
    """
    Get the lunch menu from KuuKuu
    """
    url = KUUKUU_URL
    soup = get_soup(url)

    # Weekly menu is in the second <section>
    weekly_menu = soup.findAll("section")[1]

    children = weekly_menu.findAll("p")
    todays_menu = ["", f":kuukuu: KuuKuu {url}", ""]

    # Get today's menu
    todays_menu.extend(get_submenu(children, today_fi, tomorrow_fi))

    return "\n".join(todays_menu)


def lunch_pihka():
    """
    Get the lunch menu from Pihka
    """
    url = PIHKA_URL
    soup = get_soup(url)

    # Weekly menu is in <div id="primary">
    weekly_menu = soup.find("div", id="primary")
    children = weekly_menu.find_all("div", class_="menu-day")

    todays_menu = ["", f":pihka: Pihka {url}", ""]
    print(today_en, tomorrow_en)

    # Get today's menu
    menu_text = get_submenu(children, today_en, tomorrow_en)[0]
    menu_text = menu_text.replace("\n\n\n", "\n\n")
    todays_menu.append(menu_text)

    return "\n".join(todays_menu)


def lunch_savel():
    """
    Get the lunch menu from Sävel
    """
    url = SAVEL_URL
    soup = get_soup(url)

    # Weekly menu is in <div id="cL">
    weekly_menu = soup.find("div", class_="menu-box")
    weekly_menu = weekly_menu.find("div", class_="wysiwyg")
    children = weekly_menu.findChildren()
    todays_menu = ["", f":savel: Sävel {url}", ""]

    # Get the stuff before Monday: weekly burger
    todays_menu.extend(get_submenu(children, "viikon burgerit:", monday))
    todays_menu.append("")

    # Get today's menu
    todays_menu.extend(get_submenu(children, today_fi, tomorrow_fi))

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
    todays_menu = ["", f":sogno: Sogno {url}", ""]

    # Get today's menu
    todays_menu.extend(get_submenu(children, today_fi, tomorrow_fi))

    return "\n".join(todays_menu)


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
        "-u", "--user", help="Send to this Slack user instead of the lunch channel"
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Don't post to Slack"
    )
    args = parser.parse_args()

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

    for restaurant in restaurants:

        try:
            # Call function from a string
            function = "lunch_" + restaurant
            # Like calling lunch_savel()
            menu = locals()[function]()

        except AttributeError:
            print(restaurant)
            traceback.print_exc()
            continue

        print(menu)

        # Escape ' like in "Pasta all'amatriciana" by
        # replacing ' with '"'"'
        # https://stackoverflow.com/a/1250279/724176
        menu = menu.replace("'", "'\"'\"'")

        if not args.dry_run:

            if args.user:
                target = f"-u {args.user}"
            else:
                target = "-c lunch"

            slacker_cmd = ("slacker -t $LUNCHBOT_TOKEN -n LunchBot -i {} {}").format(
                random.choice(EMOJI), target
            )
            # print(slacker_cmd)

            cmd = f"echo '{menu}' | {slacker_cmd}"
            # print(cmd.encode("utf8"))
            os.system(cmd)

# End of file
