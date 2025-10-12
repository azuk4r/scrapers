# ttdownloader
Requests-based scraper to download all posts (images and videos with no watermark) from a TikTok profile, [demo here](https://x.com/azuk4r/status/1963535850714575259)
### Arguments
| Argument | Description |
|----------|-------------|
| `profile_url` | TikTok profile URL (required) |
| `--download_path DOWNLOAD_PATH` | Custom directory to save media |
| `--proxy PROXY` | Optional proxy URL |
| `-h, --help` | Show help message and exit |
### Notes
- Easy to use, simply install the requirements.txt with `pip install -r requirements.txt`, preferably inside a virtual environment (you can create it with `python3 -m venv venv` and activate it with `source venv/bin/activate`)
- Supports http/s and socks5 proxies (in case you want to use it with Tor btw)
### Credits
Special thanks to [requests](https://github.com/psf/requests) because without this it would not have been possible, and above all to TikTok's "private" endpoints for being so accessible to nosy people like me! (with love). And of course, thanks to all the developers of the other modules I've used!
### Disclaimer
This is a tool for educational / personal use only — the author is not responsible for any misuse

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
