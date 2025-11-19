import os
from audio_io import load_wav

# Definição das constantes de nomes de efeitos baseados na VEDO A8

EFFECTS_MAP = {
    "REV-HALL1":     "01.wav",
    "REV-HALL2":     "02.wav",
    "REV-ROOM1":     "03.wav",
    "REV-ROOM2":     "04.wav",
    "REV-STAGE A":   "05.wav",
    "REV-STAGE AB":  "06.wav",
    "REV-STAGE B":   "07.wav",
    "REV-STAGE Bb":  "08.wav",
    "REV-STAGE C":   "09.wav",
    "REV-STAGE D":   "10.wav",
    "REV-STAGE Dd":  "11.wav",
    "REV-STAGE E":   "12.wav",
    "REV-STAGE F":   "13.wav",
    "REV-STAGE Fb":  "14.wav",
    "REV-STAGE G":   "15.wav",
    "REV-STAGE Gb":  "16.wav",
    "RET-STATE GTHT":"17.wav",
    "CHORUS":        "18.wav",
    "FLANGER":       "19.wav",
    "PHASER":        "20.wav",
    "RADIO-VOICE":   "21.wav",
    "TREMOLO":       "22.wav",
    "AUTO-WAH":      "23.wav",
    "VOCAL":         "24.wav",
    "ORIGINAL":      "original.wav"
}

class AudioManager:
    def __init__(self, base_folder="audio_files", dry_key="ORIGINAL"):
        self.base_folder = base_folder
        self.dry_key = dry_key
        self.dry_filename = EFFECTS_MAP.get(dry_key, "original.wav") 
        self.dry_path = os.path.join(base_folder, self.dry_filename)
        self.audio_cache = {} 
        
    def get_dry_audio(self):
        """Retorna (fs, data) do áudio original usando a chave 'ORIGINAL'."""
        if self.dry_key not in self.audio_cache:
            print(f"Carregando áudio original: {self.dry_filename}...")
            fs, data = load_wav(self.dry_path) 
            self.audio_cache[self.dry_key] = (fs, data)
        return self.audio_cache[self.dry_key]

    def verify_files(self):
        """Verifica se todos os arquivos mapeados existem na pasta."""
        missing = []
        
        if not os.path.exists(self.dry_path):
            missing.append(self.dry_filename)
            
        for effect_name, filename in EFFECTS_MAP.items():
            full_path = os.path.join(self.base_folder, filename)
            if not os.path.exists(full_path):
                missing.append(f"{effect_name}: {filename}")
        
        if missing:
            print("⚠️  AVISO: Os seguintes arquivos não foram encontrados:")
            for m in missing:
                print(f"   - {m}")
            print("Verifique se os nomes na pasta audio_files correspondem ao EFFECTS_MAP.")
            return False
        
        print("✅ Todos os arquivos de áudio foram localizados com sucesso.")
        return True

    def get_dry_audio(self):
        """Retorna (fs, data) do áudio original."""
        if "DRY" not in self.audio_cache:
            print(f"Carregando áudio original: {self.dry_filename}...")
            self.audio_cache["DRY"] = load_wav(self.dry_path)
        return self.audio_cache["DRY"]

    def get_target_audio(self, effect_key):
        """Retorna (fs, data) do áudio processado pela mesa para um efeito específico."""
        if effect_key not in EFFECTS_MAP:
            raise ValueError(f"Efeito '{effect_key}' não definido no mapa.")
            
        filename = EFFECTS_MAP[effect_key]
        full_path = os.path.join(self.base_folder, filename)
        
        if effect_key not in self.audio_cache:
            print(f"Carregando alvo para {effect_key}: {filename}...")
            self.audio_cache[effect_key] = load_wav(full_path)
            
        return self.audio_cache[effect_key]