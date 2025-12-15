import pygame
import random
import asyncio
import os

# 初始化 Pygame
pygame.init()

# 常量定义
WIDTH, HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS_BASE = 10
FPS_MAX = 20

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GOLD = (255, 215, 0)
GREEN_LIGHT = (0, 255, 0)
GREEN_DARK = (0, 150, 0)

# 字体
FONT_LARGE = pygame.font.SysFont(None, 50)
FONT_MEDIUM = pygame.font.SysFont(None, 35)
FONT_SMALL = pygame.font.SysFont(None, 25)

class Snake:
    def __init__(self):
        self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (0, -1)  # 初始向上
        self.grow = False

    def update(self, grid_width, grid_height):
        head = self.body[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        # 边界穿透
        new_head = (new_head[0] % grid_width, new_head[1] % grid_height)
        self.body.insert(0, new_head)
        if not self.grow:
            self.body.pop()
        self.grow = False

    def collide_self(self):
        return self.body[0] in self.body[1:]

    def set_direction(self, new_dir):
        if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
            self.direction = new_dir

    def draw(self, screen):
        for i, segment in enumerate(self.body):
            alpha = i / len(self.body)
            color = (int(GREEN_LIGHT[0] * (1 - alpha) + GREEN_DARK[0] * alpha),
                     int(GREEN_LIGHT[1] * (1 - alpha) + GREEN_DARK[1] * alpha),
                     int(GREEN_LIGHT[2] * (1 - alpha) + GREEN_DARK[2] * alpha))
            rect = pygame.Rect(segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

class Food:
    def __init__(self, grid_width, grid_height):
        self.types = [
            ('normal', RED, 1),
            ('special', BLUE, 5),
            ('rare', GOLD, 10)
        ]
        self.reset(grid_width, grid_height)

    def reset(self, grid_width, grid_height):
        probs = [0.7, 0.25, 0.05]
        food_type = random.choices(self.types, weights=probs)[0]
        self.pos = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
        self.type_name, self.color, self.score = food_type
        self.pulse = 0

    def update(self):
        self.pulse += 0.2

    def draw(self, screen):
        size = GRID_SIZE + int(3 * abs((self.pulse % 2) - 1))
        offset = (GRID_SIZE - size) // 2
        rect = pygame.Rect(self.pos[0] * GRID_SIZE + offset, self.pos[1] * GRID_SIZE + offset, size, size)
        pygame.draw.ellipse(screen, self.color, rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('网页版贪吃蛇')
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.snake = Snake()
        self.food = Food(GRID_WIDTH, GRID_HEIGHT)
        self.score = 0
        self.lives = 3
        self.speed = FPS_BASE
        self.speed_boost_end = 0
        self.paused = False
        self.game_over = False
        self.highscore = self.load_highscore()

    def load_highscore(self):
        try:
            with open('highscore.txt', 'r') as f:
                return int(f.read().strip())
        except:
            return 0

    def save_highscore(self):
        if self.score > self.highscore:
            self.highscore = self.score
            with open('highscore.txt', 'w') as f:
                f.write(str(self.highscore))

    def update(self):
        if self.paused or self.game_over:
            return

        self.snake.update(GRID_WIDTH, GRID_HEIGHT)
        self.food.update()

        if self.snake.body[0] == self.food.pos:
            self.score += self.food.score
            self.snake.grow = True
            self.food.reset(GRID_WIDTH, GRID_HEIGHT)
            if self.score % 10 == 0:
                self.speed = min(self.speed + 1, FPS_MAX)

        current_time = pygame.time.get_ticks()
        effective_speed = self.speed * 1.5 if self.food.type_name == 'special' and current_time < self.speed_boost_end else self.speed
        if self.food.type_name == 'special':
            self.speed_boost_end = current_time + 5000

        if self.snake.collide_self():
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.save_highscore()
            else:
                self.snake.body = self.snake.body[:1]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_UP:
                    self.snake.set_direction((0, -1))
                elif event.key == pygame.K_DOWN:
                    self.snake.set_direction((0, 1))
                elif event.key == pygame.K_LEFT:
                    self.snake.set_direction((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    self.snake.set_direction((1, 0))
        return True

    def draw(self):
        self.screen.fill(WHITE)
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, (240, 240, 240), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, (240, 240, 240), (0, y), (WIDTH, y))

        self.snake.draw(self.screen)
        self.food.draw(self.screen)

        score_text = FONT_MEDIUM.render(f"分数: {self.score}", True, BLACK)
        lives_text = FONT_MEDIUM.render(f"生命: {self.lives}", True, BLACK)
        high_text = FONT_SMALL.render(f"最高分: {self.highscore}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (10, 50))
        self.screen.blit(high_text, (10, 90))

        if self.paused:
            pause_text = FONT_LARGE.render("暂停 (P继续)", True, BLACK)
            self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2))

        if self.game_over:
            over_text = FONT_LARGE.render("游戏结束", True, RED)
            final_text = FONT_MEDIUM.render(f"最终分数: {self.score}", True, BLACK)
            restart_text = FONT_SMALL.render("空格重新开始 / ESC退出", True, BLACK)
            self.screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 60))
            self.screen.blit(final_text, (WIDTH // 2 - final_text.get_width() // 2, HEIGHT // 2))
            self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.flip()

    def draw_menu(self):
        self.screen.fill(WHITE)
        title = FONT_LARGE.render("贪吃蛇网页版", True, GREEN_LIGHT)
        start_text = FONT_MEDIUM.render("空格开始游戏", True, BLACK)
        quit_text = FONT_SMALL.render("ESC退出", True, BLACK)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 50))
        self.screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
        self.screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 50))
        pygame.display.flip()

    async def run(self):
        running = True
        waiting = True  # 从主菜单开始
        while running:
            if waiting:
                self.draw_menu()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.reset()
                            waiting = False
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                await asyncio.sleep(0)
                continue

            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.speed)
            await asyncio.sleep(0)

async def main():
    game = Game()
    await game.run()

if __name__ == "__main__":
    asyncio.run(main())