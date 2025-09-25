import pygame
import sys
import math
import numpy as np
from pygame.locals import *

# Инициализация Pygame
pygame.init()

# Настройки окна
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 400
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Моделирование столкновения тележек')

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)


# Параметры системы
class Cart:
    def __init__(self, x, mass, velocity, color, friction=0.02, load_mass=0, load_pos=0):
        self.x = x  # Позиция по горизонтали
        self.y = WINDOW_HEIGHT - 100  # Фиксированная высота
        self.mass = mass  # Масса тележки
        self.velocity = velocity  # Скорость
        self.color = color  # Цвет
        self.friction = friction  # Коэффициент трения
        self.load_mass = load_mass  # Масса груза
        self.load_pos = load_pos  # Позиция груза относительно центра (-1 слева, 0 центр, 1 справа)
        self.angular_velocity = 0  # Угловая скорость
        self.width = 60
        self.height = 40
        self.wheel_radius = 10
        self.rotation_angle = 0  # Угол поворота груза

    @property
    def total_mass(self):
        return self.mass + self.load_mass

    @property
    def moment_of_inertia(self):
        # Простое приближение момента инерции
        return self.load_mass * (20 ** 2) if self.load_mass > 0 else 0

    def apply_friction(self, dt):
        if abs(self.velocity) > 0.01:
            friction_force = self.friction * self.total_mass * 9.8
            acceleration = -friction_force / self.total_mass
            self.velocity += acceleration * dt

            # Остановка при очень малой скорости
            if abs(self.velocity) < 0.1:
                self.velocity = 0

        # Торможение вращения
        if abs(self.angular_velocity) > 0.01:
            self.angular_velocity *= 0.99
            if abs(self.angular_velocity) < 0.01:
                self.angular_velocity = 0

    def update(self, dt):
        self.x += self.velocity * dt
        self.rotation_angle += self.angular_velocity * dt
        self.apply_friction(dt)

    def draw(self, surface):
        # Рисуем тележку
        cart_rect = pygame.Rect(self.x - self.width // 2, self.y - self.height, self.width, self.height)
        pygame.draw.rect(surface, self.color, cart_rect)

        # Рисуем колеса
        pygame.draw.circle(surface, BLACK, (int(self.x - self.width // 3), self.y), self.wheel_radius)
        pygame.draw.circle(surface, BLACK, (int(self.x + self.width // 3), self.y), self.wheel_radius)

        # Рисуем груз (если есть)
        if self.load_mass > 0:
            load_x = self.x + self.load_pos * 15
            load_y = self.y - self.height - 10
            pygame.draw.rect(surface, GREEN, (load_x - 10, load_y - 20, 20, 20))

            # Показываем вращение
            if abs(self.angular_velocity) > 0.1:
                font = pygame.font.Font(None, 20)
                text = font.render(f"ω: {self.angular_velocity:.1f}", True, BLACK)
                surface.blit(text, (load_x - 15, load_y - 40))

    def get_impulse(self):
        return self.total_mass * self.velocity


# Параметры симуляции
def reset_simulation():
    global cart1, cart2, time, e, show_vectors, paused, collision_occurred

    # Создаем тележки с начальными параметрами
    cart1 = Cart(200, mass1, velocity1, RED, friction1, load_mass1, load_pos1)
    cart2 = Cart(800, mass2, velocity2, BLUE, friction2, load_mass2, load_pos2)

    time = 0
    collision_occurred = False


# Начальные параметры (можно изменять)
mass1 = 1.0
mass2 = 1.0
velocity1 = 2.0
velocity2 = -1.0
friction1 = 0.01
friction2 = 0.01
e = 0.8  # Коэффициент восстановления (0-1)
load_mass1 = 0.5
load_pos1 = 0.5
load_mass2 = 0.5
load_pos2 = -0.5

reset_simulation()

# Интерфейс
font = pygame.font.Font(None, 24)
show_vectors = True
paused = False
clock = pygame.time.Clock()
dt = 0.1  # Шаг времени


def draw_controls(surface):
    y_pos = 10
    params = [
        f"Масса 1: {mass1:.1f} кг",
        f"Скорость 1: {velocity1:.1f} м/с",
        f"Трение 1: {friction1:.2f}",
        f"Груз 1: {load_mass1:.1f} кг, Поз: {load_pos1:.1f}",
        f"Масса 2: {mass2:.1f} кг",
        f"Скорость 2: {velocity2:.1f} м/с",
        f"Трение 2: {friction2:.2f}",
        f"Груз 2: {load_mass2:.1f} кг, Поз: {load_pos2:.1f}",
        f"Коэф. восстановления (e): {e:.2f}",
        f"Импульс системы: {cart1.get_impulse() + cart2.get_impulse():.2f} кг·м/с",
        "Управление: SPACE - пауза, R - сброс, V - векторы, 1-8 - параметры"
    ]

    for param in params:
        text = font.render(param, True, BLACK)
        surface.blit(text, (10, y_pos))
        y_pos += 20


def handle_collision(cart1, cart2):
    global collision_occurred

    if collision_occurred:
        return

    # Проверяем столкновение
    distance = abs(cart1.x - cart2.x)
    min_distance = (cart1.width + cart2.width) // 2

    if distance < min_distance:
        collision_occurred = True

        # Сохраняем импульсы до столкновения
        p1_before = cart1.get_impulse()
        p2_before = cart2.get_impulse()
        total_p_before = p1_before + p2_before

        # 1. Закон сохранения импульса
        m1, m2 = cart1.total_mass, cart2.total_mass
        v1, v2 = cart1.velocity, cart2.velocity

        # 2. Коэффициент восстановления
        # e = (v2' - v1') / (v1 - v2)

        # Решаем систему уравнений:
        # 1) m1*v1 + m2*v2 = m1*v1' + m2*v2' (сохранение импульса)
        # 2) e = (v2' - v1') / (v1 - v2)

        # Решение:
        v1_new = (m1 * v1 + m2 * v2 + m2 * e * (v2 - v1)) / (m1 + m2)
        v2_new = (m1 * v1 + m2 * v2 + m1 * e * (v1 - v2)) / (m1 + m2)

        cart1.velocity = v1_new
        cart2.velocity = v2_new

        # Учет вращения (если груз смещен)
        # При ударе возникает момент силы, если груз не в центре
        if cart1.load_mass > 0:
            # Импульс силы при ударе: F * dt = Δp = m1*(v1_new - v1)
            impulse = m1 * (v1_new - v1)
            # Момент силы: τ = r × F = load_pos * impulse (упрощенно)
            torque = cart1.load_pos * 0.2 * impulse  # 0.2 - плечо

            if cart1.moment_of_inertia > 0:
                cart1.angular_velocity += torque / cart1.moment_of_inertia

        if cart2.load_mass > 0:
            impulse = m2 * (v2_new - v2)
            torque = cart2.load_pos * 0.2 * impulse

            if cart2.moment_of_inertia > 0:
                cart2.angular_velocity += torque / cart2.moment_of_inertia

        # Проверка сохранения импульса
        p1_after = cart1.get_impulse()
        p2_after = cart2.get_impulse()
        total_p_after = p1_after + p2_after

        print(f"\nСтолкновение:")
        print(f"До: p1={p1_before:.2f}, p2={p2_before:.2f}, сумма={total_p_before:.2f}")
        print(f"После: p1={p1_after:.2f}, p2={p2_after:.2f}, сумма={total_p_after:.2f}")
        print(f"Разница: {abs(total_p_after - total_p_before):.2f}")


# Основной цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_SPACE:
                paused = not paused
            elif event.key == K_r:
                reset_simulation()
            elif event.key == K_v:
                show_vectors = not show_vectors
            # Изменение параметров клавишами 1-8
            elif event.key == K_1:
                mass1 = max(0.1, mass1 + (0.1 if pygame.key.get_pressed()[K_LSHIFT] else -0.1))
                reset_simulation()
            elif event.key == K_2:
                velocity1 += 0.2 if pygame.key.get_pressed()[K_LSHIFT] else -0.2
                reset_simulation()
            elif event.key == K_3:
                friction1 = max(0, min(0.2, friction1 + (0.005 if pygame.key.get_pressed()[K_LSHIFT] else -0.005)))
                reset_simulation()
            elif event.key == K_4:
                load_pos1 = max(-1, min(1, load_pos1 + (0.1 if pygame.key.get_pressed()[K_LSHIFT] else -0.1)))
                reset_simulation()
            elif event.key == K_5:
                mass2 = max(0.1, mass2 + (0.1 if pygame.key.get_pressed()[K_LSHIFT] else -0.1))
                reset_simulation()
            elif event.key == K_6:
                velocity2 += 0.2 if pygame.key.get_pressed()[K_LSHIFT] else -0.2
                reset_simulation()
            elif event.key == K_7:
                friction2 = max(0, min(0.2, friction2 + (0.005 if pygame.key.get_pressed()[K_LSHIFT] else -0.005)))
                reset_simulation()
            elif event.key == K_8:
                e = max(0, min(1, e + (0.05 if pygame.key.get_pressed()[K_LSHIFT] else -0.05)))
                reset_simulation()

    if not paused:
        # Обновление физики
        handle_collision(cart1, cart2)
        cart1.update(dt)
        cart2.update(dt)
        time += dt

    # Отрисовка
    window.fill(WHITE)

    # Рисуем рельсы
    pygame.draw.rect(window, GRAY, (0, WINDOW_HEIGHT - 20, WINDOW_WIDTH, 20))

    # Рисуем тележки
    cart1.draw(window)
    cart2.draw(window)

    # Показываем векторы скоростей
    if show_vectors:
        def draw_vector(surface, x, y, vx, vy, color, scale=10):
            if abs(vx) < 0.1 and abs(vy) < 0.1:
                return
            end_x = x + vx * scale
            end_y = y + vy * scale
            pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)
            # Стрелочка
            angle = math.atan2(vy, vx)
            pygame.draw.line(surface, color, (end_x, end_y),
                             (end_x - 10 * math.cos(angle + math.pi / 6), end_y - 10 * math.sin(angle + math.pi / 6)),
                             2)
            pygame.draw.line(surface, color, (end_x, end_y),
                             (end_x - 10 * math.cos(angle - math.pi / 6), end_y - 10 * math.sin(angle - math.pi / 6)),
                             2)


        # Векторы скоростей
        draw_vector(window, cart1.x, cart1.y - cart1.height - 30, cart1.velocity, 0, RED)
        draw_vector(window, cart2.x, cart2.y - cart2.height - 30, cart2.velocity, 0, BLUE)

        # Векторы импульсов
        draw_vector(window, cart1.x, cart1.y - cart1.height - 60,
                    cart1.get_impulse() / cart1.total_mass, 0, (150, 0, 0), 5)
        draw_vector(window, cart2.x, cart2.y - cart2.height - 60,
                    cart2.get_impulse() / cart2.total_mass, 0, (0, 0, 150), 5)

    # Рисуем интерфейс
    draw_controls(window)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()