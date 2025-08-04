"""Audio processor to apply equalizer effects in real time"""
import numpy as np
from scipy import signal
from pydub import AudioSegment
import tempfile
import os
import glob
import time

class AudioProcessor:
    def __init__(self):
        self.eq_gains = [1.0, 1.0, 1.0]
        self.sample_rate = 44100
        self.processed_files = {}
        
        # Clean old files on initialization
        self.clean_old_eq_files(max_age_hours=24)
        
    def set_eq_gains(self, low, mid, high):
        """Set equalizer gains"""
        # Clear processed files with old settings
        self.clear_cache()
        self.eq_gains = [low, mid, high]
        
    def clear_cache(self):
        """Clear processed files cache"""
        print("Clearing processed files cache...")
        
        removed_count = 0
        for cache_key, temp_file in self.processed_files.items():
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    removed_count += 1
                    print(f"File removed from cache: {os.path.basename(temp_file)}")
            except Exception as e:
                print(f"Error removing {temp_file}: {e}")
        
        self.processed_files.clear()
        
        # Also clean old files when cache is cleared
        self.clean_old_eq_files(max_age_hours=0)  # Remove all eq_ files
        
        if removed_count > 0:
            print(f"Cache cleared: {removed_count} file(s) removed")
    
    def clean_old_eq_files(self, max_age_hours=24):
        """Remove old equalizer files from temp folder"""
        try:
            temp_dir = tempfile.gettempdir()
            # Search for files starting with 'eq_' in temp folder
            eq_files = glob.glob(os.path.join(temp_dir, 'eq_*.wav'))
            
            current_time = time.time()
            removed_count = 0
            
            for file_path in eq_files:
                try:
                    # Check file age
                    file_age = current_time - os.path.getmtime(file_path)
                    file_age_hours = file_age / 3600  # Convert to hours
                    
                    # Remove files older than max_age_hours
                    # If max_age_hours is 0, remove all eq_ files
                    if max_age_hours == 0 or file_age_hours > max_age_hours:
                        os.remove(file_path)
                        removed_count += 1
                        print(f"EQ file removed: {os.path.basename(file_path)} (age: {file_age_hours:.1f}h)")
                except (OSError, IOError) as e:
                    # Ignore permission errors or files in use
                    print(f"Could not remove {os.path.basename(file_path)}: {e}")
                    continue
            
            if removed_count > 0:
                print(f"EQ cleanup completed: {removed_count} file(s) removed")
            elif max_age_hours == 0:
                print("No EQ files found for removal")
            
        except Exception as e:
            print(f"Error in EQ files cleanup: {e}")
    
    def _clear_previous_processed_files(self, input_file):
        """Remove previously processed files for this specific song"""
        try:
            base_filename = os.path.basename(input_file)
            # Remove from cache and file system any processed version of this song
            keys_to_remove = []
            for cache_key, temp_path in self.processed_files.items():
                if base_filename in cache_key:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            print(f"Previous file removed: {os.path.basename(temp_path)}")
                    except:
                        pass
                    keys_to_remove.append(cache_key)
            
            # Remove cache entries
            for key in keys_to_remove:
                del self.processed_files[key]
                
        except Exception as e:
            print(f"Error clearing previous files: {e}")
        
    def apply_equalizer(self, audio_array, sample_rate):
        """Apply equalizer to audio array"""
        if len(audio_array.shape) == 1:
            return self._process_channel(audio_array, sample_rate)
        else:
            processed = np.zeros_like(audio_array)
            for i in range(audio_array.shape[1]):
                processed[:, i] = self._process_channel(audio_array[:, i], sample_rate)
            return processed
            
    def _process_channel(self, channel_data, sample_rate):
        """Process one audio channel"""
        # Cutoff frequencies
        low_freq = 250    # Bass
        mid_freq = 2000   # Mid  
        high_freq = 8000  # Treble
        
        nyquist = sample_rate / 2
        
        try:
            # Low-pass filter for bass
            low_b, low_a = signal.butter(2, min(low_freq/nyquist, 0.99), btype='low')
            low_band = signal.filtfilt(low_b, low_a, channel_data) * self.eq_gains[0]
            
            # Band-pass filter for mid
            mid_low = min(low_freq/nyquist, 0.99)
            mid_high = min(high_freq/nyquist, 0.99)
            if mid_high > mid_low:
                mid_b, mid_a = signal.butter(2, [mid_low, mid_high], btype='band')
                mid_band = signal.filtfilt(mid_b, mid_a, channel_data) * self.eq_gains[1]
            else:
                mid_band = channel_data * self.eq_gains[1] * 0.1  # Reduce contribution if invalid
            
            # High-pass filter for treble
            if high_freq/nyquist < 0.99:
                high_b, high_a = signal.butter(2, high_freq/nyquist, btype='high')
                high_band = signal.filtfilt(high_b, high_a, channel_data) * self.eq_gains[2]
            else:
                high_band = channel_data * self.eq_gains[2] * 0.1
            
            # Combine bands
            processed = low_band + mid_band + high_band
            
            # Normalize to avoid clipping
            max_val = np.max(np.abs(processed))
            if max_val > 1.0:
                processed = processed / max_val
                
            return processed
            
        except Exception as e:
            print(f"Error in audio processing: {e}")
            # In case of error, return original audio with average gain
            return channel_data * np.mean(self.eq_gains)
    
    def process_file(self, input_file):
        """Process an audio file and return the path of the processed file"""
        # Remove previously processed files for this song
        self._clear_previous_processed_files(input_file)
        
        # Clean old equalizer files before processing new file
        self.clean_old_eq_files(max_age_hours=0.5)  # Remove files older than 30 minutes
        
        # Check if file exists first
        if not os.path.exists(input_file):
            print(f"File not found: {input_file}")
            return input_file
            
        # Normalize path to avoid issues with special characters
        input_file = os.path.normpath(input_file)
        
        # Check if already processed with these settings
        cache_key = f"{os.path.basename(input_file)}_{self.eq_gains[0]:.1f}_{self.eq_gains[1]:.1f}_{self.eq_gains[2]:.1f}"
        
        if cache_key in self.processed_files and os.path.exists(self.processed_files[cache_key]):
            return self.processed_files[cache_key]
        
        try:
            print(f"Processing file: {input_file}")
            
            # Load audio file with encoding handling
            if input_file.lower().endswith('.mp3'):
                # Try different encodings for files with special characters
                audio = AudioSegment.from_file(input_file, format="mp3")
            elif input_file.lower().endswith('.wav'):
                audio = AudioSegment.from_file(input_file, format="wav")
            else:
                print(f"Unsupported format: {input_file}")
                return input_file  # Return original if format not supported
            
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            
            # Normalize to range -1 to 1
            samples = samples / (2**(audio.sample_width * 8 - 1))
            
            # Reshape for stereo if necessary
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
            
            # Apply equalization
            processed_samples = self.apply_equalizer(samples, audio.frame_rate)
            
            # Convert back to original format
            processed_samples = (processed_samples * (2**(audio.sample_width * 8 - 1))).astype(np.int16)
            
            # Create new AudioSegment
            if audio.channels == 2:
                processed_samples = processed_samples.flatten()
            
            processed_audio = AudioSegment(
                processed_samples.tobytes(),
                frame_rate=audio.frame_rate,
                sample_width=audio.sample_width,
                channels=audio.channels
            )
            
            # Save temporary file with safe name
            import string
            import random
            safe_chars = string.ascii_letters + string.digits
            temp_name = ''.join(random.choice(safe_chars) for _ in range(10))
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', prefix=f'eq_{temp_name}_')
            temp_path = temp_file.name
            temp_file.close()
            
            # Export processed audio
            processed_audio.export(temp_path, format="wav")
            
            # Add to cache
            self.processed_files[cache_key] = temp_path
            
            print(f"Processed file saved at: {temp_path}")
            return temp_path
            
        except FileNotFoundError as e:
            print(f"File not found: {input_file} - {e}")
            return input_file
        except PermissionError as e:
            print(f"Permission error accessing: {input_file} - {e}")
            return input_file
        except UnicodeDecodeError as e:
            print(f"Encoding error in file: {input_file} - {e}")
            return input_file
        except Exception as e:
            print(f"Error processing file {input_file}: {e}")
            return input_file  # Return original file in case of error
    
    def __del__(self):
        """Clean temporary files when destroying object"""
        try:
            print("Destroying AudioProcessor - cleaning temporary files...")
            self.clear_cache()
            # Remove all remaining EQ files
            self.clean_old_eq_files(max_age_hours=0)
        except:
            pass
