import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pygame
import os
from mutagen.mp3 import MP3
import arabic_reshaper
from bidi.algorithm import get_display

# إعداد المظهر
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class QuranicReciter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("مشغل القرآن الكريم")
        self.geometry("1100x750")
        
        pygame.init()
        pygame.mixer.init()
        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)

        # متغيرات الحالة
        self.playlists_data = {"القائمة الرئيسية": []} 
        self.active_playlist_name = "القائمة الرئيسية"
        self.current_song_path = ""
        self.current_song_length = 0
        self.start_offset = 0
        self.is_paused = False
        self.auto_play = tk.BooleanVar(value=True)

        self.create_widgets()
        # تقليل حجم الخط للقائمة في دالة التوسيع
        self.bind("<Configure>", self.rescale_fonts)
        self.check_events()
        self.update_ui()

    def fix_ar(self, text):
        if not text: return ""
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)

    def rescale_fonts(self, event=None):
        width = self.winfo_width()
        # تكبير عنوان القائمة الحالية بشكل ملحوظ
        header_size = max(28, int(width / 30)) 
        # تصغير حجم خط السور في القائمة
        list_size = max(13, int(width / 70)) 
        
        self.header.configure(font=("Arial", header_size, "bold"))
        self.surah_listbox.configure(font=("Arial", list_size))

    def create_widgets(self):
        # 1. العنوان العلوي (مكبر)
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", pady=20, padx=20)

        self.header = ctk.CTkLabel(self.top_frame, text=self.fix_ar(f"القائمة: {self.active_playlist_name}"), text_color="#1DB954")
        self.header.pack(side="right")

        self.switch_btn = ctk.CTkButton(self.top_frame, text=self.fix_ar("تبديل القائمة ⇄"), width=160, height=45, font=("Arial", 14, "bold"), command=self.show_playlist_selector)
        self.switch_btn.pack(side="left")

        # 2. الحاوية المركزية بنظام Grid (60% قائمة / 40% تحكم)
        self.center_container = ctk.CTkFrame(self, fg_color="transparent")
        self.center_container.pack(fill="both", expand=True, padx=20)
        
        self.center_container.grid_columnconfigure(0, weight=2) # 40% التحكم
        self.center_container.grid_columnconfigure(1, weight=3) # 60% القائمة
        self.center_container.grid_rowconfigure(0, weight=1)

        # --- الجزء الأيمن: قائمة السور (60%) ---
        self.right_half = ctk.CTkFrame(self.center_container, corner_radius=15)
        self.right_half.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ctk.CTkLabel(self.right_half, text=self.fix_ar("قائمة السور"), font=("Arial", 16, "bold")).pack(pady=10)
        
        self.surah_listbox = tk.Listbox(self.right_half, bg="#1e1e1e", fg="#e0e0e0", borderwidth=0, 
                                       highlightthickness=1, highlightcolor="#1DB954", selectbackground="#1DB954", justify="right")
        self.surah_listbox.pack(fill="both", expand=True, padx=15, pady=15)

        # --- الجزء الأيسر: لوحة التحكم (40%) ---
        self.left_half = ctk.CTkFrame(self.center_container, corner_radius=15)
        self.left_half.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ctk.CTkLabel(self.left_half, text=self.fix_ar("لوحة التحكم"), font=("Arial", 18, "bold")).pack(pady=10)
        
        btn_font_big = ("Arial", 30, "bold")
        
        self.play_btn = ctk.CTkButton(self.left_half, text="▶", width=180, height=80, font=btn_font_big, fg_color="#1DB954", command=self.play_selected)
        self.play_btn.pack(pady=5)
        
        self.pause_btn = ctk.CTkButton(self.left_half, text="⏸", width=180, height=80, font=btn_font_big, fg_color="#EBCB8B", text_color="black", command=self.toggle_pause)
        self.pause_btn.pack(pady=5)

        # أزرار التقديم والتأخير
        self.seek_btns_frame = ctk.CTkFrame(self.left_half, fg_color="transparent")
        self.seek_btns_frame.pack(pady=10)
        ctk.CTkButton(self.seek_btns_frame, text="⏩ +5s", width=85, height=45, command=lambda: self.seek_relative(5)).pack(side="left", padx=5)
        ctk.CTkButton(self.seek_btns_frame, text="⏪ -5s", width=85, height=45, command=lambda: self.seek_relative(-5)).pack(side="left", padx=5)

        # أزرار الإدارة (إضافة وحذف)
        self.add_btn = ctk.CTkButton(self.left_half, text=self.fix_ar("إضافة مقاطع +"), width=180, height=45, fg_color="#5E81AC", command=self.add_surahs)
        self.add_btn.pack(pady=5)

        self.delete_btn = ctk.CTkButton(self.left_half, text=self.fix_ar("حذف السورة المحددة 🗑"), width=180, height=45, fg_color="#BF616A", command=self.delete_selected_surah)
        self.delete_btn.pack(pady=5)

        self.auto_cb = ctk.CTkCheckBox(self.left_half, text=self.fix_ar("تشغيل تلقائي"), variable=self.auto_play)
        self.auto_cb.pack(pady=15)

        # 3. شريط التقدم السفلي
        self.bottom_panel = ctk.CTkFrame(self, height=100, corner_radius=15)
        self.bottom_panel.pack(fill="x", padx=20, pady=20)

        self.progress_label = ctk.CTkLabel(self.bottom_panel, text="00:00 / 00:00", font=("Consolas", 20, "bold"))
        self.progress_label.pack(side="right", padx=20)

        self.progress_slider = ctk.CTkSlider(self.bottom_panel, from_=0, to=100, height=20, command=self.seek_music)
        self.progress_slider.set(0)
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=20)

    # --- المنطق الوظيفي ---
    def delete_selected_surah(self):
        """حذف السورة المختارة من القائمة الحالية"""
        selection = self.surah_listbox.curselection()
        if selection:
            idx = selection[0]
            # حذف من البيانات
            del self.playlists_data[self.active_playlist_name][idx]
            # تحديث الواجهة
            self.refresh_surah_list()
            pygame.mixer.music.stop()
        else:
            messagebox.showinfo("تنبيه", "يرجى اختيار سورة لحذفها أولاً")

    def seek_relative(self, seconds):
        if self.current_song_path:
            current_pos = self.start_offset + (pygame.mixer.music.get_pos() / 1000)
            new_pos = max(0, min(current_pos + seconds, self.current_song_length))
            self.seek_music(new_pos)

    def show_playlist_selector(self):
        selector = ctk.CTkToplevel(self)
        selector.title(self.fix_ar("إدارة القوائم"))
        selector.geometry("400x500")
        selector.attributes("-topmost", True)
        lb = tk.Listbox(selector, bg="#2b2b2b", fg="#1DB954", font=("Arial", 14), justify="right")
        lb.pack(fill="both", expand=True, padx=20, pady=10)
        for name in self.playlists_data.keys(): lb.insert(tk.END, self.fix_ar(name))

        def select():
            if lb.curselection():
                self.active_playlist_name = list(self.playlists_data.keys())[lb.curselection()[0]]
                self.header.configure(text=self.fix_ar(f"القائمة: {self.active_playlist_name}"))
                self.refresh_surah_list()
                selector.destroy()

        def add_new():
            dialog = ctk.CTkInputDialog(text=self.fix_ar("اسم القائمة:"), title="New")
            new_name = dialog.get_input()
            if new_name:
                self.playlists_data[new_name] = []
                lb.insert(tk.END, self.fix_ar(new_name))

        ctk.CTkButton(selector, text=self.fix_ar("اختيار"), command=select).pack(pady=5)
        ctk.CTkButton(selector, text=self.fix_ar("قائمة جديدة +"), fg_color="#555555", command=add_new).pack(pady=5)

    def refresh_surah_list(self):
        self.surah_listbox.delete(0, tk.END)
        for path in self.playlists_data[self.active_playlist_name]:
            self.surah_listbox.insert(tk.END, self.fix_ar(os.path.basename(path)))

    def add_surahs(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3")])
        for f in files: self.playlists_data[self.active_playlist_name].append(f)
        self.refresh_surah_list()

    def play_selected(self):
        try:
            sel = self.surah_listbox.curselection()
            if not sel: return
            self.current_song_path = self.playlists_data[self.active_playlist_name][sel[0]]
            audio = MP3(self.current_song_path)
            self.current_song_length = audio.info.length
            self.progress_slider.configure(to=self.current_song_length)
            pygame.mixer.music.load(self.current_song_path)
            pygame.mixer.music.play()
            self.start_offset = 0
            self.is_paused = False
        except: pass

    def seek_music(self, val):
        if self.current_song_path:
            pygame.mixer.music.play(start=float(val))
            self.start_offset = float(val)

    def toggle_pause(self):
        if self.is_paused: pygame.mixer.music.unpause(); self.is_paused = False
        else: pygame.mixer.music.pause(); self.is_paused = True

    def check_events(self):
        for event in pygame.event.get():
            if event.type == self.SONG_END and self.auto_play.get():
                sel = self.surah_listbox.curselection()
                if sel:
                    idx = sel[0]
                    next_idx = (idx + 1) if (idx + 1 < self.surah_listbox.size()) else 0
                    self.surah_listbox.selection_clear(0, tk.END)
                    self.surah_listbox.selection_set(next_idx)
                    self.play_selected()
        self.after(100, self.check_events)

    def update_ui(self):
        if pygame.mixer.music.get_busy():
            pos = self.start_offset + (pygame.mixer.music.get_pos() / 1000)
            self.progress_slider.set(pos)
            cur_min, cur_sec = divmod(int(pos), 60)
            total_min, total_sec = divmod(int(self.current_song_length), 60)
            self.progress_label.configure(text=f"{cur_min:02d}:{cur_sec:02d} / {total_min:02d}:{total_sec:02d}")
        self.after(500, self.update_ui)

if __name__ == "__main__":
    app = QuranicReciter()
    app.mainloop()