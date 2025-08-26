import os
import random
import time
import threading
import webbrowser
import pywhatkit
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import tkinter as tk
from PIL import Image, ImageTk
import requests
from bs4 import BeautifulSoup
import wikipedia
import pyttsx3
import pyautogui
from pathlib import Path
import pygetwindow as gw
from difflib import get_close_matches
from datetime import datetime

# -------------------------
# Basic feature functions
# -------------------------
def take_screenshot(save_dir=str(Path.home() / "Pictures" / "Jarvis")):
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        fname = f"{save_dir}/screenshot_{ts}.png"
        img = pyautogui.screenshot()
        img.save(fname)
        return fname
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

# -------------------------
# App registry (edit paths)
# -------------------------
app_registry = {
    "chrome": {
        "exe": "chrome.exe",
        "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "actions": {
            "add new tab": lambda: pyautogui.hotkey('ctrl', 't'),
            "reload": lambda: pyautogui.hotkey('ctrl', 'r'),
            "close tab": lambda: pyautogui.hotkey('ctrl', 'w')
        }
    },
    "notepad": {
        "exe": "notepad.exe",
        "path": "notepad",
        "actions": {
            "add new line": lambda: pyautogui.press('enter'),
            "select all": lambda: pyautogui.hotkey('ctrl', 'a'),
            "close": lambda: pyautogui.hotkey('alt', 'f4')
        }
    },
    "whatsapp": {
        "exe": "WhatsApp.exe",
        # <-- EDIT THIS path to your WhatsApp shortcut target (or WhatsApp exe)
        "path": r"C:\Users\rosha\OneDrive\Desktop\WhatsApp - Shortcut.lnk",
        "actions": {
            "search contact": lambda: pyautogui.hotkey('ctrl', 'f'),
            "close": lambda: pyautogui.hotkey('alt', 'f4')
        }
    }
}

# -------------------------
# Voice engine & speak()
# -------------------------
engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)

def speak(text):
    # """Use gTTS primarily for nicer voice; fallback to pyttsx3 if anything breaks."""
    print("jarvis:", text)
    try:
        filename = f"voice_{random.randint(1,99999)}.mp3"
        tts = gTTS(text=text, lang='en')
        tts.save(filename)
        playsound(filename)
        os.remove(filename)
    except Exception as e:
        # fallback to offline pyttsx3
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e2:
            print("TTS failed:", e, e2)

# -------------------------
# Listen
# -------------------------
def listen(timeout=5):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("🎧 Listening...")
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=6)
            command = r.recognize_google(audio)
            print("You:", command)
            return command.lower()
        except sr.WaitTimeoutError:
            print("listen timeout")
            return ""
        except sr.UnknownValueError:
            print("couldn't understand")
            return ""
        except Exception as e:
            print("listen error:", e)
            return ""

# -------------------------
# Utilities
# -------------------------
def get_summary(query):
    try:
        topic = query.replace('who is','').replace('what is','').replace('define','').strip()
        return wikipedia.summary(topic, sentences=2)
    except Exception:
        try:
            url = f"https://html.duckduckgo.com/html?q={query}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.find_all("div", class_="result__body", limit=1)
            if results:
                title = results[0].find("a", class_="result__a")
                snippet = results[0].find("a", class_="result__snippet")
                title_text = title.text.strip() if title else ""
                snippet_text = snippet.text.strip() if snippet else ""
                return f"{title_text}. {snippet_text}"
        except Exception:
            pass
    return "Sorry, I couldn't find anything."

def is_similar(command, target_phrases, threshold=0.8):
    for phrase in target_phrases:
        match = get_close_matches(command, [phrase], cutoff=threshold)
        if match:
            return phrase
    return None

# -------------------------
# WhatsApp helpers
# -------------------------
def send_whatsapp_message(contact_name, message):
    try:
        speak(f"Sending message to {contact_name}")
        os.startfile(app_registry['whatsapp']['path'])
        time.sleep(6)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(1)
        pyautogui.typewrite(contact_name)
        time.sleep(1)
        pyautogui.press("down")
        pyautogui.press("enter")
        time.sleep(2)
        pyautogui.typewrite(message)
        pyautogui.press("enter")
        speak("Message sent.")
    except Exception as e:
        print("WhatsApp send error:", e)
        speak("Could not send message.")

def open_whatsapp_chat(contact_name):
    try:
        speak(f"Opening chat with {contact_name}")
        os.startfile(app_registry['whatsapp']['path'])
        time.sleep(6)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(1)
        pyautogui.typewrite(contact_name)
        time.sleep(1)
        pyautogui.press("down")
        pyautogui.press("enter")
    except Exception as e:
        print("open chat error:", e)
        speak("Could not open chat.")

def call_on_whatsapp(contact_name):
    try:
        speak(f"Calling {contact_name} on WhatsApp")
        os.startfile(app_registry['whatsapp']['path'])
        time.sleep(6)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(1)
        pyautogui.typewrite(contact_name)
        time.sleep(1)
        pyautogui.press("down")
        pyautogui.press("enter")
        time.sleep(3)
        # coordinates may differ per screen - you might need to adjust these
        pyautogui.moveTo(1830, 88)
        pyautogui.click()
    except Exception as e:
        print("whatsapp call error:", e)
        speak("Call failed.")

def cut_whatsapp_call():
    time.sleep(1)
    pyautogui.press('esc')

# -------------------------
# Command Processor (single definition)
# -------------------------
temp_app = None

def process_command_text(command):
    global temp_app
    if not command:
        return

    command = command.lower()

    # WhatsApp send message triggers
    trigger_phrases = [
        "send message to", "send msg to", "send whatsapp to", "mummy ko message",
        "send message mummy"
    ]
    # check prefix similarity up to 25 chars
    msg_trigger = is_similar(command[:25], trigger_phrases, threshold=0.75)
    if msg_trigger:
        contact = command.split(msg_trigger)[-1].strip()
        if contact:
            speak(f"What should I say to {contact}?")
            message = listen(8)
            if message:
                send_whatsapp_message(contact, message)
            else:
                speak("No message heard.")
        else:
            speak("Say the contact name.")
        return

    # whatsapp call
    if 'call' in command and 'whatsapp' in command:
        contact = command.replace("call on whatsapp","").replace("call","").replace("on whatsapp","").strip()
        if contact:
            call_on_whatsapp(contact)
        else:
            speak("Whom should I call?")
        return

    # open chat
    if 'chat with' in command or 'i want to chat with' in command:
        contact = command.split('with')[-1].strip()
        if contact:
            open_whatsapp_chat(contact)
        else:
            speak("Say the contact name.")
        return

    # play on youtube
    if 'play' in command:
        song = command.replace("play", "").strip()
        if song:
            pywhatkit.playonyt(song)
            speak(f"Playing {song} on YouTube")
        else:
            speak("Which song?")
        return

    # google search
    if 'search' in command:
        query = command.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        speak(f"Searching {query} on Google")
        return

    # wiki / define
    if any(q in command for q in ['who is', 'what is', 'define', 'tell me']):
        summary = get_summary(command)
        speak(summary)
        return

    # open/close websites
    if 'open youtube' in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube")
        return
    if 'open instagram' in command:
        webbrowser.open("https://www.instagram.com")
        speak("Opening Instagram")
        return
    if 'open twitter' in command:
        webbrowser.open("https://www.twitter.com")
        speak("Opening Twitter")
        return

    # file manager
    if 'open file manager' in command or 'open explorer' in command:
        try:
            os.startfile("explorer")
            speak("Opening File Manager")
        except Exception:
            speak("Could not open File Manager")
        return

    # open chrome quick
    if 'open chrome' in command:
        try:
            os.system(f'start "" "{app_registry["chrome"]["path"]}"')
            speak("Opening Chrome")
            temp_app = "chrome"
        except Exception:
            speak("Could not open Chrome")
        return

    # close current app
    if 'close this app' in command and temp_app:
        try:
            os.system(f"taskkill /f /im {app_registry[temp_app]['exe']}")
            speak(f"{temp_app} closed")
            temp_app = None
        except Exception:
            speak("Could not close the app")
        return

    # open/close apps in registry and app-specific actions
    for app, config in app_registry.items():
        if f"open {app}" in command:
            try:
                os.system(f'start "" "{config["path"]}"')
                speak(f"Opening {app}")
                temp_app = app
            except Exception:
                speak(f"Could not open {app}")
            return
        if f"close {app}" in command:
            try:
                os.system(f"taskkill /f /im {config['exe']}")
                speak(f"{app} closed")
                temp_app = None
            except Exception:
                speak(f"Could not close {app}")
            return
        # if this app is currently active, allow action keywords
        if app == temp_app:
            for action in config.get('actions', {}):
                if action in command:
                    try:
                        config['actions'][action]()
                        speak(f"Performed {action} in {app}")
                    except Exception:
                        speak(f"Could not perform {action}")
                    return

    # screenshot (catch phrases)
    if "screenshot" in command or "take screenshot" in command:
        path = take_screenshot()
        if path:
            speak(f"Screenshot taken and saved to {path}")
        else:
            speak("Sorry, I could not take the screenshot.")
        return

    # other fallback
    speak("Sorry, I didn't understand that command.")

# -------------------------
# Wake word loop+
# -------------------------
def jarvis_loop():
    while True:
        command = listen(5)
        if not command:
            time.sleep(0.2)
            continue
        # wake words
        if 'jarvis' in command or 'sir' in command:
            speak("Yes, how can I help you?")
            while True:
                user_command = listen(6)
                if not user_command:
                    # if silence, keep listening for next command
                    continue
                if 'exit' in user_command or 'quit' in user_command or 'stop' in user_command:
                    speak("Exiting command mode.")
                    break
                process_command_text(user_command)
        time.sleep(0.1)

# -------------------------
# GUI
# -------------------------
def start_gui():
    root = tk.Tk()
    root.title("jarvis AI")
    root.geometry("600x600")
    root.config(bg="black")

    # <-- EDIT: set correct gif path (remove double .gif.gif if present)
    gif_path = r"C:\Users\rosha\OneDrive\Desktop\jarvis app\jarvis app\background_loop.gif.gif"
    try:
        gif = Image.open(gif_path)
        frames = []
        try:
            while True:
                frames.append(ImageTk.PhotoImage(gif.copy()))
                gif.seek(len(frames))
        except EOFError:
            pass

        label = tk.Label(root, bg="black")
        label.pack(expand=True, fill="both")

        def update(index):
            frame = frames[index]
            label.configure(image=frame)
            root.after(100, update, (index + 1) % len(frames))

        update(0)
    except Exception as e:
        print("Could not load GIF:", e)
        # fall back to a simple label
        tk.Label(root, text="Jarvis", fg="white", bg="black", font=("Arial", 30)).pack(expand=True)

    threading.Thread(target=jarvis_loop, daemon=True).start()
    root.mainloop()

# -------------------------
# Start
# -------------------------
if __name__ == "__main__":
    start_gui() 