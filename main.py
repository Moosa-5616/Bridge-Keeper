import pygame
import random
import json
import sys
import math

pygame.init()
pygame.mixer.init()  

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

COLORS = {
    'forest_green': (44, 95, 45),     
    'forest_light': (76, 175, 80),    
    'earth_brown': (139, 69, 19),     
    'earth_light': (205, 133, 63),    
    'flood_red': (178, 34, 34),       
    'flood_dark': (139, 0, 0),        
    'bridge_blue': (70, 130, 180),    
    'bridge_light': (135, 206, 235),  
    'village_beige': (245, 222, 179), 
    'village_light': (255, 248, 220), 
    'dark_grey': (47, 79, 79),        
    'light_grey': (192, 192, 192),    
    'gold': (255, 215, 0),            
    'silver': (192, 192, 192),        
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'panel_gradient_top': (250, 250, 250),
    'panel_gradient_bottom': (230, 230, 230),
    'button_gradient_top': (180, 200, 220),
    'button_gradient_bottom': (140, 160, 180)
}

HIGH_CONTRAST_COLORS = {
    'forest_green': (0, 255, 0),       
    'forest_light': (100, 255, 100),   
    'earth_brown': (255, 140, 0),      
    'earth_light': (255, 200, 100),    
    'flood_red': (255, 0, 0),          
    'flood_dark': (200, 0, 0),         
    'bridge_blue': (0, 100, 255),      
    'bridge_light': (100, 200, 255),   
    'village_beige': (255, 255, 200),  
    'village_light': (255, 255, 255),  
    'dark_grey': (64, 64, 64),         
    'light_grey': (192, 192, 192),     
    'gold': (255, 255, 0),             
    'silver': (224, 224, 224),         
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'panel_gradient_top': (255, 255, 255),
    'panel_gradient_bottom': (224, 224, 224),
    'button_gradient_top': (200, 200, 255),
    'button_gradient_bottom': (150, 150, 200)
}

class GameState:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    SETTINGS = "settings"
    TUTORIAL = "tutorial"

class BridgeKeeper:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("The Bridge Keeper")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        
        self.village_elements = self.initialize_village()
        
        self.difficulty = 'normal'  # 'easy', 'normal', 'hard'
        self.difficulties = ['easy', 'normal', 'hard']

        self.resources = {'wood': 0, 'stone': 0, 'metal': 0}
        self.villagers_saved = 0
        self.initial_villagers = sum(element['villagers'] for element in self.village_elements)
        self.current_villagers = self.initial_villagers
        self.bridge_progress = 0
        self.bridge_required = 100

        # Adjust starting conditions based on difficulty
        if self.difficulty == 'easy':
            self.flood_timer = 400  # More time
            self.resources = {'wood': 5, 'stone': 3, 'metal': 2}  # Starting resources
        elif self.difficulty == 'hard':
            self.flood_timer = 200  # Less time
            self.resources = {'wood': 0, 'stone': 0, 'metal': 0}  # No starting resources
        else:  # normal
            self.flood_timer = 300
        self.flood_level = 0
        self.moral_choices = []
        
        self.bridge_segments = []  
        self.total_segments = 20  
        self.bridge_animation_timer = 0
        self.last_segment_built = -1
        
        self.flood_wave_timer = 0
        self.flood_bubbles = []
        self.flood_ripples = []
        self.submerged_elements = []
        self.flood_warning_level = SCREEN_HEIGHT * 0.15
        
        self.moral_standing = 100  
        self.consequence_messages = []  
        self.choice_weights = {
            'house': {'moral_impact': -25, 'category': 'severe', 'message': 'Destroyed family home'},
            'tree': {'moral_impact': -2, 'category': 'minor', 'message': 'Cut down tree'},
            'well': {'moral_impact': -15, 'category': 'major', 'message': 'Demolished community well'},
            'fence': {'moral_impact': -1, 'category': 'minimal', 'message': 'Removed fence'},
            'shed': {'moral_impact': -5, 'category': 'moderate', 'message': 'Tore down shed'},
            'statue': {'moral_impact': -8, 'category': 'moderate', 'message': 'Destroyed cultural monument'}
        }
        self.total_villagers_displaced = 0
        self.moral_choice_timer = 0  
        
        self.hovered_element = None
        self.confirmation_element = None
        self.show_confirmation = False
        
        self.character = {
            'x': 300,
            'y': 300,
            'target_x': 300,
            'target_y': 300,
            'speed': 150,  
            'direction': 'down',  
            'animation_frame': 0,
            'animation_timer': 0,
            'moving': False,
            'carrying': None,  
            'action_cooldown': 0
        }
        
        self.ui_pulse_timer = 0
        self.notification_queue = []
        self.screen_shake = {'intensity': 0, 'duration': 0}

        self.accessibility = {
            'high_contrast': False,
            'large_text': False,
            'keyboard_navigation': True,
            'screen_reader': False,
            'reduced_motion': False
        }

        self.focused_element = None
        self.focusable_elements = []
        self.tab_index = 0

        self.screen_transition = {'active': False, 'progress': 0, 'duration': 0.5}

        self.destruction_particles = []
        self.placement_particles = []
        self.ui_particles = []

        self.placed_objects = []

        self.time_of_day = 0.3  # Start in morning (0 = midnight, 0.5 = noon)
        self.day_cycle_duration = 300  # 5 minutes per day/night cycle

        # Random events system
        self.event_timer = random.randint(30, 60)  # First event in 30-60 seconds
        self.current_event = None
        self.event_duration = 0
        self.event_messages = []

        # Sound effects (placeholders - add actual sound files)
        self.sounds = {
            'dismantle': None,  # pygame.mixer.Sound('sounds/dismantle.wav') if file exists
            'pickup': None,
            'place': None,
            'event': None,
            'bridge_build': None
        }

        # Background music
        self.background_music = None  # pygame.mixer.music.load('sounds/background.ogg') if file exists

        # Achievements system
        self.achievements = []
        self.difficulty = 'normal'  # 'easy', 'normal', 'hard'
        self.difficulties = ['easy', 'normal', 'hard']

        self.possible_achievements = {
            'saint': {'name': 'Saint of the Bridge', 'description': 'Achieved maximum moral standing', 'condition': lambda self: self.moral_standing >= 150},
            'perfect_savior': {'name': 'Perfect Savior', 'description': 'Saved all villagers', 'condition': lambda self: self.villagers_saved == self.initial_villagers},
            'bridge_master': {'name': 'Bridge Master', 'description': 'Built bridge with minimal resources', 'condition': lambda self: len(self.bridge_segments) >= 15 and sum(self.resources.values()) <= 10},
            'moral_dilemma': {'name': 'Moral Dilemma', 'description': 'Made difficult choices affecting many villagers', 'condition': lambda self: self.total_villagers_displaced >= 10},
            'resourceful': {'name': 'Resourceful', 'description': 'Gathered resources efficiently', 'condition': lambda self: sum(self.resources.values()) >= 50},
            'quick_builder': {'name': 'Quick Builder', 'description': 'Completed bridge in under 2 minutes', 'condition': lambda self: self.flood_timer >= 180}  # Assuming started with 300
        }

        self.generate_initial_objects()

        # Define possible random events
        self.possible_events = [
            {
                'name': 'Resource Windfall',
                'description': 'Found extra resources!',
                'effect': lambda self: self.apply_event_effect('resource_bonus', {'wood': 3, 'stone': 2}),
                'duration': 5,
                'color': 'forest_green'
            },
            {
                'name': 'Storm Damage',
                'description': 'Storm damaged some resources',
                'effect': lambda self: self.apply_event_effect('resource_loss', {'wood': 2, 'stone': 1}),
                'duration': 5,
                'color': 'flood_red'
            },
            {
                'name': 'Villager Aid',
                'description': 'Villagers helped gather materials',
                'effect': lambda self: self.apply_event_effect('resource_bonus', {'metal': 2}),
                'duration': 5,
                'color': 'bridge_blue'
            },
            {
                'name': 'Flood Warning',
                'description': 'Flood coming sooner!',
                'effect': lambda self: self.apply_event_effect('time_penalty', 10),
                'duration': 5,
                'color': 'flood_red'
            },
            {
                'name': 'Moral Boost',
                'description': 'Community spirit lifted',
                'effect': lambda self: self.apply_event_effect('moral_bonus', 10),
                'duration': 5,
                'color': 'gold'
            },
            {
                'name': 'Lucky Find',
                'description': 'Discovered hidden resources',
                'effect': lambda self: self.apply_event_effect('resource_bonus', {'wood': 1, 'stone': 1, 'metal': 1}),
                'duration': 5,
                'color': 'gold'
            }
        ]

        scale_factor = min(SCREEN_WIDTH / 1024, SCREEN_HEIGHT / 768)

        self.fonts = {
            'title': pygame.font.Font(None, int(72 * scale_factor)),      
            'heading': pygame.font.Font(None, int(48 * scale_factor)),    
            'subheading': pygame.font.Font(None, int(36 * scale_factor)), 
            'body_large': pygame.font.Font(None, int(28 * scale_factor)), 
            'body': pygame.font.Font(None, int(24 * scale_factor)),       
            'body_small': pygame.font.Font(None, int(20 * scale_factor)), 
            'caption': pygame.font.Font(None, int(16 * scale_factor)),    
            'tiny': pygame.font.Font(None, int(14 * scale_factor))        
        }

        self.font_large = self.fonts['heading']
        self.font_medium = self.fonts['body']
        self.font_small = self.fonts['body_small']
        self.font_tiny = self.fonts['caption']
        self.font_title = self.fonts['title']
        
    def initialize_village(self):
        """Initialize village elements that can be dismantled"""
        elements = []
        # Spread houses in a grid-like pattern with random jitter
        house_rows = 3
        house_cols = 5
        house_spacing_x = 90
        house_spacing_y = 120
        house_start_x = 60
        house_start_y = 120
        for row in range(house_rows):
            for col in range(house_cols):
                x = house_start_x + col * house_spacing_x + random.randint(-15, 15)
                y = house_start_y + row * house_spacing_y + random.randint(-15, 15)
                elements.append({
                    'type': 'house',
                    'x': x,
                    'y': y,
                    'width': 40,
                    'height': 40,
                    'villagers': random.randint(2, 6),
                    'resources': {'wood': random.randint(2, 4), 'stone': random.randint(1, 2)},
                    'description': 'Family house',
                    'dismantled': False
                })

        # Spread trees randomly but avoid overlap with houses
        tree_count = 25
        tree_positions = []
        for _ in range(tree_count):
            tries = 0
            while True:
                x = random.randint(40, 580)
                y = random.randint(300, 700)
                # Avoid overlap with houses and other trees
                too_close = False
                for e in elements:
                    dist = ((x - e['x']) ** 2 + (y - e['y']) ** 2) ** 0.5
                    if dist < 50:
                        too_close = True
                        break
                for tx, ty in tree_positions:
                    dist = ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
                    if dist < 40:
                        too_close = True
                        break
                if not too_close or tries > 20:
                    break
                tries += 1
            tree_positions.append((x, y))
            elements.append({
                'type': 'tree',
                'x': x,
                'y': y,
                'width': 24,
                'height': 32,
                'villagers': 0,
                'resources': {'wood': random.randint(1, 3)},
                'description': 'Tree',
                'dismantled': False
            })

        # Spread infrastructure randomly
        infrastructure_types = ['well', 'fence', 'shed', 'statue']
        for i in range(10):
            tries = 0
            while True:
                x = random.randint(80, 550)
                y = random.randint(200, 700)
                too_close = False
                for e in elements:
                    dist = ((x - e['x']) ** 2 + (y - e['y']) ** 2) ** 0.5
                    if dist < 45:
                        too_close = True
                        break
                if not too_close or tries > 20:
                    break
                tries += 1
            t = random.choice(infrastructure_types)
            if t == 'well':
                villagers = random.randint(1, 3)
                resources = {'stone': 2, 'metal': 1}
                desc = 'Community well'
                width, height = 28, 28
            elif t == 'fence':
                villagers = 0
                resources = {'wood': 1}
                desc = 'Fence'
                width, height = 40, 16
            elif t == 'shed':
                villagers = random.randint(0, 1)
                resources = {'wood': 2, 'metal': 1}
                desc = 'Storage shed'
                width, height = 32, 24
            else:
                villagers = 0
                resources = {'stone': 1, 'metal': 1}
                desc = 'Statue'
                width, height = 24, 32
            elements.append({
                'type': t,
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'villagers': villagers,
                'resources': resources,
                'description': desc,
                'dismantled': False
            })
        return elements
    
    def generate_initial_objects(self):
        """Generate initial logs and stones for the character to find"""
        for _ in range(3):
            x = random.randint(50, 550)
            y = random.randint(50, 650)
            log = {
                'x': x,
                'y': y,
                'type': 'log',
                'placed_time': pygame.time.get_ticks()
            }
            self.placed_objects.append(log)

        for _ in range(2):
            x = random.randint(50, 550)
            y = random.randint(50, 650)
            stone = {
                'x': x,
                'y': y,
                'type': 'stone',
                'placed_time': pygame.time.get_ticks()
            }
            self.placed_objects.append(stone)

    def get_color(self, color_key):
        """Get color based on accessibility settings"""
        if self.accessibility['high_contrast']:
            return HIGH_CONTRAST_COLORS.get(color_key, COLORS.get(color_key, (255, 255, 255)))
        return COLORS.get(color_key, (255, 255, 255))

    def get_font(self, font_key):
        """Get font based on accessibility settings"""
        base_font = self.fonts.get(font_key, self.fonts['body'])
        if self.accessibility['large_text']:
            font_size = base_font.get_height() + 4
            return pygame.font.Font(None, font_size)
        return base_font

    def toggle_high_contrast(self):
        """Toggle high contrast mode"""
        self.accessibility['high_contrast'] = not self.accessibility['high_contrast']

    def toggle_large_text(self):
        """Toggle large text mode"""
        self.accessibility['large_text'] = not self.accessibility['large_text']

    def play_sound(self, sound_name):
        """Play a sound effect if available"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].play()

    def save_game(self, filename="savegame.json"):
        """Save the current game state to a file"""
        try:
            game_state = {
                'resources': self.resources,
                'villagers_saved': self.villagers_saved,
                'current_villagers': self.current_villagers,
                'initial_villagers': self.initial_villagers,
                'bridge_progress': self.bridge_progress,
                'bridge_segments': [{'y': s['y'], 'type': s['type'], 'completed': s['completed']} for s in self.bridge_segments],
                'flood_timer': self.flood_timer,
                'moral_standing': self.moral_standing,
                'total_villagers_displaced': self.total_villagers_displaced,
                'moral_choices': self.moral_choices,
                'village_elements': [{'type': e['type'], 'x': e['x'], 'y': e['y'], 'dismantled': e['dismantled'], 'villagers': e['villagers'], 'description': e['description']} for e in self.village_elements],
                'placed_objects': self.placed_objects,
                'time_of_day': self.time_of_day,
                'achievements': self.achievements,
                'accessibility': self.accessibility
            }
            with open(filename, 'w') as f:
                json.dump(game_state, f, indent=2)
            return True
        except Exception as e:
            print(f"Save failed: {e}")

    def load_game(self, filename="savegame.json"):
        """Load game state from a file"""
        try:
            with open(filename, 'r') as f:
                game_state = json.load(f)

            self.resources = game_state.get('resources', self.resources)
            self.villagers_saved = game_state.get('villagers_saved', self.villagers_saved)
            self.current_villagers = game_state.get('current_villagers', self.current_villagers)
            self.initial_villagers = game_state.get('initial_villagers', self.initial_villagers)
            self.bridge_progress = game_state.get('bridge_progress', self.bridge_progress)
            self.bridge_segments = game_state.get('bridge_segments', self.bridge_segments)
            self.flood_timer = game_state.get('flood_timer', self.flood_timer)
            self.moral_standing = game_state.get('moral_standing', self.moral_standing)
            self.total_villagers_displaced = game_state.get('total_villagers_displaced', self.total_villagers_displaced)
            self.moral_choices = game_state.get('moral_choices', self.moral_choices)
            self.village_elements = game_state.get('village_elements', self.village_elements)
            self.placed_objects = game_state.get('placed_objects', self.placed_objects)
            self.time_of_day = game_state.get('time_of_day', self.time_of_day)
            self.achievements = game_state.get('achievements', self.achievements)
            self.accessibility = game_state.get('accessibility', self.accessibility)

            return True
        except Exception as e:
            print(f"Load failed: {e}")
            return False

    def cycle_focus(self):
        """Cycle through focusable elements for keyboard navigation"""
        if not self.focusable_elements:
            self.build_focusable_elements()

        if self.focusable_elements:
            self.tab_index = (self.tab_index + 1) % len(self.focusable_elements)
            self.focused_element = self.focusable_elements[self.tab_index]

    def activate_focused_element(self):
        """Activate the currently focused element"""
        if self.focused_element and self.focused_element.get('action'):
            self.focused_element['action']()

    def build_focusable_elements(self):
        """Build list of focusable UI elements"""
        self.focusable_elements = []

        for element in self.village_elements:
            if not element['dismantled']:
                self.focusable_elements.append({
                    'type': 'village_element',
                    'element': element,
                    'action': lambda e=element: self.handle_element_action(e)
                })

        self.focusable_elements.append({
            'type': 'character',
            'action': lambda: self.character_interact()
        })

    def handle_element_action(self, element):
        """Handle action for focused element"""
        if element['type'] == 'house' and element['villagers'] > 0:
            self.confirmation_element = element
            self.show_confirmation = True
        else:
            self.dismantle_element(element)
            self.create_destruction_particles(element['x'], element['y'])
            self.character['action_cooldown'] = 0.5

    def draw_focus_indicator(self, element):
        """Draw keyboard focus indicator"""
        if not self.accessibility['keyboard_navigation'] or element != self.focused_element:
            return

        if element['type'] == 'village_element':
            village_element = element['element']
            focus_rect = pygame.Rect(
                village_element['x'] - 4, village_element['y'] - 4,
                village_element['width'] + 8, village_element['height'] + 8
            )
            focus_color = self.get_color('gold')
            pygame.draw.rect(self.screen, focus_color, focus_rect, 3)
        elif element['type'] == 'character':
            char = self.character
            focus_rect = pygame.Rect(char['x'] - 20, char['y'] - 25, 40, 50)
            focus_color = self.get_color('gold')
            pygame.draw.rect(self.screen, focus_color, focus_rect, 3)

    def start_screen_transition(self):
        """Start a screen transition effect"""
        if not self.accessibility.get('reduced_motion', False):
            self.screen_transition['active'] = True
            self.screen_transition['progress'] = 0

    def update_screen_transition(self, dt):
        """Update screen transition animation"""
        if self.screen_transition['active']:
            self.screen_transition['progress'] += dt / self.screen_transition['duration']
            if self.screen_transition['progress'] >= 1.0:
                self.screen_transition['active'] = False
                self.screen_transition['progress'] = 1.0

    def draw_screen_transition(self):
        """Draw screen transition overlay"""
        if not self.screen_transition['active']:
            return

        progress = self.screen_transition['progress']
        max_radius = math.sqrt(SCREEN_WIDTH**2 + SCREEN_HEIGHT**2) / 2
        radius = max_radius * progress

        transition_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(transition_surface, (0, 0, 0, 255),
                         (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), int(radius))

        self.screen.blit(transition_surface, (0, 0))
    
    def draw_gradient_rect(self, surface, color1, color2, rect, vertical=True):
        """Draw a gradient rectangle with improved quality"""
        x, y, w, h = rect
        if vertical:
            for i in range(h):
                ratio = i / h if h > 0 else 0
                ratio = ratio ** 0.8  
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x, y + i), (x + w - 1, y + i))
        else:
            for i in range(w):
                ratio = i / w if w > 0 else 0
                ratio = ratio ** 0.8
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x + i, y), (x + i, y + h - 1))

    def draw_rounded_rect(self, surface, color, rect, radius=8, border_color=None, border_width=0):
        """Draw a rounded rectangle with modern styling"""
        x, y, w, h = rect

        rounded_surface = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(rounded_surface, color, (radius, 0, w - 2*radius, h))
        pygame.draw.rect(rounded_surface, color, (0, radius, w, h - 2*radius))
        pygame.draw.circle(rounded_surface, color, (radius, radius), radius)
        pygame.draw.circle(rounded_surface, color, (w - radius, radius), radius)
        pygame.draw.circle(rounded_surface, color, (radius, h - radius), radius)
        pygame.draw.circle(rounded_surface, color, (w - radius, h - radius), radius)

        if border_color and border_width > 0:
            pygame.draw.rect(rounded_surface, border_color, (radius, border_width, w - 2*radius, h - 2*border_width))
            pygame.draw.rect(rounded_surface, border_color, (border_width, radius, w - 2*border_width, h - 2*radius))
            pygame.draw.circle(rounded_surface, border_color, (radius, radius), radius - border_width//2)
            pygame.draw.circle(rounded_surface, border_color, (w - radius, radius), radius - border_width//2)
            pygame.draw.circle(rounded_surface, border_color, (radius, h - radius), radius - border_width//2)
            pygame.draw.circle(rounded_surface, border_color, (w - radius, h - radius), radius - border_width//2)

        surface.blit(rounded_surface, (x, y))

    def apply_lighting_effect(self, surface, light_pos, intensity=0.3, radius=100):
        """Apply dynamic lighting effects to a surface"""
        if self.accessibility.get('reduced_motion', False):
            return  

        lighting_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)

        center_x, center_y = light_pos
        for y in range(surface.get_height()):
            for x in range(surface.get_width()):
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                if distance < radius:
                    light_intensity = max(0, 1 - (distance / radius))
                    light_intensity *= intensity

                    alpha = int(light_intensity * 255)
                    lighting_surface.set_at((x, y), (255, 255, 255, alpha))

        surface.blit(lighting_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def draw_drop_shadow(self, surface, source_surface, offset_x=4, offset_y=4, blur_radius=2):
        """Draw a drop shadow for a surface"""
        if self.accessibility.get('reduced_motion', False):
            return

        shadow = pygame.Surface((source_surface.get_width() + blur_radius*2,
                               source_surface.get_height() + blur_radius*2), pygame.SRCALPHA)

        for i in range(blur_radius):
            alpha = 60 // (i + 1)  
            shadow.blit(source_surface, (blur_radius + i, blur_radius + i))
            shadow.fill((0, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_MULT)

        surface.blit(shadow, (offset_x - blur_radius, offset_y - blur_radius))

    def draw_background_gradient(self):
        """Draw an enhanced background with gradient and texture, affected by day/night cycle"""
        # Calculate lighting factor based on time of day
        # Day: 0.2-0.8 (bright), Night: 0.8-0.2 (dim)
        if 0.2 <= self.time_of_day <= 0.8:
            lighting_factor = 1.0  # Full daylight
        elif self.time_of_day < 0.2:
            # Dawn transition
            lighting_factor = 0.3 + (self.time_of_day / 0.2) * 0.7
        else:
            # Dusk transition
            lighting_factor = 0.3 + ((1 - self.time_of_day) / 0.2) * 0.7

        for y in range(SCREEN_HEIGHT):
            if y < SCREEN_HEIGHT * 0.7:
                ratio = y / (SCREEN_HEIGHT * 0.7)
                r = int((135 + (245 - 135) * ratio) * lighting_factor)
                g = int((206 + (222 - 206) * ratio) * lighting_factor)
                b = int((235 + (179 - 235) * ratio) * lighting_factor)
            else:
                ratio = (y - SCREEN_HEIGHT * 0.7) / (SCREEN_HEIGHT * 0.3)
                r = int((245 - 20 * ratio) * lighting_factor)
                g = int((222 - 20 * ratio) * lighting_factor)
                b = int((179 - 20 * ratio) * lighting_factor)

            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        if not self.accessibility.get('reduced_motion', False):
            import random
            for _ in range(200):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                brightness = random.randint(-10, 10)
                color = (max(0, min(255, int(r + brightness))),
                        max(0, min(255, int(g + brightness))),
                        max(0, min(255, int(b + brightness))))
                self.screen.set_at((x, y), color)

        # Add stars at night
        if lighting_factor < 0.5 and not self.accessibility.get('reduced_motion', False):
            import random
            for _ in range(50):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT // 2)
                star_brightness = random.randint(100, 255) * (0.5 - lighting_factor) * 2
                star_color = (int(star_brightness), int(star_brightness), int(star_brightness + 50))
                self.screen.set_at((x, y), star_color)

    def apply_ambient_lighting(self):
        """Apply ambient lighting effects to the scene, influenced by day/night cycle"""
        if self.accessibility.get('reduced_motion', False):
            return

        # Base lighting from day/night cycle
        if 0.2 <= self.time_of_day <= 0.8:
            base_intensity = 0.9  # Bright daylight
        elif self.time_of_day < 0.2:
            base_intensity = 0.3 + (self.time_of_day / 0.2) * 0.6  # Dawn
        else:
            base_intensity = 0.3 + ((1 - self.time_of_day) / 0.2) * 0.6  # Dusk

        # Add subtle flicker for atmosphere
        time_factor = (pygame.time.get_ticks() / 10000) % (2 * 3.14159)
        flicker = 0.05 * (0.5 + 0.5 * math.sin(time_factor))
        light_intensity = base_intensity + flicker

        lighting_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        lighting_overlay.fill((255, 255, 255, int(30 * (1 - light_intensity))))

        self.screen.blit(lighting_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    def draw_enhanced_panel(self, surface, rect, title="", border_color=None, accent_color=None):
        """Draw a modern UI panel with gradients, shadows, and rounded corners"""
        x, y, w, h = rect

        shadow_color = (0, 0, 0, 60)
        for offset in range(1, 4):
            shadow_surface = pygame.Surface((w + offset*2, h + offset*2), pygame.SRCALPHA)
            shadow_surface.fill(shadow_color)
            surface.blit(shadow_surface, (x - offset, y - offset))

        panel_gradient_top = accent_color or COLORS['panel_gradient_top']
        panel_gradient_bottom = COLORS['panel_gradient_bottom']
        self.draw_rounded_rect(surface, panel_gradient_top, rect, radius=12)

        highlight_rect = (x + 2, y + 2, w - 4, h - 4)
        highlight_color = tuple(min(255, c + 20) for c in panel_gradient_top)
        self.draw_rounded_rect(surface, highlight_color, highlight_rect, radius=10)

        border_col = border_color or COLORS['light_grey']
        self.draw_rounded_rect(surface, border_col, rect, radius=12, border_color=border_col, border_width=1)

        if title:
            title_bar_height = 28
            title_bar_rect = (x + 8, y + 6, w - 16, title_bar_height)
            title_bg_color = tuple(max(0, c - 10) for c in panel_gradient_top)
            self.draw_rounded_rect(surface, title_bg_color, title_bar_rect, radius=6)

            title_color = accent_color or COLORS['forest_green']
            title_surface = self.font_medium.render(title, True, title_color)
            title_rect = title_surface.get_rect(centerx=x + w//2, centery=y + 6 + title_bar_height//2)
            surface.blit(title_surface, title_rect)

            return y + title_bar_height + 12  
        return y + 12
    
    def move_character(self, dx, dy):
        """Move character in a direction"""
        char = self.character
        step_size = 32  
        
        new_x = char['x'] + dx * step_size
        new_y = char['y'] + dy * step_size
        
        new_x = max(20, min(580, new_x))
        new_y = max(20, min(SCREEN_HEIGHT - 20, new_y))
        
        char['target_x'] = new_x
        char['target_y'] = new_y
        char['moving'] = True
        
        if dx > 0:
            char['direction'] = 'right'
        elif dx < 0:
            char['direction'] = 'left'
        elif dy > 0:
            char['direction'] = 'down'
        elif dy < 0:
            char['direction'] = 'up'
    
    def move_character_to_position(self, pos):
        """Move character to a specific position (click to move)"""
        mouse_x, mouse_y = pos
        
        if mouse_x < 600 and mouse_y < SCREEN_HEIGHT - 20:  
            char = self.character
            char['target_x'] = mouse_x
            char['target_y'] = mouse_y
            char['moving'] = True
            
            dx = mouse_x - char['x']
            dy = mouse_y - char['y']
            
            if abs(dx) > abs(dy):
                char['direction'] = 'right' if dx > 0 else 'left'
            else:
                char['direction'] = 'down' if dy > 0 else 'up'
    
    def character_interact(self):
        """Handle character interaction with nearby objects"""
        char = self.character
        interaction_range = 40
        
        if char['action_cooldown'] > 0:
            return
        
        for element in self.village_elements:
            if element['dismantled']:
                continue
                
            distance = ((element['x'] + element['width']//2 - char['x'])**2 + 
                       (element['y'] + element['height']//2 - char['y'])**2)**0.5
            
            if distance <= interaction_range:
                if element['type'] == 'house' and element['villagers'] > 0:
                    self.confirmation_element = element
                    self.show_confirmation = True
                else:
                    self.dismantle_element(element)
                    self.create_destruction_particles(element['x'], element['y'])
                    char['action_cooldown'] = 0.5
                return
        
        for obj in self.placed_objects[:]:
            distance = ((obj['x'] - char['x'])**2 + (obj['y'] - char['y'])**2)**0.5
            if distance <= interaction_range:
                if char['carrying'] is None:
                    char['carrying'] = obj['type']
                    self.placed_objects.remove(obj)
                    self.create_pickup_particles(obj['x'], obj['y'])
                    self.play_sound('pickup')
                    char['action_cooldown'] = 0.3
                return
        
        if char['carrying']:
            self.place_object(char['x'], char['y'], char['carrying'])
            self.play_sound('place')
            char['carrying'] = None
            char['action_cooldown'] = 0.5
    
    def place_object(self, x, y, obj_type):
        """Place a log or stone object"""
        new_obj = {
            'x': x,
            'y': y,
            'type': obj_type,
            'placed_time': pygame.time.get_ticks()
        }
        self.placed_objects.append(new_obj)
        self.create_placement_particles(x, y)
    
    def create_destruction_particles(self, x, y):
        """Create particle effect for destroying objects"""
        for _ in range(8):
            particle = {
                'x': x + random.randint(-10, 10),
                'y': y + random.randint(-10, 10),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-3, -1),
                'life': random.uniform(0.5, 1.5),
                'color': COLORS['earth_brown']
            }
            self.destruction_particles.append(particle)
    
    def create_placement_particles(self, x, y):
        """Create particle effect for placing objects"""
        for _ in range(5):
            particle = {
                'x': x + random.randint(-5, 5),
                'y': y + random.randint(-5, 5),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-2, 0),
                'life': random.uniform(0.3, 0.8),
                'color': COLORS['forest_green']
            }
            self.placement_particles.append(particle)
    
    def create_pickup_particles(self, x, y):
        """Create particle effect for picking up objects"""
        for _ in range(6):
            particle = {
                'x': x + random.randint(-8, 8),
                'y': y + random.randint(-8, 8),
                'vx': random.uniform(-1.5, 1.5),
                'vy': random.uniform(-2.5, -0.5),
                'life': random.uniform(0.4, 1.0),
                'color': COLORS['gold']
            }
            self.ui_particles.append(particle)
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_high_contrast()
                elif event.key == pygame.K_F10:
                    self.toggle_large_text()
                elif event.key == pygame.K_F5 and self.state == GameState.PLAYING:
                    if self.save_game():
                        # Show save message
                        save_msg = {'text': 'Game Saved!', 'color': 'forest_green', 'timestamp': pygame.time.get_ticks()}
                        self.event_messages.append(save_msg)
                        if len(self.event_messages) > 3:
                            self.event_messages.pop(0)
                elif event.key == pygame.K_F9 and self.state == GameState.MENU:
                    if self.load_game():
                        self.state = GameState.PLAYING
                        load_msg = {'text': 'Game Loaded!', 'color': 'bridge_blue', 'timestamp': pygame.time.get_ticks()}
                        self.event_messages.append(load_msg)
                        if len(self.event_messages) > 3:
                            self.event_messages.pop(0)

                if event.key == pygame.K_ESCAPE:
                    if self.show_confirmation:
                        self.show_confirmation = False
                        self.confirmation_element = None
                    elif self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING

                if event.key == pygame.K_SPACE and self.state == GameState.MENU:
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_s and self.state == GameState.MENU:
                    self.state = GameState.SETTINGS
                elif event.key == pygame.K_h and self.state == GameState.MENU:
                    self.state = GameState.TUTORIAL
                elif event.key == pygame.K_d and self.state == GameState.MENU:
                    current_idx = self.difficulties.index(self.difficulty)
                    self.difficulty = self.difficulties[(current_idx + 1) % len(self.difficulties)]
                elif event.key == pygame.K_ESCAPE and self.state in [GameState.SETTINGS, GameState.TUTORIAL]:
                    self.state = GameState.MENU

                if self.accessibility['keyboard_navigation']:
                    if event.key == pygame.K_TAB:
                        self.cycle_focus()
                    elif event.key == pygame.K_RETURN and self.focused_element:
                        self.activate_focused_element()

                if self.state == GameState.PLAYING and not self.show_confirmation:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        self.move_character(0, -1)
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        self.move_character(0, 1)
                    elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.move_character(-1, 0)
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.move_character(1, 0)
                    elif event.key == pygame.K_e:  
                        self.character_interact()

                if self.show_confirmation:
                    if event.key == pygame.K_y:  
                        self.dismantle_element(self.confirmation_element)
                        self.show_confirmation = False
                        self.confirmation_element = None
                    elif event.key == pygame.K_n:  
                        self.show_confirmation = False
                        self.confirmation_element = None
                    
            if event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.PLAYING:
                if not self.show_confirmation:
                    if event.button == 1:  
                        self.move_character_to_position(event.pos)
                    elif event.button == 3:  
                        self.handle_click(event.pos)
            
            if event.type == pygame.MOUSEMOTION and self.state == GameState.PLAYING:
                if not self.show_confirmation:
                    self.handle_hover(event.pos)
    
    def handle_click(self, pos):
        """Handle mouse clicks on village elements"""
        mouse_x, mouse_y = pos
        
        for element in self.village_elements:
            if element['dismantled']:
                continue
                
            if (element['x'] <= mouse_x <= element['x'] + element['width'] and
                element['y'] <= mouse_y <= element['y'] + element['height']):
                
                if element['type'] == 'house' and element['villagers'] > 0:
                    self.confirmation_element = element
                    self.show_confirmation = True
                else:
                    self.dismantle_element(element)
                break
    
    def handle_hover(self, pos):
        """Handle mouse hover over village elements"""
        mouse_x, mouse_y = pos
        self.hovered_element = None
        
        for element in self.village_elements:
            if element['dismantled']:
                continue
                
            if (element['x'] <= mouse_x <= element['x'] + element['width'] and
                element['y'] <= mouse_y <= element['y'] + element['height']):
                
                self.hovered_element = element
                break
    
    def dismantle_element(self, element):
        """Dismantle a village element and gather resources"""
        for resource, amount in element['resources'].items():
            self.resources[resource] += amount

        self.play_sound('dismantle')

        moral_weight = self.choice_weights.get(element['type'], {'moral_impact': 0, 'category': 'minimal', 'message': 'Unknown action'})

        choice = {
            'type': element['type'],
            'description': element['description'],
            'villagers_affected': element['villagers'],
            'resources_gained': element['resources'],
            'moral_impact': moral_weight['moral_impact'],
            'category': moral_weight['category'],
            'timestamp': pygame.time.get_ticks()
        }
        self.moral_choices.append(choice)

        self.apply_moral_consequences(choice)

        self.total_villagers_displaced += element['villagers']

        element['dismantled'] = True

        self.current_villagers -= element['villagers']
        self.current_villagers = max(0, self.current_villagers)
    
    def update_game(self, dt):
        """Update game state"""
        if self.state != GameState.PLAYING:
            return
            
        if not self.show_confirmation:
            self.flood_timer -= dt
            if self.flood_timer <= 0:
                self.end_game()
                return
        
        self.update_character(dt)

        self.update_particles_optimized(dt)

        self.ui_pulse_timer += dt

        # Update day/night cycle
        self.time_of_day = (self.time_of_day + dt / self.day_cycle_duration) % 1

        # Update random events
        self.event_timer -= dt
        if self.event_timer <= 0:
            self.trigger_random_event()
            self.event_timer = random.randint(45, 90)  # Next event in 45-90 seconds

        if self.current_event:
            self.event_duration -= dt
            if self.event_duration <= 0:
                self.current_event = None

        if self.screen_shake['duration'] > 0:
            self.screen_shake['duration'] -= dt
            if self.screen_shake['duration'] <= 0:
                self.screen_shake['intensity'] = 0

        self.update_flood_animation(dt)

        self.bridge_animation_timer += dt

        for segment in self.bridge_segments:
            if not segment['completed'] and pygame.time.get_ticks() - segment['build_time'] > 500:
                segment['completed'] = True

        self.moral_choice_timer += dt

        current_time = pygame.time.get_ticks()
        self.consequence_messages = [msg for msg in self.consequence_messages
                                   if current_time - msg['timestamp'] < 3000]

        self.event_messages = [msg for msg in self.event_messages
                              if current_time - msg['timestamp'] < 5000]

        self.auto_build_bridge()

        if self.bridge_progress >= self.bridge_required:
            self.villagers_saved = self.current_villagers
            self.end_game()
    
    def update_character(self, dt):
        """Update character movement and animation"""
        char = self.character
        
        if char['action_cooldown'] > 0:
            char['action_cooldown'] -= dt
        
        if char['moving']:
            dx = char['target_x'] - char['x']
            dy = char['target_y'] - char['y']
            distance = (dx**2 + dy**2)**0.5
            
            if distance < 3:  
                char['x'] = char['target_x']
                char['y'] = char['target_y']
                char['moving'] = False
            else:
                move_speed = char['speed'] * dt
                char['x'] += (dx / distance) * move_speed
                char['y'] += (dy / distance) * move_speed
        
        char['animation_timer'] += dt
        if char['animation_timer'] >= 0.15:  
            char['animation_frame'] = (char['animation_frame'] + 1) % 6  
            char['animation_timer'] = 0
    
    def update_particles_optimized(self, dt):
        """Update all particle systems with performance optimizations"""
        max_particles = 50 if self.accessibility.get('reduced_motion', False) else 100

        self.destruction_particles = [
            particle for particle in self.destruction_particles
            if self.update_single_particle(particle, dt, gravity=0.1)
        ][:max_particles]

        self.placement_particles = [
            particle for particle in self.placement_particles
            if self.update_single_particle(particle, dt, gravity=0.05)
        ][:max_particles//2]

        self.ui_particles = [
            particle for particle in self.ui_particles
            if self.update_single_particle(particle, dt, gravity=0.08)
        ][:max_particles//2]

    def update_single_particle(self, particle, dt, gravity=0.0):
        """Update a single particle with optimized calculations"""
        particle['x'] += particle['vx'] * dt * 60  
        particle['y'] += particle['vy'] * dt * 60
        particle['vy'] += gravity * dt * 60
        particle['life'] -= dt

        return (particle['life'] > 0 and
                0 <= particle['x'] <= SCREEN_WIDTH and
                0 <= particle['y'] <= SCREEN_HEIGHT)
    
    def auto_build_bridge(self):
        """Automatically build bridge using available resources"""
        if self.bridge_progress >= self.bridge_required:
            return
            
        wood_needed = 3
        stone_needed = 2
        metal_needed = 1
        
        while (self.resources['wood'] >= wood_needed and 
               self.resources['stone'] >= stone_needed and 
               self.resources['metal'] >= metal_needed and
               len(self.bridge_segments) < self.total_segments):
            
            self.resources['wood'] -= wood_needed
            self.resources['stone'] -= stone_needed
            self.resources['metal'] -= metal_needed
            
            segment_y = SCREEN_HEIGHT - (len(self.bridge_segments) + 1) * (SCREEN_HEIGHT // self.total_segments)
            new_segment = {
                'y': segment_y,
                'type': self.get_bridge_segment_type(len(self.bridge_segments)),
                'build_time': pygame.time.get_ticks(),
                'completed': False
            }
            self.bridge_segments.append(new_segment)
            
            self.bridge_progress = (len(self.bridge_segments) / self.total_segments) * self.bridge_required
            
            self.bridge_animation_timer = 0
            self.last_segment_built = len(self.bridge_segments) - 1
    
    def get_bridge_segment_type(self, segment_index):
        """Determine the type of bridge segment based on position"""
        total_segments = self.total_segments
        
        if segment_index < 2 or segment_index >= total_segments - 2:
            return 'foundation'  
        elif segment_index % 4 == 0:
            return 'support'    
        else:
            return 'platform'   
    
    def check_achievements(self):
        """Check and unlock achievements"""
        for key, achievement in self.possible_achievements.items():
            if key not in self.achievements and achievement['condition'](self):
                self.achievements.append(key)

    def end_game(self):
        """End the game and calculate results with moral consequences"""
        self.state = GameState.GAME_OVER

        if self.bridge_progress >= self.bridge_required:
            self.villagers_saved = self.current_villagers
        else:
            completion_ratio = self.bridge_progress / self.bridge_required
            self.villagers_saved = int(self.current_villagers * completion_ratio)

        self.apply_moral_ending_consequences()
        self.check_achievements()
    
    def draw_menu(self):
        """Draw the main menu with modern typography"""
        self.screen.fill(self.get_color('village_beige'))

        title = self.get_font('title').render("The Bridge Keeper", True, self.get_color('forest_green'))
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 180))
        self.screen.blit(title, title_rect)

        subtitle = self.get_font('subheading').render("Save the village from the flood", True, self.get_color('earth_brown'))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 230))
        self.screen.blit(subtitle, subtitle_rect)

        instructions = [
            "Control your character to manage village resources",
            "WASD/Arrow Keys: Move character around the village",
            "E Key: Interact with nearby objects (destroy/pickup/place)",
            "Left Click: Move character to position",
            "Right Click: Direct interaction with objects",
            "",
            "Gather wood, stone, and metal to build the bridge",
            "Save as many villagers as possible before the flood arrives",
            "",
            f"Difficulty: {self.difficulty.title()} (Press D to change)",
            "",
            "Press SPACE to start",
            "Press S for Settings",
            "Press H for Help/Tutorial",
            "Press F9 to Load Saved Game",
            "",
            "In-Game: F5 (Save) | F11 (High Contrast) | F10 (Large Text)"
        ]

        y_start = 320
        for i, instruction in enumerate(instructions):
            if instruction == "":
                y_start += 10  
                continue

            if "SPACE to start" in instruction:
                font = self.get_font('body')
                color = self.get_color('bridge_blue')
            elif "Accessibility:" in instruction:
                font = self.get_font('caption')
                color = self.get_color('dark_grey')
            else:
                font = self.get_font('body_small')
                color = self.get_color('dark_grey')

            text = font.render(instruction, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_start + i * 25))
            self.screen.blit(text, text_rect)
    
    def draw_game(self):
        """Draw the main game screen with enhanced graphics"""
        shake_x = shake_y = 0
        if self.screen_shake['intensity'] > 0:
            import random
            shake_x = random.randint(-self.screen_shake['intensity'], self.screen_shake['intensity'])
            shake_y = random.randint(-self.screen_shake['intensity'], self.screen_shake['intensity'])

        self.draw_background_gradient()

        self.apply_ambient_lighting()
        
        shake_surface = None
        if shake_x != 0 or shake_y != 0:
            shake_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            shake_surface.fill(COLORS['village_beige'])
            draw_surface = shake_surface
        else:
            draw_surface = self.screen
        
        self.draw_flood_animation()
        
        for element in self.village_elements:
            if element['dismantled']:
                continue

            self.draw_village_element(element)

            if element == self.hovered_element:
                self.draw_hover_effect(element)

            if self.focused_element and self.focused_element.get('type') == 'village_element' and self.focused_element.get('element') == element:
                self.draw_focus_indicator(self.focused_element)
        
        self.draw_placed_objects()
        
        self.draw_character()
        
        self.draw_particles()
        
        river_rect = pygame.Rect(600, 0, 100, SCREEN_HEIGHT)
        self.draw_gradient_rect(self.screen, COLORS['bridge_blue'], COLORS['bridge_light'], river_rect)
        
        self.draw_bridge()
        
        bridge_area = pygame.Rect(615, 0, 70, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['dark_grey'], bridge_area, 2)
        
        self.draw_interaction_indicator()
        
        self.draw_enhanced_ui()

        if self.focused_element and self.focused_element.get('type') == 'character':
            self.draw_focus_indicator(self.focused_element)
        
        if shake_surface is not None and (shake_x != 0 or shake_y != 0):
            self.screen.blit(shake_surface, (shake_x, shake_y))
    
    def draw_pixel_perfect_rect(self, surface, color, rect, outline_color=None):
        """Draw a pixel-perfect rectangle without anti-aliasing"""
        x, y, w, h = rect
        x, y, w, h = int(x), int(y), int(w), int(h)
        pygame.draw.rect(surface, color, (x, y, w, h))
        if outline_color:
            pygame.draw.rect(surface, outline_color, (x, y, w, h), 1)
    
    def draw_pixel_art_sprite(self, x, y, sprite_data, pixel_size=4, scale=1.0):
        """Draw an enhanced pixel art sprite with better quality"""
        for row_idx, row in enumerate(sprite_data):
            for col_idx, color_key in enumerate(row):
                if color_key and color_key in COLORS:
                    pixel_x = x + int(col_idx * pixel_size * scale)
                    pixel_y = y + int(row_idx * pixel_size * scale)
                    size = int(pixel_size * scale)

                    base_color = self.get_color(color_key)

                    if color_key in ['earth_brown', 'dark_grey', 'flood_red']:
                        highlight_color = tuple(min(255, c + 15) for c in base_color)
                        self.draw_pixel_perfect_rect(self.screen, highlight_color,
                                                   (pixel_x, pixel_y, size//2, size//2))
                        self.draw_pixel_perfect_rect(self.screen, base_color,
                                                   (pixel_x + size//2, pixel_y + size//2, size - size//2, size - size//2))
                        shadow_color = tuple(max(0, c - 20) for c in base_color)
                        self.draw_pixel_perfect_rect(self.screen, shadow_color,
                                                   (pixel_x + size//2, pixel_y, size - size//2, size//2))
                        self.draw_pixel_perfect_rect(self.screen, shadow_color,
                                                   (pixel_x, pixel_y + size//2, size//2, size - size//2))
                    else:
                        self.draw_pixel_perfect_rect(self.screen, base_color,
                                                   (pixel_x, pixel_y, size, size))

    def draw_village_element(self, element):
        """Draw a village element with true pixel art style"""
        x, y = int(element['x']), int(element['y'])
        
        if element['type'] == 'house':
            house_sprite = [
                ['', '', '', '', '', '', '', '', 'flood_red', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', '', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', '', '', '', '', '', ''],
                ['', '', '', '', '', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', '', '', '', '', ''],
                ['', '', '', '', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', '', '', '', ''],
                ['', '', '', 'flood_red', 'flood_red', 'flood_red', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', '', '', ''],
                ['', '', 'flood_red', 'flood_red', 'flood_red', 'dark_grey', 'dark_grey', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'dark_grey', 'dark_grey', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', '', ''],
                ['', 'flood_red', 'flood_red', 'flood_red', 'dark_grey', 'dark_grey', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'dark_grey', 'dark_grey', 'flood_red', 'flood_red', 'flood_red', '', '', '', '', ''],
                ['flood_red', 'flood_red', 'flood_red', 'dark_grey', 'dark_grey', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'dark_grey', 'dark_grey', 'flood_red', 'flood_red', 'flood_red', '', '', '', ''],
                ['dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey'],
                ['black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'black', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'black', 'bridge_blue', 'white', 'bridge_blue', 'black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black', 'bridge_blue', 'white', 'bridge_blue', 'black', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'black', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'black', 'black', 'black', 'black', 'black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black', 'black', 'black', 'black', 'black', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'black'],
                ['black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black']
            ]
            self.draw_pixel_art_sprite(x, y, house_sprite, pixel_size=3)
            
            char = self.character
            distance = ((element['x'] + element['width']//2 - char['x'])**2 + 
                       (element['y'] + element['height']//2 - char['y'])**2)**0.5
            
            if distance <= 40 and not char['moving']:  
                interaction_rect = pygame.Rect(element['x'] - 2, element['y'] - 2, 
                                             element['width'] + 4, element['height'] + 4)
                pygame.draw.rect(self.screen, COLORS['gold'], interaction_rect, 2)
            
        elif element['type'] == 'tree':
            tree_sprite = [
                ['', '', '', '', '', '', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', '', '', '', '', '', ''],
                ['', '', '', '', '', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', '', '', '', '', ''],
                ['', '', '', '', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', '', '', '', ''],
                ['', '', '', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'village_beige', 'forest_green', 'forest_green', 'village_beige', 'forest_green', 'forest_light', 'forest_green', 'forest_green', '', '', ''],
                ['', '', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', '', ''],
                ['', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_green', ''],
                ['forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'village_beige', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'village_beige', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_green'],
                ['forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green'],
                ['forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green'],
                ['', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_light', 'forest_green', 'forest_green', 'forest_green', ''],
                ['', '', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', '', ''],
                ['', '', '', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', '', '', ''],
                ['', '', '', '', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', 'forest_green', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', '', '', '', ''],
                ['', '', '', '', '', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', '', '', '', '', '']
            ]
            self.draw_pixel_art_sprite(x, y, tree_sprite, pixel_size=3)
            
        elif element['type'] == 'well':
            well_sprite = [
                ['', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', '', ''],
                ['', '', 'earth_brown', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'black', 'black', 'earth_brown', 'earth_brown', 'earth_brown', '', '', ''],
                ['', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', '', ''],
                ['dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', ''],
                ['dark_grey', 'dark_grey', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'black', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'white', 'bridge_blue', 'bridge_blue', 'white', 'bridge_blue', 'black', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'black', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'black', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'black', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey'],
                ['', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', '']
            ]
            self.draw_pixel_art_sprite(x, y, well_sprite, pixel_size=3)
            
        elif element['type'] == 'fence':
            fence_sprite = [
                ['black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'village_beige', 'black', '', 'black', 'earth_brown', 'village_beige', 'black', '', 'black', 'earth_brown', 'village_beige', 'black', '', 'black', 'earth_brown', 'village_beige'],
                ['black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                ['black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown', 'black', '', 'black', 'earth_brown', 'earth_brown'],
                ['black', 'black', 'black', 'black', '', 'black', 'black', 'black', 'black', '', 'black', 'black', 'black', 'black', '', 'black', 'black', 'black']
            ]
            self.draw_pixel_art_sprite(x, y, fence_sprite, pixel_size=3)
            
        elif element['type'] == 'shed':
            shed_sprite = [
                ['', '', '', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', '', '', ''],
                ['', '', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', '', ''],
                ['', '', '', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', '', '', ''],
                ['black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'dark_grey', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'dark_grey', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black', 'forest_green', 'forest_green', 'black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black', 'forest_green', 'earth_brown', 'black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black', 'forest_green', 'forest_green', 'black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black', 'forest_green', 'forest_green', 'black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black', 'forest_green', 'forest_green', 'black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black', 'black', 'black', 'black', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'black'],
                ['black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black', 'black']
            ]
            self.draw_pixel_art_sprite(x, y, shed_sprite, pixel_size=3)
            
        elif element['type'] == 'statue':
            statue_sprite = [
                ['', '', '', '', '', '', 'bridge_blue', 'bridge_blue', 'bridge_blue', 'bridge_blue', '', '', '', '', '', ''],
                ['', '', '', '', '', 'bridge_blue', 'bridge_blue', 'white', 'white', 'bridge_blue', 'bridge_blue', '', '', '', '', ''],
                ['', '', '', '', 'village_beige', 'village_beige', 'bridge_blue', 'white', 'white', 'bridge_blue', 'village_beige', 'village_beige', '', '', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'bridge_blue', 'bridge_blue', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', 'village_beige', 'village_beige', 'village_beige', 'flood_red', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'flood_red', 'village_beige', 'village_beige', 'village_beige', '', ''],
                ['', '', 'village_beige', 'village_beige', 'flood_red', 'flood_red', 'flood_red', 'village_beige', 'village_beige', 'flood_red', 'flood_red', 'flood_red', 'village_beige', 'village_beige', '', ''],
                ['', '', 'village_beige', 'village_beige', 'village_beige', 'flood_red', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'flood_red', 'village_beige', 'village_beige', 'village_beige', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', '', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', '', '', ''],
                ['', '', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', '', ''],
                ['', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', ''],
                ['dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'dark_grey', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'dark_grey', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'village_beige', 'dark_grey', 'dark_grey'],
                ['dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey']
            ]
            self.draw_pixel_art_sprite(x, y, statue_sprite, pixel_size=3)

    def draw_hover_effect(self, element):
        """Draw hover effect around an element"""
        x, y = int(element['x']), int(element['y'])
        width, height = element['width'], element['height']
        
        for i in range(3):
            outline_color = COLORS['white'] if i == 0 else COLORS['bridge_blue']
            outline_rect = pygame.Rect(x - i - 1, y - i - 1, width + 2*(i+1), height + 2*(i+1))
            pygame.draw.rect(self.screen, outline_color, outline_rect, 1)
        
        self.draw_resource_tooltip(element)
    
    def draw_resource_tooltip(self, element):
        """Draw an enhanced tooltip showing what resources this element provides"""
        mouse_pos = pygame.mouse.get_pos()
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] - 80

        tooltip_width = 220
        if tooltip_x + tooltip_width > SCREEN_WIDTH:
            tooltip_x = mouse_pos[0] - tooltip_width - 15
        if tooltip_y < 0:
            tooltip_y = mouse_pos[1] + 20

        tooltip_lines = [
            f"{element['type'].title()}: {element['description']}",
            "Resources gained:"
        ]

        for resource, amount in element['resources'].items():
            tooltip_lines.append(f"  • {resource.title()}: +{amount}")

        if element['villagers'] > 0:
            tooltip_lines.append(f"Villagers displaced: {element['villagers']}")
            tooltip_lines.append("This will affect your moral standing!")

        line_height = 18
        tooltip_height = len(tooltip_lines) * line_height + 20

        tooltip_rect = (tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        self.draw_enhanced_panel(self.screen, tooltip_rect, "", self.get_color('dark_grey'))

        for i, line in enumerate(tooltip_lines):
            if "displaced" in line or "moral" in line:
                color = self.get_color('flood_red')
                font = self.get_font('body_small')
            elif "Resources" in line:
                color = self.get_color('forest_green')
                font = self.get_font('body_small')
            else:
                color = self.get_color('black')
                font = self.get_font('body_small')

            text = font.render(line, True, color)
            self.screen.blit(text, (tooltip_x + 10, tooltip_y + 10 + i * line_height))
    
    def draw_confirmation_dialog(self):
        """Draw confirmation dialog for dismantling houses"""
        if not self.show_confirmation or not self.confirmation_element:
            return
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(COLORS['black'])
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        dialog_width = 400
        dialog_height = 200
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, COLORS['village_beige'], dialog_rect)
        pygame.draw.rect(self.screen, COLORS['black'], dialog_rect, 3)
        
        element = self.confirmation_element
        dialog_lines = [
            "MORAL CHOICE",
            "",
            f"Dismantle {element['description']}?",
            f"This will displace {element['villagers']} villagers",
            "but provide resources for the bridge.",
            "",
            "Press Y to dismantle, N to cancel"
        ]
        
        line_height = 25
        start_y = dialog_y + 20
        
        for i, line in enumerate(dialog_lines):
            if line == "MORAL CHOICE":
                color = COLORS['flood_red']
                font = self.font_medium
            elif "displace" in line:
                color = COLORS['flood_red']
                font = self.font_small
            elif line.startswith("Press"):
                color = COLORS['forest_green']
                font = self.font_small
            else:
                color = COLORS['black']
                font = self.font_small
            
            text = font.render(line, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * line_height))
            self.screen.blit(text, text_rect)

    def draw_bridge(self):
        """Draw the bridge with detailed segments and construction animation"""
        bridge_x = 620
        bridge_width = 60
        
        for i, segment in enumerate(self.bridge_segments):
            segment_height = SCREEN_HEIGHT // self.total_segments
            y = segment['y']
            
            alpha = 255
            if not segment['completed']:
                time_since_built = pygame.time.get_ticks() - segment['build_time']
                alpha = min(255, int((time_since_built / 500) * 255))
            
            if segment['type'] == 'foundation':
                self.draw_bridge_foundation(bridge_x, y, bridge_width, segment_height, alpha)
            elif segment['type'] == 'support':
                self.draw_bridge_support(bridge_x, y, bridge_width, segment_height, alpha)
            else:  
                self.draw_bridge_platform(bridge_x, y, bridge_width, segment_height, alpha)
            
            if i == self.last_segment_built and self.bridge_animation_timer < 1.0:
                self.draw_construction_effects(bridge_x, y, bridge_width, segment_height)
    
    def draw_bridge_foundation(self, x, y, width, height, alpha=255):
        """Draw a bridge foundation segment (stone base)"""
        foundation_color = (*COLORS['dark_grey'][:3], alpha) if alpha < 255 else COLORS['dark_grey']
        foundation_rect = pygame.Rect(x + 5, y, width - 10, height)
        
        if alpha < 255:
            temp_surface = pygame.Surface((width - 10, height))
            temp_surface.fill(COLORS['dark_grey'])
            temp_surface.set_alpha(alpha)
            self.screen.blit(temp_surface, (x + 5, y))
        else:
            pygame.draw.rect(self.screen, COLORS['dark_grey'], foundation_rect)
        
        if alpha == 255:
            for stone_x in range(x + 8, x + width - 8, 8):
                for stone_y in range(y + 2, y + height - 2, 6):
                    stone_rect = pygame.Rect(stone_x, stone_y, 6, 4)
                    pygame.draw.rect(self.screen, COLORS['village_beige'], stone_rect)
                    pygame.draw.rect(self.screen, COLORS['black'], stone_rect, 1)
    
    def draw_bridge_support(self, x, y, width, height, alpha=255):
        """Draw a bridge support segment (wooden pillar)"""
        pillar_color = (*COLORS['earth_brown'][:3], alpha) if alpha < 255 else COLORS['earth_brown']
        pillar_rect = pygame.Rect(x + 10, y, width - 20, height)
        
        if alpha < 255:
            temp_surface = pygame.Surface((width - 20, height))
            temp_surface.fill(COLORS['earth_brown'])
            temp_surface.set_alpha(alpha)
            self.screen.blit(temp_surface, (x + 10, y))
        else:
            pygame.draw.rect(self.screen, COLORS['earth_brown'], pillar_rect)
        
        if alpha == 255:
            beam_rect1 = pygame.Rect(x + 5, y + height//3, width - 10, 4)
            beam_rect2 = pygame.Rect(x + 5, y + 2*height//3, width - 10, 4)
            pygame.draw.rect(self.screen, COLORS['village_beige'], beam_rect1)
            pygame.draw.rect(self.screen, COLORS['village_beige'], beam_rect2)
            pygame.draw.rect(self.screen, COLORS['black'], pillar_rect, 1)
    
    def draw_bridge_platform(self, x, y, width, height, alpha=255):
        """Draw a bridge platform segment (wooden planks)"""
        platform_color = (*COLORS['earth_brown'][:3], alpha) if alpha < 255 else COLORS['earth_brown']
        platform_rect = pygame.Rect(x, y, width, height)
        
        if alpha < 255:
            temp_surface = pygame.Surface((width, height))
            temp_surface.fill(COLORS['earth_brown'])
            temp_surface.set_alpha(alpha)
            self.screen.blit(temp_surface, (x, y))
        else:
            pygame.draw.rect(self.screen, COLORS['earth_brown'], platform_rect)
        
        if alpha == 255:
            for plank_y in range(y, y + height, 4):
                plank_rect = pygame.Rect(x + 2, plank_y, width - 4, 3)
                pygame.draw.rect(self.screen, COLORS['village_beige'], plank_rect)
                pygame.draw.rect(self.screen, COLORS['black'], plank_rect, 1)
    
    def draw_construction_effects(self, x, y, width, height):
        """Draw sparkling effects for newly constructed segments"""
        import random
        
        for _ in range(5):
            spark_x = x + random.randint(0, width)
            spark_y = y + random.randint(0, height)
            spark_size = random.randint(2, 4)
            
            spark_colors = [COLORS['white'], COLORS['bridge_blue'], COLORS['village_beige']]
            spark_color = random.choice(spark_colors)
            
            pygame.draw.circle(self.screen, spark_color, (spark_x, spark_y), spark_size)

    def update_flood_animation(self, dt):
        """Update flood level and animation effects"""
        time_progress = 1 - (self.flood_timer / 300)
        
        if time_progress < 0.5:
            flood_progress = time_progress * 0.4
        else:
            remaining_progress = (time_progress - 0.5) * 2
            flood_progress = 0.4 + (remaining_progress ** 1.5) * 0.6
        
        self.flood_level = int(flood_progress * SCREEN_HEIGHT * 0.6)  
        
        self.flood_wave_timer += dt * 3
        
        if self.flood_level > 0 and len(self.flood_bubbles) < 20:
            import random
            if random.random() < 0.1:  
                bubble = {
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': SCREEN_HEIGHT - self.flood_level + random.randint(-10, 10),
                    'size': random.randint(2, 6),
                    'speed': random.uniform(0.5, 2.0),
                    'life': random.uniform(2, 5)
                }
                self.flood_bubbles.append(bubble)
        
        for bubble in self.flood_bubbles[:]:
            bubble['y'] -= bubble['speed']
            bubble['life'] -= dt
            if bubble['life'] <= 0 or bubble['y'] < SCREEN_HEIGHT - self.flood_level - 50:
                self.flood_bubbles.remove(bubble)
        
        if self.flood_level > 0:
            import random
            if random.random() < 0.05:  
                ripple = {
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': SCREEN_HEIGHT - self.flood_level,
                    'radius': 0,
                    'max_radius': random.randint(20, 40),
                    'life': random.uniform(1, 2)
                }
                self.flood_ripples.append(ripple)
        
        for ripple in self.flood_ripples[:]:
            ripple['radius'] += 30 * dt
            ripple['life'] -= dt
            if ripple['life'] <= 0 or ripple['radius'] > ripple['max_radius']:
                self.flood_ripples.remove(ripple)
        
        flood_y = SCREEN_HEIGHT - self.flood_level
        for element in self.village_elements:
            if not element['dismantled']:
                element_bottom = element['y'] + element['height']
                if element_bottom > flood_y and element not in self.submerged_elements:
                    self.submerged_elements.append(element)
    
    def draw_flood_animation(self):
        """Draw enhanced flood with visual effects"""
        if self.flood_level <= 0:
            return
        
        flood_y = SCREEN_HEIGHT - self.flood_level
        
        for y in range(int(flood_y), SCREEN_HEIGHT):
            depth_ratio = (y - flood_y) / self.flood_level if self.flood_level > 0 else 0
            
            base_red = COLORS['flood_red'][0]
            base_green = COLORS['flood_red'][1]
            base_blue = COLORS['flood_red'][2]
            
            red = max(0, int(base_red * (1 - depth_ratio * 0.3)))
            green = max(0, int(base_green * (1 - depth_ratio * 0.3)))
            blue = max(0, int(base_blue * (1 - depth_ratio * 0.3)))
            
            import math
            wave_offset = int(math.sin(self.flood_wave_timer + y * 0.1) * 3)
            
            water_rect = pygame.Rect(0, y, SCREEN_WIDTH + wave_offset, 1)
            pygame.draw.rect(self.screen, (red, green, blue), water_rect)
        
        self.draw_water_surface(flood_y)
        
        for bubble in self.flood_bubbles:
            if bubble['y'] >= flood_y:  
                bubble_alpha = min(255, int(bubble['life'] * 128))
                bubble_color = (*COLORS['village_beige'][:3], bubble_alpha)
                
                bubble_surface = pygame.Surface((bubble['size'] * 2, bubble['size'] * 2))
                bubble_surface.set_alpha(bubble_alpha)
                pygame.draw.circle(bubble_surface, COLORS['village_beige'], 
                                 (bubble['size'], bubble['size']), bubble['size'])
                self.screen.blit(bubble_surface, (bubble['x'] - bubble['size'], bubble['y'] - bubble['size']))
        
        for ripple in self.flood_ripples:
            ripple_alpha = max(0, int(ripple['life'] * 128))
            if ripple_alpha > 0:
                ripple_surface = pygame.Surface((ripple['radius'] * 2, ripple['radius'] * 2))
                ripple_surface.set_alpha(ripple_alpha)
                pygame.draw.circle(ripple_surface, COLORS['white'], 
                                 (int(ripple['radius']), int(ripple['radius'])), int(ripple['radius']), 2)
                self.screen.blit(ripple_surface, (ripple['x'] - ripple['radius'], ripple['y'] - ripple['radius']))
        
        self.draw_submersion_effects(flood_y)
    
    def draw_water_surface(self, flood_y):
        """Draw animated water surface"""
        import math
        
        surface_points = []
        for x in range(0, SCREEN_WIDTH, 4):
            wave_height = math.sin(self.flood_wave_timer + x * 0.05) * 2
            surface_points.append((x, flood_y + wave_height))
        
        surface_points.append((SCREEN_WIDTH, flood_y))
        surface_points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        surface_points.append((0, SCREEN_HEIGHT))
        
        if len(surface_points) > 3:
            highlight_color = (min(255, COLORS['flood_red'][0] + 30), 
                             min(255, COLORS['flood_red'][1] + 30),
                             min(255, COLORS['flood_red'][2] + 30))
            
            surface = pygame.Surface((SCREEN_WIDTH, 4))
            surface.set_alpha(128)
            surface.fill(highlight_color)
            self.screen.blit(surface, (0, flood_y - 2))
    
    def draw_submersion_effects(self, flood_y):
        """Draw effects for submerged village elements"""
        for element in self.submerged_elements:
            if element['dismantled']:
                continue
            
            element_bottom = element['y'] + element['height']
            if element_bottom > flood_y:
                submersion_depth = element_bottom - flood_y
                submersion_ratio = min(1.0, submersion_depth / element['height'])
                
                overlay_height = int(submersion_ratio * element['height'])
                overlay_rect = pygame.Rect(element['x'], 
                                         element['y'] + element['height'] - overlay_height,
                                         element['width'], overlay_height)
                
                water_overlay = pygame.Surface((element['width'], overlay_height))
                water_overlay.set_alpha(64)
                water_overlay.fill(COLORS['flood_red'])
                self.screen.blit(water_overlay, (overlay_rect.x, overlay_rect.y))
    
    def apply_moral_consequences(self, choice):
        """Apply consequences for moral choices"""
        moral_impact = choice['moral_impact']
        category = choice['category']
        
        self.moral_standing += moral_impact
        self.moral_standing = max(0, min(200, self.moral_standing))  
        
        if category == 'severe':
            if choice['villagers_affected'] > 0:
                message_text = f"Displaced {choice['villagers_affected']} villagers!"
                color = 'flood_red'
            else:
                message_text = "Destroyed vital infrastructure!"
                color = 'flood_red'
        elif category == 'major':
            message_text = "Damaged community resource!"
            color = 'flood_red'
        elif category == 'moderate':
            message_text = "Removed village structure"
            color = 'earth_brown'
        elif category == 'minor':
            message_text = "Gathered natural resources"
            color = 'forest_green'
        else:  
            message_text = "Minor change to village"
            color = 'dark_grey'
        
        consequence_msg = {
            'text': message_text,
            'color': color,
            'timestamp': pygame.time.get_ticks(),
            'moral_change': moral_impact
        }
        self.consequence_messages.append(consequence_msg)
        
        if len(self.consequence_messages) > 3:
            self.consequence_messages.pop(0)
    
    def get_moral_standing_description(self):
        """Get description of current moral standing"""
        if self.moral_standing >= 150:
            return ("Saint", "village_beige")
        elif self.moral_standing >= 120:
            return ("Virtuous", "forest_green")
        elif self.moral_standing >= 80:
            return ("Balanced", "bridge_blue")
        elif self.moral_standing >= 50:
            return ("Pragmatic", "earth_brown")
        elif self.moral_standing >= 20:
            return ("Ruthless", "flood_red")
        else:
            return ("Destroyer", "black")
    
    def get_ending_moral_category(self):
        """Determine moral category for ending calculation"""
        if self.moral_standing >= 120:
            return "virtuous"
        elif self.moral_standing >= 80:
            return "balanced"
        elif self.moral_standing >= 50:
            return "pragmatic"
        else:
            return "ruthless"
    
    def draw_moral_feedback(self):
        """Draw recent moral consequence messages"""
        if not self.consequence_messages:
            return
        
        message_x = SCREEN_WIDTH - 300
        message_y = 150
        
        for i, msg in enumerate(self.consequence_messages):
            age = pygame.time.get_ticks() - msg['timestamp']
            alpha = max(0, 255 - int((age / 3000) * 255))  
            
            if alpha > 0:
                msg_bg = pygame.Rect(message_x - 5, message_y + i * 25, 290, 20)
                bg_surface = pygame.Surface((290, 20))
                bg_surface.set_alpha(min(alpha, 128))
                bg_surface.fill(COLORS['village_beige'])
                self.screen.blit(bg_surface, (message_x - 5, message_y + i * 25))
                
                text_surface = self.font_small.render(msg['text'], True, COLORS[msg['color']])
                text_surface.set_alpha(alpha)
                self.screen.blit(text_surface, (message_x, message_y + i * 25 + 2))
                
                if msg['moral_change'] != 0:
                    change_text = f"({msg['moral_change']:+d})"
                    change_color = 'forest_green' if msg['moral_change'] > 0 else 'flood_red'
                    change_surface = self.font_small.render(change_text, True, COLORS[change_color])
                    change_surface.set_alpha(alpha)
                    self.screen.blit(change_surface, (message_x + 200, message_y + i * 25 + 2))
    
    def apply_event_effect(self, effect_type, params):
        """Apply the effect of a random event"""
        if effect_type == 'resource_bonus':
            for resource, amount in params.items():
                self.resources[resource] += amount
            message = f"Event: Gained {', '.join([f'+{v} {k}' for k, v in params.items()])}"
        elif effect_type == 'resource_loss':
            for resource, amount in params.items():
                self.resources[resource] = max(0, self.resources[resource] - amount)
            message = f"Event: Lost {', '.join([f'{v} {k}' for k, v in params.items()])}"
        elif effect_type == 'time_penalty':
            self.flood_timer = max(5, self.flood_timer - params)
            message = f"Event: Flood accelerated by {params} seconds!"
        elif effect_type == 'moral_bonus':
            self.moral_standing = min(200, self.moral_standing + params)
            message = f"Event: Moral standing +{params}"

        event_msg = {
            'text': message,
            'color': 'gold',
            'timestamp': pygame.time.get_ticks()
        }
        self.event_messages.append(event_msg)
        if len(self.event_messages) > 3:
            self.event_messages.pop(0)

    def trigger_random_event(self):
        """Trigger a random event"""
        if not self.possible_events:
            return

        event = random.choice(self.possible_events)
        self.current_event = event
        self.event_duration = event['duration']

        # Apply the effect immediately
        event['effect'](self)

        self.play_sound('event')

        # Add notification
        event_msg = {
            'text': f"Event: {event['name']} - {event['description']}",
            'color': event['color'],
            'timestamp': pygame.time.get_ticks()
        }
        self.event_messages.append(event_msg)
        if len(self.event_messages) > 3:
            self.event_messages.pop(0)

    def apply_moral_ending_consequences(self):
        """Apply moral consequences to the ending outcomes"""
        moral_category = self.get_ending_moral_category()

        if moral_category == "virtuous":
            if self.villagers_saved > 0:
                bonus_saved = min(3, self.total_villagers_displaced // 2)
                self.villagers_saved += bonus_saved
                self.villagers_saved = min(self.villagers_saved, self.initial_villagers)

        elif moral_category == "balanced":
            pass

        elif moral_category == "pragmatic":
            if self.villagers_saved > 0:
                efficiency_loss = max(1, self.villagers_saved // 10)
                self.villagers_saved -= efficiency_loss
                self.villagers_saved = max(0, self.villagers_saved)

        elif moral_category == "ruthless":
            if self.villagers_saved > 0:
                cooperation_loss = max(2, self.villagers_saved // 4)
                self.villagers_saved -= cooperation_loss
                self.villagers_saved = max(0, self.villagers_saved)

            if self.total_villagers_displaced > 5:
                moral_refusal = min(3, self.total_villagers_displaced // 3)
                self.villagers_saved -= moral_refusal
                self.villagers_saved = max(0, self.villagers_saved)

        self.ending_moral_category = moral_category

        self.final_moral_score = self.moral_standing
    
    def draw_placed_objects(self):
        """Draw logs and stones placed by the character"""
        for obj in self.placed_objects:
            x, y = int(obj['x']), int(obj['y'])
            
            if obj['type'] == 'log':
                log_sprite = [
                    ['earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                    ['earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown'],
                    ['earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown'],
                    ['earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                    ['earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown'],
                    ['earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_light', 'earth_brown'],
                    ['earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                    ['dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey']
                ]
                self.draw_pixel_art_sprite(x - 16, y - 4, log_sprite, pixel_size=3)
                
            elif obj['type'] == 'stone':
                stone_sprite = [
                    ['', '', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', '', ''],
                    ['', 'dark_grey', 'light_grey', 'light_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'light_grey', 'light_grey', 'dark_grey', ''],
                    ['dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey', 'dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey'],
                    ['dark_grey', 'light_grey', 'white', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'white', 'light_grey', 'dark_grey'],
                    ['dark_grey', 'dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey', 'dark_grey'],
                    ['dark_grey', 'dark_grey', 'dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey', 'dark_grey', 'dark_grey'],
                    ['dark_grey', 'dark_grey', 'dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey', 'dark_grey', 'dark_grey'],
                    ['dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey'],
                    ['dark_grey', 'light_grey', 'white', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'white', 'light_grey', 'dark_grey'],
                    ['dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey', 'dark_grey', 'light_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey'],
                    ['', 'dark_grey', 'light_grey', 'light_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'light_grey', 'light_grey', 'dark_grey', ''],
                    ['', '', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', 'dark_grey', '', '']
                ]
                self.draw_pixel_art_sprite(x - 12, y - 6, stone_sprite, pixel_size=3)
    
    def draw_character(self):
        """Draw the animated character sprite with enhanced animations"""
        char = self.character
        x, y = int(char['x']), int(char['y'])

        frame = char['animation_frame'] % 6

        # Bigger stickman with hammer (21x27 grid)
        character_sprite = [
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', 'black', 'black', 'black', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', 'black', '', 'black', '', 'black', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', 'black', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', 'black', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', 'black', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', 'black', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', 'black', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', 'black', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', 'black', '', '', '', '', '', '', '', '', '', ''],
        ]
        # Hammer in right hand (gray and brown)
        # Add hammer head (gray)
        character_sprite[8][16] = 'light_grey'
        character_sprite[8][17] = 'light_grey'
        character_sprite[9][17] = 'light_grey'
        # Add hammer handle (brown)
        character_sprite[10][17] = 'earth_brown'
        character_sprite[11][17] = 'earth_brown'
        character_sprite[12][17] = 'earth_brown'
        character_sprite[13][17] = 'earth_brown'
        character_sprite[14][17] = 'earth_brown'
        character_sprite[15][17] = 'earth_brown'
        character_sprite[16][17] = 'earth_brown'
        character_sprite[17][17] = 'earth_brown'
        character_sprite[18][17] = 'earth_brown'
        character_sprite[19][17] = 'earth_brown'
        character_sprite[20][17] = 'earth_brown'
        
        self.draw_pixel_art_sprite(x - 16, y - 20, character_sprite, pixel_size=3)
        
        if char['carrying']:
            carry_y = y - 30
            if char['carrying'] == 'log':
                carry_sprite = [
                    ['earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown'],
                    ['earth_light', 'earth_brown', 'earth_brown', 'earth_light', 'earth_brown', 'earth_brown'],
                    ['earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown', 'earth_brown']
                ]
                self.draw_pixel_art_sprite(x - 6, carry_y, carry_sprite, pixel_size=3)
            elif char['carrying'] == 'stone':
                carry_sprite = [
                    ['', 'dark_grey', 'dark_grey', 'dark_grey', ''],
                    ['dark_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey'],
                    ['dark_grey', 'light_grey', 'white', 'light_grey', 'dark_grey'],
                    ['dark_grey', 'light_grey', 'light_grey', 'light_grey', 'dark_grey'],
                    ['', 'dark_grey', 'dark_grey', 'dark_grey', '']
                ]
                self.draw_pixel_art_sprite(x - 5, carry_y, carry_sprite, pixel_size=3)
    
    def draw_particles(self):
        """Draw all particle systems with enhanced effects"""
        for particle in self.destruction_particles:
            size = max(1, int(particle['life'] * 4))
            alpha = int(min(255, particle['life'] * 255))

            glow_size = size * 3
            glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)

            for radius in range(glow_size, 0, -1):
                glow_alpha = int(alpha * (radius / glow_size) * 0.3)
                pygame.draw.circle(glow_surface, (*particle['color'][:3], glow_alpha),
                                 (glow_size, glow_size), radius)

            pygame.draw.circle(glow_surface, (*particle['color'][:3], alpha),
                             (glow_size, glow_size), size)

            self.screen.blit(glow_surface, (int(particle['x'] - glow_size), int(particle['y'] - glow_size)))

        for particle in self.placement_particles:
            size = max(1, int(particle['life'] * 5))
            alpha = int(min(255, particle['life'] * 255))

            sparkle_surface = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)

            color = (*particle['color'][:3], alpha)
            center = size * 2

            pygame.draw.line(sparkle_surface, color, (0, center), (size * 4, center), max(1, size//2))
            pygame.draw.line(sparkle_surface, color, (center, 0), (center, size * 4), max(1, size//2))
            pygame.draw.line(sparkle_surface, color, (size, size), (size * 3, size * 3), max(1, size//3))
            pygame.draw.line(sparkle_surface, color, (size * 3, size), (size, size * 3), max(1, size//3))

            self.screen.blit(sparkle_surface, (int(particle['x'] - size * 2), int(particle['y'] - size * 2)))

        for particle in self.ui_particles:
            size = max(1, int(particle['life'] * 4))
            alpha = int(min(255, particle['life'] * 255))

            bloom_surface = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)

            for i in range(3):
                bloom_alpha = int(alpha * (0.8 - i * 0.2))
                bloom_color = (*particle['color'][:3], bloom_alpha)
                pygame.draw.circle(bloom_surface, bloom_color, (size * 1.5, size * 1.5), size + i * 2)

            self.screen.blit(bloom_surface, (int(particle['x'] - size * 1.5), int(particle['y'] - size * 1.5)))
    
    def draw_interaction_indicator(self):
        """Draw interaction range around character"""
        char = self.character
        if not char['moving'] and char['action_cooldown'] <= 0:
            center = (int(char['x']), int(char['y']))
            radius = 40
            
            pulse = (pygame.time.get_ticks() / 1000.0) % 2.0
            alpha = int(30 + 20 * pulse)
            
            circle_surface = pygame.Surface((radius * 4, radius * 4))
            circle_surface.set_alpha(alpha)
            circle_surface.fill(COLORS['gold'])
            pygame.draw.circle(circle_surface, COLORS['gold'], (radius * 2, radius * 2), radius, 2)
            
            self.screen.blit(circle_surface, (center[0] - radius * 2, center[1] - radius * 2))
    
    def draw_enhanced_ui(self):
        """Draw the enhanced user interface with better organization"""
        resource_rect = (10, 5, 280, 120)
        content_y = self.draw_enhanced_panel(self.screen, resource_rect, "Resources", self.get_color('forest_green'))

        resource_colors = {
            'wood': self.get_color('earth_brown'),
            'stone': self.get_color('dark_grey'),
            'metal': self.get_color('silver')
        }
        
        for i, (resource, amount) in enumerate(self.resources.items()):
            y_pos = content_y + i * 22
            
            icon_rect = pygame.Rect(20, y_pos + 2, 16, 16)
            glow_rect = pygame.Rect(18, y_pos, 20, 20)
            glow_surface = pygame.Surface((20, 20))
            glow_surface.set_alpha(40)
            glow_surface.fill(resource_colors[resource])
            self.screen.blit(glow_surface, glow_rect)
            
            pygame.draw.rect(self.screen, resource_colors[resource], icon_rect)
            pygame.draw.rect(self.screen, COLORS['black'], icon_rect, 1)
            
            text = self.get_font('body_small').render(f"{resource.title()}: {amount}", True, self.get_color('black'))
            self.screen.blit(text, (45, y_pos + 2))
            
            required = 3 if resource == 'wood' else 2 if resource == 'stone' else 1
            segments = amount // required
            
            bar_x, bar_y = 180, y_pos + 5
            bar_width, bar_height = 80, 8
            
            bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(self.screen, COLORS['dark_grey'], bg_rect)
            
            if segments > 0:
                fill_width = min(segments, 20) * (bar_width // 20)
                fill_rect = (bar_x, bar_y, fill_width, bar_height)
                self.draw_gradient_rect(self.screen, resource_colors[resource], 
                                      tuple(max(0, c - 30) for c in resource_colors[resource]), fill_rect)
            
            pygame.draw.rect(self.screen, COLORS['black'], bg_rect, 1)
        
        bridge_rect = (300, 5, 250, 120)
        bridge_y = self.draw_enhanced_panel(self.screen, bridge_rect, "Bridge Progress", self.get_color('bridge_blue'))

        segments_completed = len(self.bridge_segments)
        progress_percent = int((segments_completed / self.total_segments) * 100)

        progress_text = self.get_font('body_large').render(f"{progress_percent}%", True, self.get_color('bridge_blue'))
        self.screen.blit(progress_text, (315, bridge_y + 5))

        segment_text = self.get_font('body_small').render(f"{segments_completed}/{self.total_segments} Segments", True, self.get_color('black'))
        self.screen.blit(segment_text, (315, bridge_y + 30))
        
        bar_rect = (315, bridge_y + 50, 220, 16)
        pygame.draw.rect(self.screen, COLORS['dark_grey'], bar_rect)
        
        if segments_completed > 0:
            fill_width = (segments_completed / self.total_segments) * 216
            fill_rect = (317, bridge_y + 52, fill_width, 12)
            self.draw_gradient_rect(self.screen, COLORS['bridge_light'], COLORS['bridge_blue'], fill_rect)
        
        pygame.draw.rect(self.screen, COLORS['black'], bar_rect, 2)
        
        if segments_completed < self.total_segments:
            req_text = self.font_small.render("Next: 3 Wood, 2 Stone, 1 Metal", True, COLORS['dark_grey'])
            self.screen.blit(req_text, (315, bridge_y + 75))
        
        time_rect = (560, 5, 180, 120)
        time_y = self.draw_enhanced_panel(self.screen, time_rect, "Game Status", self.get_color('flood_red'))

        minutes = int(self.flood_timer // 60)
        seconds = int(self.flood_timer % 60)

        if self.flood_timer < 60:
            pulse = (pygame.time.get_ticks() / 200) % 2
            timer_color = self.get_color('flood_red') if pulse < 1 else self.get_color('flood_dark')
        else:
            timer_color = self.get_color('black')

        timer_text = self.get_font('body').render(f"{minutes:02d}:{seconds:02d}", True, timer_color)
        self.screen.blit(timer_text, (575, time_y + 5))

        # Time of day indicator
        if 0.2 <= self.time_of_day <= 0.8:
            time_desc = "Day"
            time_color = self.get_color('gold')
        elif self.time_of_day < 0.2 or self.time_of_day > 0.8:
            time_desc = "Night"
            time_color = self.get_color('dark_grey')
        else:
            time_desc = "Twilight"
            time_color = self.get_color('bridge_blue')

        time_text = self.get_font('body_small').render(f"Time: {time_desc}", True, time_color)
        self.screen.blit(time_text, (575, time_y + 25))

        villager_color = self.get_color('forest_green') if self.current_villagers == self.initial_villagers else self.get_color('flood_red')
        villager_text = self.get_font('body_small').render(f"Villagers: {self.current_villagers}/{self.initial_villagers}", True, villager_color)
        self.screen.blit(villager_text, (575, time_y + 45))

        if self.total_villagers_displaced > 0:
            displaced_text = self.get_font('body_small').render(f"Displaced: {self.total_villagers_displaced}", True, self.get_color('flood_red'))
            self.screen.blit(displaced_text, (575, time_y + 65))

        standing_desc, standing_color = self.get_moral_standing_description()
        standing_text = self.get_font('body_small').render(f"Moral: {standing_desc}", True, self.get_color(standing_color))
        self.screen.blit(standing_text, (575, time_y + 85))
        

    def draw_ui(self):
        """Draw the user interface"""
        y_pos = 10
        
        resource_panel = pygame.Rect(10, 5, 220, 120)
        pygame.draw.rect(self.screen, COLORS['village_beige'], resource_panel)
        pygame.draw.rect(self.screen, COLORS['black'], resource_panel, 2)
        
        title_text = self.font_medium.render("Resources", True, COLORS['forest_green'])
        self.screen.blit(title_text, (15, 10))
        y_pos = 35
        
        resource_colors = {
            'wood': COLORS['earth_brown'],
            'stone': COLORS['dark_grey'], 
            'metal': COLORS['bridge_blue']
        }
        
        for resource, amount in self.resources.items():
            icon_rect = pygame.Rect(20, y_pos + 2, 12, 12)
            pygame.draw.rect(self.screen, resource_colors[resource], icon_rect)
            pygame.draw.rect(self.screen, COLORS['black'], icon_rect, 1)
            
            text = self.font_small.render(f"{resource.title()}: {amount}", True, COLORS['black'])
            self.screen.blit(text, (40, y_pos))
            
            if resource == 'wood':
                required = 3
            elif resource == 'stone':
                required = 2
            else:  
                required = 1
            
            segments = amount // required
            bar_width = 60
            bar_height = 8
            bar_x = 150
            bar_y = y_pos + 4
            
            bar_bg = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(self.screen, COLORS['dark_grey'], bar_bg)
            
            fill_width = min(segments, 20) * (bar_width // 20)
            if fill_width > 0:
                fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
                pygame.draw.rect(self.screen, resource_colors[resource], fill_rect)
            
            pygame.draw.rect(self.screen, COLORS['black'], bar_bg, 1)
            
            y_pos += 22
        
        minutes = int(self.flood_timer // 60)
        seconds = int(self.flood_timer % 60)
        timer_color = COLORS['flood_red'] if self.flood_timer < 60 else COLORS['black']
        timer_text = self.font_medium.render(f"Time: {minutes:02d}:{seconds:02d}", True, timer_color)
        self.screen.blit(timer_text, (20, 130))
        
        bridge_panel = pygame.Rect(250, 5, 200, 80)
        pygame.draw.rect(self.screen, COLORS['village_beige'], bridge_panel)
        pygame.draw.rect(self.screen, COLORS['black'], bridge_panel, 2)
        
        bridge_title = self.font_medium.render("Bridge Progress", True, COLORS['bridge_blue'])
        self.screen.blit(bridge_title, (255, 10))
        
        segments_completed = len(self.bridge_segments)
        segment_text = self.font_small.render(f"Segments: {segments_completed}/{self.total_segments}", True, COLORS['black'])
        self.screen.blit(segment_text, (255, 30))
        
        bar_width = 180
        bar_height = 12
        bar_x = 260
        bar_y = 50
        
        bar_bg = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, COLORS['dark_grey'], bar_bg)
        
        if segments_completed > 0:
            fill_width = (segments_completed / self.total_segments) * bar_width
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(self.screen, COLORS['bridge_blue'], fill_rect)
        
        pygame.draw.rect(self.screen, COLORS['black'], bar_bg, 1)
        
        if segments_completed < self.total_segments:
            cost_text = self.font_small.render("Next: 3 Wood, 2 Stone, 1 Metal", True, COLORS['dark_grey'])
            self.screen.blit(cost_text, (255, 67))
        
        villager_color = COLORS['forest_green'] if self.current_villagers == self.initial_villagers else COLORS['flood_red']
        villager_text = self.font_small.render(f"Villagers: {self.current_villagers}/{self.initial_villagers}", True, villager_color)
        self.screen.blit(villager_text, (20, 165))
        
        if self.total_villagers_displaced > 0:
            displaced_text = self.font_small.render(f"Displaced: {self.total_villagers_displaced}", True, COLORS['flood_red'])
            self.screen.blit(displaced_text, (20, 185))
        
        moral_panel = pygame.Rect(470, 5, 180, 120)
        pygame.draw.rect(self.screen, COLORS['village_beige'], moral_panel)
        pygame.draw.rect(self.screen, COLORS['black'], moral_panel, 2)
        
        moral_title = self.font_medium.render("Moral Standing", True, COLORS['black'])
        self.screen.blit(moral_title, (475, 10))
        
        standing_desc, standing_color = self.get_moral_standing_description()
        standing_text = self.font_small.render(f"Status: {standing_desc}", True, COLORS[standing_color])
        self.screen.blit(standing_text, (475, 30))
        
        value_text = self.font_small.render(f"Score: {self.moral_standing}/200", True, COLORS['black'])
        self.screen.blit(value_text, (475, 45))
        
        bar_bg = pygame.Rect(475, 60, 170, 10)
        pygame.draw.rect(self.screen, COLORS['dark_grey'], bar_bg)
        
        fill_width = (self.moral_standing / 200) * 170
        if fill_width > 0:
            fill_color = COLORS[standing_color]
            fill_rect = pygame.Rect(475, 60, fill_width, 10)
            pygame.draw.rect(self.screen, fill_color, fill_rect)
        
        pygame.draw.rect(self.screen, COLORS['black'], bar_bg, 1)
        
        choices_text = self.font_small.render(f"Choices: {len(self.moral_choices)}", True, COLORS['dark_grey'])
        self.screen.blit(choices_text, (475, 75))
        
        severe_choices = sum(1 for choice in self.moral_choices if choice.get('category') == 'severe')
        if severe_choices > 0:
            severe_text = self.font_small.render(f"Severe: {severe_choices}", True, COLORS['flood_red'])
            self.screen.blit(severe_text, (475, 90))
        
        self.draw_moral_feedback()

        # Draw event messages
        if self.event_messages:
            event_y = 200
            events_text = self.font_small.render("Recent Events:", True, COLORS['dark_grey'])
            self.screen.blit(events_text, (20, event_y))
            event_y += 20

            for msg in self.event_messages[-3:]:
                event_text = self.font_small.render(msg['text'], True, COLORS[msg['color']])
                self.screen.blit(event_text, (25, event_y))
                event_y += 15

        if self.moral_choices:
            choice_y = event_y + 10 if self.event_messages else 200
            choices_text = self.font_small.render("Recent Choices:", True, COLORS['dark_grey'])
            self.screen.blit(choices_text, (20, choice_y))
            choice_y += 20

            for choice in self.moral_choices[-3:]:
                if choice['villagers_affected'] > 0:
                    text = f"Dismantled {choice['type']} (-{choice['villagers_affected']} villagers)"
                    color = COLORS['flood_red']
                else:
                    text = f"Dismantled {choice['type']}"
                    color = COLORS['earth_brown']

                choice_text = self.font_small.render(text, True, color)
                self.screen.blit(choice_text, (25, choice_y))
                choice_y += 15
        
        if self.show_confirmation:
            instruction = self.font_small.render("Moral choice pending - see dialog above", True, COLORS['flood_red'])
        else:
            instruction = self.font_small.render("Click elements to dismantle them", True, COLORS['dark_grey'])
        self.screen.blit(instruction, (20, SCREEN_HEIGHT - 40))
    
    def draw_game_over(self):
        """Draw the enhanced game over screen with achievements"""
        self.screen.fill(COLORS['village_beige'])

        survival_rate = self.villagers_saved / self.initial_villagers if self.initial_villagers > 0 else 0
        total_dismantled = len([c for c in self.moral_choices])

        if survival_rate >= 0.8:
            ending = "Hero's Bridge"
            message = "You saved most of the village!"
            color = COLORS['bridge_blue']
        elif survival_rate >= 0.5:
            ending = "Difficult Choices"
            message = "Half the village survived your decisions."
            color = COLORS['earth_brown']
        elif survival_rate >= 0.2:
            ending = "Heavy Sacrifice"
            message = "Few survived, but some is better than none."
            color = COLORS['flood_red']
        else:
            ending = "The Flood Wins"
            message = "The village was lost to the waters."
            color = COLORS['dark_grey']

        title = self.font_large.render(ending, True, color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 120))
        self.screen.blit(title, title_rect)

        msg = self.font_medium.render(message, True, COLORS['black'])
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH//2, 160))
        self.screen.blit(msg, msg_rect)

        # Detailed statistics
        stats = [
            f"Elements Dismantled: {total_dismantled}",
            f"Bridge Completion: {int((self.bridge_progress/self.bridge_required)*100)}%",
            f"Final Moral Standing: {self.moral_standing}/200 ({self.get_moral_standing_description()[0]})",
            f"Total Resources Gathered: {sum(self.resources.values())}",
            f"Villagers Displaced: {self.total_villagers_displaced}",
            f"Random Events Experienced: {len([msg for msg in self.event_messages if 'Event:' in msg['text']])}"
        ]

        y_start = 220
        for i, stat in enumerate(stats):
            text = self.font_small.render(stat, True, COLORS['dark_grey'])
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_start + i * 25))
            self.screen.blit(text, text_rect)

        # Achievements
        if self.achievements:
            achievement_title = self.font_medium.render("Achievements Unlocked:", True, COLORS['gold'])
            achievement_rect = achievement_title.get_rect(center=(SCREEN_WIDTH//2, y_start + len(stats) * 25 + 40))
            self.screen.blit(achievement_title, achievement_rect)
            for i, ach_key in enumerate(self.achievements):
                ach = self.possible_achievements[ach_key]
                ach_text = self.font_small.render(f"• {ach['name']}: {ach['description']}", True, COLORS['gold'])
                ach_rect = ach_text.get_rect(center=(SCREEN_WIDTH//2, y_start + len(stats) * 25 + 60 + i * 20))
                self.screen.blit(ach_text, ach_rect)

        restart_y = y_start + len(stats) * 25 + 60 + (len(self.achievements) if self.achievements else 0) * 20 + 40
        restart = self.get_font('body_small').render("Press SPACE to play again or ESC to quit", True, self.get_color('forest_green'))
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH//2, restart_y))
        self.screen.blit(restart, restart_rect)

    def draw_settings(self):
        """Draw the settings menu"""
        self.screen.fill(self.get_color('village_beige'))

        title = self.get_font('title').render("Settings", True, self.get_color('forest_green'))
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)

        settings = [
            ("High Contrast Mode", self.accessibility['high_contrast'], "F11"),
            ("Large Text", self.accessibility['large_text'], "F10"),
            ("Keyboard Navigation", self.accessibility['keyboard_navigation'], "Tab"),
            ("Reduced Motion", self.accessibility.get('reduced_motion', False), "N/A")
        ]

        y_start = 200
        for i, (setting_name, enabled, key) in enumerate(settings):
            panel_rect = (200, y_start + i * 80, 600, 60)
            self.draw_enhanced_panel(self.screen, panel_rect, "", self.get_color('bridge_blue'))

            name_text = self.get_font('body').render(setting_name, True, self.get_color('black'))
            self.screen.blit(name_text, (220, y_start + i * 80 + 10))

            status_text = "ON" if enabled else "OFF"
            status_color = self.get_color('forest_green') if enabled else self.get_color('flood_red')
            status_surface = self.get_font('body').render(status_text, True, status_color)
            self.screen.blit(status_surface, (700, y_start + i * 80 + 10))

            if key != "N/A":
                key_text = self.get_font('caption').render(f"Shortcut: {key}", True, self.get_color('dark_grey'))
                self.screen.blit(key_text, (220, y_start + i * 80 + 35))

        instructions = [
            "Use F11/F10 to toggle settings",
            "Press ESC to return to menu"
        ]

        for i, instruction in enumerate(instructions):
            text = self.get_font('body_small').render(instruction, True, self.get_color('dark_grey'))
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, 600 + i * 30))
            self.screen.blit(text, text_rect)

    def draw_tutorial(self):
        """Draw the tutorial/help screen"""
        self.screen.fill(self.get_color('village_beige'))

        title = self.get_font('title').render("How to Play", True, self.get_color('forest_green'))
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title, title_rect)

        tutorial_sections = [
            ("Objective", [
                "You are the Bridge Keeper! Your mission is to save the village",
                "from an impending flood by building a bridge to higher ground.",
                "Gather resources by dismantling village structures, but be mindful",
                "of the moral consequences of your choices."
            ]),
            ("Controls", [
                "WASD or Arrow Keys: Move your character around the village",
                "Left Click: Move character to clicked position",
                "Right Click: Interact with village elements directly",
                "E Key: Interact with nearby objects (dismantle/pickup/place)",
                "ESC: Pause game or return to menu",
                "F11: Toggle high contrast mode",
                "F10: Toggle large text mode"
            ]),
            ("Gameplay", [
                "• Village elements (houses, trees, wells, etc.) provide resources",
                "• Dismantling houses displaces villagers and affects your moral standing",
                "• Use wood, stone, and metal to automatically build bridge segments",
                "• Random events can help or hinder your progress",
                "• The day/night cycle affects visibility and atmosphere",
                "• Save as many villagers as possible before the flood arrives!"
            ]),
            ("Moral Choices", [
                "Every action has consequences. Houses with villagers require",
                "confirmation before dismantling. Your moral standing affects",
                "the final outcome and determines your legacy as Bridge Keeper."
            ]),
            ("Tips", [
                "• Balance resource gathering with villager welfare",
                "• Use the day/night cycle to your advantage",
                "• Pay attention to random events for opportunities",
                "• Plan your dismantling strategy carefully",
                "• Accessibility options are available for all players"
            ])
        ]

        y_start = 140
        for section_title, lines in tutorial_sections:
            section_header = self.get_font('heading').render(section_title, True, self.get_color('earth_brown'))
            section_rect = section_header.get_rect(center=(SCREEN_WIDTH//2, y_start))
            self.screen.blit(section_header, section_rect)
            y_start += 40

            for line in lines:
                text = self.get_font('body_small').render(line, True, self.get_color('black'))
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_start))
                self.screen.blit(text, text_rect)
                y_start += 20

            y_start += 20

        back_text = self.get_font('body').render("Press ESC to return to menu", True, self.get_color('bridge_blue'))
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
        self.screen.blit(back_text, back_rect)
    
    def run(self):
        """Main game loop"""
        # Start background music if available
        if self.background_music:
            pygame.mixer.music.play(-1)  # Loop indefinitely

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  
            
            self.handle_events()
            self.update_game(dt)
            
            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.SETTINGS:
                self.draw_settings()
            elif self.state == GameState.TUTORIAL:
                self.draw_tutorial()
            elif self.state == GameState.PLAYING:
                self.draw_game()
                self.draw_confirmation_dialog()
            elif self.state == GameState.PAUSED:
                self.draw_game()
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.fill(COLORS['black'])
                overlay.set_alpha(128)
                self.screen.blit(overlay, (0, 0))
                
                pause_text = self.font_large.render("PAUSED", True, COLORS['white'])
                pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(pause_text, pause_rect)
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
                
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    self.__init__()  
                elif keys[pygame.K_ESCAPE]:
                    self.running = False
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = BridgeKeeper()
    game.run()
