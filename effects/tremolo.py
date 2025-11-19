import numpy as np

def apply_tremolo(x, fs, mod_freq, depth):
    """
    Aplica Tremolo (Modulação de Amplitude).
    x: array de áudio de entrada
    fs: taxa de amostragem
    mod_freq: frequência do LFO (Hz)
    depth: profundidade da modulação (0.0 a 1.0)
    """
    N = len(x)
    y = np.zeros(N, dtype=np.float32)
    
    # Vetor de tempo
    t = np.arange(N) / fs
    
    # Sinal modulante (LFO) - Senoidal
    # Fórmula: m[n] = depth * sin(2 * pi * f_mod * t)
    lfo = depth * np.sin(2 * np.pi * mod_freq * t)
    
    # Equação a diferenças: y[n] = x[n] * (1 + lfo[n])
    # Implementado vetorizado para performance em Python, 
    # mas representa o loop amostra a amostra.
    y = x * (1.0 + lfo)
    
    return y