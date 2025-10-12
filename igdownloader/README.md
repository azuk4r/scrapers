# igdownloader
Selenium-based scraper that downloads all posts (images and videos) from an Instagram profile, [demo here](https://x.com/azuk4r/status/1944466277986398370)
### Arguments
| Argument | Description |
|----------|-------------|
| `--profile_url PROFILE_URL` | Instagram profile URL (required) |
| `--cookies COOKIES` | Path to cookies JSON file |
| `--proxy PROXY` | Proxy URL |
| `--output OUTPUT` | Custom path directory for results |
| `--debug` | Enable debug mode |
| `-h, --help` | Show help message and exit |
### Notes
- Make sure **FFmpeg** is installed
- The proxy argument configures selenium and requests. If you want to configure proxy for FFmpeg also (recommended), you have to configure your environment variables. In Linux it would be done this way:
  ```bash
  export HTTP_PROXY=http://username:password@ip:port
  export HTTPS_PROXY=http://username:password@ip:port
  export NO_PROXY=localhost,127.0.0.1,::1
  ```
- Currently the tool has no support for proxies with authentication for selenium (it will only use them for requests)
- The stealth covers almost all leaks, but if you are going to use this with multiple accounts worry about the WebGL fingerprinting
- Some descriptions cannot be obtained if the window is not maximized
### PoW
###### 5625 NASA instagram pics collage
![nasa_collage](nasa_collage.jpeg)
### Credits
This tool relies on [selenium](https://github.com/SeleniumHQ/selenium), [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager), [requests](https://github.com/psf/requests) and [FFmpeg](https://github.com/FFmpeg/FFmpeg) (via [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)) — thanks to all their developers!
### Disclaimer
This is a tool for educational / personal use only — the author is not responsible for any misuse

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
