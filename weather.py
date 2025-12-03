from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Validate required environment variables
if not ACCUWEATHER_API_KEY:
    raise ValueError("ACCUWEATHER_API_KEY environment variable is required")

# Determine which LLM provider to use
llm_provider = None
if GROQ_API_KEY:
    llm_provider = "groq"
    from groq import Groq
    llm_client = Groq(api_key=GROQ_API_KEY)
    llm_model = "llama3-8b-8192"
elif ANTHROPIC_API_KEY:
    llm_provider = "anthropic"
    from anthropic import Anthropic
    llm_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    llm_model = "claude-3-haiku-20240307"
else:
    raise ValueError("Either GROQ_API_KEY or ANTHROPIC_API_KEY environment variable is required")

# Initialize FastAPI app
app = FastAPI(title="WeatherLLM", description="Weather chatbot with LLM integration")

# Request/Response models
class WeatherRequest(BaseModel):
    zip_code: str

class ChatRequest(BaseModel):
    zip_code: str
    message: str

class WeatherResponse(BaseModel):
    zip_code: str
    weather: str

class ChatResponse(BaseModel):
    response: str
    weather: str

# Weather API functions
def get_location_key(zip_code: str) -> str:
    """Convert ZIP code to AccuWeather location key"""
    try:
        res = requests.get(
            "https://dataservice.accuweather.com/locations/v1/postalcodes/search",
            params={"apikey": ACCUWEATHER_API_KEY, "q": zip_code}
        )
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get location key from AccuWeather")
        data = res.json()
        if not data:
            raise HTTPException(status_code=404, detail="Invalid ZIP code")
        return data[0]["Key"]
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to AccuWeather: {str(e)}")

def get_weather(location_key: str) -> str:
    """Get current weather conditions from AccuWeather"""
    try:
        res = requests.get(
            f"https://dataservice.accuweather.com/currentconditions/v1/{location_key}",
            params={"apikey": ACCUWEATHER_API_KEY, "details": False}
        )
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get weather data from AccuWeather")
        data = res.json()
        if not data:
            raise HTTPException(status_code=404, detail="No weather data available")
        cond = data[0]
        weather_text = cond["WeatherText"]
        temp = cond["Temperature"]["Imperial"]["Value"]
        return f"{weather_text}, {temp}°F"
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to AccuWeather: {str(e)}")

def get_llm_response(weather_data: str, user_message: str) -> str:
    """Get response from LLM provider"""
    forecast_details = {"text": weather_data}
    
    prompt = f"""You are a helpful weather assistant. Use ONLY the JSON data provided below to answer the user.
Do NOT hallucinate or invent extra facts.

Weather data (JSON):
{json.dumps(forecast_details)}

User wants to know: "{user_message}"
Keep your answer under 100 characters, be friendly and conversational."""

    try:
        if llm_provider == "groq":
            response = llm_client.chat.completions.create(
                model=llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=100
            )
            return response.choices[0].message.content
        elif llm_provider == "anthropic":
            response = llm_client.messages.create(
                model=llm_model,
                max_tokens=100,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting LLM response: {str(e)}")

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the HTML frontend"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather Chat Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            padding: 30px;
        }
        
        h1 {
            color: #667eea;
            margin-bottom: 25px;
            text-align: center;
            font-size: 28px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .chat-container {
            background: #f7f7f7;
            border-radius: 8px;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
            border: 2px solid #e0e0e0;
        }
        
        .chat-message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
            max-width: 80%;
        }
        
        .chat-message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .chat-message.bot {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
        }
        
        .chat-message.system {
            background: #ffeaa7;
            color: #333;
            text-align: center;
            margin: 0 auto;
        }
        
        .sender {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 14px;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        button {
            flex: 1;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button.primary {
            background: #667eea;
            color: white;
        }
        
        button.primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button.secondary {
            background: #74b9ff;
            color: white;
        }
        
        button.secondary:hover {
            background: #0984e3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(9, 132, 227, 0.4);
        }
        
        button.clear {
            background: #dfe6e9;
            color: #2d3436;
        }
        
        button.clear:hover {
            background: #b2bec3;
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            font-weight: 500;
            margin-top: 15px;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 24px;
            }
            
            .button-group {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌤️ Weather Chat Bot</h1>
        
        <div class="input-group">
            <label for="zipCode">ZIP Code:</label>
            <input type="text" id="zipCode" placeholder="e.g., 02139" maxlength="10">
        </div>
        
        <div class="input-group">
            <label for="chatDisplay">Chat:</label>
            <div class="chat-container" id="chatDisplay"></div>
        </div>
        
        <div class="input-group">
            <label for="message">Your Message:</label>
            <input type="text" id="message" placeholder="Type your message here...">
        </div>
        
        <div class="button-group">
            <button class="primary" id="sendBtn">Send Message</button>
            <button class="secondary" id="weatherBtn">Get Weather</button>
            <button class="clear" id="clearBtn">Clear Chat</button>
        </div>
        
        <div class="status" id="status" style="display: none;"></div>
    </div>
    
    <script>
        const chatDisplay = document.getElementById('chatDisplay');
        const zipCodeInput = document.getElementById('zipCode');
        const messageInput = document.getElementById('message');
        const sendBtn = document.getElementById('sendBtn');
        const weatherBtn = document.getElementById('weatherBtn');
        const clearBtn = document.getElementById('clearBtn');
        const statusDiv = document.getElementById('status');
        
        function addMessage(message, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${sender.toLowerCase()}`;
            
            const senderDiv = document.createElement('div');
            senderDiv.className = 'sender';
            senderDiv.textContent = sender;
            
            const contentDiv = document.createElement('div');
            contentDiv.textContent = message;
            
            messageDiv.appendChild(senderDiv);
            messageDiv.appendChild(contentDiv);
            chatDisplay.appendChild(messageDiv);
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        }
        
        function showStatus(message, type) {
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
            statusDiv.style.display = 'block';
        }
        
        function hideStatus() {
            statusDiv.style.display = 'none';
        }
        
        async function getWeather() {
            const zipCode = zipCodeInput.value.trim();
            if (!zipCode) {
                showStatus('Please enter a ZIP code', 'error');
                return;
            }
            
            showStatus('Getting weather...', 'info');
            sendBtn.disabled = true;
            weatherBtn.disabled = true;
            
            try {
                const response = await fetch('/api/weather', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ zip_code: zipCode })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to get weather');
                }
                
                const data = await response.json();
                addMessage(`Weather for ZIP ${data.zip_code}:`, 'System');
                addMessage(data.weather, 'Weather');
                showStatus('Weather retrieved successfully', 'success');
            } catch (error) {
                addMessage(`Error: ${error.message}`, 'System');
                showStatus('Error getting weather', 'error');
            } finally {
                sendBtn.disabled = false;
                weatherBtn.disabled = false;
            }
        }
        
        async function sendMessage() {
            const zipCode = zipCodeInput.value.trim();
            const message = messageInput.value.trim();
            
            if (!zipCode) {
                showStatus('Please enter a ZIP code', 'error');
                return;
            }
            
            if (!message) {
                showStatus('Please enter a message', 'error');
                return;
            }
            
            addMessage(message, 'You');
            messageInput.value = '';
            
            showStatus('Processing...', 'info');
            sendBtn.disabled = true;
            weatherBtn.disabled = true;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ zip_code: zipCode, message: message })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to get response');
                }
                
                const data = await response.json();
                addMessage(data.response, 'Bot');
                showStatus('Message sent successfully', 'success');
            } catch (error) {
                addMessage(`Error: ${error.message}`, 'System');
                showStatus('Error processing message', 'error');
            } finally {
                sendBtn.disabled = false;
                weatherBtn.disabled = false;
            }
        }
        
        function clearChat() {
            chatDisplay.innerHTML = '';
            hideStatus();
        }
        
        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        weatherBtn.addEventListener('click', getWeather);
        clearBtn.addEventListener('click', clearChat);
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        zipCodeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') getWeather();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/weather", response_model=WeatherResponse)
async def get_weather_endpoint(request: WeatherRequest):
    """Get weather for a ZIP code"""
    location_key = get_location_key(request.zip_code)
    weather_data = get_weather(location_key)
    return WeatherResponse(zip_code=request.zip_code, weather=weather_data)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Send a message to the LLM with weather context"""
    location_key = get_location_key(request.zip_code)
    weather_data = get_weather(location_key)
    llm_response = get_llm_response(weather_data, request.message)
    return ChatResponse(response=llm_response, weather=weather_data)

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "llm_provider": llm_provider,
        "accuweather_configured": bool(ACCUWEATHER_API_KEY)
    }