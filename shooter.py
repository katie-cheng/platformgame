# Step 1: Imports
import pygame
import os

pygame.init()

# Step 2: Set up display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 720

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

# Step 14: Set framerate
clock = pygame.time.Clock()
FPS = 60

# define game variables
GRAVITY = 0.75

# Step 9: Define player action variables
moving_left = False
moving_right = False

# Step 15: Draw background
BG = (144, 201, 120)
RED = (255, 0, 0)

# Step 15: Draw background
def draw_bg():
    screen.fill(BG)
    pygame.draw.line(screen, RED, (0, 300), (SCREEN_WIDTH, 300)) # floor

# Step 6: Add a class for the soldier character
class Soldier(pygame.sprite.Sprite): # Sprite class is built into pygame
    def __init__(self, char_type, x, y, scale, speed): # Constructor
        pygame.sprite.Sprite.__init__(self) # Inherit functionality from pygame's Sprite class
        
        self.alive = True
        
        self.char_type = char_type

        # Step 10: Add movement variables
        self.speed = speed

        self.direction = 1
        self.vel_y = 0 #no vertical velocity to begin with
        self.jump = False
        self.in_air = True # assumes character is in the air until it isn't
        self.flip = False

        self.animation_list = []
        self.frame_index = 0
        self.action = 0

        self.update_time = pygame.time.get_ticks()
        
        # Load all images for the players in one place
        animation_types = ['Idle', 'Run', 'Jump'] # iterate through this
        
        for animation in animation_types:

            # Reset temporary list of images
            # Idle Bobbing animation
            temp_list = []

            # Count number of files in folder (frames in animation)
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))

            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png')
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)

            self.animation_list.append(temp_list)

        '''
        # Run animation
        temp_list = []
        for i in range(6):
            img = pygame.image.load(f'img/{self.char_type}/Run/{i}.png')
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            temp_list.append(img)
        
        # List of lists
        self.animation_list.append(temp_list)
        '''
        
        # Access the correct type of animation AND the correct frame
        self.image = self.animation_list[self.action][self.frame_index]

        # img = pygame.image.load(f'img/{self.char_type}/Idle/0.png')
        # anything that starts with self is an instance variable, or a variable that belongs to the object
        # self.image = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def move(self, moving_left, moving_right):
        # Step 11: Reset movement variables
        dx = 0
        dy = 0

        # Step 12: Assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        
        # Jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -12
            self.jump = False
            self.in_air = True

        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10 # terminal velocity
        dy += self.vel_y

        # check collision with floor
        if self.rect.bottom + dy > 300:
            dy = 300 - self.rect.bottom
            self.in_air = False

        # Step 13: Update rectangle position
        self.rect.x += dx
        self.rect.y += dy

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        # update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # reset back to the start of the animation
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def update_action(self, new_action):
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    # Step 8: Draw the character as a method
    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


# Step 7: Create a player object of the Solider class
player = Soldier('player', 200, 200, 3, 5)
# player2 = Soldier(400, 200, 3)

'''
# Step 4: Spawn character
x = 200
y = 200
scale = 3
img = pygame.image.load('img/player/Idle/0.png')
img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
rect = img.get_rect() # This is the actual rectangle of the character
rect.center = (x, y) # Center the rectangle where the character image is
'''

# Step 3: Game Loop
run = True
while run:

    # Step 14: Set framerate
    clock.tick(FPS)

    draw_bg()

    # Step 4: Spawn character
    # screen.blit(img, rect)
    
    # Step 7: Draw the player
    # screen.blit(player.image, player.rect)

    player.update_animation()
    # Step 8: Draw the player
    player.draw()
    # player2.draw()

    # Update player actions
    if player.alive: # only update if player is alive
        if player.in_air:
            player.update_action(2) # jump
        elif moving_left or moving_right:
            player.update_action(1) # run
        else:
            player.update_action(0) # idle

        player.move(moving_left, moving_right)

    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            run = False


        # Keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            # jump
            if event.key == pygame.K_w and player.alive:
                player.jump = True

            # Escape key escapes the game
            if event.key == pygame.K_ESCAPE:
                run = False
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
                

    # Step 5: Update display
    pygame.display.update()

pygame.quit()

