# lunchbot

[![Build Status](https://travis-ci.org/hugovk/lunchbot.svg?branch=master)](https://travis-ci.org/hugovk/lunchbot)
[![Python: 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Check what's for lunch at local restaurants and post to Slack

## Setup

```bash
pip install --upgrade -r requirements.txt
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
```bash
!/bin/bash

export PATH=/usr/local/bin:$PATH
export LUNCHBOT_TOKEN="TODO_ENTER_YOURS"

python /path/to/lunchbot.py >> /tmp/lunchbot.log 2>&1
```

And then run `crontab -e` and add this to post at 11:30am every workday (days 1-5):
```
30 11 * * 1-5 /path/to/lunchbot.sh
```
