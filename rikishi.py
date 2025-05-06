import pyxel
import random
import json

SCREEN_W = 248
SCREEN_H = 248
PLAYER_W = 15  # ←画像の幅に合わせて修正
PLAYER_H = 21  # ←画像の高さに合わせて修正
PLAYER_Y = 16
FALL_SPEED = 2

ENEMY1_ANIM = [
    {"x": 0,  "y": 24, "w": 16, "h": 24, "frames": 3},
    {"x": 16, "y": 24, "w": 16, "h": 24, "frames": 6},
    {"x": 0,  "y": 24, "w": 16, "h": 24, "frames": 3},
    {"x": 32, "y": 24, "w": 16, "h": 24, "frames": 6},
]
ENEMY1_W = 16
ENEMY1_H = 24

ENEMY2_ANIM = [
    {"x": 0,  "y": 0,  "w": 15, "h": 21, "frames": 5},
    {"x": 16, "y": 0,  "w": 8,  "h": 21, "frames": 3},
    {"x": 32, "y": 0,  "w": 14, "h": 20, "frames": 5},
    {"x": 16, "y": 0,  "w": 8,  "h": 21, "frames": 3},
]
ENEMY2_W = 16
ENEMY2_H = 21

class Game:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="RIKISHI")
        self.state = "title"
        self.title_bgm_played = False  # タイトルBGM再生済みフラグ

        with open(f"rikishi_last.json", "rt") as f:
            self.music = json.loads(f.read())
        
        # リソースファイル（.pyxres）に設定してあるSEに番号が被らないよう、番号を指定して読み込み
        for ch, sound in enumerate(self.music):
            set_channel = ch + 16
            pyxel.sounds[set_channel].set(*sound)
        
        with open(f"goonies.json", "rt") as f:
            self.stage_music = json.loads(f.read())
        
        # リソースファイル（.pyxres）に設定してあるSEに番号が被らないよう、番号を指定して読み込み
        for ch, sound in enumerate(self.stage_music):
            set_channel = ch + 20
            pyxel.sounds[set_channel].set(*sound)

        with open(f"rikishi_base.json", "rt") as f:
            self.ope_music = json.loads(f.read())
        
        # リソースファイル（.pyxres）に設定してあるSEに番号が被らないよう、番号を指定して読み込み
        for ch, sound in enumerate(self.ope_music):
            set_channel = ch + 25
            pyxel.sounds[set_channel].set(*sound)
        
        self.hit_enemy = None  # None, "enemy1", "enemy2"
        self.hit_anim_timer = 0
        self.played_gameover_se = False
        
        pyxel.load("rikishi.pyxres")
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.stage = 1
        self.reset_stage()
        self.gameover = False
        self.waiting_music = False
        self.music_after = None  # "stage" or "gameover"
        self.bgm_playing = False
        # ずれ演出フラグのリセット
        self.hit_enemy = None
        self.hit_anim_timer = 0

        self.played_gameover_se = False
        self.gameclear = False

    def reset_stage(self):
        self.player_x = (SCREEN_W - PLAYER_W) // 2
        self.player_y = PLAYER_Y
        self.player_vx = 1.5 + self.stage * 0.5
        self.player_dir = 1
        self.falling = False

        # 敵のY座標を上の方に調整
        self.enemy1_y = SCREEN_H - 119
        self.enemy1_x = random.randint(16, SCREEN_W - 16 - ENEMY1_W)
        self.enemy1_vx = random.uniform(1.0, 2.0) + self.stage * 0.6
        self.enemy1_dir = 1
        self.enemy1_anim_frame = 0
        self.enemy1_anim_counter = 0

        self.enemy2_y = self.enemy1_y - 53
        self.enemy2_x = random.randint(16, SCREEN_W - 16 - ENEMY2_W)
        self.enemy2_vx = random.uniform(1.0, 2.0) + self.stage * 0.6
        self.enemy2_dir = 1
        self.enemy2_anim_frame = 0
        self.enemy2_anim_counter = 0

        self.waiting_music = False
        self.music_after = None
        self.bgm_playing = False

        # ずれ演出フラグのリセット
        self.hit_enemy = None
        self.hit_anim_timer = 0

        self.played_gameover_se = False

        # ステージ開始時にBGM再生
        self.start_bgm()
    
    def start_bgm(self):
        for ch, sound in enumerate(self.stage_music):
            set_sound_id = ch + 20
            pyxel.sounds[set_sound_id].set(*sound)
            pyxel.play(ch, set_sound_id, loop=True)
        self.bgm_playing = True
    
    def stop_bgm(self):
        pyxel.stop()
        self.bgm_playing = False

    def update(self):
        if self.state == "title":
            if not self.title_bgm_played:
                for ch, sound in enumerate(self.ope_music):
                    set_sound_id = ch + 25
                    pyxel.sounds[set_sound_id].set(*sound)
                    pyxel.play(ch, set_sound_id, loop=False)
                self.title_bgm_played = True
            # 入力でゲーム開始
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                pyxel.stop()  # タイトルBGM停止
                self.state = "game"
                self.reset_game()
            return
        if self.waiting_music:
            # 16, 17, 18チャンネルすべて停止していれば
            if (pyxel.play_pos(0) is None and
                pyxel.play_pos(1) is None and
                pyxel.play_pos(2) is None and
                pyxel.play_pos(3) is None):
                if self.music_after == "stage":
                    self.stage += 1
                    if self.stage > 10:
                        self.gameclear = True
                    else:
                        self.reset_stage()
                    self.waiting_music = False  # ← 念のため
                elif self.music_after == "gameover":
                    self.gameover = True
                    self.waiting_music = False  # ← これが重要！
            return
        
        if self.gameover or self.gameclear:
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.reset_game()
            return
        
        # BGMが止まっていたら再開（SE再生中以外で）
        if not self.bgm_playing and not self.waiting_music:
            self.start_bgm()

        # 敵キャラは常に動く＆アニメーション
        self.enemy1_x += self.enemy1_vx * self.enemy1_dir
        if self.enemy1_x > SCREEN_W - ENEMY1_W:
            self.enemy1_x = SCREEN_W - ENEMY1_W
            self.enemy1_dir = -1
        if self.enemy1_x < 0:
            self.enemy1_x = 0
            self.enemy1_dir = 1
        self.update_enemy_anim("enemy1")

        self.enemy2_x += self.enemy2_vx * self.enemy2_dir
        if self.enemy2_x > SCREEN_W - ENEMY2_W:
            self.enemy2_x = SCREEN_W - ENEMY2_W
            self.enemy2_dir = -1
        if self.enemy2_x < 0:
            self.enemy2_x = 0
            self.enemy2_dir = 1
        self.update_enemy_anim("enemy2")

        if not self.falling:
            self.player_x = (SCREEN_W - PLAYER_W) // 2
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.falling = True
        else:
            # ステージに関係なく一定の落下速度（FALL_SPEED * 5.0）
            self.player_y += FALL_SPEED * 5.0

            #敵1との当たり判定
            if (self.player_x + PLAYER_W > self.enemy1_x and
                self.player_x < self.enemy1_x + ENEMY1_W and
                self.player_y + PLAYER_H > self.enemy1_y and
                self.player_y < self.enemy1_y + ENEMY1_H):
                self.play_stage_music(after="stage")
                self.hit_enemy = "enemy1"
                self.hit_anim_timer = 0
                return

            #敵2との当たり判定
            if (self.player_x + PLAYER_W > self.enemy2_x and
                self.player_x < self.enemy2_x + ENEMY2_W and
                self.player_y + PLAYER_H > self.enemy2_y and
                self.player_y < self.enemy2_y + ENEMY2_H):
                self.play_stage_music(after="gameover")
                self.hit_enemy = "enemy2"
                self.hit_anim_timer = 0
                return
            
            if self.player_y > SCREEN_H:
                self.gameover = True
                # 敵に当たっていない場合のみ効果音を1度だけ鳴らす
                if not self.hit_enemy and not self.played_gameover_se:
                    pyxel.play(0, 0)  # チャンネル0でSOUND0を再生
                    self.played_gameover_se = True
                # BGMだけ止める
                pyxel.stop(1)
                pyxel.stop(2)
                pyxel.stop(3)
        
        if self.hit_enemy:
            self.hit_anim_timer += 1
            # 例: 30フレーム（0.5秒）で演出終了
            if self.hit_anim_timer > 30:
                self.hit_enemy = None

    def play_stage_music(self, after):
        self.stop_bgm()  # BGMを止める
        for ch, sound in enumerate(self.music):
            set_sound_id = ch + 16  # サウンドIDは16, 17, 18, 19...
            pyxel.sounds[set_sound_id].set(*sound)
            pyxel.play(ch, set_sound_id, loop=False)  # チャンネルは0～3
        
        self.waiting_music = True
        self.music_after = after  # "stage" or "gameover"

    def update_enemy_anim(self, enemy):
        if enemy == "enemy1":
            anim = ENEMY1_ANIM
            frame = self.enemy1_anim_frame
            counter = self.enemy1_anim_counter
        else:
            anim = ENEMY2_ANIM
            frame = self.enemy2_anim_frame
            counter = self.enemy2_anim_counter

        counter += 1
        if counter >= anim[frame]["frames"]:
            counter = 0
            frame = (frame + 1) % len(anim)

        if enemy == "enemy1":
            self.enemy1_anim_frame = frame
            self.enemy1_anim_counter = counter
        else:
            self.enemy2_anim_frame = frame
            self.enemy2_anim_counter = counter
    
    def draw_text_with_bg(self, x, y, text, text_color, bg_color=0):
        w = len(text) * 4  # 1文字4ピクセル幅
        h = 6              # 文字高さ
        pyxel.rect(x - 2, y - 2, w + 4, h + 4, bg_color)  # ちょっと余白つき
        pyxel.text(x, y, text, text_color)

    def draw(self):
        if self.state == "title":
            pyxel.cls(0)
            #画像を中央よりやや上に表示
            img_x = 48
            img_y = 72
            img_w = 113 - 48 + 1
            img_h = 224 - 72 + 1
            draw_x = (SCREEN_W - img_w) // 2
            draw_y = (SCREEN_H - img_h) // 2 - 20  # やや上
            pyxel.blt(draw_x, draw_y, 0, img_x, img_y, img_w, img_h, colkey=0)
            # 点滅テキスト
            if (pyxel.frame_count // 30) % 2 == 0:
                msg = "Press SPACE or Tap"
                text_x = SCREEN_W // 2 - len(msg)*2
                text_y = draw_y + img_h + 12
                self.draw_text_with_bg(text_x, text_y, msg, 7)
            return


        # 背景
        pyxel.blt(0, 0, 1, 0, 0, SCREEN_W, SCREEN_H, colkey=None)

        # 敵1描画
        e1_anim = ENEMY1_ANIM[self.enemy1_anim_frame]
        e1_x = int(self.enemy1_x)
        e1_y = int(self.enemy1_y)
        e1_img = 0
        e1_flip = self.enemy1_dir == -1

        if self.hit_enemy == "enemy1":
            # 下部（上から8ドット以降）を下に8ドット分ずらして描画
            pyxel.blt(
                e1_x, e1_y + 8,
                e1_img,
                e1_anim["x"], e1_anim["y"] + 8,
                e1_anim["w"] * (-1 if e1_flip else 1),
                e1_anim["h"] - 8,
                colkey=0
            )
            # 上部8ドットを下に8ドット分ずらして重ね描画
            pyxel.blt(
                e1_x, e1_y + 8,
                e1_img,
                e1_anim["x"], e1_anim["y"],
                e1_anim["w"] * (-1 if e1_flip else 1),
                8,
                colkey=0
            )
        else:
            pyxel.blt(
                e1_x, e1_y,
                e1_img,
                e1_anim["x"], e1_anim["y"],
                e1_anim["w"] * (-1 if e1_flip else 1),
                e1_anim["h"],
                colkey=0
            )

        # 敵2描画
        e2_anim = ENEMY2_ANIM[self.enemy2_anim_frame]
        e2_x = int(self.enemy2_x)
        e2_y = int(self.enemy2_y)
        e2_img = 0
        e2_flip = self.enemy2_dir == -1

        if self.hit_enemy == "enemy2":
            pyxel.blt(
                e2_x, e2_y + 8,
                e2_img,
                e2_anim["x"], e2_anim["y"] + 8,
                e2_anim["w"] * (-1 if e2_flip else 1),
                e2_anim["h"] - 8,
                colkey=0
            )
            pyxel.blt(
                e2_x, e2_y + 8,
                e2_img,
                e2_anim["x"], e2_anim["y"],
                e2_anim["w"] * (-1 if e2_flip else 1),
                8,
                colkey=0
            )
        else:
            pyxel.blt(
                e2_x, e2_y,
                e2_img,
                e2_anim["x"], e2_anim["y"],
                e2_anim["w"] * (-1 if e2_flip else 1),
                e2_anim["h"],
                colkey=0
            )

        # プレイヤーキャラ描画
        # 敵に当たった時は8ドット下にずらす
        player_y = self.player_y + 8 if self.hit_enemy else self.player_y
        pyxel.blt(self.player_x, player_y, 0, 0, 48, PLAYER_W, PLAYER_H, colkey=0)

        # ステージ表示
        pyxel.text(4, 4, f"STAGE: {self.stage}", 7)


        # ゲームオーバー表示
        if self.gameover:
            self.draw_text_with_bg(SCREEN_W//2-30, SCREEN_H//2-10, "GAME OVER", 8)
            self.draw_text_with_bg(SCREEN_W//2-60, SCREEN_H//2+16, "Press SPACE or Tap to Retry", 6)

        if self.gameclear:
            self.draw_text_with_bg(SCREEN_W//2-40, SCREEN_H//2-10, "GAME CLEAR!!", 10)
            self.draw_text_with_bg(SCREEN_W//2-60, SCREEN_H//2+16, "Press SPACE or Tap to Retry", 6)
        
Game()
