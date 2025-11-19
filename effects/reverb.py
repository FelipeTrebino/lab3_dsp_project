import numpy as np

class CombFilter:
    # Filtro Pente IIR: y[n] = x[n] + g * y[n-M]
    def __init__(self, delay_samples, gain):
        self.delay_samples = delay_samples
        self.gain = gain
        self.buffer = np.zeros(delay_samples) 
        self.ptr = 0
    
    def process(self, x):
        # 1. Leitura da amostra atrasada (y[n-M])
        delayed_val = self.buffer[self.ptr]
        
        # 2. Saída (saída de feedback, como usado na topologia Schroeder)
        y = delayed_val
        
        # 3. Atualiza buffer (Realimentação IIR)
        # O novo valor no buffer é a soma da entrada (x[n]) mais a versão atrasada (g * y[n-M])
        self.buffer[self.ptr] = x + (self.gain * delayed_val)
        
        # 4. Atualiza ponteiro circular
        self.ptr = (self.ptr + 1) % self.delay_samples
            
        return y

class AllPassFilter:
    # Filtro Passa-Tudo: y[n] = -g * x[n] + x[n-M] + g * y[n-M]
    def __init__(self, delay_samples, gain):
        self.delay_samples = delay_samples
        self.gain = gain
        self.buffer = np.zeros(delay_samples)
        self.ptr = 0
        
    def process(self, x):
        # 1. Leitura do valor atrasado (x[n-M] / y[n-M])
        delayed_val = self.buffer[self.ptr]
        
        # 2. Entrada para o buffer (x[n] + g * y[n-M])
        input_to_buffer = x + (self.gain * delayed_val)
        
        # 3. Saída (All-Pass)
        y = (-self.gain * x) + delayed_val
        
        # 4. Atualiza buffer
        self.buffer[self.ptr] = input_to_buffer
        
        # 5. Atualiza ponteiro circular
        self.ptr = (self.ptr + 1) % self.delay_samples
            
        return y

def apply_reverb(x, fs, delays_combs, gains_combs, delays_ap, gains_ap, wet_gain=0.1):
    """
    Aplica Reverb baseado na estrutura de Schroeder (Comb e All-Pass).
    Parâmetros são arrays para suportar topologias complexas, 
    mas podem ser usados com um único valor (ex: [0.03]).
    """
    
    # 1. Instanciar Filtros
    comb = CombFilter(int(delays_combs[0]*fs), gains_combs[0])
    ap = AllPassFilter(int(delays_ap[0]*fs), gains_ap[0])
    
    N = len(x)
    y = np.zeros(N, dtype=np.float32)
    
    dry_gain = 1.0 - wet_gain
    
    # 2. Processamento Amostra a Amostra
    for n in range(N):
        input_sample = x[n]
        
        # 1. Processa Comb
        comb_out = comb.process(input_sample)
            
        # 2. Processa AllPass (para difusão)
        ap_out = ap.process(comb_out)
            
        # 3. Mix final: Dry + Wet (Wet atenuado)
        # O ganho wet é crucial para evitar clipping.
        y[n] = (dry_gain * input_sample) + (wet_gain * ap_out)
            
    return y