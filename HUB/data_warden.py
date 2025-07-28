import pygame
import sys
import time
from database_class import Database as DB

# Initialize Pygame
pygame.init()

db = DB("MQTT_System", "postgres", "altahhan2004!")
#db.create_daily_log_entries()

#print (db.get_board_count(1))

last_state = db.get_last_state(1)
last_state = last_state.split(" ")
total_production = last_state[1]
loaded = last_state[2]

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Two Numbers with Circles")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# Fonts
font_large = pygame.font.SysFont(None, 120)

# Numbers to display
left_number = 42
right_number = 99

# Circle settings
circle_radius = 10
circle_spacing = 30
circle_y = 30
circle_start_x = WIDTH // 2 - circle_spacing

# Main loop
clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill(WHITE)

    # Draw 3 circles
    for i in range(3):
        circle_x = circle_start_x + i * circle_spacing
        pygame.draw.circle(screen, GRAY, (circle_x, circle_y), circle_radius)

    # Render numbers
    text1 = font_large.render(total_production, True, BLACK)
    text2 = font_large.render(loaded, True, BLACK)

    # Position numbers side by side
    spacing = 40
    total_width = text1.get_width() + spacing + text2.get_width()
    start_x = (WIDTH - total_width) // 2
    y_pos = HEIGHT // 2

    screen.blit(text1, (start_x, y_pos))
    screen.blit(text2, (start_x + text1.get_width() + spacing, y_pos))

    pygame.display.flip()
    clock.tick(60)
