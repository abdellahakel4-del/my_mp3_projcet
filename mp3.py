import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pygame
import os
from mutagen.mp3 import MP3

# إعداد المظهر العام
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green") # لون أخضر مريح للعين (مناسب لسمة القرآن)

class QuranicReciter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Quranic Reciter")
        self.geometry("800x600")

        pygame.init()
        pygame.mixer.init()

        # أحداث نهاية المقطع
        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)

        # متغيرات الحالة
        self.is_paused = False
        self.current_song_path = ""
        self.current_song_length = 0
        self.start_time = 0 
        self.song_paths = []
        self.auto_play = tk.BooleanVar(value=True)

        self.create_widgets()
        self.check_events()
        self.update_ui()

    def create_widgets(self):
        # --- العنوان العلوي ---
        self.header = ctk.CTkLabel(self, text="📖 Quranic Reciter", font=("Arial", 28, "bold"), text_color="#1DB954")
        self.header.pack(pady=20)

        # --- الحاوية الرئيسية ---
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # الجزء الأيسر (قائمة السور)
        self.left_frame = ctk.CTkFrame(self.main_container, width=300)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.left_frame, text="Playlist Frame", font=("Arial", 16, "bold")).pack(pady=5)
        
        self.playlist = tk.Listbox(self.left_frame, bg="#2b2b2b", fg="white", borderwidth=0, 
                                   highlightthickness=0, selectbackground="#1DB954", font=("Arial", 11))
        self.playlist.pack(fill="both", expand=True, padx=10, pady=5)

        # الجزء الأيمن (التحكم والتقدم)
        self.right_frame = ctk.CTkFrame(self.main_container)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # شريط التقدم والوقت
        self.progress_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=20)

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="00:00 / 00:00", font=("Arial", 14))
        self.progress_label.pack()

        self.progress_slider = ctk.CTkSlider(self.right_frame, from_=0, to=100, command=self.seek_music)
        self.progress_slider.set(0)
        self.progress_slider.pack(fill="x", padx=20, pady=10)

        # خيار التشغيل التلقائي
        self.auto_play_cb = ctk.CTkCheckBox(self.right_frame, text="Auto-play Next Surah", variable=self.auto_play)
        self.auto_play_cb.pack(pady=10)

        # أزرار التحكم الصغير (⏪ ▶ ⏸ ⏩)
        self.controls_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.controls_box.pack(pady=10)

        ctk.CTkButton(self.controls_box, text="⏪ -5s", width=60, command=lambda: self.seek_relative(-5)).grid(row=0, column=0, padx=5)
        ctk.CTkButton(self.controls_box, text="▶ PLAY", width=80, fg_color="#1DB954", command=self.play_selected).grid(row=0, column=1, padx=5)
        ctk.CTkButton(self.controls_box, text="⏸ PAUSE", width=80, fg_color="#EBCB8B", text_color="black", command=self.toggle_pause).grid(row=0, column=2, padx=5)
        ctk.CTkButton(self.controls_box, text="⏩ +5s", width=60, command=lambda: self.seek_relative(5)).grid(row=0, column=3, padx=5)

        # مستوى الصوت
        ctk.CTkLabel(self.right_frame, text="Volume Control").pack(pady=(20, 0))
        self.volume_slider = ctk.CTkSlider(self.right_frame, from_=0, to=1, command=self.set_volume)
        self.volume_slider.set(0.7)
        self.volume_slider.pack(fill="x", padx=40, pady=10)

        # --- الجزء السفلي (أزرار الإدارة) ---
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(self.bottom_frame, text="+ Add Surahs", command=self.add_songs).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(self.bottom_frame, text="🗑 Delete Selected", fg_color="#BF616A", command=self.delete_song).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(self.bottom_frame, text="■ STOP", fg_color="#D08770", command=self.stop_song).pack(side="left", padx=10, expand=True)

    # --- الوظائف المنطقية (بدون تغيير في الجوهر) ---
    def add_songs(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3")])
        for f in files:
            self.song_paths.append(f)
            self.playlist.insert(tk.END, os.path.basename(f))

    def play_selected(self):
        try:
            selected_index = self.playlist.curselection()[0]
            self.current_song_path = self.song_paths[selected_index]
            audio = MP3(self.current_song_path)
            self.current_song_length = audio.info.length
            self.progress_slider.configure(to=self.current_song_length)
            pygame.mixer.music.load(self.current_song_path)
            pygame.mixer.music.play()
            self.start_time = 0
            self.is_paused = False
        except:
            messagebox.showwarning("Notice", "Please select a Surah first!")

    def play_next(self):
        try:
            current_index = self.playlist.curselection()[0]
            next_index = current_index + 1 if current_index + 1 < self.playlist.size() else 0
            self.playlist.selection_clear(0, tk.END)
            self.playlist.selection_set(next_index)
            self.play_selected()
        except: pass

    def toggle_pause(self):
        if not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
        else:
            pygame.mixer.music.unpause()
            self.is_paused = False

    def stop_song(self):
        pygame.mixer.music.stop()
        self.is_paused = False
        self.start_time = 0
        self.progress_slider.set(0)

    def seek_relative(self, seconds):
        if self.current_song_path:
            current_pos = self.start_time + (pygame.mixer.music.get_pos() / 1000)
            new_pos = max(0, min(current_pos + seconds, self.current_song_length))
            self.jump_to_time(new_pos)

    def jump_to_time(self, new_pos):
        pygame.mixer.music.play(start=new_pos)
        self.start_time = new_pos
        self.progress_slider.set(new_pos)

    def seek_music(self, val):
        if self.current_song_path:
            self.jump_to_time(float(val))

    def set_volume(self, val):
        pygame.mixer.music.set_volume(float(val))

    def delete_song(self):
        try:
            selected_index = self.playlist.curselection()[0]
            self.song_paths.pop(selected_index)
            self.playlist.delete(selected_index)
            self.stop_song()
        except: pass

    def check_events(self):
        for event in pygame.event.get():
            if event.type == self.SONG_END:
                if self.auto_play.get() and not self.is_paused:
                    self.play_next()
        self.after(100, self.check_events)

    def update_ui(self):
        if pygame.mixer.music.get_busy():
            actual_pos = self.start_time + (pygame.mixer.music.get_pos() / 1000)
            self.progress_slider.set(actual_pos)
            cur_min, cur_sec = divmod(int(actual_pos), 60)
            total_min, total_sec = divmod(int(self.current_song_length), 60)
            self.progress_label.configure(text=f"{cur_min:02d}:{cur_sec:02d} / {total_min:02d}:{total_sec:02d}")
        self.after(1000, self.update_ui)

if __name__ == "__main__":
    app = QuranicReciter()
    app.mainloop()