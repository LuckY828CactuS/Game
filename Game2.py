import pygame
import sys
import math
import os
import random  # Добавлен импорт модуля random
from pygame.locals import *

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D коридор с текстурами")

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
FLOOR_COLOR = (80, 80, 80)
CEILING_COLOR = (60, 60, 80)

# Параметры движения
STEP_SIZE = 0.01
TURN_ANGLE = 2.5
FOV = 60


# Загрузка текстур стен
def load_textures():
    textures = []
    # Создаем папку для текстур, если ее нет
    if not os.path.exists('textures'):
        os.makedirs('textures')
        print("Создана папка 'textures'. Добавьте туда свои изображения для текстур стен.")

    # Пытаемся загрузить текстуры
    for i in range(1, 5):
        try:
            texture = pygame.image.load(f'textures/wall_{i}.jpg')
            texture = pygame.transform.scale(texture, (64, 64))
            textures.append(texture)
        except:
            # Если текстуры нет, создаем простую текстуру
            texture = pygame.Surface((64, 64))
            texture.fill((random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
            pygame.draw.line(texture, BLACK, (0, 0), (63, 63), 2)
            pygame.draw.line(texture, BLACK, (63, 0), (0, 63), 2)
            textures.append(texture)
            print(f"Текстура wall_{i}.jpg не найдена, создана временная замена")

    return textures


wall_textures = load_textures()


# Класс для рендеринга 3D коридора
class CorridorRenderer:
    def __init__(self):
        self.player_x = 1.5
        self.player_y = 1.5
        self.player_angle = 0
        # Карта (1 - стена, 0 - пустое пространство)
        # Числа от 1 до 4 соответствуют разным текстурам
        self.map = [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 2],
            [3, 0, 0, 0, 2],
            [3, 0, 0, 0, 2],
            [1, 1, 1, 1, 1]
        ]

    def move_forward(self):
        rad = math.radians(self.player_angle)
        new_x = self.player_x + math.sin(rad) * STEP_SIZE
        new_y = self.player_y + math.cos(rad) * STEP_SIZE

        if 0 <= int(new_x) < 5 and 0 <= int(new_y) < 5:
            if self.map[int(new_y)][int(new_x)] == 0:
                self.player_x = new_x
                self.player_y = new_y

    def move_backward(self):
        rad = math.radians(self.player_angle)
        new_x = self.player_x - math.sin(rad) * STEP_SIZE
        new_y = self.player_y - math.cos(rad) * STEP_SIZE

        if 0 <= int(new_x) < 5 and 0 <= int(new_y) < 5:
            if self.map[int(new_y)][int(new_x)] == 0:
                self.player_x = new_x
                self.player_y = new_y

    def turn_left(self):
        self.player_angle = (self.player_angle + TURN_ANGLE) % 360

    def turn_right(self):
        self.player_angle = (self.player_angle - TURN_ANGLE) % 360

    def render(self, surface):
        surface.fill(CEILING_COLOR)
        pygame.draw.rect(surface, FLOOR_COLOR, (0, HEIGHT // 2, WIDTH, HEIGHT // 2))

        # Рендеринг стен с помощью raycasting
        for x in range(WIDTH):
            ray_angle = (self.player_angle - FOV / 2) + (x / WIDTH) * FOV
            rad = math.radians(ray_angle)

            ray_x, ray_y = self.player_x, self.player_y
            sin, cos = math.sin(rad), math.cos(rad)

            distance = 0
            wall_type = 0
            hit_wall = False

            while not hit_wall and distance < 20:
                distance += 0.05
                ray_x = self.player_x + sin * distance
                ray_y = self.player_y + cos * distance

                if 0 <= int(ray_x) < 5 and 0 <= int(ray_y) < 5:
                    if self.map[int(ray_y)][int(ray_x)] > 0:
                        hit_wall = True
                        wall_type = self.map[int(ray_y)][int(ray_x)] - 1

            if hit_wall:
                corrected_distance = distance * math.cos(math.radians(ray_angle - self.player_angle))
                wall_height = min(int(HEIGHT / (corrected_distance + 0.0001)), HEIGHT * 2)

                # Вычисляем координату текстуры
                hit_x = ray_x - int(ray_x)
                hit_y = ray_y - int(ray_y)

                if abs(hit_x) > abs(hit_y):
                    tex_x = int(hit_y * 64) if sin > 0 else 64 - int(hit_y * 64)
                else:
                    tex_x = int(hit_x * 64) if cos > 0 else 64 - int(hit_x * 64)

                tex_x %= 64

                # Получаем вертикальный срез текстуры
                texture_slice = pygame.Surface((1, 64))
                texture_slice.blit(wall_textures[wall_type], (0, 0), (tex_x, 0, 1, 64))

                # Масштабируем срез текстуры по высоте стены
                texture_slice = pygame.transform.scale(texture_slice, (1, wall_height))

                # Затемнение в зависимости от расстояния
                darkness = min(255, int(distance * 20))
                texture_slice.fill((darkness, darkness, darkness), special_flags=pygame.BLEND_MULT)

                # Рисуем стену
                wall_y = (HEIGHT - wall_height) // 2
                surface.blit(texture_slice, (x, wall_y))

        # Мини-карта
        self.render_minimap(surface)

        # Информация
        self.render_info(surface)

    def render_minimap(self, surface):
        map_size = 100
        cell_size = map_size // 5
        for y in range(5):
            for x in range(5):
                if self.map[y][x] > 0:
                    color = [RED, GREEN, BLUE, WHITE][self.map[y][x] - 1]
                    pygame.draw.rect(surface, color,
                                     (WIDTH - map_size + x * cell_size,
                                      y * cell_size,
                                      cell_size, cell_size))

        player_map_x = WIDTH - map_size + int(self.player_x * cell_size)
        player_map_y = int(self.player_y * cell_size)
        pygame.draw.circle(surface, WHITE, (player_map_x, player_map_y), 3)

        end_x = player_map_x + math.sin(math.radians(self.player_angle)) * 15
        end_y = player_map_y + math.cos(math.radians(self.player_angle)) * 15
        pygame.draw.line(surface, WHITE, (player_map_x, player_map_y), (end_x, end_y), 2)

    def render_info(self, surface):
        font = pygame.font.SysFont(None, 24)
        info = [
            f"Позиция: X={self.player_x:.1f}, Y={self.player_y:.1f}",
            f"Угол: {self.player_angle}°",
            "Управление: Стрелки - движение/поворот, ESC - выход",
            "Добавьте текстуры в папку 'textures' (wall_1.jpg, wall_2.jpg и т.д.)"
        ]

        for i, text in enumerate(info):
            text_surface = font.render(text, True, WHITE)
            surface.blit(text_surface, (10, 10 + i * 25))


# Основные объекты
renderer = CorridorRenderer()
clock = pygame.time.Clock()

# Главный игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

    keys = pygame.key.get_pressed()
    if keys[K_UP]:
        renderer.move_forward()
    if keys[K_DOWN]:
        renderer.move_backward()
    if keys[K_LEFT]:
        renderer.turn_right()
    if keys[K_RIGHT]:
        renderer.turn_left()

    screen.fill(BLACK)
    renderer.render(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()