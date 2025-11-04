import pygame
import sys
import random
import math
import os
import asyncio

# --- 初期設定 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- 色の定義 ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0); RED = (255, 0, 0); DARK_RED = (139, 0, 0)
GREEN = (0, 255, 0); BLUE = (0, 0, 255); GRAY = (128, 128, 128); GOLD = (255, 215, 0)

# --- ゲームの状態 ---
STATE_TITLE = "title"; STATE_PLAYING = "playing"; STATE_RULES = "rules"; STATE_ACHIEVEMENTS = "achievements"
STATE_GAME_OVER = "game_over"; STATE_CLEAR = "clear"

# --- テキスト描画関数 ---
def draw_text(screen, text, font, color, x, y, align="center"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "center": text_rect.center = (x, y)
    elif align == "topleft": text_rect.topleft = (x, y)
    elif align == "topright": text_rect.topright = (x, y)
    screen.blit(text_surface, text_rect)

# --- プレイヤークラス (タッチ操作対応) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 50)); self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.world_x, self.world_y = 0, 0
        self.stamina, self.max_stamina = 100, 100
        self.base_speed, self.height = 5, 0
        
        self.moving_up = False
        self.moving_down = False
        self.moving_left = False
        self.moving_right = False

    def update(self):
        keys = pygame.key.get_pressed()
        
        kb_up = keys[pygame.K_w]
        kb_down = keys[pygame.K_s]
        kb_left = keys[pygame.K_a]
        kb_right = keys[pygame.K_d]

        move_y = 0
        if kb_up or self.moving_up: move_y -= 1
        if kb_down or self.moving_down: move_y += 1
            
        move_x = 0
        if kb_left or self.moving_left: move_x -= 1
        if kb_right or self.moving_right: move_x += 1

        current_speed = self.base_speed * (self.stamina / self.max_stamina)
        if current_speed < self.base_speed / 3: current_speed = self.base_speed / 3
        
        is_moving = (move_x != 0 or move_y != 0)
        
        if is_moving:
            move_mag = math.sqrt(move_x**2 + move_y**2)
            self.world_x += (move_x / move_mag) * current_speed
            self.world_y += (move_y / move_mag) * current_speed
            
            self.stamina -= 0.025
            if self.stamina < 0: self.stamina = 0
        else:
            self.stamina += 0.2
            if self.stamina > self.max_stamina: self.stamina = self.max_stamina

        self.moving_up = False
        self.moving_down = False
        self.moving_left = False
        self.moving_right = False

# --- 津波クラス (変更なし) ---
class Tsunami(pygame.sprite.Sprite):
    def __init__(self, player_base_speed):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT * 2)); self.image.fill(BLUE)
        self.target_height = random.randint(100, 1000)
        self.world_y = SCREEN_HEIGHT / 2
        self.rect = self.image.get_rect(topleft=(0, SCREEN_HEIGHT))
        self.base_speed = player_base_speed / 3; self.speed = self.base_speed
        self.speed_multiplier = 1.3; self.speed_up_interval = 20 * 1000
        self.last_speed_up = pygame.time.get_ticks()

    def update(self, player_world_y):
        now = pygame.time.get_ticks()
        if now - self.last_speed_up > self.speed_up_interval:
            self.speed *= self.speed_multiplier; self.last_speed_up = now
        self.world_y -= self.speed
        self.rect.y = (self.world_y - player_world_y) + (SCREEN_HEIGHT / 2)

    def slow_down(self):
        if self.speed > self.base_speed: self.speed /= self.speed_multiplier

# --- アイテム/障害物クラス (変更なし) ---
class WorldObject(pygame.sprite.Sprite):
    def __init__(self, obj_type, image, size, player_world_pos):
        super().__init__()
        self.type = obj_type
        self.image = pygame.Surface(size, pygame.SRCALPHA); self.image.blit(image, (0,0))
        spawn_range = 800
        self.world_x = player_world_pos[0] + random.randint(-spawn_range, spawn_range)
        self.world_y = player_world_pos[1] + random.randint(-spawn_range, spawn_range)
        self.rect = self.image.get_rect()

    def update(self, player_world_x, player_world_y):
        self.rect.centerx = self.world_x - player_world_x + SCREEN_WIDTH / 2
        self.rect.centery = self.world_y - player_world_y + SCREEN_HEIGHT / 2
        return not (-100 < self.rect.centerx < SCREEN_WIDTH + 100 and -100 < self.rect.centery < SCREEN_HEIGHT + 100)

# --- ゲーム本体クラス ---
class Game:
    def __init__(self):
        self.screen = None  
        self.clock = pygame.time.Clock()
        
        # --- フォントのロード (ウェブ対応版) ---
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        
        # 1. カスタムフォントを試行
        try:
            font_path = "font.ttf"
            if os.path.exists(font_path):
                self.font_large = pygame.font.Font(font_path, 74)
                self.font_medium = pygame.font.Font(font_path, 50)
                self.font_small = pygame.font.Font(font_path, 30)
                print("カスタムフォント (font.ttf) の読み込みに成功しました。")
            else:
                # 2. デフォルトフォント (None) を試行
                self.font_large = pygame.font.Font(None, 80)
                self.font_medium = pygame.font.Font(None, 56)
                self.font_small = pygame.font.Font(None, 36)
                print("システムフォント (None) の読み込みに成功しました。")
        except Exception as e:
            print(f"★ フォントの読み込みに失敗 ({e})。最終手段としてデフォルトのフォントを取得します。")
            # 3. 組み込みの代替フォントを取得
            default_font_name = pygame.font.get_default_font()
            self.font_large = pygame.font.Font(default_font_name, 80)
            self.font_medium = pygame.font.Font(default_font_name, 56)
            self.font_small = pygame.font.Font(default_font_name, 36)
            
        self.bgm_volume = 0.5
        self.sfx_volume = 0.5
        
        self.bgm_paths = {
            "lobby": os.path.join("sounds", "Lobby.wav"),
            "normal": os.path.join("sounds", "ordinary.wav"),
            "hard": os.path.join("sounds", "difficult.wav")
        }
        self.current_bgm = None
        self.sounds_loaded = False  

        self.init_dummy_sounds()  

        self.game_state = STATE_TITLE
        self.hard_mode_unlocked = False; self.is_hard_mode = False
        self.achievements = {
            "survived_1_min": {"text": "1分間 生存する", "unlocked": False},"survived_3_min": {"text": "3分間 生存する", "unlocked": False},
            "cleared_300m": {"text": "高さ300mをクリア", "unlocked": False},"cleared_800m": {"text": "高さ800mをクリア", "unlocked": False},
        }
        self.hard_mode_achievements = {
            "hm_survived_2_min": {"text": "2分間 生存する", "unlocked": False},"hm_survived_4_min": {"text": "4分間 生存する", "unlocked": False},
            "hm_cleared_500m": {"text": "高さ500mをクリア", "unlocked": False},"hm_cleared_1000m": {"text": "高さ1000mをクリア", "unlocked": False},
        }
        self.notification_text = ""; self.notification_time = 0
    
    def init_dummy_sounds(self):
        """ダミーサウンド（音なし）で変数を初期化する"""
        class DummySound:
            def play(self): pass
            def set_volume(self, vol): pass
        self.get_item_sound = DummySound()
        self.damage_sound = DummySound()
        self.game_over_sound = DummySound()
        self.clear_sound = DummySound()
        self.all_sfx = [self.get_item_sound, self.damage_sound, self.game_over_sound, self.clear_sound]
        self.sounds_loaded = False

    def load_real_sounds(self):
        """★ 実際のサウンドを読み込む（new_gameから呼ばれる）"""
        if self.sounds_loaded:
            return  
            
        try:
            pygame.mixer.init()  
            self.get_item_sound = pygame.mixer.Sound(os.path.join("sounds", "get_item.wav"))
            self.damage_sound = pygame.mixer.Sound(os.path.join("sounds", "damage.wav"))
            self.game_over_sound = pygame.mixer.Sound(os.path.join("sounds", "game_over.wav"))
            self.clear_sound = pygame.mixer.Sound(os.path.join("sounds", "clear.wav"))
            self.all_sfx = [self.get_item_sound, self.damage_sound, self.game_over_sound, self.clear_sound]
            self.set_sfx_volume()
            self.sounds_loaded = True
            print("サウンドの読み込みに成功しました。")
        except pygame.error as e:
            print(f"★ 音声ファイルの読み込みに失敗しました: {e}")
            self.init_dummy_sounds()  

    def set_sfx_volume(self):
        for sfx in self.all_sfx:
            sfx.set_volume(self.sfx_volume)

    def play_bgm(self, track_name):
        if not self.sounds_loaded:  
            return
        if self.current_bgm == track_name:
            return
        try:
            pygame.mixer.music.load(self.bgm_paths[track_name])
            pygame.mixer.music.set_volume(self.bgm_volume)
            pygame.mixer.music.play(loops=-1)
            self.current_bgm = track_name
        except pygame.error as e:
            print(f"BGM '{self.bgm_paths.get(track_name)}' の読み込みに失敗: {e}")
            self.current_bgm = None
    
    def set_notification(self, text):
        self.notification_text = text; self.notification_time = pygame.time.get_ticks()

    def draw_notification(self):
        if self.notification_text and pygame.time.get_ticks() - self.notification_time < 3000:
            draw_text(self.screen, self.notification_text, self.font_small, GOLD, SCREEN_WIDTH - 20, 20, align="topright")
        else: self.notification_text = ""
    
    def spawn_object(self, obj_type, player_pos):
        if obj_type == "glass": img = pygame.Surface((15, 15)); img.fill(GRAY); return WorldObject(obj_type, img, (15, 15), player_pos)
        elif obj_type == "blue_orb": img = pygame.Surface((25, 25), pygame.SRCALPHA); pygame.draw.circle(img, BLUE, (12,12), 12); return WorldObject(obj_type, img, (25, 25), player_pos)
        elif obj_type == "green_orb": img = pygame.Surface((25, 25), pygame.SRCALPHA); pygame.draw.circle(img, GREEN, (12,12), 12); return WorldObject(obj_type, img, (25, 25), player_pos)
        elif obj_type == "stairs": img = pygame.Surface((40, 40)); img.fill(WHITE); return WorldObject(obj_type, img, (40, 40), player_pos)

    def new_game(self):
        self.load_real_sounds()  
        self.play_bgm("hard" if self.is_hard_mode else "normal")
        
        self.all_sprites = pygame.sprite.Group(); self.glass_sprites = pygame.sprite.Group()
        self.blue_orb_sprites = pygame.sprite.Group(); self.green_orb_sprites = pygame.sprite.Group()
        self.stair_sprites = pygame.sprite.Group()
        self.player = Player(); self.tsunami = Tsunami(self.player.base_speed)
        self.start_time = pygame.time.get_ticks(); self.last_height_gain = self.start_time
        player_pos = (self.player.world_x, self.player.world_y)
        for _ in range(20): obj = self.spawn_object("glass", player_pos); self.all_sprites.add(obj); self.glass_sprites.add(obj)
        for _ in range(1): obj = self.spawn_object("blue_orb", player_pos); self.all_sprites.add(obj); self.blue_orb_sprites.add(obj)
        for _ in range(3): obj = self.spawn_object("green_orb", player_pos); self.all_sprites.add(obj); self.green_orb_sprites.add(obj)
        for _ in range(10): obj = self.spawn_object("stairs", player_pos); self.all_sprites.add(obj); self.stair_sprites.add(obj)
        self.object_respawn_timers = []
    
    # ★ 各ループ (show_title_screen, play_game など) は async def に変更
    async def show_title_screen(self):
        pygame.mouse.set_visible(True)
        
        play_button = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2, 400, 60); rules_button = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2 + 80, 400, 60)
        hard_mode_button = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2 + 160, 400, 60); achieve_button = pygame.Rect(SCREEN_WIDTH - 220, 20, 200, 60)
        y_pos = SCREEN_HEIGHT - 80; bgm_minus_btn = pygame.Rect(100, y_pos, 40, 40); bgm_plus_btn = pygame.Rect(320, y_pos, 40, 40)
        sfx_minus_btn = pygame.Rect(SCREEN_WIDTH - 360, y_pos, 40, 40); sfx_plus_btn = pygame.Rect(SCREEN_WIDTH - 140, y_pos, 40, 40)
        
        # ループに入る前に1回描画とフリップを実行 (ウェブ環境でのフリーズ対策)
        self.screen.fill(BLACK)
        draw_text(self.screen, "津波から逃げろ！", self.font_large, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5)
        # 描画省略
        pygame.display.flip() 
        await asyncio.sleep(0) # ブラウザに制御を返す
        
        while self.game_state == STATE_TITLE:
            self.clock.tick(FPS); self.screen.fill(BLACK)
            draw_text(self.screen, "津波から逃げろ！", self.font_large, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5)
            pygame.draw.rect(self.screen, GRAY, play_button); pygame.draw.rect(self.screen, GRAY, rules_button); pygame.draw.rect(self.screen, GRAY, achieve_button)
            draw_text(self.screen, "プレイ / Enter", self.font_medium, WHITE, play_button.centerx, play_button.centery)
            draw_text(self.screen, "ルール / R", self.font_medium, WHITE, rules_button.centerx, rules_button.centery)
            draw_text(self.screen, "実績 / C", self.font_small, WHITE, achieve_button.centerx, achieve_button.centery)
            if self.hard_mode_unlocked:
                pygame.draw.rect(self.screen, DARK_RED, hard_mode_button); draw_text(self.screen, "ハードモード / H", self.font_medium, WHITE, hard_mode_button.centerx, hard_mode_button.centery)
            pygame.draw.rect(self.screen, GRAY, bgm_minus_btn); draw_text(self.screen, "-", self.font_medium, WHITE, bgm_minus_btn.centerx, bgm_minus_btn.centery)
            pygame.draw.rect(self.screen, GRAY, bgm_plus_btn); draw_text(self.screen, "+", self.font_medium, WHITE, bgm_plus_btn.centerx, bgm_plus_btn.centery)
            draw_text(self.screen, f"BGM: {int(self.bgm_volume * 100)}%", self.font_small, WHITE, 230, y_pos + 20)
            pygame.draw.rect(self.screen, GRAY, sfx_minus_btn); draw_text(self.screen, "-", self.font_medium, WHITE, sfx_minus_btn.centerx, sfx_minus_btn.centery)
            pygame.draw.rect(self.screen, GRAY, sfx_plus_btn); draw_text(self.screen, "+", self.font_medium, WHITE, sfx_plus_btn.centerx, sfx_plus_btn.centery)
            draw_text(self.screen, f"SFX: {int(self.sfx_volume * 100)}%", self.font_small, WHITE, SCREEN_WIDTH - 250, y_pos + 20)
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: self.running = False; return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: self.is_hard_mode = False; self.game_state = STATE_PLAYING; self.new_game(); return
                    if event.key == pygame.K_r: self.game_state = STATE_RULES; return
                    if event.key == pygame.K_c: self.game_state = STATE_ACHIEVEMENTS; return
                    if event.key == pygame.K_h and self.hard_mode_unlocked: self.is_hard_mode = True; self.game_state = STATE_PLAYING; self.new_game(); return
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_button.collidepoint(event.pos): self.is_hard_mode = False; self.game_state = STATE_PLAYING; self.new_game(); return
                    if rules_button.collidepoint(event.pos): self.game_state = STATE_RULES; return
                    if achieve_button.collidepoint(event.pos): self.game_state = STATE_ACHIEVEMENTS; return
                    if self.hard_mode_unlocked and hard_mode_button.collidepoint(event.pos): self.is_hard_mode = True; self.game_state = STATE_PLAYING; self.new_game(); return
                    if bgm_minus_btn.collidepoint(event.pos): 
                        self.bgm_volume = max(0.0, round(self.bgm_volume - 0.1, 1))
                        if self.sounds_loaded: pygame.mixer.music.set_volume(self.bgm_volume)
                    if bgm_plus_btn.collidepoint(event.pos): 
                        self.bgm_volume = min(1.0, round(self.bgm_volume + 0.1, 1))
                        if self.sounds_loaded: pygame.mixer.music.set_volume(self.bgm_volume)
                    if sfx_minus_btn.collidepoint(event.pos): 
                        self.sfx_volume = max(0.0, round(self.sfx_volume - 0.1, 1))
                        if self.sounds_loaded: self.set_sfx_volume()
                    if sfx_plus_btn.collidepoint(event.pos): 
                        self.sfx_volume = min(1.0, round(self.sfx_volume + 0.1, 1))
                        if self.sounds_loaded: self.set_sfx_volume()
            
            pygame.display.flip()
            await asyncio.sleep(0) # ★ pygbag用

    async def show_achievements_screen(self):
        back_button = pygame.Rect(20, 20, 150, 60)
        while self.game_state == STATE_ACHIEVEMENTS:
            self.clock.tick(FPS); self.screen.fill(BLACK)
            draw_text(self.screen, "ノーマルモード実績", self.font_medium, WHITE, SCREEN_WIDTH / 2, 80)
            y_offset = 140
            for ach in self.achievements.values():
                draw_text(self.screen, ach["text"], self.font_small, GRAY, SCREEN_WIDTH / 2 - 200, y_offset, align="topleft")
                if ach["unlocked"]: draw_text(self.screen, "【達成】", self.font_small, GOLD, SCREEN_WIDTH / 2 + 250, y_offset, align="topleft")
                else: draw_text(self.screen, "【未達成】", self.font_small, WHITE, SCREEN_WIDTH / 2 + 250, y_offset, align="topleft")
                y_offset += 50
            if self.hard_mode_unlocked:
                y_offset += 20; draw_text(self.screen, "ハードモード実績", self.font_medium, RED, SCREEN_WIDTH / 2, y_offset); y_offset += 60
                for ach in self.hard_mode_achievements.values():
                    draw_text(self.screen, ach["text"], self.font_small, GRAY, SCREEN_WIDTH / 2 - 200, y_offset, align="topleft")
                    if ach["unlocked"]: draw_text(self.screen, "【達成】", self.font_small, GOLD, SCREEN_WIDTH / 2 + 250, y_offset, align="topleft")
                    else: draw_text(self.screen, "【未達成】", self.font_small, WHITE, SCREEN_WIDTH / 2 + 250, y_offset, align="topleft")
                    y_offset += 50
            pygame.draw.rect(self.screen, GRAY, back_button); draw_text(self.screen, "戻る / Q", self.font_small, WHITE, back_button.centerx, back_button.centery)
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: self.running = False; return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: self.game_state = STATE_TITLE; return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint(event.pos): self.game_state = STATE_TITLE; return
            pygame.display.flip()
            await asyncio.sleep(0) # ★ pygbag用

    async def show_rules_screen(self):
        rules_pages = [["--- ルール (1/2) ---","下から迫りくる津波から逃げるゲームです。","W, A, S, Dキー または タッチ で移動します。","キャラクターは画面中央に固定され、世界が動きます。","目標の高さまで到達すればクリアです。","","--- スタミナ ---","左上の緑のバーがスタミナです。","移動すると減少し、速度が低下します。","止まると回復します。"],["--- アイテムと障害物 (2/2) ---","[階段]: 白いオブジェクト。触れると高さが10上昇します。","[緑の球]: スタミナが20回復します。","[青い球]: 津波の速度を一時的に一段階下げます。","[ガラス片]: 灰色のオブジェクト。触れるとスタミナが30減少します。","","--- ハードモード ---","ノーマル実績を全て達成すると解放されます。","より過酷な環境で高みを目指しましょう。"]]
        current_page = 0; back_button = pygame.Rect(20, 20, 150, 60); prev_button = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT - 80, 80, 60); next_button = pygame.Rect(SCREEN_WIDTH/2 + 20, SCREEN_HEIGHT - 80, 80, 60)
        while self.game_state == STATE_RULES:
            self.clock.tick(FPS); self.screen.fill(BLACK)
            for i, line in enumerate(rules_pages[current_page]): draw_text(self.screen, line, self.font_small, WHITE, SCREEN_WIDTH / 2, 100 + i * 40)
            pygame.draw.rect(self.screen, GRAY, back_button); draw_text(self.screen, "戻る / Q", self.font_small, WHITE, back_button.centerx, back_button.centery)
            if current_page > 0: pygame.draw.rect(self.screen, GRAY, prev_button); draw_text(self.screen, "← / A", self.font_small, WHITE, prev_button.centerx, prev_button.centery)
            if current_page < len(rules_pages) - 1: pygame.draw.rect(self.screen, GRAY, next_button); draw_text(self.screen, "→ / D", self.font_small, WHITE, next_button.centerx, next_button.centery)
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: self.running = False; return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: self.game_state = STATE_TITLE; return
                    if event.key == pygame.K_a and current_page > 0: current_page -= 1
                    if event.key == pygame.K_d and current_page < len(rules_pages) - 1: current_page += 1
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint(event.pos): self.game_state = STATE_TITLE; return
                    if prev_button.collidepoint(event.pos) and current_page > 0: current_page -= 1
                    if next_button.collidepoint(event.pos) and current_page < len(rules_pages) - 1: current_page += 1
            pygame.display.flip()
            await asyncio.sleep(0) # ★ pygbag用

    async def play_game(self):
        pygame.mouse.set_visible(False)
        
        bg_color = DARK_RED if self.is_hard_mode else BLACK
        glass_respawn = 500 if self.is_hard_mode else 1000
        other_respawn = 5000 if self.is_hard_mode else 1667
        glass_damage = 60 if self.is_hard_mode else 30
        
        while self.game_state == STATE_PLAYING:
            self.clock.tick(FPS); now = pygame.time.get_ticks()
            
            mouse_pressed = pygame.mouse.get_pressed()[0]  

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: self.running = False; return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.game_state = STATE_TITLE; return

            if mouse_pressed:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] < SCREEN_WIDTH / 2: self.player.moving_left = True
                else: self.player.moving_right = True
                if mouse_pos[1] < SCREEN_HEIGHT / 2: self.player.moving_up = True
                else: self.player.moving_down = True

            self.player.update(); self.tsunami.update(self.player.world_y)
            
            player_pos = (self.player.world_x, self.player.world_y)
            for obj in self.all_sprites:
                if obj.update(self.player.world_x, self.player.world_y):
                    respawn_delay = glass_respawn if obj.type == 'glass' else other_respawn
                    self.object_respawn_timers.append((now + respawn_delay, obj.type, player_pos)); obj.kill()
            
            hits = pygame.sprite.spritecollide(self.player, self.glass_sprites, True)
            for hit in hits: self.damage_sound.play(); self.player.stamina -= glass_damage; self.object_respawn_timers.append((now + glass_respawn, hit.type, player_pos))
            hits = pygame.sprite.spritecollide(self.player, self.blue_orb_sprites, True)
            for hit in hits: self.get_item_sound.play(); self.tsunami.slow_down(); self.object_respawn_timers.append((now + other_respawn, hit.type, player_pos))
            hits = pygame.sprite.spritecollide(self.player, self.green_orb_sprites, True)
            for hit in hits: self.get_item_sound.play(); self.player.stamina += 20; self.object_respawn_timers.append((now + other_respawn, hit.type, player_pos))
            hits = pygame.sprite.spritecollide(self.player, self.stair_sprites, True)
            for hit in hits: self.get_item_sound.play(); self.player.height += 10; self.object_respawn_timers.append((now + other_respawn, hit.type, player_pos))
            
            for i in range(len(self.object_respawn_timers) - 1, -1, -1):
                spawn_time, obj_type, pos = self.object_respawn_timers[i]
                if now >= spawn_time:
                    if (obj_type == "glass" and len(self.glass_sprites) < 20) or (obj_type == "blue_orb" and len(self.blue_orb_sprites) < 1) or (obj_type == "green_orb" and len(self.green_orb_sprites) < 3) or (obj_type == "stairs" and len(self.stair_sprites) < 10):
                        new_obj = self.spawn_object(obj_type, pos)
                        self.all_sprites.add(new_obj)
                        if obj_type == "glass": self.glass_sprites.add(new_obj)
                        elif obj_type == "blue_orb": self.blue_orb_sprites.add(new_obj)
                        elif obj_type == "green_orb": self.green_orb_sprites.add(new_obj)
                        elif obj_type == "stairs": self.stair_sprites.add(new_obj)
                    self.object_respawn_timers.pop(i)
            
            if now - self.last_height_gain > 10000: self.player.height += 1; self.last_height_gain = now
            if self.player.rect.bottom >= self.tsunami.rect.y:
                self.final_survival_time = (now - self.start_time) / 1000; self.game_state = STATE_GAME_OVER; self.check_achievements(); return
            if self.player.height >= self.tsunami.target_height:
                self.final_survival_time = (now - self.start_time) / 1000; self.final_height = self.player.height; self.game_state = STATE_CLEAR; self.check_achievements(); return
            
            self.screen.fill(bg_color); self.screen.blit(self.tsunami.image, self.tsunami.rect); self.all_sprites.draw(self.screen); self.screen.blit(self.player.image, self.player.rect)
            stamina_ratio = self.player.stamina / self.player.max_stamina
            pygame.draw.rect(self.screen, RED, (10, 10, 200, 30)); pygame.draw.rect(self.screen, GREEN, (10, 10, 200 * stamina_ratio, 30));
            draw_text(self.screen, f"スタミナ: {int(self.player.stamina)}", self.font_small, WHITE, 110, 25)
            draw_text(self.screen, f"目標: {self.tsunami.target_height} m", self.font_small, WHITE, SCREEN_WIDTH - 20, 25, align="topright")
            draw_text(self.screen, f"高さ: {self.player.height} m", self.font_small, WHITE, SCREEN_WIDTH - 20, 65, align="topright")
            distance_to_tsunami = self.tsunami.world_y - self.player.world_y
            draw_text(self.screen, f"津波との距離: {max(0, int(distance_to_tsunami / 10))} m", self.font_small, WHITE, SCREEN_WIDTH - 20, 105, align="topright")
            self.draw_notification(); pygame.display.flip()
            await asyncio.sleep(0) # ★ pygbag用

    def check_achievements(self):
        ach_dict = self.hard_mode_achievements if self.is_hard_mode else self.achievements
        if self.is_hard_mode:
            if self.final_survival_time >= 120 and not ach_dict["hm_survived_2_min"]["unlocked"]: ach_dict["hm_survived_2_min"]["unlocked"] = True; self.set_notification("実績解除: ハード 2分間生存")
            if self.final_survival_time >= 240 and not ach_dict["hm_survived_4_min"]["unlocked"]: ach_dict["hm_survived_4_min"]["unlocked"] = True; self.set_notification("実績解除: ハード 4分間生存")
            if self.game_state == STATE_CLEAR:
                if self.final_height >= 500 and not ach_dict["hm_cleared_500m"]["unlocked"]: ach_dict["hm_cleared_500m"]["unlocked"] = True; self.set_notification("実績解除: ハード 高さ500mクリア")
                if self.final_height >= 1000 and not ach_dict["hm_cleared_1000m"]["unlocked"]: ach_dict["hm_cleared_1000m"]["unlocked"] = True; self.set_notification("実績解除: ハード 高さ1000mクリア")
        else:
            if self.final_survival_time >= 60 and not ach_dict["survived_1_min"]["unlocked"]: ach_dict["survived_1_min"]["unlocked"] = True; self.set_notification("実績解除: 1分間 生存する")
            if self.final_survival_time >= 180 and not ach_dict["survived_3_min"]["unlocked"]: ach_dict["survived_3_min"]["unlocked"] = True; self.set_notification("実績解除: 3分間 生存する")
            if self.game_state == STATE_CLEAR:
                if self.final_height >= 300 and not ach_dict["cleared_300m"]["unlocked"]: ach_dict["cleared_300m"]["unlocked"] = True; self.set_notification("実績解除: 高さ300mをクリア")
                if self.final_height >= 800 and not ach_dict["cleared_800m"]["unlocked"]: ach_dict["cleared_800m"]["unlocked"] = True; self.set_notification("実績解除: 高さ800mをクリア")
        if not self.hard_mode_unlocked and all(ach['unlocked'] for ach in self.achievements.values()):
            self.hard_mode_unlocked = True; self.set_notification("ハードモードが解放されました！")

    async def show_end_screen(self, main_message, score_message):
        pygame.mouse.set_visible(True)
        retry_button = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2 + 50, 400, 80)
        title_button = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2 + 150, 400, 80)
        waiting = True
        while waiting:
            self.clock.tick(FPS); self.screen.fill(BLACK)
            draw_text(self.screen, main_message, self.font_large, RED, SCREEN_WIDTH/2, SCREEN_HEIGHT/4)
            draw_text(self.screen, score_message, self.font_medium, WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50)
            pygame.draw.rect(self.screen, GRAY, retry_button); pygame.draw.rect(self.screen, GRAY, title_button)
            draw_text(self.screen, "もう一度プレイ / R", self.font_small, WHITE, retry_button.centerx, retry_button.centery)
            draw_text(self.screen, "タイトルに戻る / Q", self.font_small, WHITE, title_button.centerx, title_button.centery)
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: self.running = False; waiting = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: self.game_state = STATE_PLAYING; self.new_game(); waiting = False
                    if event.key == pygame.K_q: self.game_state = STATE_TITLE; waiting = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if retry_button.collidepoint(event.pos): self.game_state = STATE_PLAYING; self.new_game(); waiting = False
                    if title_button.collidepoint(event.pos): self.game_state = STATE_TITLE; waiting = False
            pygame.display.flip()
            await asyncio.sleep(0) # ★ pygbag用 - ここを修正しました


# --- 実行の起点 (コードの末尾に追加) ---

async def main():
    """ゲームのメインエントリーポイント (非同期)"""
    
    # 1. Pygameの初期化
    pygame.init()
    
    # 2. 画面とオブジェクトの作成
    try:
        # pygbag/ブラウザ環境では、画面スケーリングを試みる
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
    except pygame.error:
        # エラーが出た場合は、通常の初期化に戻す
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
    pygame.display.set_caption("津波から逃げろ！")
    
    game = Game()
    game.screen = screen # Gameクラスに画面オブジェクトを渡す
    game.running = True

    # 3. メインのステートマシンループ
    # 各ステートの関数は非同期 (async) なので await で呼び出す必要がある
    while game.running:
        if game.game_state == STATE_TITLE:
            await game.show_title_screen()
        elif game.game_state == STATE_RULES:
            await game.show_rules_screen()
        elif game.game_state == STATE_ACHIEVEMENTS:
            await game.show_achievements_screen()
        elif game.game_state == STATE_PLAYING:
            await game.play_game()
        # End Screen (GAME_OVER/CLEAR) は show_end_screen() で処理
        elif game.game_state == STATE_GAME_OVER or game.game_state == STATE_CLEAR:
            
            # サウンド再生をメインループ内で一度行い、エンドスクリーンがすぐに描画に入れるようにする
            if game.game_state == STATE_CLEAR:
                main_message = "クリア！"
                score_message = f"到達高度: {game.final_height} m"
                game.clear_sound.play()
            else: # STATE_GAME_OVER
                main_message = "ゲームオーバー"
                score_message = f"生存時間: {game.final_survival_time:.2f} 秒"
                game.game_over_sound.play()
                
            await game.show_end_screen(main_message, score_message)

    # 4. 終了処理
    pygame.quit()
    sys.exit()


# ★★★ pygbag/ブラウザ対応の実行ブロック ★★★
if __name__ == "__main__":
    try:
        # 標準的なPython環境
        asyncio.run(main())
    except RuntimeError as e:
        # pygbag (WebAssembly/pyodide) 環境 - main()関数を自動で実行
        # ブラウザ環境では、この try/except を通って pass するのが通常動作です。
        if "RuntimeError: Task attached to a different loop" not in str(e):
             print(f"非同期ランタイムエラー: {e}")
        pass