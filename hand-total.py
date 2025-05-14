import tkinter as tk
from PIL import Image, ImageTk
import random
import os
import winsound
import sys
import requests
import subprocess
import tempfile

if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

VERSION_URL = "https://raw.githubusercontent.com/0venToast/Blackjack-Trainers/refs/heads/main/hand-version.json"
version = "1.0.1"

def download_new_version(download_url, temp_path):
    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print("Download error:", e)
        return False

def check_for_updates():
    try:
        response = requests.get(VERSION_URL)
        data = response.json()
        latest_version = data["version"]
        download_url = data["url"]

        if version != latest_version:
            answer = tk.messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available. Update now?")
            if answer:
                # Download new file to temp
                temp_path = os.path.join(tempfile.gettempdir(), "new_version.exe")
                if download_new_version(download_url, temp_path):
                    launcher_path = os.path.join(os.path.dirname(sys.executable), "Updater.exe")
                    subprocess.Popen([launcher_path, sys.executable, temp_path])
                    root.destroy()
                    sys.exit()
    except Exception as e:
        print("Update check failed:", e)

# Define card values
cards_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

root = tk.Tk()
check_for_updates()  # Check for updates at the start

# Suits and card ranks
suits = ['hearts', 'diamonds', 'clubs', 'spades']
ranks = list(cards_values.keys())

# Path to card images
CARD_FOLDER = "cards"

class BlackjackTrainer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blackjack Math Trainer")
        self.geometry("600x400")
        self.configure(bg="white")

        self.deck = [(rank, suit) for rank in ranks for suit in suits]
        self.card_images = {}

        # Load all card images
        for rank, suit in self.deck:
            path = os.path.join(CARD_FOLDER, f"{rank}_of_{suit}.jpg")
            image = Image.open(path).resize((100, 150))  # Resize nicely
            self.card_images[(rank, suit)] = ImageTk.PhotoImage(image)

        self.cards_frame = tk.Frame(self, bg="white")
        self.cards_frame.pack(pady=50)

        self.entry = tk.Entry(self)
        self.entry.pack(pady=20)
        self.entry.bind("<Return>", self.check_answer)

        self.feedback_label = tk.Label(self, text="", bg="white", font=("Arial", 18))
        self.feedback_label.pack(pady=20)

        # Start the first round automatically
        self.after(1000, self.start_round)

    def start_round(self):
        # Reset everything at the start of a new round
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        self.feedback_label.config(text="")  # Clear feedback
        self.entry.delete(0, tk.END)  # Clear previous answer

        self.hand = random.sample(self.deck, random.randint(2, 4))  # Select random cards for hand
        self.current_card_index = 0  # Start with the first card

        self.show_next_card()  # Show the first card

    def show_next_card(self):
        if self.current_card_index < len(self.hand):
            card = self.hand[self.current_card_index]
            label = tk.Label(self.cards_frame, image=self.card_images[card])
            label.pack(side="left", padx=10)

            self.current_card_index += 1

            # Show next card after a small delay (1 second)
            self.after(500, self.show_next_card)
        else:
            # Once all cards have been shown, wait for the user input
            self.feedback_label.config(text="Enter the total value:")

    def calculate_total(self):
        total = 0
        aces = 0
        for rank, suit in self.hand:
            total += cards_values[rank]
            if rank == 'A':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def check_answer(self, event=None):
        guess = self.entry.get()
        actual = self.calculate_total()

        try:
            guess = int(guess)
            if guess == actual:
                self.feedback_label.config(text=f"Correct! Total was {actual}")
                self.play_sound("correct_answer.wav")  # Play correct answer sound
            else:
                self.feedback_label.config(text=f"Wrong! Total was {actual}")
                self.play_sound("wrong_answer.wav")
        except ValueError:
            self.feedback_label.config(text=f"Invalid input! Total was {actual}")
            self.play_sound("wrong_answer.wav")

        # Start the next round after a short delay
        self.after(1000, self.start_round)  # Start new round automatically
        self.entry.delete(0, tk.END)  # Clear entry field

    def play_sound(self, sound_file):
        try:
            winsound.PlaySound(f"sounds/{sound_file}", winsound.SND_FILENAME)  # Play the sound
        except Exception as e:
            print(f"Error playing sound: {e}")  # If there's an error, print it

if __name__ == "__main__":
    app = BlackjackTrainer()
    app.mainloop()