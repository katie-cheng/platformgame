# Step 1: Imports
import pygame

pygame.init()

# Step 2: Set up display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

# Step 4: Spawn character
x = 200
y = 200
scale = 3
img = pygame.image.load('img/player/Idle/0.png')
img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
rect = img.get_rect() # This is the actual rectangle of the character
rect.center = (x, y) # Center the rectangle where the character image is

# Step 3: Game Loop
run = True
while run:

    # Step 4: Spawn character
    screen.blit(img, rect)

    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            run = False


    # Step 5: Update display
    pygame.display.update()

pygame.quit()

