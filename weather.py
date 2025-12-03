import customtkinter as ctk
from tkinter import messagebox
import requests
from agno.agent import Agent
from agno.models.ollama import Ollama
import threading
import json

# AccuWeather API key (replace with your key)
ACCUWEATHER_API_KEY = "Ws7ArJGsol4yi8MIxDXATlkKwGjTLliN"

class WeatherChatGUI:
    def __init__(self, root):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.root = root  # use the single CTk instance from main(), do not create another

        # Initialize the LLM agent with enhanced context - optimized for speed
        try:
            self.agent = Agent(
                model=Ollama(id="smollm2"
                ),  # Using smollm2 for speed
                markdown=False,  # Disable markdown for speed
                instructions="""You are a helpful weather assistant. Keep responses under 100 characters when possible. Be conversational and direct.
                
                Rules:
                - Keep responses short and friendly
                - Briefly explain the current weather conditions
                - Ask simple follow-up questions, pertaining to the user's plans
                - Be concise but helpful
                - Avoid overly technical terms
                """,
                # Disable memory for speed
                memory=False,
                # Simplified context
                context="Quick weather assistant - short, helpful responses"
            )
        except Exception as e:
            print(f"Error initializing agent: {e}")
            # Fallback to basic configuration
            self.agent = Agent(
                model=Ollama(id="phi4-mini:latest"),
                markdown=False
            )
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Weather Chat Bot",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # ZIP Code input
        ctk.CTkLabel(main_frame, text="ZIP Code:").grid(row=1, column=0, sticky="w", pady=5)
        self.zip_entry = ctk.CTkEntry(
             main_frame,
             width=200,
             placeholder_text="e.g. 02139"
        )
        self.zip_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Chat display area
        ctk.CTkLabel(main_frame, text="Chat:").grid(row=2, column=0, sticky="w", pady=(10, 0))

        self.chat_display = ctk.CTkTextbox(main_frame, width=400, height=300)
        self.chat_display.configure(state="disabled")
        self.chat_display.grid(row=2, column=1, sticky="nsew", pady=(10, 0), padx=(10, 0))
        
        # Message input
        ctk.CTkLabel(main_frame, text="Your Message:").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.message_entry = ctk.CTkEntry(
            main_frame,
            width=400,
            placeholder_text="Type your message here…"
        )
        self.message_entry.grid(row=3, column=1, sticky="ew", pady=(10, 0), padx=(10, 0))
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # Send button
        self.send_button = ctk.CTkButton(button_frame, text="Send Message", command=self.send_message)
        self.send_button.pack(side="left", padx=(0, 10))
        
        # Get Weather button
        self.weather_button = ctk.CTkButton(button_frame, text="Get Weather", command=self.get_weather_only)
        self.weather_button.pack(side="left", padx=(0, 10))

        # Clear button
        clear_button = ctk.CTkButton(button_frame, text="Clear Chat", command=self.clear_chat)
        clear_button.pack(side="left")

        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="Ready", text_color="green")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Bind Enter key to send message
        self.message_entry.bind('<Return>', lambda _: self.send_message())
        self.zip_entry.bind('<Return>', lambda _: self.get_weather_only())

    def get_location_key(self, zip_code):
        """Convert ZIP code to AccuWeather location key"""
        try:
            res = requests.get(
                "http://dataservice.accuweather.com/locations/v1/postalcodes/search",
                params={"apikey": "Ws7ArJGsol4yi8MIxDXATlkKwGjTLliN", "q": zip_code}
            )
            if res.status_code != 200:
                return None
            data = res.json()
            if not data:
                return None
            return data[0]["Key"]
        except Exception as e:
            self.add_to_chat(f"Error getting location key: {str(e)}", "System")
            return None

    def get_weather(self, location_key):
        """Get current weather conditions from AccuWeather"""
        try:
            res = requests.get(
                f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}",
                params={"apikey": "Ws7ArJGsol4yi8MIxDXATlkKwGjTLliN", "details": False}
            )
            if res.status_code != 200:
                return None
            data = res.json()
            if not data:
                return None
            cond = data[0]
            weather_text = cond["WeatherText"]
            temp = cond["Temperature"]["Imperial"]["Value"]
            return f"{weather_text}, {temp}°F"
        except Exception as e:
            self.add_to_chat(f"Error getting weather: {str(e)}", "System")
            return None
            
    def add_to_chat(self, message, sender=""):
        """Add message to chat display"""
        self.chat_display.configure(state="normal")
        if sender:
            self.chat_display.insert(ctk.END, f"{sender}: {message}\n\n")
        else:
            self.chat_display.insert(ctk.END, f"{message}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        
    def update_status(self, message, color="black"):
        """Update status label"""
        self.status_label.configure(text=message, text_color=color)
        
    def get_weather_only(self):
        """Get weather without sending to chatbot"""
        zip_code = self.zip_entry.get().strip()
        if not zip_code:
            messagebox.showerror("Error", "Please enter a ZIP code")
            return

        self.update_status("Getting weather...", "blue")

        def weather_thread():
            # Get AccuWeather location key
            loc_key = self.get_location_key(zip_code)
            if not loc_key:
                self.add_to_chat("Invalid ZIP code or unable to get location key.", "System")
                self.update_status("Error getting location", "red")
                return

            # Fetch current conditions
            forecast = self.get_weather(loc_key)
            if not forecast:
                self.add_to_chat("Failed to get weather data.", "System")
                self.update_status("Error getting weather", "red")
                return

            self.add_to_chat(f"Weather for ZIP {zip_code}:", "System")
            self.add_to_chat(forecast, "Weather")
            self.update_status("Weather retrieved successfully", "green")

        threading.Thread(target=weather_thread, daemon=True).start()
        
    def send_message(self):
        """Send message to chatbot"""
        zip_code = self.zip_entry.get().strip()
        user_message = self.message_entry.get().strip()

        if not zip_code:
            messagebox.showerror("Error", "Please enter a ZIP code")
            return

        # Clear message entry
        self.message_entry.delete(0, ctk.END)

        # Add user message to chat
        if user_message:
            self.add_to_chat(user_message, "You")

        self.update_status("Processing...", "blue")

        # Disable buttons during processing
        self.send_button.configure(state=ctk.DISABLED)
        self.weather_button.configure(state=ctk.DISABLED)

        def chat_thread():
            try:
                # Get AccuWeather location key
                loc_key = self.get_location_key(zip_code)
                if not loc_key:
                    self.add_to_chat("Invalid ZIP code or unable to get location key.", "System")
                    self.update_status("Error getting location", "red")
                    return

                # Fetch current conditions
                forecast = self.get_weather(loc_key)
                if not forecast:
                    self.add_to_chat("Failed to get weather data.", "System")
                    self.update_status("Error getting weather", "red")
                    return

                # 1) Turn your forecast into a small dict with more fields:
                forecast_details = {
                    "text": forecast,
                    # pull extra fields if you want – e.g. humidity, wind, precipProb…
                    # "humidity": cond["RelativeHumidity"],
                    # "precipProbability": cond["PrecipitationProbability"]
                }

                # 2) Build a stricter prompt
                prompt = f"""
                You are a weather assistant. Use ONLY the JSON data provided below to answer the user.
                Do NOT hallucinate or invent extra facts.

                Weather data (JSON):
                {json.dumps(forecast_details)}

                User wants to know: "{user_message}"
                Keep your answer under 80 characters, be friendly.
                """

                # 3) Lower temperature/top_p for accuracy
                reply = self.agent.run(
                    prompt,
                    temperature=0.0,
                    max_tokens=80,
                    top_p=0.5
                )

                # Debug: Print available attributes
                print(f"Reply object type: {type(reply)}")
                print(f"Reply attributes: {dir(reply)}")

                # Add chatbot response to chat
                if hasattr(reply, 'message'):
                    response_text = reply.message
                elif hasattr(reply, 'content'):
                    response_text = reply.content
                elif hasattr(reply, 'text'):
                    response_text = reply.text
                elif hasattr(reply, 'response'):
                    response_text = reply.response
                else:
                    response_text = str(reply)

                self.add_to_chat(response_text, "Bot")
                self.update_status("Message sent successfully", "green")

            except Exception as e:
                self.add_to_chat(f"Error: {str(e)}", "System")
                self.update_status("Error processing message", "red")
            finally:
                # Re-enable buttons
                self.send_button.configure(state=ctk.NORMAL)
                self.weather_button.configure(state=ctk.NORMAL)
                self.send_button.configure(state=ctk.NORMAL)
                self.weather_button.configure(state=ctk.NORMAL)
                self.weather_button.start()

        threading.Thread(target=chat_thread, daemon=True).start()
def main():
    root = ctk.CTk()
    
    # Make the window borderless and always on top
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    
    # Position & size it — make it large enough for the chat area!
    screen_width = root.winfo_screenwidth()
    # Increase to accommodate the 400×300 chat textbox
    widget_w, widget_h = 600, 500
    x = screen_width - widget_w - 50
    y = 50
    root.geometry(f"{widget_w}x{widget_h}+{x}+{y}")
    
    app = WeatherChatGUI(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()