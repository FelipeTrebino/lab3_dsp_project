import os
import sys
from file_manager import AudioManager, EFFECTS_MAP 
from effects.reverb import apply_reverb
from audio_io import save_wav

def main():
    # 1. Configuração de pastas e gerenciador
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Pasta '{output_folder}' criada.")

    manager = AudioManager(base_folder="audio_files", dry_key="ORIGINAL") 
    
    if not os.path.exists(manager.dry_path):
        print(f"Erro: O arquivo {manager.dry_filename} (Chave ORIGINAL) não foi encontrado em {manager.base_folder}")
        return

    # 2. Carregar o áudio de entrada
    fs, audio_original = manager.get_dry_audio()

    # 3. Definição dos Parâmetros Fixos (Schroeder Reverb - "Hall" Fixo)
    fixed_delays_combs = [0.4799, 0.4999, 0.5399, 0.5801] 
    
    # Ganhos Conservadores (Decaimento Rápido)
    # Valores < 0.8 garantem estabilidade e decaimento rápido.
    fixed_gains_combs = [0.742, 0.733, 0.715, 0.697] 
    
    # Ganhos dos Filtros All-Pass (Valor Seguro)
    fixed_delays_ap = [0.1051, 0.0337]
    fixed_gains_ap = [0.7, 0.7]      
    
    wet_gain_conservative = 0.1 # 20% de sinal úmido

    print("Aplicando efeito Reverb (Valores Fixos)...")
    print(f" > Fs: {fs} Hz")

    # 4. Aplicação do Efeito
    processed_audio = apply_reverb(
        audio_original, 
        fs, 
        fixed_delays_combs, 
        fixed_gains_combs, 
        fixed_delays_ap, 
        fixed_gains_ap,
        wet_gain=wet_gain_conservative
    )

    # 5. Salvar o resultado
    output_filename = "reverb_fixed_output.wav"
    full_output_path = os.path.join(output_folder, output_filename)
    
    save_wav(full_output_path, fs, processed_audio)
    
    print(f"✅ Processamento concluído!")
    print(f"Áudio original '{manager.dry_filename}' processado e salvo em: {full_output_path}")

if __name__ == "__main__":
    main()