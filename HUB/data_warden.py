import pygame
import sys
import time
from database_class import Database as DB
from config import config

# Initialize Pygame
pygame.init()

try:
    db_config = config.get_db_config()
    db = DB(**db_config)
except Exception as e:
    print(f"Failed to initialize database connection: {e}")
    sys.exit(1)

# Board ID to monitor (currently set to 1, will be expanded for multi-board monitoring)
BOARD_ID = 1

# Initialize production count
try:
    total_production = str(db.get_board_production_count(BOARD_ID))
except Exception as e:
    print(f"Failed to get initial production count: {e}")
    total_production = "0"

# Get last state for loaded count (keeping this for now)
last_state = db.get_last_state(BOARD_ID)
if last_state and len(last_state.split(" ")) >= 3:
    last_state_parts = last_state.split(" ")
    loaded = last_state_parts[2]
else:
    loaded = "0"

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Live Production Monitor - Board 1")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Fonts
font_large = pygame.font.SysFont(None, 120)
font_medium = pygame.font.SysFont(None, 48)
font_small = pygame.font.SysFont(None, 32)

# Circle settings
circle_radius = 10
circle_spacing = 30
circle_y = 30
circle_start_x = WIDTH // 2 - circle_spacing

# Update interval for live data (in seconds)
UPDATE_INTERVAL = 2.0
last_update_time = time.time()

# Main loop
clock = pygame.time.Clock()
while True:
    current_time = time.time()
    
    # Update production count periodically
    if current_time - last_update_time >= UPDATE_INTERVAL:
        try:
            total_production = str(db.get_board_production_count(BOARD_ID))
            last_update_time = current_time
        except Exception as e:
            print(f"Failed to update production count: {e}")
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill(WHITE)

    # Draw 3 circles (status indicators)
    for i in range(3):
        circle_x = circle_start_x + i * circle_spacing
        # Make the first circle green to indicate live monitoring
        color = GREEN if i == 0 else GRAY
        pygame.draw.circle(screen, color, (circle_x, circle_y), circle_radius)

    # Render production count (large, prominent display)
    production_text = font_large.render(total_production, True, BLACK)
    
    # Render labels
    production_label = font_medium.render("Production Count", True, BLUE)
    board_label = font_small.render(f"Board {BOARD_ID}", True, BLACK)
    
    # Position production count in center
    production_x = (WIDTH - production_text.get_width()) // 2
    production_y = HEIGHT // 2 - 20
    
    # Position labels
    label_x = (WIDTH - production_label.get_width()) // 2
    label_y = production_y - 80
    
    board_x = (WIDTH - board_label.get_width()) // 2
    board_y = production_y + 80
    
    # Draw everything
    screen.blit(production_label, (label_x, label_y))
    screen.blit(production_text, (production_x, production_y))
    screen.blit(board_label, (board_x, board_y))

    pygame.display.flip()
    clock.tick(60)
