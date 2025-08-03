from ctypes import CDLL, POINTER, c_float, c_int
import tkinter as tk
import os
import sys

# Adiciona o diretório parent ao path para importar audio_processor
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from audio_processor import AudioProcessor

class Eq:
    def __init__(self):
        # Configurações do equalizador
        self.eq_gains = [1.0, 1.0, 1.0]  # Grave, Médio, Agudo
        self.audio_processor = AudioProcessor()
        self.callback = None  # Callback para notificar mudanças no app principal
        self.enabled = False
        
    def set_callback(self, callback_func):
        """Define função callback para comunicar com o player principal"""
        self.callback = callback_func
        
    def process_current_track(self, input_file):
        """Processa a faixa atual com as configurações do equalizador"""
        if not self.enabled:
            return input_file  # Retorna arquivo original se equalizador desabilitado
        return self.audio_processor.process_file(input_file)
        
    def apply_eq_to_audio(self, audio_data, sample_rate):
        """Aplica equalizador real ao áudio usando o processador"""
        return self.audio_processor.apply_equalizer(audio_data, sample_rate)

    def apply_eq(self, slider1, slider2, slider3):
        # Só aplica se o equalizador estiver ativo
        if not self.enabled:
            self.status_label.config(text="Equalizador está desativado")
            return
            
        # Atualiza os ganhos do equalizador
        self.eq_gains = [slider1.get(), slider2.get(), slider3.get()]
        self.audio_processor.set_eq_gains(self.eq_gains[0], self.eq_gains[1], self.eq_gains[2])
        
        # Atualiza o status
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"EQ: Graves={self.eq_gains[0]:.1f} Médios={self.eq_gains[1]:.1f} Agudos={self.eq_gains[2]:.1f}")
        
        print(f"Equalizer settings updated: Grave={self.eq_gains[0]:.1f}, Médio={self.eq_gains[1]:.1f}, Agudo={self.eq_gains[2]:.1f}")
        
        # Notifica o player principal sobre a mudança
        if self.callback:
            self.callback(self.eq_gains)

    def open_window(self):
        window = tk.Toplevel()
        window.title("Equalizer")
        window.resizable(False, False)
        window.configure(bg="#5A262C")

        # Frame principal
        main_frame = tk.Frame(window, bg="#5A262C")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Título
        title_label = tk.Label(main_frame, text="Equalizador de Áudio", 
                              font=("Arial", 14, "bold"), 
                              bg="#5A262C", fg="white")
        title_label.pack(pady=(0, 20))

        # Sliders
        slider1 = tk.Scale(main_frame, from_=0, to=2, resolution=0.1, 
                          orient=tk.HORIZONTAL, label="Graves (250Hz)", 
                          bg="#5A262C", fg="white", highlightbackground="#5A262C",
                          length=300, font=("Arial", 10))
        slider1.set(1.0)  # Valor padrão
        slider1.pack(pady=10)

        slider2 = tk.Scale(main_frame, from_=0, to=2, resolution=0.1, 
                          orient=tk.HORIZONTAL, label="Médios (2kHz)", 
                          bg="#5A262C", fg="white", highlightbackground="#5A262C",
                          length=300, font=("Arial", 10))
        slider2.set(1.0)  # Valor padrão
        slider2.pack(pady=10)

        slider3 = tk.Scale(main_frame, from_=0, to=2, resolution=0.1, 
                          orient=tk.HORIZONTAL, label="Agudos (8kHz)", 
                          bg="#5A262C", fg="white", highlightbackground="#5A262C",
                          length=300, font=("Arial", 10))
        slider3.set(1.0)  # Valor padrão
        slider3.pack(pady=10)

        # Botões
        button_frame = tk.Frame(main_frame, bg="#5A262C")
        button_frame.pack(pady=20)

        apply_btn = tk.Button(button_frame, text="Aplicar Equalizador", 
                             command=lambda: self.apply_eq(slider1, slider2, slider3),
                             bg="#321316", fg="white", font=("Arial", 10, "bold"),
                             padx=20, pady=5, cursor="hand2")
        apply_btn.pack(side="left", padx=5)

        reset_btn = tk.Button(button_frame, text="Reset", 
                             command=lambda: self.reset_eq(slider1, slider2, slider3),
                             bg="#4A1A1D", fg="white", font=("Arial", 10),
                             padx=20, pady=5, cursor="hand2")
        reset_btn.pack(side="left", padx=5)

        # Botão para ativar/desativar equalizador
        self.toggle_btn = tk.Button(button_frame, text="Ativar EQ", 
                                   command=lambda: self.toggle_eq(slider1, slider2, slider3),
                                   bg="#5A1A1D", fg="white", font=("Arial", 10),
                                   padx=20, pady=5, cursor="hand2")
        self.toggle_btn.pack(side="left", padx=5)

        # Label de status
        self.status_label = tk.Label(main_frame, text="Pronto para usar", 
                                    bg="#5A262C", fg="#CCCCCC", font=("Arial", 9))
        self.status_label.pack(pady=(10, 0))

    def reset_eq(self, slider1, slider2, slider3):
        """Reset todos os sliders para 1.0"""
        slider1.set(1.0)
        slider2.set(1.0)
        slider3.set(1.0)
        self.eq_gains = [1.0, 1.0, 1.0]
        self.audio_processor.set_eq_gains(1.0, 1.0, 1.0)
        self.status_label.config(text="Equalizador resetado para padrão")
        
        # Notifica o player principal
        if self.callback:
            self.callback(self.eq_gains)
    
    def toggle_eq(self, slider1, slider2, slider3):
        """Ativa/desativa o equalizador"""
        self.enabled = not self.enabled
        
        if self.enabled:
            self.toggle_btn.config(text="Desativar EQ")
            self.status_label.config(text="Equalizador ativado")
            # Aplica as configurações atuais
            self.apply_eq(slider1, slider2, slider3)
        else:
            self.toggle_btn.config(text="Ativar EQ")
            self.status_label.config(text="Equalizador desativado")
            # Limpa o cache para forçar uso do arquivo original
            self.audio_processor.clear_cache()
            # Notifica o player para usar arquivo original
            if self.callback:
                self.callback([1.0, 1.0, 1.0])  # Valores neutros
