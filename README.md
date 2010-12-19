# rss2mobi

Greg Hewgill  
http://hewgill.com

`rss2mobi` is a script that downloads new feeds from Google Reader and uses `kindlegen` to create a Mobipocket e-book output file.

## Requirements

- Python 3.1
- [`kindlegen`](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000234621)

## Configuration

Copy the supplied `rss2mobi.config.example` to `rss2mobi.config`.
Edit this file (it is in JSON format) and supply your Google Reader username and password.
If `kindlegen` is not in your `PATH`, set the full pathname of `kindlegen` here too.

## Usage

To run `rss2mobi`:

    python3.1 rss2mobi.py

The output file is `tmp/reader-YYYY-MM-DD.mobi` where `YYYY-MM-DD` is the current date.
