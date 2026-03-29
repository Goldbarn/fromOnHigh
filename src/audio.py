import pygame
import array
import math

class AudioManager:
    def __init__(self):
        # Ensure Pygame's mixer is initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        init_params = pygame.mixer.get_init()
        if init_params:
            self.freq, self.size, self.channels = init_params
        else:
            self.freq, self.size, self.channels = 44100, -16, 2
            
        self.sounds = {
            'move': self._generate_jump_sound(),
            'found_city': self._generate_gold_win_sound()
        }

    def play(self, name):
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def _generate_waveform(self, duration, func):
        """
        Generates a Pygame Sound object using a mathematical waveform function.
        This is incredibly low-resource as it generates synthetic audio in memory
        instead of loading and reading external files.
        """
        num_samples = int(self.freq * duration)
        buf = array.array('h')
        max_amp = 32767
        
        for i in range(num_samples):
            t = float(i) / self.freq
            val = int(func(t) * max_amp)
            
            # Clip value to 16-bit range to prevent overflow distortion
            val = max(-32768, min(32767, val))
            
            # Duplicate across channels (stereo setup usually requires 2 channels)
            for _ in range(self.channels):
                buf.append(val)
                
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _generate_jump_sound(self):
        duration = 0.15
        def wave(t):
            # Pitch slide from 300Hz to 600Hz for a quick 'swoosh' jump
            freq = 300 + (300 * (t / duration))
            volume = 1.0 - (t / duration)
            return volume * math.sin(2 * math.pi * freq * t)
        return self._generate_waveform(duration, wave)

    def _generate_gold_win_sound(self):
        duration = 0.6
        def wave(t):
            # Cartoon 'finding gold' / winning sound: fast ascending major arpeggio
            if t < 0.1:
                freq = 523.25  # C5
            elif t < 0.2:
                freq = 659.25  # E5
            elif t < 0.3:
                freq = 783.99  # G5
            else:
                freq = 1046.50 # C6
                
            # Envelope to give each note a distinct "pluck" and fade out the final note
            note_t = t % 0.1 if t < 0.3 else (t - 0.3)
            note_duration = 0.1 if t < 0.3 else 0.3
            volume = max(0, 1.0 - (note_t / note_duration))
            
            # Bright synth twinkle (base frequency + 1 octave harmonic)
            return volume * 0.4 * (math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(2 * math.pi * freq * 2 * t))
        return self._generate_waveform(duration, wave)