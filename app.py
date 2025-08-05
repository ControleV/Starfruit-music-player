# Metadata reader
from mutagen.easyid3 import EasyID3
from mutagen.wave import WAVE
from mutagen.mp3 import MP3

# Get music covers
from PIL import Image, ImageTk, ImageDraw
from mutagen.id3 import ID3, APIC
import io

# Graphic interface and file manipulation
from tkinter import ttk, DoubleVar
from tkinter import filedialog
from os import listdir, path
from random import shuffle
from os.path import join
import tkinter as tk
import pygame.mixer
import webbrowser

# Audio processing
from tools.equalizer.audio_processor import AudioProcessor
from tools.equalizer.equalizer import Eq

# System tray
from threading import Thread
import pystray

class ScrollingText:
    """Class for creating scrolling text in labels"""
    
    def __init__(self, label_widget, max_width=25, scroll_speed=150):
        self.label = label_widget
        self.max_width = max_width
        self.scroll_speed = scroll_speed
        self.original_text = ""
        self.current_position = 0
        self.is_scrolling = False
        self.scroll_job = None
        self.pause_counter = 0
        self.pause_duration = 10
        
    def set_text(self, text):
        """Sets the text and starts scrolling if necessary"""
        self.original_text = text
        self.current_position = 0
        self.pause_counter = 0
        
        # Stop previous scroll if running
        if self.scroll_job:
            self.label.after_cancel(self.scroll_job)
            self.scroll_job = None
        
        # If the text fits the maximum width, it just displays
        if len(text) <= self.max_width:
            self.label.config(text=text)
            self.is_scrolling = False
        else:
            self.is_scrolling = True
            self._scroll_text()
    
    def _scroll_text(self):
        """Internal function that scrolls the text"""
        if not self.is_scrolling or not self.original_text:
            return
        
        text = self.original_text
        
        # If it's at the end, take a break
        if self.current_position >= len(text):
            if self.pause_counter < self.pause_duration:
                self.pause_counter += 1
                # Show text from beginning while paused
                visible_text = text[:self.max_width]
                self.label.config(text=visible_text)
                self.scroll_job = self.label.after(self.scroll_speed, self._scroll_text)
                return
            else:
                self.current_position = 0
                self.pause_counter = 0
        
        extended_text = text + "   "
        
        # Calculates visible text
        if self.current_position < len(extended_text):
            visible_text = extended_text[self.current_position:self.current_position + self.max_width]
            
            # If visible text is smaller than max_width, complete with beginning
            if len(visible_text) < self.max_width and self.current_position + self.max_width > len(extended_text):
                remaining = self.max_width - len(visible_text)
                visible_text += text[:remaining]
        else:
            self.current_position = 0
            visible_text = text[:self.max_width]
    
        self.label.config(text=visible_text)
        self.current_position += 1
        
        # Schedule next scroll
        self.scroll_job = self.label.after(self.scroll_speed, self._scroll_text)
    
    def stop_scrolling(self):
        self.is_scrolling = False
        if self.scroll_job:
            self.label.after_cancel(self.scroll_job)
            self.scroll_job = None

def create_frutiger_button_image(width:int=40, height:int=40):
    """Creates a frutiger style to use as button background"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        color1 = (50, 19, 22)
        color2 = (33, 12, 14)
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        draw.rectangle([0, y, width, y+1], fill=(r, g, b))
    
    # Rounded border
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, width, height], radius=12, fill=255)
    img.putalpha(mask)

    return img

def update_playlist_box(playing_idx=None):
    """Updates the playlist widget with emoji on the playing music"""
    
    playlist_box.config(state="normal")
    playlist_box.delete("1.0", tk.END)
    
    for idx, item in enumerate(playlist):
        tag = "bg_red" if idx % 2 == 0 else "bg_darkred"
        prefix = "▶️ " if playing_idx is not None and idx == playing_idx else ""
        playlist_box.insert(tk.END, f"{prefix}{idx} - {item['nome']}\n", tag)
    
    playlist_box.config(state="disabled")

def time_formatting(seconds:int):
    minutes = seconds // 60
    seconds = seconds % 60

    return f"{minutes:02d}:{seconds:02d}"

def get_cover(mp3_path:str):
    """Returns a PIL.Image object of the MP3 cover, or None if none exists"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                image = Image.open(io.BytesIO(tag.data))
                return image
    except Exception:
        return None
    
def update_cover(right_frame:ttk.Frame, default_image:ImageTk.PhotoImage, current_index:int):
    try:
        music_path = playlist[current_index]['caminho']
        image = get_cover(music_path)
    except:
        image = False

    for widget in right_frame.grid_slaves(row=1, column=1):
        widget.destroy()

    if image:
        image = image.resize((120, 120))
        image_tk = ImageTk.PhotoImage(image)
        label_cover = tk.Label(right_frame, image=image_tk, bg="#5A262C", borderwidth=0, highlightthickness=0)
        label_cover.image = image_tk
        label_cover.grid(row=1, column=1, padx=10)
    else:
        label_cover = tk.Label(right_frame, image=default_image, bg="#5A262C", borderwidth=0, highlightthickness=0)
        label_cover.image = default_image
        label_cover.grid(row=1, column=1, padx=10)

class SystemTrayHandler:
    """Class to manage the system tray"""
    def __init__(self, root_window):
        self.root = root_window
        self.icon = None
        self.is_hidden = False
        self.tray_image = Image.open("images/default_cover.png").resize((64, 64))

    def create_tray_icon(self):
        """Creates the icon in the system tray"""
        menu = pystray.Menu(
            pystray.MenuItem("Show/Hide", self.toggle_window),
            pystray.MenuItem("Play/Pause", self.toggle_playback),
            pystray.MenuItem("Next", self.next_track),
            pystray.MenuItem("Previous", self.previous_track),
            pystray.MenuItem("Quit", self.quit_app)
        )
        self.icon = pystray.Icon(
            "Starfruit Music Player",
            icon=self.tray_image,
            title="Starfruit Music Player",
            menu=menu)
        return self.icon
    
    def toggle_window(self, icon=None, item=None):
        """Show/hide the main window"""
        if self.is_hidden:
            self.root.deiconify()
            self.root.lift()
            self.is_hidden = False
        else:
            self.root.withdraw()
            self.is_hidden = True
    
    def toggle_playback(self, icon=None, item=None):
        """Controls music play/pause"""
        try:
            if hasattr(self.root, '_play_music_func'):
                self.root._play_music_func(">")
        except Exception as e:
            print(e)
    
    def next_track(self, icon=None, item=None):
        """Next track"""
        pass
    
    def previous_track(self, icon=None, item=None):
        """Previous track"""
        pass
    
    def quit_app(self, icon=None, item=None):
        """Exit the application"""
        if self.icon:
            self.icon.stop()
        if hasattr(self.root, '_quit_app_func'):
            self.root._quit_app_func()
        else:
            self.root.quit()
    
    def run_tray(self):
        """Runs tray icon in separate thread"""
        if self.icon:
            self.icon.run()
    
    def stop_tray(self):
        """Stop the tray icon"""
        if self.icon:
            self.icon.stop()

def main():
    """App's main function"""
    pygame.mixer.init() # pygame.mixer is not the best option and will be changed later.

    root = tk.Tk()
    root.title("Starfruit Music Player")
    root.resizable(False, False)
    root.iconbitmap("StarfruitMusicPlayer_Ico.ico")

    global playlist
    playlist = []
    current_index = 0
    is_paused = False
    
    global tray_handler
    tray_handler = SystemTrayHandler(root)
    
    audio_processor = AudioProcessor()
    eq = Eq()
    eq.audio_processor = audio_processor
    
    def on_eq_change(gains):
        """Callback called when equalizer settings change"""
        print(f"Equalizer updated: Bass={gains[0]:.1f}, Mid={gains[1]:.1f}, Treble={gains[2]:.1f}")

        if playlist and 0 <= current_index < len(playlist):
            pygame.mixer.music.stop()
            play_music_w_eq()
    eq.set_callback(on_eq_change)

    # Fonts
    strong = ("Arial", 12, "bold")
    normal = ("Arial", 10)

    style = ttk.Style()
    style.theme_use('clam')

    style.configure("default.TFrame", background="#5A262C")
    style.configure("darker.TFrame", background="#321316")

    style.configure("texto_default.TLabel", background="#5A262C", foreground="#FFFFFF")
    style.configure("texto_darker.TLabel", background="#321316", foreground="#FFFFFF")
    style.configure("checkbox_default.TCheckbutton", background="#5A262C", foreground="#FFFFFF")
    style.map("checkbox_default.TCheckbutton",
            background=[("active", "#5A262C"), ("selected", "#5A262C")],
            foreground=[("active", "#FFFFFF"), ("selected", "#FFFFFF")]
            )
    style.configure("progressbar_default.Horizontal.TProgressbar",
        troughcolor="#321316",
        background="#e58015",
        bordercolor="#5A262C",
        lightcolor="#321316",
        darkcolor="#321316"
    )
    style.configure("default_scale.Horizontal.TScale")

    def create_frames():
        container_frame = ttk.Frame(root, style="default.TFrame")
        container_frame.pack(fill=tk.BOTH, expand=True)
        container_frame.grid_columnconfigure(1, weight=0)

        left_frame = ttk.Frame(container_frame, style="default.TFrame")
        left_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ns")

        right_frame = ttk.Frame(container_frame, style="default.TFrame")
        right_frame.grid(row=1, column=1, padx=10, pady=10, sticky="n")
        right_frame.grid_columnconfigure(1, weight=0, minsize=200)

        footer_frame = ttk.Frame(root, style="darker.TFrame")
        footer_frame.pack(fill=tk.BOTH)

        playlist_frame = ttk.Frame(left_frame, style="default.TFrame")
        playlist_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        details_frame = ttk.Frame(right_frame, style="default.TFrame")
        details_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        button_frame = ttk.Frame(right_frame, style="default.TFrame")
        button_frame.grid(row=30, column=1, padx=10, pady=10, sticky="ew")

        options_frame = ttk.Frame(right_frame, style="default.TFrame")
        options_frame.grid(row=31, column=1, padx=5, pady=5, sticky="ew")

        return {
            "container": container_frame,
            "left": left_frame,
            "right": right_frame,
            "footer": footer_frame,
            "playlist": playlist_frame,
            "details": details_frame,
            "button": button_frame,
            "options": options_frame
            }
    frames = create_frames()

    global nome_musica, nome_artista, nome_album
    music_name = ttk.Label(frames['right'], text="Music's name", font=strong, style="texto_default.TLabel", width=25, anchor="center")
    music_name.grid(row=0, column=1)

    artist_name = ttk.Label(frames['right'], text="Artist's name", style="texto_default.TLabel", width=25, anchor="center")
    artist_name.grid(row=2, column=1)

    album_name = ttk.Label(frames['right'], text="Album's name", style="texto_default.TLabel", width=25, anchor="center")
    album_name.grid(row=3, column=1)
    
    # Scrolling texts
    global scrolling_music, scrolling_artist, scrolling_album
    scrolling_music = ScrollingText(music_name, max_width=25, scroll_speed=150)
    scrolling_artist = ScrollingText(artist_name, max_width=25, scroll_speed=150)
    scrolling_album = ScrollingText(album_name, max_width=25, scroll_speed=150)

    # Timestamps
    global label_duration, label_total_duration
    label_duration = ttk.Label(frames["right"], text="00:00", font=normal, style="texto_default.TLabel")
    label_duration.grid(row=4, column=0)

    label_total_duration = ttk.Label(frames["right"], text="00:00", font=normal, style="texto_default.TLabel")
    label_total_duration.grid(row=4, column=2)

    # Progressbar
    progress_var = DoubleVar()
    progress_bar = ttk.Progressbar(
        frames["right"],
        variable=progress_var,
        maximum=100,
        mode='determinate',
        style='progressbar_default.Horizontal.TProgressbar'
    )
    progress_bar.grid(row=4, column=1, padx=5, pady=5, sticky='ew')

    # Playlist
    label = ttk.Label(frames["left"], text="Playlist", font=strong, style="texto_default.TLabel")
    label.grid(row=0, column=0, padx=10, pady=10)

    global playlist_box
    playlist_box = tk.Text(frames["left"], height=16, width=40, background="#321316")
    playlist_box.grid(row=1, column=0, padx=5, pady=5)
    playlist_box.config(state="disabled")

    playlist_box.tag_configure("bg_red", background="#f09696")
    playlist_box.tag_configure("bg_darkred", background="#e27e7e")

    # Buttons
    frutiger_img = create_frutiger_button_image()
    frutiger_img_tk = ImageTk.PhotoImage(frutiger_img)

    global back_button, play_button, next_button
    back_button = tk.Button(
        frames["button"],
        image=frutiger_img_tk,
        text="|<",
        compound="center",
        fg="white",
        bg="#5A262C",
        command=lambda:play_music("|<"),
        font=normal,
        bd=0,
        highlightthickness=0,
        activebackground="#5A262C",
        cursor="hand2",
        takefocus=False
        )
    back_button.grid(row=0, column=0, padx=5)

    play_button = tk.Button(
        frames["button"],
        image=frutiger_img_tk,
        text=">",
        compound="center",
        fg="white",
        bg="#5A262C",
        command=lambda:play_music(">"),
        font=normal,
        bd=0,
        highlightthickness=0,
        activebackground="#5A262C",
        cursor="hand2",
        takefocus=False
        )
    play_button.grid(row=0, column=1, padx=5)

    next_button = tk.Button(
        frames["button"],
        image=frutiger_img_tk,
        text=">|",
        compound="center",
        fg="white",
        bg="#5A262C",
        command=lambda:play_music(">|"),
        font=normal,
        bd=0,
        highlightthickness=0,
        activebackground="#5A262C",
        cursor="hand2",
        takefocus=False
        )
    next_button.grid(row=0, column=3, padx=5)

    random_button = tk.Button(
        frames["button"],
        image=frutiger_img_tk,
        text="><",
        compound="center",
        fg="white",
        bg="#5A262C",
        command=lambda:play_music("><"),
        font=normal,
        bd=0,
        highlightthickness=0,
        activebackground="#5A262C",
        cursor="hand2",
        takefocus=False
        )
    random_button.grid(row=0, column=4, padx=5)

    # Autoplay
    autoplay_var = tk.BooleanVar()
    autoplay_checkbox = ttk.Checkbutton(
        frames["options"],
        text="Autoplay",
        variable=autoplay_var,
        style="checkbox_default.TCheckbutton",
        cursor="hand2",
        takefocus=False)
    autoplay_checkbox.grid(row=0, column=0)

    # Volume slider
    volume_var = tk.DoubleVar(value=0.5)
    def set_volume(val):
        """Set pygame.music volume"""
        pygame.mixer.music.set_volume(float(val))
    volume_slider = ttk.Scale(
        frames["options"],
        from_=0,
        to=1,
        orient="horizontal",
        variable=volume_var,
        command=set_volume,
        length=120,
        style="default_scale.Horizontal.TScale"
    )
    volume_slider.grid(row=0, column=2, columnspan=2, padx=5)
    volume_label = ttk.Label(frames["options"], text="📢", style="texto_default.TLabel")
    volume_label.grid(row=0, column=1, columnspan=1, padx=5)
    set_volume(0.5)

    # Log
    label_log = ttk.Label(frames["footer"], text="Welcome to Starfruit Music Player! :3", style="texto_darker.TLabel")
    label_log.pack()

    # Cover
    default_image = Image.open("images/default_cover.png").resize((120, 120))
    default_image_tk = ImageTk.PhotoImage(default_image)
    update_cover(frames["right"], default_image_tk, current_index=0)

    # System tray
    def on_closing():
        """When the user tries to close the window, it minimizes to tray"""
        tray_handler.toggle_window()
        return "break"
    
    def quit_app():
        """Function to exit the application completely"""
        scrolling_music.stop_scrolling()
        scrolling_artist.stop_scrolling()
        scrolling_album.stop_scrolling()
        
        tray_handler.stop_tray()
        root.quit()

    # Menus
    def create_menus():
        """This function creates and configures all the app menus"""
        menu_bar = tk.Menu(frames["container"], background='blue', fg='white')

        file_menu_bar = tk.Menu(menu_bar, tearoff=0)
        file_menu_bar.add_command(label="Load folder", command=lambda:load_folder())
        file_menu_bar.add_separator()
        file_menu_bar.add_command(label="Minimize to tray", command=tray_handler.toggle_window)
        file_menu_bar.add_separator()
        file_menu_bar.add_command(label="Quit", command=quit_app)
        menu_bar.add_cascade(label="File", menu=file_menu_bar)

        tools_menu_bar = tk.Menu(menu_bar, tearoff=0)
        tools_menu_bar.add_command(label="Equalizer", command=lambda:eq.open_window())
        menu_bar.add_cascade(label="Tools", menu=tools_menu_bar)

        about_menu_bar = tk.Menu(menu_bar, tearoff=0)
        about_menu_bar.add_command(label="Github", command=lambda:webbrowser.open('https://github.com/ControleV/Starfruit-music-player'))
        menu_bar.add_cascade(label="About", menu=about_menu_bar)

        root.config(menu=menu_bar)
    create_menus()

    def play_music_w_eq():
        """Plays the current song applying equalization"""
        if playlist and 0 <= current_index < len(playlist):
            original_path = playlist[current_index]['caminho']
            
            try:
                # Check if equalizer is active and process accordingly
                if eq.enabled:
                    processed_path = eq.process_current_track(original_path)
                    # Check if processing was successful
                    if processed_path != original_path and path.exists(processed_path):
                        pygame.mixer.music.load(processed_path)
                        print(f"Playing with equalization: {path.basename(original_path)}")
                    else:
                        pygame.mixer.music.load(original_path)
                        print(f"Playing without equalization (File not processed): {path.basename(original_path)}")
                else:
                    # Equalizer disabled - load original file directly
                    pygame.mixer.music.load(original_path)
                    print(f"Playing the original file (EQ disabled): {path.basename(original_path)}")
                
                pygame.mixer.music.play()
                play_button.config(text="||")
                is_paused = False
                
            except Exception as e:
                print(f"An error has occurred: {e}")
                try:
                    pygame.mixer.music.load(original_path)
                    pygame.mixer.music.play()
                    play_button.config(text="||")
                    is_paused = False
                    print(f"Playing original file: {path.basename(original_path)}")
                except Exception as e2:
                    print(f"Fatal error: {e2}")
                    play_button.config(text=">")

    def play_music(option:str):
        """Plays the song at the specified index in the playlist"""
        nonlocal current_index
        nonlocal is_paused

        # Handle play/pause first (without unloading music)
        if option == ">":
            if pygame.mixer.music.get_busy() and not is_paused:
                # Music is playing, so pause it
                pygame.mixer.music.pause()
                play_button.config(text=">")
                is_paused = True
                return
            elif is_paused:
                # Music is paused, so unpause it
                pygame.mixer.music.unpause()
                play_button.config(text="||")
                is_paused = False
                return

        # For other operations (change tracks), unload and clear cache
        pygame.mixer.music.unload()
        audio_processor.clear_cache()
        
        if option == "|<": current_index -= 1
        elif option == ">|": current_index += 1
        elif option == "><":
            if playlist:
                shuffle(playlist)
                current_index = 0
                play_music_w_eq()
                update_playlist_box(playing_idx=current_index)
                scrolling_music.set_text(playlist[current_index]['nome'])
                scrolling_artist.set_text(f"Artist: {playlist[current_index]['artista']}")
                scrolling_album.set_text(f"Album: {playlist[current_index]['album']}")
                update_cover(frames["right"], default_image_tk, current_index)
                return

        if playlist:
            if current_index < 0: current_index = 0
            elif current_index >= len(playlist): current_index = 0

            play_music_w_eq()

            scrolling_music.set_text(playlist[current_index]['nome'])
            scrolling_artist.set_text(f"Artist: {playlist[current_index]['artista']}")
            scrolling_album.set_text(f"Album: {playlist[current_index]['album']}")

            update_playlist_box(playing_idx=current_index)
            update_cover(frames["right"], default_image_tk, current_index)

            return True
        return False
    
    tray_handler.next_track = lambda icon=None, item=None: play_music(">|")
    tray_handler.previous_track = lambda icon=None, item=None: play_music("|<")
    
    root._play_music_func = play_music
    root._quit_app_func = quit_app
    
    def load_folder():
        """Load a folder and add music files to the playlist"""
        nonlocal current_index
        current_index = 0

        folder = filedialog.askdirectory()
        if folder:
            pygame.mixer.music.stop()
            play_button.config(text=">")
            playlist_box.config(state="normal")
            playlist_box.delete("1.0", tk.END)
            playlist.clear()

            for idx, item in enumerate(listdir(folder)):
                item_lower = item.lower()
                if item_lower.endswith('.mp3') or item_lower.endswith('.wav'):
                    full_path = join(folder, item)
                    artist = "Unknown"
                    album = "Unknown"

                    if item_lower.endswith('.mp3'):
                        audio = MP3(full_path, ID3=EasyID3)
                        artist = audio.get('artist', ['Unknown'])[0]
                        album = audio.get('album', ['Unknown'])[0]

                    elif item_lower.endswith('.wav'):
                        audio = WAVE(full_path)
                        artist = audio.get('artist', ['Unknown'])[0] if 'artist' in audio else "Unknown"
                        album = audio.get('album', ['Unknown'])[0] if 'album' in audio else "Unknown"

                    playlist.append({
                        'nome': item[:-4],
                        'caminho': full_path,
                        'artista': artist,
                        'album': album
                    })
                    
                    tag = "bg_red" if idx % 2 == 0 else "bg_darkred"
                    playlist_box.insert(tk.END, f"{idx} - {item[:-4]}\n", tag)
                    
            playlist_box.config(state="disabled")

            if playlist:
                play_music(">")

    def check_music_end():
        """Check if the song has finished, and if so, play the next one automatically, if the autoplay option is checked."""
        if (
            autoplay_var.get()
            and playlist
            and not is_paused
            and not pygame.mixer.music.get_busy()
        ):
            play_music(">|")
                
        root.after(500, check_music_end)
    def music_stats():
        """Gets the current status of the song"""

        if playlist and 0 <= current_index < len(playlist):
            path = playlist[current_index]['caminho']

            pos_ms = pygame.mixer.music.get_pos()
            pos_sec = max(0, pos_ms // 1000)

            if path.lower().endswith('.mp3'):
                audio = MP3(path)
                total_duration = int(audio.info.length)

            elif path.lower().endswith('.wav'):
                audio = WAVE(path)
                total_duration = int(audio.info.length)

            else:
                total_duration = 0

            label_duration.config(text=time_formatting(pos_sec))
            label_total_duration.config(text=time_formatting(total_duration))

            # Update progress bar
            if total_duration > 0:
                progress = (pos_sec / total_duration) * 100
                progress_var.set(progress)

            else:
                progress_var.set(0)

        root.after(500, music_stats)

    check_music_end()
    music_stats()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    tray_icon = tray_handler.create_tray_icon()
    tray_thread = Thread(target=tray_handler.run_tray, daemon=True)
    tray_thread.start()
    
    root.mainloop()
    pygame.mixer.music.unload()
    audio_processor.clear_cache()
    tray_handler.stop_tray()

if __name__ == "__main__":
    main()
