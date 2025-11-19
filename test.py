import pyaudio
import numpy as np
import pygame
import sys
import threading
import queue
import math

# Configurações de áudio (mesmas do anterior)
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

# Parâmetros de reverb (mesmos)
REVERB_TYPES = {
    'Room': {'delay_ms': 30, 'decay': 0.6, 'num_combs': 4},
    'Hall': {'delay_ms': 80, 'decay': 0.9, 'num_combs': 6},
    'Plate': {'delay_ms': 50, 'decay': 0.7, 'num_combs': 3},
    'Spring': {'delay_ms': 120, 'decay': 0.5, 'num_combs': 8}
}

# Cores para visual "pedal de guitarra" (preto, prata, verde LED, etc.)
BLACK = (0, 0, 0)
SILVER = (192, 192, 192)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

class GuitarReverbPedal:
    def _init_(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Reverb Pedal - Guitar FX")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.input_gain = 1.0
        self.output_volume = 1.0
        self.reverb_mix = 0.5
        self.reverb_type_idx = 0  # 0: Room, 1: Hall, etc.
        self.reverb_types = list(REVERB_TYPES.keys())
        self.comb_filters = []
        self.data_queue = queue.Queue()
        self.running = False
        self.audio_thread = None
        
        # Dispositivos (simplificado: assume padrão; expanda se necessário)
        self.input_device = 0
        self.output_device = 0
        self.devices = self.get_device_list()
        
        # Posições para knobs (círculos rotativos)
        self.knob_pos = {
            'input_gain': (150, 300), 'output_volume': (300, 300),
            'reverb_mix': (450, 300)
        }
        self.knob_radius = 40
        self.knob_angles = {k: math.pi / 2 for k in self.knob_pos}  # Posição inicial (meio)
        
        # Posição para switch de tipo
        self.switch_pos = (600, 300)
        self.switch_on = False  # Para toggle visual
        
        # Status LED
        self.led_pos = (400, 100)
        self.led_on = False
        
    def get_device_list(self):
        # Retorna lista simples; em produção, liste via PyAudio
        return [(0, "Default Input"), (1, "Guitar Interface"), (0, "Default Output"), (1, "Speakers")]
    
    def init_comb_filters(self, delay_ms, decay, num_combs):
        self.comb_filters = []
        delay_samples = int(RATE * delay_ms / 1000.0)
        for i in range(num_combs):
            offset = i * (delay_samples // num_combs)
            self.comb_filters.append({'delay': delay_samples + offset, 'feedback': decay, 'buffer': np.zeros(delay_samples)})
    
    def value_from_angle(self, angle):
        # Converte ângulo para valor 0-1 (ou 0-2 para gain/vol)
        return (angle / (math.pi * 2)) * 2  # 0 a 2 para gain/vol, ajuste para mix 0-1 se preciso
    
    def angle_from_value(self, value, max_val=2.0):
        return (value / max_val) * (math.pi * 2)
    
    def process_reverb(self, data):
        input_sig = np.frombuffer(data, dtype=np.float32)
        input_sig *= self.input_gain
        
        dry = input_sig.copy()
        wet = np.zeros_like(input_sig)
        
        for comb in self.comb_filters:
            delay_buf = comb['buffer']
            feedback = comb['feedback']
            delay_len = comb['delay']
            
            for i in range(len(input_sig)):
                if i >= delay_len:
                    delayed = delay_buf[(i - delay_len) % delay_len]
                    wet[i] += delayed * 0.25
                    delay_buf[i % delay_len] = input_sig[i] + delayed * feedback
                else:
                    delay_buf[i % delay_len] = input_sig[i]
        
        output = (1 - self.reverb_mix) * dry + self.reverb_mix * wet
        output *= self.output_volume
        output = np.clip(output, -1.0, 1.0)
        
        return output.tobytes()
    
    def callback(self, in_data, frame_count, time_info, status):
        self.data_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def audio_thread_func(self):
        while self.running:
            try:
                data = self.data_queue.get(timeout=0.1)
                processed = self.process_reverb(data)
                self.stream.write(processed)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erro no áudio: {e}")
                break
    
    def start_stream(self):
        if self.stream:
            self.stop_stream()
        
        try:
            params = REVERB_TYPES[self.reverb_types[self.reverb_type_idx]]
            self.init_comb_filters(params['delay_ms'], params['decay'], params['num_combs'])
            
            self.stream = self.pa.open(
                format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True,
                input_device_index=self.input_device, output_device_index=self.output_device,
                frames_per_buffer=CHUNK, stream_callback=self.callback
            )
            self.stream.start_stream()
            self.running = True
            self.audio_thread = threading.Thread(target=self.audio_thread_func, daemon=True)
            self.audio_thread.start()
            self.led_on = True
            print("Pedal ativado! Toque sua guitarra.")
        except Exception as e:
            print(f"Erro: {e}")
    
    def stop_stream(self):
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.led_on = False
            print("Pedal desativado.")
    
    def draw_pedal_body(self):
        # Corpo do pedal: retângulo arredondado com "metal"
        rect = pygame.Rect(100, 150, 600, 300)
        pygame.draw.rect(self.screen, DARK_GRAY, rect)
        pygame.draw.rect(self.screen, SILVER, rect, 5)  # Borda prata
        
        # Detalhes: parafusos nos cantos
        for pos in [(100,150), (100,450), (700,150), (700,450)]:
            pygame.draw.circle(self.screen, BLACK, pos, 8)
            pygame.draw.circle(self.screen, SILVER, pos, 8, 2)
        
        # Label "REVERB" no topo
        text = self.font.render("REVERB FX", True, WHITE)
        self.screen.blit(text, (300, 120))
    
    def draw_knob(self, pos, angle, label, value):
        x, y = pos
        # Círculo do knob
        pygame.draw.circle(self.screen, LIGHT_GRAY, (x, y), self.knob_radius)
        pygame.draw.circle(self.screen, DARK_GRAY, (x, y), self.knob_radius, 3)
        
        # Linha indicadora
        end_x = x + self.knob_radius * math.cos(angle)
        end_y = y + self.knob_radius * math.sin(angle)
        pygame.draw.line(self.screen, RED, (x, y), (end_x, end_y), 4)
        
        # Label e valor
        label_text = self.small_font.render(label, True, WHITE)
        self.screen.blit(label_text, (x - 20, y + 50))
        val_text = self.small_font.render(f"{value:.1f}", True, YELLOW)
        self.screen.blit(val_text, (x - 15, y + 70))
    
    def draw_switch(self):
        x, y = self.switch_pos
        # Caixa do switch
        pygame.draw.rect(self.screen, BLACK, (x-10, y-20, 20, 40))
        pygame.draw.rect(self.screen, SILVER, (x-10, y-20, 20, 40), 2)
        # Posição do toggle
        toggle_y = y - 10 if self.switch_on else y + 10
        pygame.draw.circle(self.screen, GREEN if self.switch_on else RED, (x, toggle_y), 8)
        
        text = self.small_font.render("TYPE", True, WHITE)
        self.screen.blit(text, (x - 15, y + 30))
        type_text = self.small_font.render(self.reverb_types[self.reverb_type_idx], True, WHITE)
        self.screen.blit(type_text, (x - 40, y + 50))
    
    def draw_led(self):
        x, y = self.led_pos
        color = GREEN if self.led_on else RED
        pygame.draw.circle(self.screen, color, (x, y), 10)
        pygame.draw.circle(self.screen, WHITE, (x, y), 10, 2)
        text = self.small_font.render("ON", True, WHITE)
        self.screen.blit(text, (x + 15, y - 5))
    
    def draw_buttons(self):
        # Botão Start (verde)
        pygame.draw.rect(self.screen, GREEN, (150, 500, 100, 40))
        pygame.draw.rect(self.screen, WHITE, (150, 500, 100, 40), 2)
        start_text = self.small_font.render("START", True, BLACK)
        self.screen.blit(start_text, (170, 510))
        
        # Botão Stop (vermelho)
        pygame.draw.rect(self.screen, RED, (300, 500, 100, 40))
        pygame.draw.rect(self.screen, WHITE, (300, 500, 100, 40), 2)
        stop_text = self.small_font.render("STOP", True, WHITE)
        self.screen.blit(stop_text, (320, 510))
        
        # Instruções
        instr = self.small_font.render("Clique nos knobs para girar | Switch para mudar tipo", True, WHITE)
        self.screen.blit(instr, (400, 550))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop_stream()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Detectar clique em knob
                for knob, pos in self.knob_pos.items():
                    dist = math.hypot(mouse_pos[0] - pos[0], mouse_pos[1] - pos[1])
                    if dist <= self.knob_radius:
                        self.dragging_knob = knob
                        self.drag_start = mouse_pos
                        self.drag_center = pos
                        return  # Inicia drag
                # Detectar clique em switch
                switch_dist = math.hypot(mouse_pos[0] - self.switch_pos[0], mouse_pos[1] - self.switch_pos[1])
                if switch_dist <= 20:
                    self.switch_on = not self.switch_on
                    self.reverb_type_idx = (self.reverb_type_idx + 1) % len(self.reverb_types)
                # Botões
                if 150 <= mouse_pos[0] <= 250 and 500 <= mouse_pos[1] <= 540:
                    self.start_stream()
                elif 300 <= mouse_pos[0] <= 400 and 500 <= mouse_pos[1] <= 540:
                    self.stop_stream()
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging_knob = None
            elif event.type == pygame.MOUSEMOTION and hasattr(self, 'dragging_knob'):
                if self.dragging_knob:
                    mouse_pos = pygame.mouse.get_pos()
                    dx = mouse_pos[0] - self.drag_start[0]
                    dy = mouse_pos[1] - self.drag_start[1]
                    angle_change = math.atan2(dy, dx)
                    current_angle = self.knob_angles[self.dragging_knob]
                    new_angle = current_angle + angle_change
                    new_angle = max(0, min(math.pi * 2, new_angle))  # Limita rotação
                    self.knob_angles[self.dragging_knob] = new_angle
                    
                    # Atualiza valor
                    if self.dragging_knob == 'reverb_mix':
                        self.reverb_mix = new_angle / (math.pi * 2)  # 0-1
                    else:
                        self.input_gain = self.value_from_angle(new_angle) if self.dragging_knob == 'input_gain' else self.output_volume
                        if self.dragging_knob == 'output_volume':
                            self.output_volume = self.value_from_angle(new_angle)
    
    def update(self):
        # Atualiza ângulos baseados em valores (para redraw)
        self.knob_angles['input_gain'] = self.angle_from_value(self.input_gain)
        self.knob_angles['output_volume'] = self.angle_from_value(self.output_volume)
        self.knob_angles['reverb_mix'] = self.angle_from_value(self.reverb_mix, 1.0)  # Para mix 0-1
    
    def draw(self):
        self.screen.fill(BLACK)
        self.draw_pedal_body()
        self.draw_knob(self.knob_pos['input_gain'], self.knob_angles['input_gain'], "GAIN IN", self.input_gain)
        self.draw_knob(self.knob_pos['output_volume'], self.knob_angles['output_volume'], "VOL OUT", self.output_volume)
        self.draw_knob(self.knob_pos['reverb_mix'], self.knob_angles['reverb_mix'], "MIX", self.reverb_mix)
        self.draw_switch()
        self.draw_led()
        self.draw_buttons()
        pygame.display.flip()
    
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "_main_":
    pedal = GuitarReverbPedal()
    pedal.run()