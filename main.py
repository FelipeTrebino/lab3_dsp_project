import sys
from file_manager import AudioManager, EFFECTS_MAP
from metrics import calculate_mse, calculate_snr
from optimizer import optimize_reverb_parameters
from effects.reverb import apply_reverb
from audio_io import save_wav

def main():
    # 1. Inicializa o gerenciador de arquivos
    # Certifique-se de que a pasta 'audio_files' está no mesmo diretório do script
    manager = AudioManager(base_folder="audio_files", dry_filename="original.wav")
    
    # Verifica se está tudo lá
    if not manager.verify_files():
        sys.exit("Corrija os nomes dos arquivos ou a pasta antes de continuar.")

    # 2. Carrega o áudio Dry (referência)
    fs, dry_audio = manager.get_dry_audio()
    
    print("\n=== INICIANDO PROCESSO DE OTIMIZAÇÃO VEDO A8 ===")

    # 3. Loop através dos efeitos desejados
    # Por enquanto, vamos focar nos Reverbs, pois usam o mesmo algoritmo base
    reverb_list = ["REV-HALL 1", "REV-ROOM 2", "REV-STAGE B"]
    
    for effect_name in reverb_list:
        print(f"\n---------------------------------------------")
        print(f"Processando: {effect_name}")
        
        try:
            # Carrega o áudio alvo da mesa
            _, target_audio = manager.get_target_audio(effect_name)
            
            # Executa Otimização (Encontrar Ganhos)
            # Nota: O algoritmo de otimização precisa saber que tipo de delay usar.
            # Para este exemplo, o optimizer usará delays padrão, mas ajustará os ganhos.
            best_gains = optimize_reverb_parameters(dry_audio, target_audio, fs)
            
            print(f" > Ganhos Otimizados: {best_gains}")
            
            # Gera o áudio com os novos parâmetros para validação auditiva
            # (Usando delays fixos do exemplo anterior - idealmente delays seriam variáveis por efeito)
            fixed_delays_combs = [0.0297, 0.0371, 0.0411, 0.0437]
            fixed_delays_ap = [1.051, 0.337, 0.113]
            fixed_gains_ap = [0.7, 0.7, 0.7]
            
            my_processed = apply_reverb(dry_audio, fs, fixed_delays_combs, best_gains, fixed_delays_ap, fixed_gains_ap)
            
            # Calcula métrica final
            snr = calculate_snr(target_audio, my_processed)
            print(f" > SNR Final: {snr:.2f} dB")
            
            # Salva resultado
            out_name = f"output/reconstructed_{effect_name.replace(' ', '_')}.wav"
            save_wav(out_name, fs, my_processed)
            print(f" > Arquivo gerado: {out_name}")
            
        except Exception as e:
            print(f"Erro ao processar {effect_name}: {e}")

if __name__ == "__main__":
    main()