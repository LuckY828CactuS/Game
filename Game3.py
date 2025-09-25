import pygame
import os
import sys
from pygame.locals import *

# Инициализация Pygame
pygame.init()

# Настройки окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Симуляция движения по коридору')

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Параметры движения
STEP_SIZE = 100  # шаг перемещения в пикселях
ROTATION_ANGLE = 45  # угол поворота в градусах

# Начальная позиция и направление
x, y = 0, 0
current_angle = 0  # 0, 45, 90, 135, 180, 225, 270, 315


# Загрузка изображений
def load_images():
    images = {}
    base_path = "images"  # Папка с изображениями

    if not os.path.exists(base_path):
        print(f"Папка {base_path} не найдена! Будут использоваться демо-изображения")
        return None

    for img_file in os.listdir(base_path):
        if not img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        # Разбираем имя файла (формат "x0_y100_angle45.jpg")
        try:
            # Удаляем расширение и разбиваем по '_'
            parts = img_file[:-4].split('_')
            if len(parts) != 3:
                continue

            x = int(parts[0][1:])  # "x0" -> 0
            y = int(parts[1][1:])  # "y100" -> 100
            angle = int(parts[2][5:])  # "angle45" -> 45
        except:
            print(f"Неверный формат имени файла: {img_file}")
            continue

        # Загружаем изображение
        img_path = os.path.join(base_path, img_file)
        try:
            image = pygame.image.load(img_path).convert()
            images[(x, y, angle)] = image
            print(f"Загружено: {img_path}")
        except pygame.error as e:
            print(f"Ошибка загрузки {img_path}: {e}")

    return images if images else None


# Создание демо-изображения
def create_demo_image(x, y, angle):
    surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    surf.fill(BLACK)

    # Рисуем простой коридор с учетом позиции и угла
    font = pygame.font.Font(None, 36)
    text = font.render(f"Позиция: ({x}, {y}), Угол: {angle}°", True, WHITE)
    surf.blit(text, (50, 50))

    # Простое представление коридора
    pygame.draw.rect(surf, (100, 100, 100), (300, 200, 200, 200))

    return surf


# Загрузка или создание изображений
images = load_images()
if images is None:
    print("Создаю демо-изображения...")
    images = {}
    for x_pos in range(-500, 501, STEP_SIZE):
        for y_pos in range(-500, 501, STEP_SIZE):
            for angle in range(0, 360, ROTATION_ANGLE):
                images[(x_pos, y_pos, angle)] = create_demo_image(x_pos, y_pos, angle)

# Основной цикл
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        # Обработка клавиш
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

            # Движение вперед/назад
            if event.key == K_UP:
                x += STEP_SIZE
            elif event.key == K_DOWN:
                x -= STEP_SIZE

            # Повороты
            elif event.key == K_LEFT:
                current_angle = (current_angle - ROTATION_ANGLE) % 360
            elif event.key == K_RIGHT:
                current_angle = (current_angle + ROTATION_ANGLE) % 360

    # Получаем текущее изображение
    current_image = images.get((x, y, current_angle))
    if current_image is None:
        current_image = create_demo_image(x, y, current_angle)

    # Отрисовка
    window.blit(current_image, (0, 0))

    # Отображение информации
    font = pygame.font.Font(None, 24)
    info_text = [
        f"Позиция: X={x}, Y={y}",
        f"Угол обзора: {current_angle}°",
        "Управление: Стрелки - движение/поворот, ESC - выход"
    ]

    for i, text in enumerate(info_text):
        text_surface = font.render(text, True, WHITE)
        window.blit(text_surface, (10, 10 + i * 30))

    pygame.display.update()
    clock.tick(30)

pygame.quit()
sys.exit()