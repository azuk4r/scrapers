# igdownloader
Selenium-based scraper that downloads all posts (images and videos) from an Instagram profile, [demo here](https://x.com/azuk4r/status/1944466277986398370)
### Arguments
| Argument | Description |
|----------|-------------|
| `--profile_url PROFILE_URL` | Instagram profile URL (required) |
| `--cookies COOKIES` | Path to cookies JSON file |
| `--proxy PROXY` | Proxy with auth: `http://user:pass@ip:port` |
| `--output OUTPUT` | Custom path directory for results |
| `--debug` | Enable debug mode |
| `-h, --help` | Show help message and exit |
### Notes
- Make sure **FFmpeg** is installed
- The proxy argument configures the browser proxy extension and requests. If you want to configure proxy for FFmpeg also (recommended), you have to configure your environment variables. In Linux it would be done this way:
  ```bash
  export HTTP_PROXY=http://username:password@ip:port
  export HTTPS_PROXY=http://username:password@ip:port
  export NO_PROXY=localhost,127.0.0.1,::1
  ```
- The stealth covers almost all leaks, but if you are going to use this with multiple accounts worry about the WebGL image hash btw
- Some descriptions cannot be obtained if the window is not maximized
### Credits
This tool relies on [FFmpeg](https://github.com/FFmpeg/FFmpeg) (via [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)), [selenium](https://github.com/SeleniumHQ/selenium), [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) and [requests](https://github.com/psf/requests) — thanks to all their developers!
### Disclaimer
This is a tool for educational / personal use only — the author is not responsible for any misuse
### PoW
###### 5625 NASA instagram pics collage
![nasa_collage](nasa_collage.jpeg)
