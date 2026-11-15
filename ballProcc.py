import threading
import pygame
import sys
import random
import time
import urllib.request
import json

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Jumping Balls")

COLORS = [
    (255, 99, 71),  # Red
    (46, 204, 113),  #  Green
    (52, 152, 219),  #  Blue
    (241, 196, 15),  # Yellow
    (155, 89, 182),  # Purple
    (230, 126, 34),  # Orange
    (26, 188, 156),  # torkiz
    (255, 192, 203)  # Pink
]
BLACK = (0, 0, 0)

active_balls = []
balls_lock = threading.Lock()


def report_active_count():
    with balls_lock:
        print(f"Current Active Threads/Balls: {len(active_balls)}")


class AIAgentThread(threading.Thread):
    def __init__(self, start_id):
        super().__init__()
        self.daemon = True
        self.next_ball_id = start_id
        self.is_running = True
        self.model = "llama3.2:1b"
        self.url = "http://localhost:11434/api/generate"

    def ask_ollama(self, active_count):
        prompt = (
            f"You are the Game Director for a jumping balls game. "
            f"There are currently {active_count} balls active on screen. "
            f"Choose ONE action from this exact list: ADD_BALL, CHANGE_COLOR, SPEED_UP, SLOW_DOWN. "
            f"If there are 2 or fewer balls, prefer ADD_BALL. Otherwise vary your choices. "
            f"Reply with ONLY the single action word and nothing else."
        )
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            req = urllib.request.Request(
                self.url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["response"].strip().upper()
        except Exception as e:
            print(f"AI agent error: {e}")
            return "NONE"

    def run(self):
        print(" ai Game Director started.")
        while self.is_running:
            time.sleep(3)  #wait 3 seconds

            with balls_lock:
                count = len(active_balls)

            if count == 0:
                break

            decision = self.ask_ollama(count)
            print(f"ai decision: {decision}")

            with balls_lock:
                if len(active_balls) == 0:
                    break

                if "ADD_BALL" in decision:
                    new_ball = BallThread(ball_id=self.next_ball_id)
                    self.next_ball_id += 1
                    active_balls.append(new_ball)
                    new_ball.start()
                    print(f"ai action: Spawned new Ball-{new_ball.ball_id}!")

                elif "CHANGE_COLOR" in decision:
                    target = random.choice(active_balls)
                    target.change_color()
                    print(f"ai action: Changed color of Ball-{target.ball_id}!")

                elif "SPEED_UP" in decision:
                    target = random.choice(active_balls)
                    target.change_speed(0.08)
                    print(f"ai action: Sped up Ball-{target.ball_id}!")

                elif "SLOW_DOWN" in decision:
                    target = random.choice(active_balls)
                    target.change_speed(0.4)
                    print(f"ai action: Slowed down Ball-{target.ball_id}!")



class BallThread(threading.Thread):
    def __init__(self, ball_id):
        super().__init__()
        self.ball_id = ball_id
        self.radius = 20

        # Initial random spawn
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)

        self.color = random.choice(COLORS)
        self.moves_left = random.randint(20, 50)
        self.delay = 0.2  #delay for ai to enter
        self.is_alive = True


    def change_color(self):
        """changes color"""
        self.color = random.choice(COLORS)


    def change_speed(self, new_delay):
        """changes speed"""
        self.delay = new_delay

    def run(self):
        """starting the thread of the ball"""
        print(f"START Thread -- {self.ball_id} started running.")
        report_active_count()

        while self.moves_left > 0 and self.is_alive:
            # Change location randomly all over the map
            self.x = random.randint(self.radius, WIDTH - self.radius)
            self.y = random.randint(self.radius, HEIGHT - self.radius)

            self.moves_left -= 1

            # Uses self.delay
            time.sleep(self.delay)

        with balls_lock:
            if self in active_balls:
                active_balls.remove(self)

        print(f"<-- [END] Thread-{self.ball_id} has finished.")
        report_active_count()
try:
    num_balls = int(input("How many balls do you want to create? "))
except ValueError:
    num_balls = 5

for i in range(num_balls):
    ball = BallThread(ball_id=i + 1)
    active_balls.append(ball)
    ball.start()

ai_agent = AIAgentThread(start_id=num_balls + 1)
ai_agent.start()

clock = pygame.time.Clock()
FPS = 60

running = True
initial_creation_done = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            ai_agent.is_running = False
            for ball in active_balls:
                ball.is_alive = False

    with balls_lock:
        if len(active_balls) == 0 and initial_creation_done:
            print("All threads finished. Closing application.")
            running = False

    screen.fill(BLACK)

    with balls_lock:
        for ball in active_balls:
            pygame.draw.circle(screen, ball.color, (int(ball.x), int(ball.y)), ball.radius)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()