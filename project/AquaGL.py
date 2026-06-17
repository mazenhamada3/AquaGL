import pygame
from pygame.locals import DOUBLEBUF, OPENGL, RESIZABLE, VIDEORESIZE, QUIT, K_a, K_d, K_w, K_s
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import math
import time

# ---------- constants / initial state ----------
fish_x = fish_y = 0.0
fish_speed = 0.15
fish_direction = -1
fish_scale = 0.6

FISH_HALF_WIDTH = 1.9
FISH_HALF_HEIGHT = 1.0
COLLISION_HALF_WIDTH = 1.0
COLLISION_HALF_HEIGHT = 0.4

WORLD_LIMIT_X = 10.0
WORLD_LIMIT_Y = 6.0

enemies = []
MAX_ENEMIES = 10
SPAWN_CHANCE = 0.03

background_texture = None
font_large = font_medium = font_small = None
background_music = eat_sound = win_sound = lose_sound = None

game_started = game_over = game_won = False
game_end_time = None
score = 0

WIN_SIZE = 1.7
GAME_END_DELAY = 5.0

# ---------- helpers ----------
def init_fonts():
    global font_large, font_medium, font_small
    if font_large is None:
        font_large = pygame.font.Font(None, 100)
        font_medium = pygame.font.Font(None, 60)
        font_small = pygame.font.Font(None, 45)

def draw_quad(x1, y1, x2, y2, z):
    glBegin(GL_QUADS)
    glVertex3f(x1, y1, z)
    glVertex3f(x2, y1, z)
    glVertex3f(x2, y2, z)
    glVertex3f(x1, y2, z)
    glEnd()

def draw_overlay(r, g, b, a):
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(r, g, b, a)
    draw_quad(-WORLD_LIMIT_X, -WORLD_LIMIT_Y, WORLD_LIMIT_X, WORLD_LIMIT_Y, 1.0)
    glDisable(GL_BLEND)

def disable_3d():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

def enable_3d():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def load_sound(path, volume=0.7):
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        return s
    except:
        return None

def draw_score():
    init_fonts()
    if not font_small: return
    
    score_text = f"SCORE: {score}"
    text_surface = font_small.render(score_text, True, (255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    width, height = text_surface.get_width(), text_surface.get_height()
    
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    
    disable_3d()
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor4f(1.0, 1.0, 1.0, 1.0)
    
    screen_x, screen_y = -WORLD_LIMIT_X + 2.0, WORLD_LIMIT_Y - 1.0
    w, h = width / 70.0, height / 70.0
    
    glPushMatrix()
    glTranslatef(screen_x, screen_y, 2.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1); glVertex3f(0, 0, 0)
    glTexCoord2f(1, 1); glVertex3f(w, 0, 0)
    glTexCoord2f(1, 0); glVertex3f(w, -h, 0)
    glTexCoord2f(0, 0); glVertex3f(0, -h, 0)
    glEnd()
    glPopMatrix()
    
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)
    enable_3d()
    glDeleteTextures([texture_id])

# ---------- resources ----------
def load_background_texture(image_path):
    global background_texture
    try:
        bg_surface = pygame.image.load(image_path)
        bg_data = pygame.image.tostring(bg_surface, "RGBA", True)
        width, height = bg_surface.get_width(), bg_surface.get_height()
        background_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, background_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, bg_data)
        return True
    except:
        return False

def load_audio():
    global background_music, eat_sound, win_sound, lose_sound
    try:
        pygame.mixer.init()
        for ext in ['.mp3', '.ogg', '.wav']:
            try:
                pygame.mixer.music.load(f"audio/background_music.mp3")
                pygame.mixer.music.set_volume(0.3)
                break
            except:
                continue
        
        eat_sound = load_sound("audio/eat.wav", 0.5)
        win_sound = load_sound("audio/win.wav", 0.7)
        lose_sound = load_sound("audio/lose.wav", 0.7)
    except:
        pass

def draw_background():
    if not background_texture: return
    
    disable_3d()
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, background_texture)
    glColor3f(1.0, 1.0, 1.0)
    
    glPushMatrix()
    glTranslatef(0, 0, -1)
    size_x, size_y = WORLD_LIMIT_X * 1.2, WORLD_LIMIT_Y * 1.2
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex3f(-size_x, -size_y, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex3f(size_x, -size_y, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex3f(size_x, size_y, 0.0)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size_x, size_y, 0.0)
    glEnd()
    glPopMatrix()
    
    glDisable(GL_TEXTURE_2D)
    enable_3d()

# ---------- Simplified UI screens ----------
def draw_ui_screen(title, subtitle, overlay_color, title_color, show_size=True, show_score=True):
    init_fonts()
    draw_overlay(*overlay_color)
    draw_text_textured(title, 0, 1, font_large, title_color, 2.0 if "GAME" in title else 2.5)
    draw_text_textured(subtitle, 0, -0.5, font_medium, (255,255,255), 1.5)
    
    if show_size:
        draw_text_textured(f"Final Size: {round(fish_scale, 2)}", 0, -2, font_small, (200,200,200), 1.2)
    if show_score:
        draw_text_textured(f"Final Score: {score}", 0, -3.5, font_small, (255,255,200), 1.2)

def draw_start_screen():
    init_fonts()
    draw_overlay(0.0, 0.0, 0.0, 0.5)
    draw_text_textured("FEEDING FRENZY", 0, 2, font_large, (255,200,0), 2.0)
    draw_text_textured("Press Any Key to Start", 0, -1, font_medium, (255,255,255), 1.4)
    draw_text_textured("Use WASD to Move", 0, -3, font_small, (200,200,200), 1.0)

def draw_text_textured(text, x, y, font, color, scale=1.0):
    if not font: return
    
    text_surface = font.render(text, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    width, height = text_surface.get_width(), text_surface.get_height()
    
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    
    disable_3d()
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor4f(1.0, 1.0, 1.0, 1.0)
    
    w, h = (width / 100.0) * scale, (height / 100.0) * scale
    glPushMatrix()
    glTranslatef(x, y, 2.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0,0); glVertex3f(-w/2, -h/2, 0)
    glTexCoord2f(1,0); glVertex3f(w/2, -h/2, 0)
    glTexCoord2f(1,1); glVertex3f(w/2, h/2, 0)
    glTexCoord2f(0,1); glVertex3f(-w/2, h/2, 0)
    glEnd()
    glPopMatrix()
    
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)
    enable_3d()
    glDeleteTextures([texture_id])

# ---------- lighting ----------
def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    
    glLightfv(GL_LIGHT0, GL_POSITION, [2.0, 4.0, 2.0, 1.0])
    ambient = [0.3, 0.3, 0.3, 1.0]
    diffuse = [0.8, 0.8, 0.8, 1.0]
    specular = [1.0, 1.0, 1.0, 1.0]
    
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular)
    glMaterialfv(GL_FRONT, GL_SPECULAR, specular)
    glMateriali(GL_FRONT, GL_SHININESS, 64)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

# ---------- fish drawing ----------
def get_enemy_color(scale):
    if scale < 0.6: return (0.3, 1.0, 0.3)
    if scale < 0.9: return (0.2, 0.8, 0.9)
    if scale < 1.2: return (0.1, 0.5, 0.9)
    return (0.8, 0.2, 0.3)

def get_enemy_tail_color(scale):
    if scale < 0.6: return (0.2, 0.8, 0.2)
    if scale < 0.9: return (0.1, 0.6, 0.7)
    if scale < 1.2: return (0.05, 0.3, 0.7)
    return (0.6, 0.1, 0.2)

def get_enemy_fin_color(scale):
    if scale < 0.6: return (0.4, 1.0, 0.4)
    if scale < 0.9: return (0.3, 0.9, 0.9)
    if scale < 1.2: return (0.2, 0.6, 1.0)
    return (1.0, 0.3, 0.4)

def draw_fish(x, y, direction, scale, is_player):
    glPushMatrix()
    glTranslatef(x, y, 0.0)
    glScalef(direction * scale, scale, 1.0)
    glNormal3f(0.0, 0.0, 1.0)

    if not is_player and scale <= fish_scale:
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        pulse = 0.3 + 0.2 * math.sin(time.time() * 5)
        glColor4f(0.0, 1.0, 0.0, pulse)
        
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.0, -0.1)
        for i in range(33):
            angle = 2.0 * math.pi * i / 32
            vx = 1.56 * math.cos(angle)  # 1.2 * 1.3
            vy = 0.91 * math.sin(angle)  # 0.7 * 1.3
            glVertex3f(vx, vy, -0.1)
        glEnd()
        
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    glColor3f(1.0, 0.6, 0.0) if is_player else glColor3f(*get_enemy_color(scale))
    
    # body
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0.0, 0.0, 0.0)
    for i in range(33):
        angle = 2.0 * math.pi * i / 32
        glVertex3f(1.2 * math.cos(angle), 0.7 * math.sin(angle), 0.0)
    glEnd()

    if is_player:
        glColor3f(0.0, 0.0, 0.0)
        for stripe_x in [-0.2, 0.2, 0.6]:
            if abs(stripe_x) < 1.2:
                stripe_height = 0.7 * math.sqrt(1 - (stripe_x / 1.2) ** 2)
                glBegin(GL_QUADS)
                glVertex3f(stripe_x - 0.05, -stripe_height, 0.01)
                glVertex3f(stripe_x + 0.05, -stripe_height, 0.01)
                glVertex3f(stripe_x + 0.05, stripe_height, 0.01)
                glVertex3f(stripe_x - 0.05, stripe_height, 0.01)
                glEnd()

    # tail
    glColor3f(1.0, 0.5, 0.0) if is_player else glColor3f(*get_enemy_tail_color(scale))
    glBegin(GL_TRIANGLES)
    glVertex3f(1.2, 0.0, 0.0)
    glVertex3f(1.9, 0.6, 0.0)
    glVertex3f(1.9, -0.6, 0.0)
    glEnd()

    # dorsal fin
    glColor3f(1.0, 0.7, 0.2) if is_player else glColor3f(*get_enemy_fin_color(scale))
    glBegin(GL_TRIANGLES)
    glVertex3f(-0.2, 0.3, 0.0)
    glVertex3f(0.4, 0.3, 0.0)
    glVertex3f(0.1, 1.0, 0.0)
    glEnd()

    # eye
    if is_player:
        eye_cx, eye_cy = -0.6, 0.2
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(eye_cx, eye_cy, 0.01)
        for i in range(33):
            angle = 2.0 * math.pi * i / 32
            glVertex3f(eye_cx + 0.12 * math.cos(angle), eye_cy + 0.12 * math.sin(angle), 0.01)
        glEnd()
        
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(eye_cx, eye_cy, 0.02)
        for i in range(33):
            angle = 2.0 * math.pi * i / 32
            glVertex3f(eye_cx + 0.05 * math.cos(angle), eye_cy + 0.05 * math.sin(angle), 0.02)
        glEnd()

    glPopMatrix()

# ---------- enemies ----------
def spawn_enemy():
    side = random.choice(["left", "right"])
    scale = random.uniform(0.4, 1.6)
    speed = random.uniform(0.04, 0.12)
    y = random.uniform(-WORLD_LIMIT_Y + 1.5, WORLD_LIMIT_Y - 1.5)
    
    x = -WORLD_LIMIT_X - 3 if side == "left" else WORLD_LIMIT_X + 3
    move_dir = 1 if side == "left" else -1
    
    enemies.append({"x": x, "y": y, "scale": scale, "speed": speed, "move_dir": move_dir})

def update_enemies():
    global enemies
    enemies = [e for e in enemies if -WORLD_LIMIT_X - 5 < e["x"] < WORLD_LIMIT_X + 5]
    for e in enemies:
        e["x"] += e["speed"] * e["move_dir"]

def draw_enemies():
    for e in enemies:
        direction = 1 if e["move_dir"] < 0 else -1
        draw_fish(e["x"], e["y"], direction, e["scale"], False)

# ---------- collisions ----------
def check_player_enemy_collisions():
    global fish_scale, enemies, game_over, game_won, game_end_time, score
    
    new_enemies = []
    p_hw = COLLISION_HALF_WIDTH * fish_scale
    p_hh = COLLISION_HALF_HEIGHT * fish_scale
    
    for e in enemies:
        e_hw = COLLISION_HALF_WIDTH * e["scale"]
        e_hh = COLLISION_HALF_HEIGHT * e["scale"]
        
        if abs(fish_x - e["x"]) < (p_hw + e_hw) and abs(fish_y - e["y"]) < (p_hh + e_hh):
            if e["scale"] <= fish_scale:
                fish_scale += 0.05 * e["scale"]
                score += 100
                if eat_sound: eat_sound.play()
                
                if fish_scale >= WIN_SIZE:
                    game_won = True
                    game_end_time = pygame.time.get_ticks() / 1000.0
                    pygame.mixer.music.stop()
                    if win_sound:
                        pygame.mixer.stop()
                        win_sound.play()
                    return True
                continue
            else:
                game_over = True
                game_end_time = pygame.time.get_ticks() / 1000.0
                pygame.mixer.music.stop()
                if lose_sound:
                    pygame.mixer.stop()
                    lose_sound.play()
                return False
        
        new_enemies.append(e)
    
    enemies = new_enemies
    return True

# ---------- viewport / projection ----------
FOV = 45.0

def apply_projection(width, height):
    """Rebuilds the viewport, projection matrix, and world bounds for the given
    window size. Called once at startup and again on every VIDEORESIZE event."""
    global WORLD_LIMIT_X, WORLD_LIMIT_Y

    aspect = width / height
    glViewport(0, 0, width, height)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV, aspect, 0.1, 50.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -20.0)

    WORLD_LIMIT_X = 20.0 * math.tan(math.radians(FOV / 2.0)) * aspect
    WORLD_LIMIT_Y = 20.0 * math.tan(math.radians(FOV / 2.0))

# ---------- main ----------
def main():
    global fish_x, fish_y, fish_direction, fish_scale, WORLD_LIMIT_X, WORLD_LIMIT_Y
    global game_started, game_over, game_won, game_end_time, score

    pygame.init()

    info = pygame.display.Info()
    display = (int(info.current_w * 0.8), int(info.current_h * 0.8))
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL | RESIZABLE)

    apply_projection(*display)
    setup_lighting()
    load_background_texture("Demo/background.png")
    load_audio()

    running = True
    clock = pygame.time.Clock()

    while running:
        current_time = pygame.time.get_ticks() / 1000.0
        if (game_over or game_won) and game_end_time and current_time - game_end_time >= GAME_END_DELAY:
            break

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                display = (max(event.w, 200), max(event.h, 150))
                pygame.display.set_mode(display, DOUBLEBUF | OPENGL | RESIZABLE)
                apply_projection(*display)
            elif event.type == pygame.KEYDOWN and not game_started and not game_over and not game_won:
                game_started = True
                try: pygame.mixer.music.play(-1)
                except: pass

        if game_started and not game_over and not game_won:
            keys = pygame.key.get_pressed()
            if keys[K_a]: fish_x -= fish_speed; fish_direction = 1
            if keys[K_d]: fish_x += fish_speed; fish_direction = -1
            if keys[K_w]: fish_y += fish_speed
            if keys[K_s]: fish_y -= fish_speed

            max_x = WORLD_LIMIT_X - FISH_HALF_WIDTH * fish_scale
            min_x = -WORLD_LIMIT_X + FISH_HALF_WIDTH * fish_scale
            max_y = WORLD_LIMIT_Y - FISH_HALF_HEIGHT * fish_scale
            min_y = -WORLD_LIMIT_Y + FISH_HALF_HEIGHT * fish_scale
            fish_x = max(min_x, min(max_x, fish_x))
            fish_y = max(min_y, min(max_y, fish_y))

            if len(enemies) < MAX_ENEMIES and random.random() < SPAWN_CHANCE:
                spawn_enemy()

            update_enemies()
            check_player_enemy_collisions()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_background()
        draw_fish(fish_x, fish_y, fish_direction, fish_scale, True)

        if game_started and not game_over and not game_won:
            draw_enemies()
            draw_score()
        elif not game_started:
            draw_start_screen()
        elif game_over:
            draw_enemies()
            draw_ui_screen("GAME OVER", "You were eaten!", (0.5, 0.0, 0.0, 0.6), (255,50,50))
        elif game_won:
            draw_enemies()
            draw_ui_screen("YOU WIN!", "You're the biggest fish!", (0.2, 0.5, 0.0, 0.6), (255,215,0))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()