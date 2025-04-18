# Darknet Crawler

Enhanced crawler for .onion (darknet) sites using Tor network.

## Overview

This tool is a multi-threaded web crawler specifically designed for navigating and indexing .onion websites through the Tor network. It maintains a persistent database of discovered URLs and can handle authenticated sessions for accessing invite-only sites.

## Features

- **Tor Integration**: Routes all requests through Tor for anonymity and .onion site access
- **Multi-threaded**: Concurrent crawling with customizable thread count
- **Persistent Storage**: Saves all discovered URLs in an SQLite database
- **Rate Limiting**: Configurable delay between requests to avoid overloading servers
- **Authentication Support**: Can handle login forms for accessing protected areas
- **Optional Selenium**: Support for JavaScript-heavy sites using Firefox with Tor proxying
- **Resumable**: Can continue crawling from where it left off

## Requirements

- Python 3.6+
- Tor service running on localhost:9050
- Required Python packages:
  - requests
  - beautifulsoup4
  - PySocks
  - selenium (optional, for JavaScript support)

## Installation

1. Ensure Tor is installed and running:
   ```bash
   # Debian/Ubuntu
   sudo apt install tor
   sudo systemctl start tor
   
   # macOS (using Homebrew)
   brew install tor
   brew services start tor
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/Joieux/darknet-crawler.git
   cd darknet-crawler
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. If using Selenium (optional):
   - Install Firefox
   - Download [geckodriver](https://github.com/mozilla/geckodriver/releases)
   - Update `SELENIUM_DRIVER_PATH` in the script

## Usage

### Basic Usage

```bash
python darknet_crawler.py --seed http://somedarknetsite.onion
```

### With Custom Settings

```bash
python darknet_crawler.py \
  --seed http://somedarknetsite.onion \
  --delay 10 \
  --db custom_crawler.db \
  --threads 2
```

### Authenticated Crawling

```bash
python darknet_crawler.py \
  --seed http://somedarknetsite.onion \
  --login-url http://somedarknetsite.onion/login \
  --login-data username=myuser password=mypass
```

## Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--seed` | Starting URL (required) | - |
| `--delay` | Seconds between requests | 5 |
| `--db` | SQLite database path | crawler.db |
| `--threads` | Number of worker threads | 4 |
| `--login-url` | URL for authentication | - |
| `--login-data` | Key=value pairs for login form | - |

## Advanced Configuration

For more advanced settings, you can modify these variables in the script:

- `TOR_SOCKS_PROXY`: Tor proxy address
- `HEADERS`: HTTP headers for requests
- `USE_SELENIUM`: Enable/disable Selenium for JavaScript support
- `SELENIUM_DRIVER_PATH`: Path to geckodriver

## How It Works

1. The crawler starts with a seed URL and adds it to the queue.
2. Worker threads pull URLs from the queue and fetch their content.
3. New links found on pages are added to the database and queue if not seen before.
4. The process continues until the queue is empty or interrupted.
5. All discovered URLs are stored in the SQLite database for later analysis.

## Security Considerations

- All traffic is routed through Tor for anonymity
- The crawler respects delays between requests to avoid detection
- Custom User-Agent can be configured to avoid fingerprinting

## Troubleshooting

### Script Not Running

If you see errors like `import: command not found`:
```bash
# Make sure to run with Python
python3 ./darknet_crawler.py

# Or make the script executable
chmod +x ./darknet_crawler.py
./darknet_crawler.py
```

### Connection Issues

If the crawler can't connect to .onion sites:
```bash
# Check if Tor is running
systemctl status tor

# Verify SOCKS proxy is working
curl --socks5 127.0.0.1:9050 https://check.torproject.org
```

## Disclaimer

This tool is for research and educational purposes only. Users are responsible for ensuring compliance with applicable laws and regulations. The authors are not responsible for any misuse of this software.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.