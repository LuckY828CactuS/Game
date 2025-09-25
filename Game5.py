import pygame
import sys
import math
import numpy as np
from pygame.locals import *

# Инициализация Pygame
pygame.init()

# Параметры экрана
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Моделирование столкновения автомобилей")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)


class Car:
    def __init__(self, x, y, width, height, color, mass, velocity, angle=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.mass = mass
        self.velocity = list(velocity)
        self.angle = angle
        self.angular_velocity = 0
        # Момент инерции прямоугольника относительно центра масс
        self.moment_of_inertia = mass * (width ** 2 + height ** 2) / 12

    def get_corners(self):
        # Возвращает координаты углов автомобиля в мировых координатах
        corners = []
        half_w = self.width / 2
        half_h = self.height / 2
        for dx, dy in [(-half_w, -half_h), (half_w, -half_h),
                       (half_w, half_h), (-half_w, half_h)]:
            # Поворачиваем точку относительно центра
            rot_x = dx * math.cos(self.angle) - dy * math.sin(self.angle)
            rot_y = dx * math.sin(self.angle) + dy * math.cos(self.angle)
            corners.append((self.x + rot_x, self.y + rot_y))
        return corners

    def draw(self, surface):
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, self.color, (0, 0, self.width, self.height))

        # Центр масс (точка вращения)
        pygame.draw.circle(car_surface, BLACK, (self.width // 2, self.height // 2), 3)

        rotated_car = pygame.transform.rotate(car_surface, math.degrees(self.angle))
        car_rect = rotated_car.get_rect(center=(self.x, self.y))
        surface.blit(rotated_car, car_rect)

        # Рисуем вектор скорости
        speed = math.hypot(*self.velocity)
        if speed > 0.1:
            end_pos = (self.x + self.velocity[0] * 5, self.y + self.velocity[1] * 5)
            pygame.draw.line(surface, GREEN, (self.x, self.y), end_pos, 2)

        # Рисуем вектор вращения
        if abs(self.angular_velocity) > 0.01:
            radius = 20
            start_angle = math.pi / 2
            end_angle = start_angle + math.copysign(math.pi / 4, self.angular_velocity)
            pygame.draw.arc(surface, YELLOW,
                            (self.x - radius, self.y - radius, radius * 2, radius * 2),
                            start_angle, end_angle, 2)

    def move(self, dt, friction):
        # Обновляем позицию
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        self.angle += self.angular_velocity * dt

        # Применяем трение (разное для линейного и углового движения)
        linear_friction = friction ** dt
        angular_friction = 0.98 ** dt  # Дополнительное демпфирование вращения

        self.velocity[0] *= linear_friction
        self.velocity[1] *= linear_friction
        self.angular_velocity *= angular_friction

        # Обработка границ экрана с отскоком
        if self.x < 0:
            self.x = 0
            self.velocity[0] *= -0.7
            self.angular_velocity *= 0.7
        elif self.x > WIDTH:
            self.x = WIDTH
            self.velocity[0] *= -0.7
            self.angular_velocity *= 0.7

        if self.y < 0:
            self.y = 0
            self.velocity[1] *= -0.7
            self.angular_velocity *= 0.7
        elif self.y > HEIGHT:
            self.y = HEIGHT
            self.velocity[1] *= -0.7
            self.angular_velocity *= 0.7


def find_collision_point(car1, car2):
    # Находим ближайшие точки между автомобилями
    min_dist = float('inf')
    collision_point = None

    # Проверяем все стороны обоих автомобилей
    for i in range(4):
        for j in range(4):
            # Получаем точки на контурах автомобилей
            c1 = car1.get_corners()
            c2 = car2.get_corners()

            # Проверяем расстояние между точками
            dist = math.hypot(c1[i][0] - c2[j][0], c1[i][1] - c2[j][1])
            if dist < min_dist:
                min_dist = dist
                collision_point = ((c1[i][0] + c2[j][0]) / 2, (c1[i][1] + c2[j][1]) / 2)

    return collision_point


def collide(car1, car2, e, scenario):
    m1, m2 = car1.mass, car2.mass
    v1, v2 = np.array(car1.velocity), np.array(car2.velocity)
    pos1, pos2 = np.array([car1.x, car1.y]), np.array([car2.x, car2.y])

    # Находим точку столкновения на контурах автомобилей
    collision_point = find_collision_point(car1, car2)
    if collision_point is None:
        return

    collision_point = np.array(collision_point)

    # Вектор нормали столкновения (от car1 к car2)
    normal = pos2 - pos1
    distance = np.linalg.norm(normal)
    if distance == 0:
        return

    normal = normal / distance

    # Векторы от центров масс к точке столкновения
    r1 = collision_point - pos1
    r2 = collision_point - pos2

    # Относительная скорость в точке столкновения (с учетом вращения)
    v1_collision = v1 + np.array([-car1.angular_velocity * r1[1], car1.angular_velocity * r1[0]])
    v2_collision = v2 + np.array([-car2.angular_velocity * r2[1], car2.angular_velocity * r2[0]])
    v_rel = np.dot((v1_collision - v2_collision), normal)

    # Эффективный коэффициент восстановления
    effective_e = e * min(1, np.linalg.norm(v1_collision - v2_collision) / 5)

    # Импульс
    j = -(1 + effective_e) * v_rel
    j /= (1 / m1 + 1 / m2 + (np.cross(r1, normal) ** 2) / car1.moment_of_inertia +
          (np.cross(r2, normal) ** 2) / car2.moment_of_inertia)
    impulse = j * normal

    # Обновляем линейные скорости
    car1.velocity = (v1 + impulse / m1).tolist()
    car2.velocity = (v2 - impulse / m2).tolist()

    # Обновляем угловые скорости (вращение относительно центра масс)
    torque1 = np.cross(r1, impulse)
    torque2 = np.cross(r2, impulse)

    car1.angular_velocity += torque1 / car1.moment_of_inertia
    car2.angular_velocity -= torque2 / car2.moment_of_inertia

    # Для второго сценария усиливаем вращение
    if scenario == 2:
        speed_factor = min(1, np.linalg.norm(v1_collision - v2_collision) / 8)
        car1.angular_velocity *= 1.3 * speed_factor
        car2.angular_velocity *= 1.3 * speed_factor

    # Ограничиваем максимальное вращение
    max_rotation = 0.8
    car1.angular_velocity = max(-max_rotation, min(max_rotation, car1.angular_velocity))
    car2.angular_velocity = max(-max_rotation, min(max_rotation, car2.angular_velocity))


def check_collision(car1, car2):
    # Проверка столкновения с помощью Separating Axis Theorem (SAT)
    def project(poly, axis):
        dots = [np.dot(p, axis) for p in poly]
        return min(dots), max(dots)

    def overlap(a, b):
        return a[0] <= b[1] and b[0] <= a[1]

    poly1 = car1.get_corners()
    poly2 = car2.get_corners()

    # Проверяем все возможные оси
    axes = []
    for i in range(len(poly1)):
        edge = np.subtract(poly1[(i + 1) % len(poly1)], poly1[i])
        axes.append(np.array([-edge[1], edge[0]]))

    for i in range(len(poly2)):
        edge = np.subtract(poly2[(i + 1) % len(poly2)], poly2[i])
        axes.append(np.array([-edge[1], edge[0]]))

    # Нормализуем все оси
    axes = [a / np.linalg.norm(a) for a in axes]

    for axis in axes:
        proj1 = project(poly1, axis)
        proj2 = project(poly2, axis)

        if not overlap(proj1, proj2):
            return False

    return True


def draw_ui(screen, car1, car2, e, friction, scenario):
    font = pygame.font.SysFont(None, 24)

    scenarios = [
        "1: Удар по центру",
        "2: Удар сбоку (с вращением)",
        "3: Малый удар",
        "4: Сильный удар"
    ]

    texts = [
        f"Автомобиль 1: m={car1.mass}кг, v=({car1.velocity[0]:.1f}, {car1.velocity[1]:.1f}) ω={math.degrees(car1.angular_velocity):.1f}°",
        f"Автомобиль 2: m={car2.mass}кг, v=({car2.velocity[0]:.1f}, {car2.velocity[1]:.1f}) ω={math.degrees(car2.angular_velocity):.1f}°",
        f"Коэф. восстановления: {e:.1f} | Трение: {friction:.2f}",
        f"Сценарий: {scenarios[scenario - 1]}",
        "Управление: 1-4 - сценарии, Q/W - масса 1, A/S - скорость 1",
        "E/D - масса 2, Z/X - скорость 2, C/V - упругость, F/G - трение",
        "R - сброс, SPACE - пауза"
    ]

    for i, text in enumerate(texts):
        screen.blit(font.render(text, True, BLACK), (10, 10 + i * 25))


def create_cars(scenario, m1, m2, v1, v2):
    if scenario == 1:
        return (
            Car(300, HEIGHT // 2, 60, 30, RED, m1, (v1, 0)),
            Car(700, HEIGHT // 2, 60, 30, BLUE, m2, (-v2, 0))
        )
    elif scenario == 2:
        return (
            Car(300, HEIGHT // 2 + 40, 60, 30, RED, m1, (v1, 0)),
            Car(700, HEIGHT // 2 - 20, 60, 30, BLUE, m2, (-v2 * 0.8, 0.5))
        )
    elif scenario == 3:
        return (
            Car(300, HEIGHT // 2, 60, 30, RED, m1, (v1 / 2, 0)),
            Car(700, HEIGHT // 2, 60, 30, BLUE, m2, (-v2 / 2, 0))
        )
    elif scenario == 4:
        return (
            Car(300, HEIGHT // 2, 80, 40, RED, int(m1 * 1.5), (v1 * 1.5, 0)),
            Car(700, HEIGHT // 2, 50, 25, BLUE, int(m2 / 1.5), (-v2 * 1.5, 0))
        )


def main():
    clock = pygame.time.Clock()
    dt = 0.1

    # Начальные параметры
    m1, m2 = 1500, 1200
    v1, v2 = 4, 3
    e = 0.5
    friction = 1
    scenario = 1
    running = False

    car1, car2 = create_cars(scenario, m1, m2, v1, v2)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:
                if event.key == K_r:
                    car1, car2 = create_cars(scenario, m1, m2, v1, v2)
                    running = False

                if event.key == K_SPACE:
                    running = not running

                if not running:
                    # Изменение параметров
                    if event.key == K_q: m1 += 100
                    if event.key == K_w: m1 = max(500, m1 - 100)
                    if event.key == K_a: v1 = min(10, v1 + 0.5)
                    if event.key == K_s: v1 = max(0, v1 - 0.5)

                    if event.key == K_e: m2 += 100
                    if event.key == K_d: m2 = max(500, m2 - 100)
                    if event.key == K_z: v2 = min(10, v2 + 0.5)
                    if event.key == K_x: v2 = max(0, v2 - 0.5)

                    if event.key == K_c: e = min(1, round(e + 0.1, 1))
                    if event.key == K_v: e = max(0, round(e - 0.1, 1))

                    if event.key == K_f: friction = min(0.99, round(friction + 0.01, 2))
                    if event.key == K_g: friction = max(0.9, round(friction - 0.01, 2))

                    if event.key in (K_1, K_2, K_3, K_4):
                        scenario = int(chr(event.key))

                    car1, car2 = create_cars(scenario, m1, m2, v1, v2)

        # Отрисовка
        screen.fill(WHITE)
        pygame.draw.rect(screen, GRAY, (0, HEIGHT // 2 - 100, WIDTH, 200))

        if running:
            car1.move(dt, friction)
            car2.move(dt, friction)

            if check_collision(car1, car2):
                collide(car1, car2, e, scenario)

        car1.draw(screen)
        car2.draw(screen)
        draw_ui(screen, car1, car2, e, friction, scenario)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()