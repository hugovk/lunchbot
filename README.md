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
```

## Cron

For regular posting, you can use something like cron. For example, create /path/to/lunchbot.sh:
```
!/bin/bash

export PATH=/usr/local/bin:$PATH
export LUNCHBOT_TOKEN="TODO_ENTER_YOURS"

python /path/to/lunchbot.py >> /tmp/lunchbot.log 2>&1
```

And then run `crontab -e` and add this to post at 11:30am every workday (days 1-5):
```
30 11 * * 1-5 /path/to/lunchbot.sh
```
