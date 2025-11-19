import numpy as np

class CombFilter:
    def __init__(self, delay_samples, gain):
        self.delay_samples = delay_samples
        self.gain = gain
        self.buffer = np.zeros(delay_samples + 1)
        self.ptr = 0
    
    def process(self, x):
        # y[n] = x[n-M] + g * y[n-M] (Filtro IIR Comb)
        # Estrutura Schroeder:
        # saida_delay = buffer[ptr]
        # y = saida_delay
        # entrada_buffer = x + g * saida_delay
        
        delayed_val = self.buffer[self.ptr]
        
        # Saída do filtro
        y = delayed_val
        
        # Atualiza buffer (Realimentação)
        self.buffer[self.ptr] = x + (self.gain * delayed_val)
        
        # Incrementa ponteiro circular
        self.ptr += 1
        if self.ptr >= self.delay_samples:
            self.ptr = 0
            
        return y

class AllPassFilter:
    def __init__(self, delay_samples, gain):
        self.delay_samples = delay_samples
        self.gain = gain
        self.buffer = np.zeros(delay_samples + 1)
        self.ptr = 0
        
    def process(self, x):
        # Schroeder All-Pass:
        # y[n] = -g * x[n] + x[n-M] + g * y[n-M]
        
        delayed_val = self.buffer[self.ptr]
        
        # Calcula saída
        y = -self.gain * x + delayed_val
        
        # Atualiza buffer
        self.buffer[self.ptr] = x + (self.gain * delayed_val)
        
        self.ptr += 1
        if self.ptr >= self.delay_samples:
            self.ptr = 0
            
        return y

def apply_reverb(x, fs, delays_combs, gains_combs, delays_ap, gains_ap, wet_gain=0.05):
    """
    Implementação de Reverb Schroeder com ganho wet explícito.
    """
    # Inicializa filtros
    combs = [CombFilter(int(d*fs), g) for d, g in zip(delays_combs, gains_combs)]
    allpasses = [AllPassFilter(int(d*fs), g) for d, g in zip(delays_ap, gains_ap)]
    
    N = len(x)
    y = np.zeros(N, dtype=np.float32)
    dry_gain = 1.0 - wet_gain # Garante que o Dry + Wet não exceda 1.0 sem controle

    # Processamento amostra a amostra
    for n in range(N):
        input_sample = x[n]
        
        # 1. Processa Combs em paralelo
        comb_out_sum = 0.0
        for comb in combs:
            comb_out_sum += comb.process(input_sample)
            
        # 2. A soma dos combs passa pelos AllPasses em série
        ap_out = comb_out_sum
        for ap in allpasses:
            ap_out = ap.process(ap_out)
            
        # 3. Mix final: Dry + Wet (Wet atenuado pelo wet_gain)
        # O wet_gain é o fator crucial para evitar o estouro.
        y[n] = (dry_gain * input_sample) + (wet_gain * ap_out)
            
    return y