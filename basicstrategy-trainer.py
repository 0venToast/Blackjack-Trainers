import tkinter as tk
from tkinter import messagebox
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

VERSION_URL = "https://raw.githubusercontent.com/0venToast/Action-Runner/refs/heads/main/version.json"
version = "1.2.1"

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

CARD_PATH = "cards"
CARD_WIDTH = 100
CARD_HEIGHT = 150

# All possible cards
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']

# Simplified Blackjack values
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

def basic_strategy(player_hand, dealer_card, can_split):
    total = hand_value(player_hand)
    soft = is_soft(player_hand)
    dealer_val = CARD_VALUES[dealer_card[0]]
    if can_split and player_hand[0][0] == player_hand[1][0]:
        pair = player_hand[0][0]
        if pair == 'A' or pair == '8':
            return 'Split'
        if pair in ['2', '3', '7'] and dealer_val <= 7:
            return 'Split'
        if pair == '6' and dealer_val <= 6:
            return 'Split'
        if pair == '9' and dealer_val not in [7, 10, 11]:
            return 'Split'
        if pair == '4' and dealer_val in [5, 6]:
            return 'Split'

    if soft:
        if total == 13 or total == 14:
            return 'Double' if dealer_val in [5, 6] else 'Hit'
        elif total == 15 or total == 16:
            return 'Double' if dealer_val in [4, 5, 6] else 'Hit'
        elif total == 17:
            return 'Double' if dealer_val in [3, 4, 5, 6] else 'Hit'
        elif total == 18:
            if dealer_val in [2, 3, 4, 5, 6]:
                return 'Double' 
            elif dealer_val in [7, 8]:
                return 'Stand'
            else: 
                return 'Hit'
        elif total == 19:
            return 'Double' if dealer_val in [6] else 'Stand'
        else:
            return 'Stand'
    else:
        if total <= 8:
            return 'Hit'
        elif total == 9:
            return 'Double' if dealer_val in range(3, 7) else 'Hit'
        elif total == 10:
            return 'Double' if dealer_val < 10 else 'Hit'
        elif total == 11:
            return 'Double'
        elif total == 12:
            return 'Hit' if dealer_val in [2, 3, 7, 8, 9, 10, 11] else 'Stand'
        elif total in [13, 14, 15, 16]:
            return 'Stand' if dealer_val in range(2, 7) else 'Hit'
        else:
            return 'Stand'

def hand_value(hand):
    value = sum(CARD_VALUES[card[0]] for card in hand)
    aces = sum(1 for card in hand if card[0] == 'A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def is_soft(hand):
    return any(card[0] == 'A' for card in hand) and hand_value(hand) <= 21

class BlackjackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Basic Strategy Trainer")
        self.frame = tk.Frame(root)
        self.frame.pack()

        self.canvas = tk.Canvas(self.frame, width=600, height=325, bg="white")
        self.canvas.pack()

        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(pady=10)

        self.buttons = {}
        for action in ["Hit", "Stand", "Double", "Split"]:
            self.buttons[action] = tk.Button(self.button_frame, text=action, command=lambda a=action: self.check_action(a))
            self.buttons[action].pack(side=tk.LEFT, padx=10)

        self.load_cards()
        self.next_hand()

    def load_cards(self):
        self.card_images = {}
        for rank in RANKS:
            for suit in SUITS:
                name = f"{rank}_of_{suit}"
                path = os.path.join(CARD_PATH, name + ".jpg")
                if os.path.exists(path):
                    img = Image.open(path).resize((CARD_WIDTH, CARD_HEIGHT))
                    self.card_images[name] = ImageTk.PhotoImage(img)

    def draw_hand(self):
        self.canvas.delete("all")

        # Draw dealer's up card (center top)
        dealer_card = self.dealer_hand[0]
        dealer_img = self.card_images[f"{dealer_card[0]}_of_{dealer_card[1]}"]
        dealer_x = (600 - CARD_WIDTH) // 2
        dealer_y = 10
        self.canvas.create_image(dealer_x, dealer_y, image=dealer_img, anchor=tk.NW)

        # Add more vertical space between dealer and player cards
        vertical_padding = 10  # Adjust this as needed

        # Draw player's cards (center bottom)
        player_y = dealer_y + CARD_HEIGHT + vertical_padding
        total_width = len(self.player_hand) * (CARD_WIDTH + 10) - 10
        start_x = (600 - total_width) // 2
        for i, card in enumerate(self.player_hand):
            img = self.card_images[f"{card[0]}_of_{card[1]}"]
            self.canvas.create_image(start_x + i * (CARD_WIDTH + 10), player_y, image=img, anchor=tk.NW)



    def deal_hand(self):
        deck = [(rank, suit) for rank in RANKS for suit in SUITS]
        random.shuffle(deck)
        self.player_hand = [deck.pop(), deck.pop()]
        self.dealer_hand = [deck.pop(), deck.pop()]

    def check_action(self, user_action):
        dealer_card = self.dealer_hand[0]
        correct_action = basic_strategy(self.player_hand, dealer_card, self.can_split())
        if user_action == correct_action:
            self.play_sound("correct_answer.wav")
            messagebox.showinfo("Correct!", f"{user_action} was the correct move.")
        else:
            self.play_sound("wrong_answer.wav")
            messagebox.showerror("Incorrect", f"{user_action} was not the best move.\nYou should have: {correct_action}")
        self.next_hand()

    def can_split(self):
        return self.player_hand[0][0] == self.player_hand[1][0]

    def next_hand(self):
        self.deal_hand()
        self.draw_hand()

    def play_sound(self, sound_file):
        try:
            winsound.PlaySound(f"sounds/{sound_file}", winsound.SND_FILENAME)  # Play the sound
        except Exception as e:
            print(f"Error playing sound: {e}")  # If there's an error, print it

root = tk.Tk()
app = BlackjackApp(root)
root.mainloop()