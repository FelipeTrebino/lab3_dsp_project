import os
from file_manager import AudioManager
from effects.reverb import apply_reverb
from effects.flanger import apply_flanger
from effects.tremolo import apply_tremolo
from pitch_shift.shift_assets import shift_to_note

from audio_io import save_wav

def main():
    manager = AudioManager(base_folder="audio_files", dry_key="ORIGINAL") 
    fs, audio_original = manager.get_dry_audio()

    # Comb Filters
    combs_ms = [29.7, 37.1, 41.1, 43.7] # Delays (Tamanho da sala), em ms
    combs_gains = [0.77, 0.75, 0.73, 0.71] # Ganhos 
    
    # All-Pass (Difusão)
    aps_ms = [5.0, 1.7] # Delays em ms
    aps_gains = [0.7, 0.7] # Ganhos

    print("Aplicando Reverb...")
    
    processed_audio_reverb = apply_reverb(
        audio_original, 
        fs, 
        combs_ms,    
        combs_gains, 
        aps_ms,
        aps_gains,
        wet_gain=1
    )
    
    processed_audio_flanger = apply_flanger(
        audio_original, 
        fs
    )
    
    processed_audio_tremolo = apply_tremolo(
        audio_original,
        fs
    )
    
    reverb_A4 = shift_to_note(processed_audio_reverb, fs, target_note="A4", root_note="C4")
    reverb_A3 = shift_to_note(processed_audio_reverb, fs, target_note="A3", root_note="C4")
    
          
    save_wav("output/reverb_test_A4.wav", fs, reverb_A4)
    save_wav("output/reverb_test_A3.wav", fs, reverb_A3)
    save_wav("output/flanger_test.wav", fs, processed_audio_flanger)
    save_wav("output/tremolo_test.wav", fs, processed_audio_tremolo)

if __name__ == "__main__":
    main()