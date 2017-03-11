# lunchbot

[![Build Status](https://travis-ci.org/hugovk/lunchbot.svg?branch=master)](https://travis-ci.org/hugovk/lunchbot)

Check what's for lunch at local restaurants and post to Slack

## Setup

```bash
pip install BeautifulSoup4 lxml slacker-cli

```

To post to Slack, get a [token](https://github.com/juanpabloaj/slacker-cli#tokens) and save it in the `LUNCHBOT_TOKEN` environment variable.

## Usage

```bash
# Just print out but don't post
python lunchbot.py --dry-run

# Post to #lunch channel
python lunchbot.py

# For testing, post to some username instead of the #lunch channel
python lunchbot.py --user username
