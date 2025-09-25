import pygame
import sys
import math
import random

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sega F1 Style Racing Game")

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)


# Параметры машины игрока
class Car:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.width = 40
        self.height = 70
        self.speed = 0
        self.max_speed = 10
        self.acceleration = 0.1
        self.deceleration = 0.05
        self.rotation = 0  # Угол поворота в градусах
        self.rotation_speed = 3  # Скорость поворота

    def update(self):
        # Ограничение скорости
        if self.speed > self.max_speed:
            self.speed = self.max_speed
        elif self.speed < -self.max_speed / 2:  # Задний ход медленнее
            self.speed = -self.max_speed / 2

        # Движение
        rad = math.radians(self.rotation)
        self.x -= self.speed * math.sin(rad)
        self.y -= self.speed * math.cos(rad)

        # Границы экрана
        if self.x < 0:
            self.x = 0
        elif self.x > WIDTH - self.width:
            self.x = WIDTH - self.width

        if self.y < 0:
            self.y = 0
        elif self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height

    def draw(self):
        # Создаем поверхность для машины
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, RED, (0, 0, self.width, self.height))

        # Рисуем "нос" машины
        pygame.draw.polygon(car_surface, RED, [
            (self.width // 2, 0),
            (self.width, self.height // 3),
            (self.width // 2, self.height // 3)
        ])

        # Поворачиваем машину
        rotated_car = pygame.transform.rotate(car_surface, self.rotation)
        rect = rotated_car.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))

        # Рисуем машину на экране
        screen.blit(rotated_car, rect.topleft)


# Класс для трассы
class Track:
    def __init__(self):
        self.outer_points = []
        self.inner_points = []
        self.checkpoints = []
        self.generate_track()

    def generate_track(self):
        # Генерация простой трассы с поворотами
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        outer_radius = 250
        inner_radius = 150

        for angle in range(0, 360, 5):
            rad = math.radians(angle)

            # Внешняя граница
            ox = center_x + outer_radius * math.cos(rad)
            oy = center_y + outer_radius * math.sin(rad)
            self.outer_points.append((ox, oy))

            # Внутренняя граница
            ix = center_x + inner_radius * math.cos(rad)
            iy = center_y + inner_radius * math.sin(rad)
            self.inner_points.append((ix, iy))

            # Чекпоинты
            if angle % 30 == 0:
                mx = center_x + (outer_radius + inner_radius) // 2 * math.cos(rad)
                my = center_y + (outer_radius + inner_radius) // 2 * math.sin(rad)
                self.checkpoints.append((mx, my, angle))

    def draw(self):
        # Рисуем внешнюю границу
        pygame.draw.polygon(screen, GRAY, self.outer_points)

        # Рисуем внутреннюю границу (траву)
        pygame.draw.polygon(screen, GREEN, self.inner_points)

        # Рисуем чекпоинты
        for i, (x, y, angle) in enumerate(self.checkpoints):
            color = BLUE if i == 0 else WHITE  # Первый чекпоинт выделен
            pygame.draw.circle(screen, color, (int(x), int(y)), 5)


# Класс для обработки столкновений
class Collision:
    @staticmethod
    def point_in_polygon(point, polygon):
        x, y = point
        inside = False
        n = len(polygon)
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside


# Основные объекты игры
car = Car()
track = Track()
collision = Collision()
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# Игровые переменные
score = 0
current_checkpoint = 0
game_time = 0
running = True

# Главный игровой цикл
while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обработка ввода с клавиатуры
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        car.speed += car.acceleration
    elif keys[pygame.K_DOWN]:
        car.speed -= car.deceleration
    else:
        # Постепенное замедление при отпущенных клавишах
        if car.speed > 0:
            car.speed -= car.deceleration / 2
            if car.speed < 0:
                car.speed = 0
        elif car.speed < 0:
            car.speed += car.deceleration / 2
            if car.speed > 0:
                car.speed = 0

    if keys[pygame.K_LEFT]:
        car.rotation += car.rotation_speed
    if keys[pygame.K_RIGHT]:
        car.rotation -= car.rotation_speed

    # Обновление игрового состояния
    car.update()
    game_time += 1 / 60  # Предполагаем 60 FPS

    # Проверка чекпоинтов
    car_center = (car.x + car.width // 2, car.y + car.height // 2)
    if current_checkpoint < len(track.checkpoints):
        checkpoint_x, checkpoint_y, _ = track.checkpoints[current_checkpoint]
        distance = math.sqrt((car_center[0] - checkpoint_x) ** 2 + (car_center[1] - checkpoint_y) ** 2)
        if distance < 30:
            score += 100
            current_checkpoint += 1
            if current_checkpoint >= len(track.checkpoints):
                current_checkpoint = 0  # Зацикливаем чекпоинты

    # Проверка столкновений с границами трассы
    if (collision.point_in_polygon(car_center, track.outer_points) and
            not collision.point_in_polygon(car_center, track.inner_points)):
        # Машина на трассе - все хорошо
        pass
    else:
        # Столкновение - замедление
        car.speed *= 0.9

    # Отрисовка
    screen.fill(BLACK)

    # Рисуем трассу
    track.draw()

    # Рисуем машину
    car.draw()

    # Рисуем UI
    score_text = font.render(f"Score: {score}", True, WHITE)
    time_text = font.render(f"Time: {game_time:.1f}s", True, WHITE)
    speed_text = font.render(f"Speed: {abs(car.speed * 10):.1f} km/h", True, WHITE)

    screen.blit(score_text, (10, 10))
    screen.blit(time_text, (10, 50))
    screen.blit(speed_text, (10, 90))

    # Обновление экрана
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()