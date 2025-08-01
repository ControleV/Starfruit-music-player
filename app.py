# Leitura de metadados
from mutagen.easyid3 import EasyID3
from mutagen.wave import WAVE
from mutagen.mp3 import MP3

# Coletar a capa das músicas
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk
import io

# Interface gráfica e manipulação de arquivos
from tkinter import filedialog
from tkinter import ttk, font
from random import shuffle
from os.path import join
from os import listdir
import tkinter as tk
import pygame.mixer


def atualizar_playlist_box(tocando_idx=None):
    """Atualiza o Text widget mostrando a playlist, com emoji na música tocando."""
    
    playlist_box.config(state="normal")
    playlist_box.delete("1.0", tk.END)
    
    for idx, item in enumerate(playlist):
        tag = "bg_red" if idx % 2 == 0 else "bg_darkred"
        prefixo = "▶️ " if tocando_idx is not None and idx == tocando_idx else ""
        playlist_box.insert(tk.END, f"{prefixo}{idx} - {item['nome']}\n", tag)
    
    playlist_box.config(state="disabled")

def formatar_tempo(segundos:int):
    minutos = segundos // 60
    segundos = segundos % 60

    return f"{minutos:02d}:{segundos:02d}"

def obter_capa_mp3(caminho_mp3:str):
    """Retorna um objeto PIL.Image da capa do MP3, ou None de não houver."""

    try:
        audio = MP3(caminho_mp3, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                imagem = Image.open(io.BytesIO(tag.data))
                return imagem
    except Exception:
        pass

    return None
def atualizar_capa(right_frame:ttk.Frame, imagem_padrao_tk:ImageTk.PhotoImage, indice_atual:int):
    try:
        caminho = playlist[indice_atual]['caminho']
        imagem = obter_capa_mp3(caminho)
    except:
        imagem = False

    if imagem:
        imagem = imagem.resize((120, 120))
        imagem_tk = ImageTk.PhotoImage(imagem)
        label_capa = tk.Label(right_frame, image=imagem_tk, bg="#5A262C", borderwidth=0, highlightthickness=0)
        label_capa.image = imagem_tk # Evita garbage collection
        label_capa.grid(row=1, column=1, padx=10)
    else:
        label_capa = tk.Label(right_frame, image=imagem_padrao_tk, bg="#5A262C", borderwidth=0, highlightthickness=0)
        label_capa.image = imagem_padrao_tk
        label_capa.grid(row=1, column=1, padx=10)

def main():
    """Função principal para iniciar o aplicativo."""

    pygame.mixer.init()

    root = tk.Tk()
    root.title("Starfruit Music Player")
    root.resizable(False, False)


    # Variável global para a lista de reprodução
    global playlist
    playlist = []
    indice_atual = 0
    is_paused = False

    # Fontes
    strong = ("Arial", 12, "bold")
    normal = ("Arial", 10)

    # Definindo layouts para estilização
    style = ttk.Style()
    style.configure("default.TFrame", background="#5A262C")
    style.configure("darker.TFrame", background="#321316")


    # Estlização de widgets
    style.configure("texto_default.TLabel", background="#5A262C", foreground="#FFFFFF")
    style.configure("texto_darker.TLabel", background="#321316", foreground="#FFFFFF")
    style.configure("botao_default.TButton", background="#5A262C")
    style.configure("checkbox_default.TCheckbutton", background="#5A262C", foreground="#FFFFFF")


    # Frame principal
    container_frame = ttk.Frame(root, style="default.TFrame")
    container_frame.pack(fill=tk.BOTH, expand=True)

    # Barra de menu
    menu_bar = tk.Menu(container_frame, background='blue', fg='white')
    file_menu_bar = tk.Menu(menu_bar, tearoff=0)

    # Frame Esquerdo
    left_frame = ttk.Frame(container_frame, style="default.TFrame")
    left_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ns")

    # Frame Direito
    right_frame = ttk.Frame(container_frame, style="default.TFrame")
    right_frame.grid(row=1, column=1, padx=10, pady=10, sticky="n")

    # Frame do rodapé
    footer_frame = ttk.Frame(root, style="darker.TFrame")
    footer_frame.pack(fill=tk.BOTH)

    # Frame para a Lista de Reprodução
    playlist_frame = ttk.Frame(left_frame, style="default.TFrame")
    playlist_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # Frame para os detalhes da música
    details_frame = ttk.Frame(right_frame, style="default.TFrame")
    details_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    # Frame para os botões na mesma linha
    button_frame = ttk.Frame(right_frame, style="default.TFrame")
    button_frame.grid(row=30, column=1, padx=10, pady=10, sticky="ew")





    global nome_musica, nome_artista, nome_album
    nome_musica = ttk.Label(right_frame, text="Nome da música", font=strong, style="texto_default.TLabel")
    nome_musica.grid(row=0, column=1)

    nome_artista = ttk.Label(right_frame, text="Nome do artista", style="texto_default.TLabel")
    nome_artista.grid(row=2, column=1)

    nome_album = ttk.Label(right_frame, text="Nome do album", style="texto_default.TLabel")
    nome_album.grid(row=3, column=1)


    # Estatísticas da música
    global label_duracao, label_duracao_total
    label_duracao = ttk.Label(right_frame, text="00:00", font=normal, style="texto_default.TLabel")
    label_duracao.grid(row=4, column=0)

    label_duracao_total = ttk.Label(right_frame, text="00:00", font=normal, style="texto_default.TLabel")
    label_duracao_total.grid(row=4, column=2)


    # Lista de reprodução
    label = ttk.Label(left_frame, text="Lista de reprodução", font=strong, style="texto_default.TLabel")
    label.grid(row=0, column=0, padx=10, pady=10)

    global playlist_box
    playlist_box = tk.Text(left_frame, height=15, width=40, background="#321316")
    playlist_box.grid(row=1, column=0, padx=5, pady=5)
    playlist_box.config(state="disabled")
    



    # Configuração de tags para cores
    playlist_box.tag_configure("bg_red", background="#f09696")
    playlist_box.tag_configure("bg_darkred", background="#e27e7e")

    # Criando menu de arquivo
    file_menu_bar.add_command(label="Carregar pasta", command=lambda:carregar_pasta())
    file_menu_bar.add_separator()
    file_menu_bar.add_command(label="Sair", command=root.quit)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu_bar)
    root.config(menu=menu_bar)


    global back_button, play_button, next_button
    # Música anterior
    back_button = ttk.Button(button_frame, text="|<", command=lambda:tocar_musica("|<"), width=5, style="botao_default.TButton", takefocus=False)
    back_button.grid(row=0, column=0)

    # Tocar música
    play_button = ttk.Button(button_frame, text=">", command=lambda:tocar_musica(">"), width=5, style="botao_default.TButton", takefocus=False)
    play_button.grid(row=0, column=1)

    # próxima música
    next_button = ttk.Button(button_frame, text=">|", command=lambda:tocar_musica(">|"), width=5, style="botao_default.TButton", takefocus=False)
    next_button.grid(row=0, column=3)

    # Randomizar playlist
    random_button = ttk.Button(button_frame, text="><", command=lambda:tocar_musica("><"), width=5, style="botao_default.TButton", takefocus=False)
    random_button.grid(row=0, column=4)

    # Tocar próxima música automaticamente
    autoplay_var = tk.BooleanVar()
    autoplay_checkbox = ttk.Checkbutton(button_frame, text="Autoplay", variable=autoplay_var, style="checkbox_default.TCheckbutton", takefocus=False)
    autoplay_checkbox.grid(row=1, column=0, columnspan=4, pady=5)


    # Logs
    label_logs = ttk.Label(footer_frame, text="Bem-vindo ao Starfruit Music Player! :3", style="texto_darker.TLabel")
    label_logs.pack()

    # Define a capa padrão e já aplica
    imagem_padrao = Image.open("images/default_cover.png").resize((120, 120))
    imagem_padrao_tk = ImageTk.PhotoImage(imagem_padrao)
    atualizar_capa(right_frame, imagem_padrao_tk, indice_atual=0)

    def tocar_musica(option:str):
        """Toca a música no índice especificado da playlist."""

        nonlocal indice_atual
        nonlocal is_paused

        if option == "|<": indice_atual -= 1
        elif option == ">|": indice_atual += 1
        elif option == ">":
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                play_button.config(text=">")
                is_paused = True
                return
            elif pygame.mixer.music.get_pos() != -1:
                pygame.mixer.music.unpause()
                play_button.config(text="||")
                is_paused = False
                return
        elif option == "><":
            if playlist:
                shuffle(playlist)
                indice_atual = 0
                pygame.mixer.music.load(playlist[indice_atual]['caminho'])
                pygame.mixer.music.play()
                play_button.config(text="||")
                atualizar_playlist_box(tocando_idx=indice_atual)
                return

        if playlist:
            if indice_atual < 0: indice_atual = 0
            elif indice_atual >= len(playlist):indice_atual = 0

            pygame.mixer.music.load(playlist[indice_atual]['caminho'])
            pygame.mixer.music.play()
            play_button.config(text="||")

            nome_musica.config(text = f"{playlist[indice_atual]['nome']}")
            nome_artista.config(text = f"Artista: {playlist[indice_atual]['artista']}")
            nome_album.config(text = f"Album: {playlist[indice_atual]['album']}")

            atualizar_playlist_box(tocando_idx=indice_atual)

            atualizar_capa(right_frame, imagem_padrao_tk, indice_atual)

            return True
        
        return False
    
    def carregar_pasta():
        """Carrega uma pasta e adiciona arquivos de música à lista de reprodução."""

        nonlocal indice_atual
        indice_atual = 0

        pasta = filedialog.askdirectory()
        if pasta:
            pygame.mixer.music.stop()
            play_button.config(text=">")
            playlist_box.config(state="normal")
            playlist_box.delete("1.0", tk.END)
            playlist.clear()

            for idx, item in enumerate(listdir(pasta)):
                item_lower = item.lower()
                if item_lower.endswith('.mp3') or item_lower.endswith('.wav'):
                    caminho_completo = join(pasta, item)
                    artista = "Desconhecido"
                    album = "Desconhecido"

                    if item_lower.endswith('.mp3'):
                        audio = MP3(caminho_completo, ID3=EasyID3)
                        artista = audio.get('artist', ['Desconhecido'])[0]
                        album = audio.get('album', ['Desconhecido'])[0]

                    elif item_lower.endswith('.wav'):
                        audio = WAVE(caminho_completo)
                        artista = audio.get('artist', ['Desconhecido'])[0] if 'artist' in audio else "Desconhecido"
                        album = audio.get('album', ['Desconhecido'])[0] if 'album' in audio else "Desconhecido"

                    playlist.append({
                        'nome': item[:-4],
                        'caminho': caminho_completo,
                        'artista': artista,
                        'album': album
                    })
                    
                    tag = "bg_red" if idx % 2 == 0 else "bg_darkred"
                    playlist_box.insert(tk.END, f"{idx} - {item[:-4]}\n", tag)
                    
            playlist_box.config(state="disabled")
    def checar_fim_musica():
        """Verifica se a música acabou, e se sim, toca a próxima automaticamente, caso a opção de autoplay esteja marcada."""

        if (
        autoplay_var.get()
        and playlist
        and not is_paused
        and not pygame.mixer.music.get_busy()):
            
            if pygame.mixer.music.get_pos() >= 0:
                tocar_musica(">|")
            else:
                tocar_musica(">")


        root.after(500, checar_fim_musica)
    def music_stats():
        """Coleta o estado atual da música"""

        if playlist and 0 <= indice_atual < len(playlist):
            caminho = playlist[indice_atual]['caminho']

            pos_ms = pygame.mixer.music.get_pos()
            pos_seg = max(0, pos_ms // 1000)

            if caminho.endswith('.mp3'):
                audio = MP3(caminho)
                duracao_total = int(audio.info.length)

            elif caminho.endswith('.wav'):
                audio = WAVE(caminho)
                duracao_total = int(audio.info.length)
            else:
                duracao_total = 0

            label_duracao.config(text=formatar_tempo(pos_seg))
            label_duracao_total.config(text=formatar_tempo(duracao_total))

        root.after(500, music_stats)

    checar_fim_musica()
    music_stats()
    root.mainloop()

if __name__ == "__main__":
    main()
