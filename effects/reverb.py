import numpy as np
from effects.assets import IIRCombFilter, AllPassFilter

def apply_reverb(x, fs, delays_combs_ms, gains_combs, delays_ap_ms, gains_ap, wet_gain=0.4):
    
    print(f"--- Reverb: Processando {len(x)} amostras a {fs}Hz ---")
    
    # 1. Inicializa Filtros (Recebendo MS direto)
    combs = []
    for i in range(len(delays_combs_ms)):
        combs.append(IIRCombFilter(delays_combs_ms[i], gains_combs[i], fs))
        
    aps = []
    for i in range(len(delays_ap_ms)):
        aps.append(AllPassFilter(delays_ap_ms[i], gains_ap[i], fs))
    
    N = len(x)
    y = np.zeros(N, dtype=np.float32)
        
    # 2. Loop de Áudio
    for n in range(N):
        input_sample = x[n]
        # Soma dos Combs (Paralelo)
        comb_sum = 0.0
        for comb in combs:
            comb_sum += comb.process(input_sample)
            
        # Série de All-Pass
        ap_out = comb_sum
        for ap in aps:
            ap_out = ap.process(ap_out)
            
        reverb_signal = ap_out
        
        y[n] = (x[n] * (1 - wet_gain)) + (reverb_signal * wet_gain)/ len(combs)  # Normaliza pela quantidade de combs
            
    # 3. Normalização de Segurança (Evita o ruído digital se passar de 1.0)
    max_amp = np.max(np.abs(y))
    if max_amp > 1.0:
        print(f" > Normalizando volume final (Pico: {max_amp:.2f})")
        y = y / max_amp
        
    return y