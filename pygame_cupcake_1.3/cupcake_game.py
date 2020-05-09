#!/usr/bin/env python
# coding: utf-8

import pygame
from pygame.locals import *
import sys
import time
import numpy as np
from PIL import Image
import copy


class Game:
    """ ゲームのメインクラス """

    def __init__(self, step=False, image=False):
        # ステップ実行
        self.step_flg = step
        # 学習データを画像にするか
        self.image_flg = image
        # ゲーム画面の画像
        self.observation_space = None
        # 状態：プレイ中
        self.status = 'PLAY'
        # スコア初期化
        self.score = 0

        pygame.init()

        # 既定のウィンドウ、32bit
        pygame.display.set_mode((300,400), 0, 32)
        pygame.display.set_caption('cupcake')
        self.screen = pygame.display.get_surface()

        self.init_game()
        self._get_observation()

        # step=Falseの時
        if not self.step_flg:
            clock = pygame.time.Clock()
            while True:
                # 25秒でゲーム再スタート
                clock.tick(25)
                self.update()
                self.draw(self.screen)
                pygame.display.update()

    def init_game(self):
        """ ゲームオブジェクトの初期化 """
        self.player = Player()
        self.cupcake = Cupcake()
        self.background = BackGround()
        # タイマースタート
        self.start_time = time.time()
        self.last_time = self.start_time

    # ここからgym互換関数群
    def reset(self):
        """ gymからゲームを再スタート """
        self.status = 'PLAY'
        self.score = 0
        self.init_game()
        self._get_observation()
        return self.observation_space

    def render(self, mode=None):
        """ pygameで画面表示されるので処理は書かない """
        pass

    def step(self, action):
        """ gymから実行されるゲーム1回分の処理 """
        if not self.step_flg:
            return None

        # 報酬を初期化
        reward = 0
        self._key_action(action)
        self.update()
        self.draw(self.screen)
        pygame.display.update()
        self._get_observation()

        # 報酬を与える
        done = self.status == 'END'
        if done:
            if self.score == 0:
                reward -= 10
            else:
                # スコアの1/100の値を報酬とする
                reward += self.score * 0.01

        return self.observation_space, reward, done, {}

    def _key_action(self, action):
        """ gymのプレイヤー操作 """
        self.player.last_position = copy.deepcopy(self.player.position)
        # 左
        if action == 0:
            self.player.position[0] -= 100

        # 右
        if action == 1:
            self.player.position[0] += 100

        # 上
        if action == 2:
            self.player.position[1] -= 100

        # 下
        if action == 3:
            self.player.position[1] += 100


        # 画面の端だったら動かない
        # 左端
        if self.player.position[0] < 10:
            self.player.position[0] += 100

        # 右端
        if self.player.position[0] > 250:
            self.player.position[0] -= 100

        # 上端
        if self.player.position[1] < 10:
            self.player.position[1] += 100

        # 下端
        if self.player.position[1] > 350:
            self.player.position[1] -= 100

        self.player.rect.center = copy.deepcopy(self.player.position)

        # プレイヤーが移動したか
        is_act = self.player.position != self.player.last_position
        if is_act:
            # ケーキの隣のマスだったら加点
            is_next = abs(self.cupcake.position[0] - self.player.position[0]) < 101 \
                      or abs(self.cupcake.position[1] - self.player.position[1]) < 101
            if is_next:
                self.score += 10

    def _get_observation(self):
        """ ゲーム画面の画像を設定 """
        if self.image_flg:
            resize_x = 120
            resize_y = 160
            cut_y_rate = 0.06
            # ゲーム画面をリサイズして設定
            pil_img = Image.fromarray(pygame.surfarray.array3d(self.screen))
            resized_img = pil_img.resize((resize_x, resize_y), Image.LANCZOS)
            self.observation_space = np.asarray(resized_img)[:][int(resize_y * cut_y_rate):]
        else:
            self.observation_space = np.array(self.player.position)
        return None
    # ここまでgym互換関数群

    def draw(self, screen):
        """ 画面描画 """

        # 画面更新間隔
        pygame.time.wait(100)

        # ゲーム画面
        if self.status == 'PLAY':
            screen.fill((0, 0, 0, 0))
            # 背景
            screen.blit(self.background.img, self.background.rect)
            # スコア
            font = pygame.font.SysFont(None, 20)
            rect_score = font.render('SCORE:' + str(self.score), True, (160,100,65))
            screen.blit(rect_score, [10, 10])
            # ケーキ
            screen.blit(self.cupcake.img, self.cupcake.rect)
            # プレイヤー
            screen.blit(self.player.img, self.player.rect)

        # スコア画面
        elif self.status == 'END':
            font = pygame.font.SysFont(None, 50)
            rect_msg = font.render('SCORE:' + str(self.score), True, (160, 100, 65))
            # スコアを表示
            self.screen.fill((255, 250, 165, 0))
            self.screen.blit(rect_msg, [50,150])

    def update(self):
        """ ゲーム画面の更新 """

        # 開始から20秒経過したらゲーム終了
        current_time = time.time()
        play_time = current_time - self.start_time
        if play_time >= 20:
            self.status = 'END'

        elif self.status == 'PLAY':
            self.player.act()

            # 前回ケーキにたどり着いた時からの時間
            interval = current_time - self.last_time
            # プレイヤーが移動したか
            is_act = self.player.position != self.player.last_position

            # プレイヤーがケーキにたどり着いた
            if self.player.rect.colliderect(self.cupcake.rect):
                # スコア加点
                self.score += 100
                # ケーキ獲得の間隔が5秒以内だったらボーナススコア
                if interval < 6:
                    self.score += 5
                # ケーキが移動
                self.cupcake.position[0] += 100
                self.cupcake.position[1] -= 100
                # ケーキが画面からはみ出る場合は反対側に移動
                self.cupcake.position[0] = self.cupcake.position[0] % 300
                self.cupcake.position[1] = self.cupcake.position[1] % 400
                self.cupcake.rect.center = self.cupcake.position
                # 今の時間を保持
                self.last_time = current_time

        for event in pygame.event.get():
            # 閉じるボタン押下
            if event.type == QUIT:
                pygame.quit()
                sys.exit()


class Player:
    """ プレイヤー """

    def __init__(self):
        self.position = [150, 345]
        self.last_position = copy.deepcopy(self.position)
        self.img, self.rect = load_image('image/valentinesday_heart_girl.png')
        self.rect.center = self.position

    def act(self):
        """ プレイヤーの移動 """
        self.last_position = copy.deepcopy(self.position)
        pressed_key = pygame.key.get_pressed()
        # 左
        if pressed_key[K_LEFT]:
            self.position[0] -= 100
        # 右
        if pressed_key[K_RIGHT]:
            self.position[0] += 100
        # 上
        if pressed_key[K_UP]:
            self.position[1] -= 100
        # 下
        if pressed_key[K_DOWN]:
            self.position[1] += 100

        # 画面の端だったら動かない
        # 左端
        if self.position[0] < 10:
            self.position[0] += 100
        # 右端
        if self.position[0] > 250:
            self.position[0] -= 100
        # 上端
        if self.position[1] < 10:
            self.position[1] += 100
        # 下端
        if self.position[1] > 350:
            self.position[1] -= 100

        self.rect.center = copy.deepcopy(self.position)


class Cupcake:
    """ カップケーキ """
    def __init__(self):
        self.position = [250, 345]
        self.img, self.rect = load_image('image/sweets_cupcake.png')
        self.rect.center = self.position


class BackGround:
    """ 背景の設定 """
    def __init__(self):
        self.img, self.rect = load_image('image/board.png')


def load_image(path):
    img = pygame.image.load(path).convert_alpha()
    rect = img.get_rect()
    return img, rect


if __name__ == '__main__':
    Game()
