import numpy as np
from scipy.optimize import minimize
from effects.reverb import apply_reverb
from metrics import calculate_mse

def optimize_reverb_parameters(original_audio, target_audio, fs):
    """
    Tenta encontrar os ganhos dos filtros Comb para aproximar o efeito da mesa.
    Assumimos delays fixos (valores padrão de Schroeder) para simplificar, 
    otimizando o 'Decay' (ganhos).
    """
    
    # Valores "padrão" para Schroeder Reverb (em segundos)
    # Variar isso é complexo pois muda o tamanho do buffer (inteiro)
    fixed_delays_combs = [0.0297, 0.0371, 0.0411, 0.0437] 
    fixed_delays_ap = [0.005, 0.0017]
    fixed_gains_ap = [0.7, 0.7] # Allpass geralmente fixo em 0.7 para difusão
    
    # Queremos descobrir os ganhos dos 4 combs (g1, g2, g3, g4)
    # Chute inicial
    initial_gains = [0.8, 0.8, 0.8, 0.8]
    
    print("Iniciando otimização de parâmetros do Reverb...")
    
    def objective_function(params):
        # Restrição: Gains devem estar entre 0 e < 1 (para estabilidade)
        if any(p >= 0.99 or p <= 0.0 for p in params):
            return 1e9 # Penalidade alta
            
        # Gera áudio com os parâmetros atuais
        # Usamos apenas um trecho do áudio (ex: 2 segundos) para ser rápido
        limit = min(len(original_audio), 2 * fs)
        
        processed = apply_reverb(
            original_audio[:limit], 
            fs, 
            fixed_delays_combs, 
            params, # Gains sendo otimizados
            fixed_delays_ap, 
            fixed_gains_ap
        )
        
        # Compara com o áudio alvo (mesa)
        error = calculate_mse(target_audio[:limit], processed)
        return error

    # Executa otimização
    res = minimize(objective_function, initial_gains, method='Nelder-Mead', tol=1e-4)
    
    return res.x # Retorna os ganhos otimizados