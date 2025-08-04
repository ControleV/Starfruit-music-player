import tkinter as tk
try:
    from .audio_processor import AudioProcessor
except ImportError:
    from audio_processor import AudioProcessor

class Eq:
    """Class to manage the audio equalizer in real time"""
    def __init__(self):
        self.eq_gains = [1.0, 1.0, 1.0]
        self.audio_processor = AudioProcessor()
        self.callback = None  # Callback to notify changes in the main app
        self.enabled = False
        
    def set_callback(self, callback_func):
        """Defines a callback function to communicate with the main player"""
        self.callback = callback_func
        
    def process_current_track(self, input_file):
        """Process the current track with the equalizer settings"""
        if not self.enabled:
            return input_file  # If not enabled, return original file
        return self.audio_processor.process_file(input_file)
        
    def apply_eq_to_audio(self, audio_data, sample_rate):
        """Applies real equalizer to audio using the processor"""
        return self.audio_processor.apply_equalizer(audio_data, sample_rate)

    def apply_eq(self, slider1, slider2, slider3):
        if not self.enabled:
            self.status_label.config(text="Equalizer is disabled")
            return

        # Update equalizer gains
        self.eq_gains = [slider1.get(), slider2.get(), slider3.get()]
        self.audio_processor.set_eq_gains(self.eq_gains[0], self.eq_gains[1], self.eq_gains[2])

        # Update status
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"EQ: Bass={self.eq_gains[0]:.1f} Mid={self.eq_gains[1]:.1f} Treble={self.eq_gains[2]:.1f}")

        print(f"Equalizer settings updated: Bass={self.eq_gains[0]:.1f}, Mid={self.eq_gains[1]:.1f}, Treble={self.eq_gains[2]:.1f}")

        if self.callback:
            self.callback(self.eq_gains)

    def open_window(self):
        window = tk.Toplevel()
        window.title("Equalizer")
        window.resizable(False, False)
        window.iconbitmap("StarfruitMusicPlayer_Ico.ico")
        window.configure(bg="#5A262C")

        # Main frame
        main_frame = tk.Frame(window, bg="#5A262C")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        title_label = tk.Label(main_frame, text="Audio Equalizer", 
                              font=("Arial", 14, "bold"), 
                              bg="#5A262C", fg="white")
        title_label.pack(pady=(0, 20))

        title_label = tk.Label(main_frame, text="⚠️ Warning: SMP is made to play music with low hardware cost.\nActivating equalizer can drastically decrease your performance!", 
                              font=("Arial", 10), 
                              bg="#5A262C", fg="yellow")
        title_label.pack(pady=(0, 20))

        slider1 = tk.Scale(main_frame, from_=0, to=2, resolution=0.1, 
                          orient=tk.HORIZONTAL, label="Bass (250Hz)", 
                          bg="#5A262C", fg="white", highlightbackground="#5A262C",
                          length=300, font=("Arial", 10))
        slider1.set(self.eq_gains[0])
        slider1.pack(pady=10)

        slider2 = tk.Scale(main_frame, from_=0, to=2, resolution=0.1, 
                          orient=tk.HORIZONTAL, label="Mid (2kHz)", 
                          bg="#5A262C", fg="white", highlightbackground="#5A262C",
                          length=300, font=("Arial", 10))
        slider2.set(self.eq_gains[1])
        slider2.pack(pady=10)

        slider3 = tk.Scale(main_frame, from_=0, to=2, resolution=0.1, 
                          orient=tk.HORIZONTAL, label="Treble (8kHz)", 
                          bg="#5A262C", fg="white", highlightbackground="#5A262C",
                          length=300, font=("Arial", 10))
        slider3.set(self.eq_gains[2])
        slider3.pack(pady=10)

        # Buttons
        button_frame = tk.Frame(main_frame, bg="#5A262C")
        button_frame.pack(pady=20)

        apply_btn = tk.Button(button_frame, text="Apply Equalizer", 
                             command=lambda: self.apply_eq(slider1, slider2, slider3),
                             bg="#321316", fg="white", font=("Arial", 10, "bold"),
                             padx=20, pady=5, cursor="hand2")
        apply_btn.pack(side="left", padx=5)

        reset_btn = tk.Button(button_frame, text="Reset", 
                             command=lambda: self.reset_eq(slider1, slider2, slider3),
                             bg="#4A1A1D", fg="white", font=("Arial", 10),
                             padx=20, pady=5, cursor="hand2")
        reset_btn.pack(side="left", padx=5)

        self.toggle_btn = tk.Button(button_frame, text="Toggle EQ", 
                                   command=lambda: self.toggle_eq(slider1, slider2, slider3),
                                   bg="#5A1A1D", fg="white", font=("Arial", 10),
                                   padx=20, pady=5, cursor="hand2")
        self.toggle_btn.pack(side="left", padx=5)

        self.status_label = tk.Label(main_frame, text="Ready to use", 
                                    bg="#5A262C", fg="#CCCCCC", font=("Arial", 9))
        self.status_label.pack(pady=(10, 0))
        
        # Update initial button state and status based on current state
        if self.enabled:
            self.toggle_btn.config(text="Disable EQ")
            self.status_label.config(text=f"EQ: Bass={self.eq_gains[0]:.1f} Mid={self.eq_gains[1]:.1f} Treble={self.eq_gains[2]:.1f}")
        else:
            self.toggle_btn.config(text="Enable EQ")
            self.status_label.config(text="Equalizer disabled")

    def reset_eq(self, slider1, slider2, slider3):
        """Reset all sliders to 1.0"""
        slider1.set(1.0)
        slider2.set(1.0)
        slider3.set(1.0)
        self.eq_gains = [1.0, 1.0, 1.0]
        self.audio_processor.set_eq_gains(1.0, 1.0, 1.0)
        self.status_label.config(text="Equalizer reset to default")

        # Notify the main player
        if self.callback:
            self.callback(self.eq_gains)
    
    def toggle_eq(self, slider1, slider2, slider3):
        """Enable or disable the equalizer"""
        self.enabled = not self.enabled
        
        if self.enabled:
            self.toggle_btn.config(text="Disable EQ")
            self.status_label.config(text="Equalizer enabled")
            self.apply_eq(slider1, slider2, slider3)
        else:
            self.toggle_btn.config(text="Enable EQ")
            self.status_label.config(text="Equalizer disabled")

            self.audio_processor.clear_cache()
            self.audio_processor.clean_old_eq_files(max_age_hours=0)  # Remove ALL eq_ files
            
            print("Equalizer disabled - temporary files removed")

            if self.callback:
                self.callback([1.0, 1.0, 1.0])
