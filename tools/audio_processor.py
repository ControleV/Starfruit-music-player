"""
Audio processor para aplicar efeitos de equalizador em tempo real
"""
import numpy as np
from scipy import signal
from pydub import AudioSegment
import tempfile
import os

class AudioProcessor:
    def __init__(self):
        self.eq_gains = [1.0, 1.0, 1.0]  # Grave, Médio, Agudo
        self.sample_rate = 44100
        self.processed_files = {}  # Cache de arquivos processados
        
    def set_eq_gains(self, low, mid, high):
        """Define os ganhos do equalizador"""
        self.eq_gains = [low, mid, high]
        # Limpa o cache quando as configurações mudam
        self.clear_cache()
        
    def clear_cache(self):
        """Limpa o cache de arquivos processados"""
        for temp_file in self.processed_files.values():
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        self.processed_files.clear()
        
    def apply_equalizer(self, audio_array, sample_rate):
        """Aplica equalizador ao array de áudio"""
        if len(audio_array.shape) == 1:
            # Mono
            return self._process_channel(audio_array, sample_rate)
        else:
            # Stereo - processa cada canal
            processed = np.zeros_like(audio_array)
            for i in range(audio_array.shape[1]):
                processed[:, i] = self._process_channel(audio_array[:, i], sample_rate)
            return processed
            
    def _process_channel(self, channel_data, sample_rate):
        """Processa um canal de áudio"""
        # Frequências de corte
        low_freq = 250    # Graves
        mid_freq = 2000   # Médios  
        high_freq = 8000  # Agudos
        
        nyquist = sample_rate / 2
        
        try:
            # Filtro passa-baixa para graves
            low_b, low_a = signal.butter(2, min(low_freq/nyquist, 0.99), btype='low')
            low_band = signal.filtfilt(low_b, low_a, channel_data) * self.eq_gains[0]
            
            # Filtro passa-banda para médios
            mid_low = min(low_freq/nyquist, 0.99)
            mid_high = min(high_freq/nyquist, 0.99)
            if mid_high > mid_low:
                mid_b, mid_a = signal.butter(2, [mid_low, mid_high], btype='band')
                mid_band = signal.filtfilt(mid_b, mid_a, channel_data) * self.eq_gains[1]
            else:
                mid_band = channel_data * self.eq_gains[1] * 0.1  # Reduz contribuição se inválida
            
            # Filtro passa-alta para agudos
            if high_freq/nyquist < 0.99:
                high_b, high_a = signal.butter(2, high_freq/nyquist, btype='high')
                high_band = signal.filtfilt(high_b, high_a, channel_data) * self.eq_gains[2]
            else:
                high_band = channel_data * self.eq_gains[2] * 0.1
            
            # Combina as bandas
            processed = low_band + mid_band + high_band
            
            # Normaliza para evitar clipping
            max_val = np.max(np.abs(processed))
            if max_val > 1.0:
                processed = processed / max_val
                
            return processed
            
        except Exception as e:
            print(f"Erro no processamento de áudio: {e}")
            # Em caso de erro, retorna o áudio original com ganho médio
            return channel_data * np.mean(self.eq_gains)
    
    def process_file(self, input_file):
        """Processa um arquivo de áudio e retorna o caminho do arquivo processado"""
        # Verifica se o arquivo existe primeiro
        if not os.path.exists(input_file):
            print(f"Arquivo não encontrado: {input_file}")
            return input_file
            
        # Normaliza o caminho para evitar problemas com caracteres especiais
        input_file = os.path.normpath(input_file)
        
        # Verifica se já foi processado com essas configurações
        cache_key = f"{os.path.basename(input_file)}_{self.eq_gains[0]:.1f}_{self.eq_gains[1]:.1f}_{self.eq_gains[2]:.1f}"
        
        if cache_key in self.processed_files and os.path.exists(self.processed_files[cache_key]):
            return self.processed_files[cache_key]
        
        try:
            print(f"Processando arquivo: {input_file}")
            
            # Carrega o arquivo de áudio com tratamento de encoding
            if input_file.lower().endswith('.mp3'):
                # Tenta diferentes encodings para arquivos com caracteres especiais
                audio = AudioSegment.from_file(input_file, format="mp3")
            elif input_file.lower().endswith('.wav'):
                audio = AudioSegment.from_file(input_file, format="wav")
            else:
                print(f"Formato não suportado: {input_file}")
                return input_file  # Retorna original se formato não suportado
            
            # Converte para array numpy
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            
            # Normaliza para range -1 a 1
            samples = samples / (2**(audio.sample_width * 8 - 1))
            
            # Reshape para stereo se necessário
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
            
            # Aplica equalização
            processed_samples = self.apply_equalizer(samples, audio.frame_rate)
            
            # Converte de volta para o formato original
            processed_samples = (processed_samples * (2**(audio.sample_width * 8 - 1))).astype(np.int16)
            
            # Cria novo AudioSegment
            if audio.channels == 2:
                processed_samples = processed_samples.flatten()
            
            processed_audio = AudioSegment(
                processed_samples.tobytes(),
                frame_rate=audio.frame_rate,
                sample_width=audio.sample_width,
                channels=audio.channels
            )
            
            # Salva arquivo temporário com nome seguro
            import string
            import random
            safe_chars = string.ascii_letters + string.digits
            temp_name = ''.join(random.choice(safe_chars) for _ in range(10))
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', prefix=f'eq_{temp_name}_')
            temp_path = temp_file.name
            temp_file.close()
            
            # Exporta o áudio processado
            processed_audio.export(temp_path, format="wav")
            
            # Adiciona ao cache
            self.processed_files[cache_key] = temp_path
            
            print(f"Arquivo processado salvo em: {temp_path}")
            return temp_path
            
        except FileNotFoundError as e:
            print(f"Arquivo não encontrado: {input_file} - {e}")
            return input_file
        except PermissionError as e:
            print(f"Erro de permissão ao acessar: {input_file} - {e}")
            return input_file
        except UnicodeDecodeError as e:
            print(f"Erro de encoding no arquivo: {input_file} - {e}")
            return input_file
        except Exception as e:
            print(f"Erro ao processar arquivo {input_file}: {e}")
            return input_file  # Retorna arquivo original em caso de erro
    
    def __del__(self):
        """Limpa arquivos temporários ao destruir objeto"""
        self.clear_cache()
