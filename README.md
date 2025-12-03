# WeatherLLM

A FastAPI web application that combines real-time weather data with AI-powered chat assistance. Get weather information for any US ZIP code and chat with an LLM that provides context-aware responses based on current weather conditions.

![Weather Chat Bot UI](https://github.com/user-attachments/assets/e1e9d195-5349-46f0-8190-2987c4afa732)

## Features

- 🌤️ **Real-time Weather Data**: Get current weather conditions from AccuWeather for any US ZIP code
- 🤖 **AI Chat Assistant**: Powered by Groq or Anthropic LLMs for intelligent weather-related conversations
- 📱 **Responsive UI**: Beautiful web interface that works on desktop and mobile
- ☁️ **Cloud Ready**: Configured for easy deployment on Render.com
- 🔒 **Secure**: All API keys stored in environment variables, HTTPS for all API calls

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **LLM Providers**: Groq (primary), Anthropic Claude (fallback)
- **Weather API**: AccuWeather
- **Deployment**: Render.com

## Prerequisites

You'll need API keys from:
- [AccuWeather](https://developer.accuweather.com/) (required)
- [Groq](https://console.groq.com/) OR [Anthropic](https://console.anthropic.com/) (at least one required)

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/tpC529/weatherllm.git
   cd weatherllm
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   ACCUWEATHER_API_KEY=your_accuweather_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```
   
   **Note**: You need at least one LLM provider (Groq or Anthropic). Groq is prioritized if both are configured.

4. **Run the application**
   ```bash
   uvicorn weather:app --reload
   ```
   
   The app will be available at `http://localhost:8000`

## Deployment on Render.com

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render.com](https://render.com)
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` configuration

3. **Configure Environment Variables** in the Render dashboard:
   - Go to your service → Environment
   - Add the following environment variables:
     - `ACCUWEATHER_API_KEY`
     - `GROQ_API_KEY` (or `ANTHROPIC_API_KEY`)

4. **Deploy**
   - Render will automatically deploy your application
   - The health check endpoint at `/api/health` ensures the service stays running

## API Endpoints

### `GET /`
Serves the HTML frontend interface.

### `POST /api/weather`
Get weather data for a ZIP code.

**Request Body:**
```json
{
  "zip_code": "02139"
}
```

**Response:**
```json
{
  "zip_code": "02139",
  "weather": "Partly cloudy, 72°F"
}
```

### `POST /api/chat`
Send a message to the LLM with weather context.

**Request Body:**
```json
{
  "zip_code": "02139",
  "message": "Should I bring an umbrella?"
}
```

**Response:**
```json
{
  "response": "Based on the current conditions (Partly cloudy, 72°F), you probably won't need an umbrella!",
  "weather": "Partly cloudy, 72°F"
}
```

### `GET /api/health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "llm_provider": "groq",
  "accuweather_configured": true
}
```

## Usage

1. Enter a US ZIP code (e.g., 02139 for Cambridge, MA)
2. Click "Get Weather" to see current conditions
3. Type a message and click "Send Message" to chat with the AI about the weather
4. The AI will provide context-aware responses based on the current weather

## Security

- ✅ No API keys hardcoded in source code
- ✅ All API keys loaded from environment variables
- ✅ HTTPS used for all external API calls
- ✅ `.env` file excluded from git via `.gitignore`
- ✅ CodeQL security scanning passed

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
