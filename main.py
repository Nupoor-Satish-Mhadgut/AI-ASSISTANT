import speech_recognition as sr
import pyttsx3
import pywhatkit as kit
import datetime
import os
import wikipedia
import requests
from newsapi import NewsApiClient
import random
from googletrans import Translator, LANGUAGES
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import sqlite3
from queue import Queue

# Initialize the speech engine for text-to-speech
engine = pyttsx3.init()

# Set up user authentication database
def setup_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def validate_login(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def take_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for the wake word 'Renu'...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}\n")
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
        command = None
    except sr.RequestError:
        print("Sorry, I am unable to reach the Google server.")
        command = None
    return command.lower() if command else None

def listen_for_renu():
    while True:
        command = take_command()
        if command and "renu" in command:
            speak("Yes, I'm listening.")
            return command.replace("renu", "").strip()

def get_weather(city):
    api_key = "API_KEY"
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(base_url)
    data = response.json()
    if data["cod"] == 200:
        main = data["main"]
        weather_description = data["weather"][0]["description"]
        temperature = main["temp"]
        speak(f"The current temperature in {city} is {temperature}°C with {weather_description}.")
    else:
        speak("Sorry, I couldn't fetch the weather data.")

def get_news():
    newsapi = NewsApiClient(api_key='API_KEY')
    top_headlines = newsapi.get_top_headlines(language='en')
    if top_headlines['status'] == 'ok':
        articles = top_headlines['articles']
        speak("Here are the top news headlines:")
        for article in articles[:5]:
            speak(article['title'])
    else:
        speak("Sorry, I couldn't fetch the latest news right now.")

def tell_joke():
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything.",
        "Why did the chicken join a band? Because it had the drumsticks!",
        "I told my wife she was drawing her eyebrows too high. She looked surprised.",
        "Why don’t skeletons fight each other? They don’t have the guts.",
    ]
    joke = random.choice(jokes)
    speak(joke)

LANGUAGE_NAME_TO_CODE = {v.lower(): k for k, v in LANGUAGES.items()}

def translate_text(text, dest_language):
    translator = Translator()
    if dest_language.lower() in LANGUAGE_NAME_TO_CODE:
        dest_language = LANGUAGE_NAME_TO_CODE[dest_language.lower()]
    else:
        if dest_language not in LANGUAGES:
            speak(f"Sorry, I don't support the language {dest_language}.")
            return
    try:
        translated = translator.translate(text, dest=dest_language)
        speak(f"Translated text: {translated.text}")
    except Exception as e:
        speak("Sorry, I couldn't translate the text.")

def open_website(website_name):
    website_name = website_name.strip().lower()
    if "." not in website_name:
        website_name += ".com"
    if not website_name.startswith("http://") and not website_name.startswith("https://"):
        website_name = "https://" + website_name
    try:
        webbrowser.open(website_name)
        speak(f"Opening {website_name}")
    except Exception as e:
        speak(f"Sorry, I couldn't open the website.")

def open_application(app_name):
    if 'notepad' in app_name:
        os.system("notepad")
        speak("Opening Notepad.")
    elif 'calculator' in app_name:
        os.system("calc")
        speak("Opening Calculator.")
    else:
        speak("Sorry, I couldn't identify the application you want to open.")

def execute_command(command):
    response = ""
    if 'hello' in command:
        response = "Hello! How can I help you today?"
    elif 'time' in command:
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        response = f"The current time is {current_time}"
    elif 'play' in command:
        song = command.replace('play', '').strip()
        response = f"Playing {song}"
        kit.playonyt(song)
    elif 'search' in command:
        search_query = command.replace('search', '').strip()
        response = f"Searching for {search_query}"
        results = wikipedia.search(search_query)
        if results:
            summary = wikipedia.summary(results[0], sentences=2)
            response = f"Here is what I found: {summary}"
        else:
            response = "Sorry, I couldn't find anything on Wikipedia."
    elif 'open website' in command:
        website_name = command.replace('open website', '').strip()
        if website_name:
            open_website(website_name)
        else:
            response = "Please specify the website you want to open."
    elif 'what is the weather' in command:
        city = command.replace('what is the weather in', '').strip()
        if city:
            get_weather(city)
        else:
            response = "Please specify the city."
    elif 'what is the news today' in command:
        get_news()
    elif 'tell me a joke' in command:
        tell_joke()
    elif 'translate' in command:
        parts = command.split('to')
        if len(parts) > 1:
            text_to_translate = parts[0].replace('translate', '').strip()
            dest_language = parts[1].strip()
            translate_text(text_to_translate, dest_language)
        else:
            response = "Please specify the text and target language."
    elif 'open' in command and ('notepad' in command or 'calculator' in command):
        open_application(command)
    elif 'increase volume' in command:
        increase_volume()
        response = "Increasing the volume."
    elif 'decrease volume' in command:
        decrease_volume()
        response = "Decreasing the volume."
    else:
        response = "Sorry, I did not understand that command."
    if response:
        speak(response)
        root.after(0, display_response, response)

# Get the current volume level (0.0 to 1.0)
def get_volume():
    return engine.getProperty('volume')

# Set the volume level (0.0 to 1.0)
def set_volume(volume_level):
    engine.setProperty('volume', volume_level)

# Function to increase volume by 10%
def increase_volume():
    current_volume = get_volume()
    new_volume = min(current_volume + 0.1, 1.0)  # Ensure volume doesn't go above 1.0
    set_volume(new_volume)
    speak("Volume increased")

# Function to decrease volume by 10%
def decrease_volume():
    current_volume = get_volume()
    new_volume = max(current_volume - 0.1, 0.0)  # Ensure volume doesn't go below 0.0
    set_volume(new_volume)
    speak("Volume decreased")

def display_response(response):
    # Display the user's command or assistant's response on the UI
    text_box.config(state='normal')
    text_box.insert(tk.END, f"You: {response}\n")
    text_box.config(state='disabled')
    text_box.see(tk.END)
    root.after(0, lambda: _update_text_box(response))

def _update_text_box(response):
    text_box.config(state='normal')
    text_box.insert(tk.END, f"Assistant: {response}\n")
    text_box.config(state='disabled')
    text_box.see(tk.END)

command_queue = Queue()

def handle_voice_command():
    command = listen_for_renu()
    if command:
        display_response(f"You: Renu {command}")
        root.after(0, execute_command, command)

def update_listening_label(text):
    root.after(0, lambda: listening_label.config(text=text))

def login_window():
    def handle_login():
        username = username_entry.get()
        password = password_entry.get()
        user = validate_login(username, password)
        if user:
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            login_window.destroy()
            main_app(username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    login_window = tk.Tk()
    login_window.title("Login")
    login_window.geometry("300x200")
    tk.Label(login_window, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)
    tk.Label(login_window, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)
    tk.Button(login_window, text="Login", command=handle_login).pack(pady=10)
    login_window.mainloop()

def main_app(username):
    global root, text_box, listening_label
    root = tk.Tk()
    root.title("Renu")
    root.geometry("600x500")
    root.configure(bg="#F8F9FA")

    # Apply custom styling
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12), padding=10)
    style.configure("TEntry", font=("Arial", 12))
    style.configure("TLabel", font=("Arial", 14))

    # Add a title label
    title_label = tk.Label(root, text="Renu - Your Personal Assistant", font=("Helvetica", 16, "bold"), bg="#007BFF", fg="white", pady=10)
    title_label.pack(fill=tk.X)

    # Text box to display conversation
    text_box = tk.Text(root, wrap=tk.WORD, state='disabled', height=15, width=70, bg="#E9ECEF", fg="#212529", font=("Courier New", 12), padx=10, pady=10)
    text_box.pack(padx=10, pady=10)

    # Change the geometry manager for listening_label to pack
    listening_label = tk.Label(root, text="Click 'Speak' to start listening...", font=("Arial", 14), bg="#F8F9FA", fg="blue")
    listening_label.pack(pady=20)  # Using pack instead of grid

    # Change the button frame layout to use pack for consistent geometry management
    button_frame = tk.Frame(root, bg="#F8F9FA")
    button_frame.pack(pady=20)  # Using pack instead of grid

    # Voice Button
    voice_button = ttk.Button(button_frame, text="Speak", command=lambda: threading.Thread(target=handle_voice_command).start())
    voice_button.pack(side=tk.LEFT, padx=10)  # Using pack for all buttons

    # Exit Button
    exit_button = ttk.Button(button_frame, text="Exit", command=lambda: root.after(0, root.quit))
    exit_button.pack(side=tk.LEFT, padx=10)

    # Volume control buttons
    volume_up_button = ttk.Button(button_frame, text="Increase Volume", command=increase_volume)
    volume_up_button.pack(side=tk.LEFT, padx=10)

    volume_down_button = ttk.Button(button_frame, text="Decrease Volume", command=decrease_volume)
    volume_down_button.pack(side=tk.LEFT, padx=10)

    speak("Hello, I am Renu. Say my name to start talking.")

    # Start listening (simulate)
    update_listening_label("Listening for 'Renu'...")

    root.mainloop()

# Setup the database and start the login process
setup_database()
login_window()
