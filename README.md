# Telegram Weather Bot

A robust Telegram bot built for reliability and efficiency. Provides weather data and occasional humor through a clean, well-architected codebase.

## What It Does

The bot handles three core functions:
- **Weather queries**: Real-time weather data for any city
- **Random jokes**: Dad jokes from a reliable API source  
- **User onboarding**: Clean welcome experience

Built to handle production load with proper error handling, rate limiting, and security measures.

## Architecture

```
telegram-bot/
├── src/
│   ├── config/           # Configuration management
│   ├── bot/
│   │   ├── handlers/     # Command processing logic
│   │   ├── services/     # External API integrations
│   │   ├── utils/        # Validation and formatting
│   │   └── bot_application.py
│   └── main.py
├── tests/                # Comprehensive test suite
├── requirements.txt      # Dependencies
├── Dockerfile           # Container deployment
└── docker-compose.yml  # Local development
```

This structure eliminates common issues I've seen in other bots: mixed concerns, poor error handling, and configuration scattered throughout the codebase.

## Setup

### Prerequisites

You'll need:
- Python 3.11+
- [Telegram bot token](https://t.me/botfather)
- [OpenWeatherMap API key](https://openweathermap.org/api) (free tier works fine)

### Local Development

```bash
git clone <repository-url>
cd telegram-bot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API credentials
```

### Configuration

Set these environment variables in your `.env`:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENWEATHER_API_KEY=your_weather_api_key_here
DEBUG=True
LOG_LEVEL=INFO
```

### Run

```bash
python src/main.py
```

The bot automatically detects development mode and uses polling. Production deployments use webhooks.

## Production Deployment

### Heroku (Recommended)

```bash
heroku create your-bot-name
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set OPENWEATHER_API_KEY=your_key
heroku config:set HEROKU_APP_NAME=your-bot-name

git push heroku main
heroku ps:scale web=1
```

Monitor with `heroku logs --tail`

### Docker

```bash
docker build -t telegram-bot .
docker run --env-file .env -p 8443:8443 telegram-bot
```

Or use docker-compose for local development:
```bash
docker-compose up --build
```

### Other Platforms

The bot works on any platform supporting Python web applications:
- Railway: `railway up`
- Render: Connect GitHub repo, configure environment variables
- DigitalOcean App Platform: Deploy from GitHub

## Key Features

### Error Handling
Every external API call is wrapped with proper timeout, retry logic, and user-friendly error messages. The bot doesn't crash when APIs are down.

### Security
- Input validation on all user commands
- Rate limiting (20 requests/minute per user)
- No storage of personal data
- Injection attempt detection

### Performance
- HTTP connection pooling
- Async operations throughout
- Circuit breaker pattern for API failures
- Minimal memory footprint (~50MB)

### Monitoring
- Structured logging
- Health checks for container orchestration
- Performance metrics tracking

## Testing

```bash
pip install -r requirements-dev.txt
pytest                          # Run all tests
pytest --cov=src               # With coverage report
pytest -m "not slow"           # Skip integration tests
```

Test coverage is maintained above 80%. Tests use proper mocking for external dependencies.

## API Rate Limits

The bot respects API limitations:
- OpenWeatherMap: 1000 calls/day on free tier
- icanhazdadjoke: No documented limits, but we implement circuit breaker
- Telegram: Built-in rate limiting handled by python-telegram-bot

## Commands

- `/start` - Initialize bot and show available commands
- `/weather <city>` - Get current weather for specified city
- `/joke` - Receive a random dad joke

## Error Recovery

The bot handles common failure scenarios:
- API timeouts: Automatic retry with exponential backoff
- Invalid city names: Clear validation messages  
- Service outages: Circuit breaker prevents cascade failures
- Malformed responses: Graceful error handling

## Configuration Options

Environment variables for customization:

```bash
# Required
TELEGRAM_BOT_TOKEN=             # Your bot token
OPENWEATHER_API_KEY=           # Weather API key

# Optional
DEBUG=False                    # Enable debug mode
LOG_LEVEL=INFO                 # Logging verbosity
PORT=8443                      # Server port
API_TIMEOUT=10                 # API request timeout
API_MAX_RETRIES=3             # Retry attempts
```

## Development

### Code Quality
```bash
black src/ tests/              # Format code
isort src/ tests/             # Sort imports  
flake8 src/ tests/           # Lint
mypy src/                   # Type checking
```

### Adding New Commands

1. Create handler in `src/bot/handlers/`
2. Inherit from `BaseHandler`
3. Implement `_process_command` method
4. Register in `bot_application.py`
5. Add tests

Example:
```python
class NewHandler(BaseHandler):
    def __init__(self):
        super().__init__("newcommand")
    
    async def _process_command(self, update, context):
        # Your command logic here
        await self._send_message(update, "Response message")
```

## Troubleshooting

### Bot Not Responding
Check logs first: `heroku logs --tail`

Common issues:
- Invalid bot token
- Webhook URL misconfiguration  
- API key not activated (OpenWeatherMap takes ~10 minutes)

### High Memory Usage
Usually indicates connection leaks. The HTTP client properly closes connections, but check logs for unusual patterns.

### Weather Command Fails
- Verify API key is active
- Check city name spelling
- Ensure API quota isn't exceeded

## Performance Notes

Response times under normal conditions:
- Start command: <100ms
- Weather command: <500ms (including API call)
- Joke command: <300ms

The bot handles 100+ concurrent users without issues. Rate limiting prevents abuse while maintaining good user experience.

## Why This Architecture?

I've built this to solve common problems I see in Telegram bots:

1. **Mixed responsibilities**: Commands, API calls, and formatting scattered everywhere
2. **Poor error handling**: Bots that crash on API failures
3. **No input validation**: Security vulnerabilities and crashes from malformed input
4. **Configuration chaos**: API keys and settings hardcoded or poorly managed
5. **No testing**: Difficult to maintain and extend

This architecture separates concerns cleanly, handles errors gracefully, and provides a solid foundation for additional features.

## License

MIT License. Use it, modify it, learn from it.
