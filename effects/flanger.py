import numpy as np

def apply_flanger(x, fs, rate, depth_ms, feedback, delay_base_ms=1.0):
    """
    Aplica Flanger com interpolação linear.
    x: input
    rate: frequência do LFO (Hz)
    depth_ms: variação do delay em ms
    feedback: ganho de realimentação (0.0 a <1.0)
    delay_base_ms: delay fixo mínimo
    """
    N = len(x)
    y = np.zeros(N, dtype=np.float32)
    
    # Converter ms para amostras
    depth_samples = int((depth_ms / 1000.0) * fs)
    base_samples = int((delay_base_ms / 1000.0) * fs)
    
    # Buffer circular simples (ou acesso direto ao array com verificação de borda)
    # LFO phase
    phase = 0.0
    phase_inc = 2 * np.pi * rate / fs
    
    # Implementação iterativa (como será em C++)
    for n in range(N):
        # Calcula o delay atual modulado pelo LFO
        # LFO varia de 0 a 1 (seno deslocado) para evitar delay negativo
        lfo_val = 0.5 * (1 + np.sin(phase)) 
        current_delay = base_samples + (lfo_val * depth_samples)
        
        # Índice de leitura (fracionário)
        read_idx = n - current_delay
        
        # Interpolação Linear
        # y = (1-frac)*x[int] + frac*x[int+1]
        i_part = int(np.floor(read_idx))
        frac = read_idx - i_part
        
        if i_part >= 0 and i_part < N - 1:
            delayed_sample = (1.0 - frac) * x[i_part] + frac * x[i_part + 1]
        else:
            delayed_sample = 0.0
            
        # Equação a diferenças do Flanger com Feedback
        # y[n] = x[n] + g_fb * y[n-1] (simplificado no loop) + delayed
        # Estrutura clássica: Input + Feedback + Delayed
        
        # Feedforward (som direto + atrasado)
        y[n] = x[n] + 0.7 * delayed_sample # 0.7 é o ganho wet
        
        # Se houver feedback (IIR Comb variável), adicionaríamos aqui:
        # Mas flanger básico é FIR Comb variável na maioria das mesas simples.
        # Se a Vedo usar feedback, a lógica muda levemente:
        # input_with_fb = x[n] + feedback * delayed_sample
        # y[n] = input_with_fb + delayed_sample (Depende da topologia)
        
        phase += phase_inc
        if phase > 2 * np.pi:
            phase -= 2 * np.pi
            
    return y