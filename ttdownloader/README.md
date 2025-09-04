# ttdownloader
Requests-based scraper to download all posts (images and videos) from a TikTok profile, [demo here](https://x.com/azuk4r/status/1963535850714575259)
### Arguments
| Argument | Description |
|----------|-------------|
| `profile_url` | tiktok profile url (required) |
| `--download_path DOWNLOAD_PATH` | custom directory to save media |
| `--proxy PROXY` | optional proxy url |
| `-h, --help` | show help message and exit |
### Notes
- Easy to use, simply install the requirements.txt with `pip install -r requirements.txt`, preferably inside a virtual environment (you can create it with `python3 -m venv venv` and activate it with `source venv/bin/activate`)
- Supports http/s and socks5 proxies (in case you want to use it with Tor btw)
### Credits
Special thanks to [requests](https://github.com/psf/requests) because without this it would not have been possible, and above all to TikTok's "private" endpoints for being so accessible to nosy people like me! (with love). And of course, thanks to all the developers of the other modules I've used!
### Disclaimer
This is a tool for educational / personal use only — the author is not responsible for any misuse
