import pygame
import os
import random

pygame.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

# Set framerate
clock = pygame.time.Clock()
FPS = 60

# Game variables
GRAVITY = 0.75

# Player action variables
moving_left = False
moving_right = False
shoot = False

# Load images
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()

# Define colors
BG = (144, 201, 120)
RED = (255, 0, 0)

# Background images
bg_list = []
bg_list.append(pygame.image.load('img/background/sky_cloud.png'))
bg_list.append(pygame.image.load('img/background/mountain.png'))
bg_list.append(pygame.image.load('img/background/pine2.png'))
bg_list.append(pygame.image.load('img/background/pine1.png'))

def draw_bg():
    screen.fill(BG)
    stagger = 0
    for bg_image in bg_list:
        screen.blit(bg_image, (0, stagger))
        stagger += 115
    pygame.draw.line(screen, RED, (0, 300), (SCREEN_WIDTH, 300))

class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        # Step 10: Add movement variables
        self.speed = speed
        # Ammo counts
        self.ammo = ammo
        self.start_ammo = ammo
        # shoot cooldown
        self.shoot_cooldown = 0
        # health
        self.health = 100
        self.max_health = self.health # useful for health bars
        self.direction = 1
        self.vel_y = 0 # no vertical velocity to begin with
        self.jump = False
        self.in_air = True # assumes character is in the air until it isn't
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20) # AI vision rectangle
        self.idling = False
        self.idling_counter = 0

        # Load all images for the players in one place
        animation_types = ['Idle', 'Run', 'Jump', 'Death'] # iterate through this
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        # Access the correct type of animation AND the correct frame
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0: # if I just shot, I need to wait before I can shoot again
            self.shoot_cooldown -= 1

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
        if self.jump and not self.in_air:
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

    def shoot(self):
        # method to shoot bullets, for ANY soldier, not just player
        if self.shoot_cooldown == 0 and self.ammo > 0: # have at least one bullet to shoot with
            self.shoot_cooldown = 20 # reset the cooldown
            bullet = Bullet(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery, self.direction) # spawn bullet in front of the player's gun but not on top of the player so that it would take damage
            bullet_group.add(bullet)
            # reduce ammo
            self.ammo -= 1

    def ai(self):
        # Logic for enemy AI
        if self.alive and player.alive:
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0) # 0 for idle
                self.idling = True
                self.idling_counter = 50

            # check if ai is near player
            if self.vision.colliderect(player.rect):
                # stop running and face the player
                self.update_action(0) # 0 for idle
                self.shoot()
            else:
                if not self.idling:
                    # logic for AI to be moving
                    ai_moving_right = self.direction == 1
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1) # 1 for run animation
                    self.move_counter += 1
                    # update AI vision as enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    if self.move_counter > 40:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    # if idling and counter is up, stop idling
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

    def update_animation(self):
        # Step 14: Update animation
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
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
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0: # if health is less than or equal to 0
            self.health = 0 # set health to 0
            self.speed = 0  # stop moving
            self.alive = False
            self.update_action(3) # runs player death animation

    # Step 8: Draw the character as a method
    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10 # bullet speed, same for all
        self.image = bullet_img # image of the bullet, already loaded
        self.rect = self.image.get_rect() # rectangle of the bullet
        self.rect.center = (x, y) # center of the bullet, easier to control than the rectangle
        self.direction = direction # direction the bullet is facing

    def update(self):
        # move bullet
        self.rect.x += self.direction * self.speed
        # check if bullet has gone off screen and delete them if they are
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill() # built into pygame, removed bullet from group

        # check collision with characters with pygame spritecollide
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill() # kill the bullet if it collides with live player
        if pygame.sprite.spritecollide(enemy, bullet_group, False):
            if enemy.alive:
                enemy.health -= 25 # enemy takes more damage
                self.kill()

# Create sprite groups
bullet_group = pygame.sprite.Group() # keeping all instances of a class together in a list

# Step 7: Create a player object of the Solider class
player = Soldier('player', 200, 200, 3, 5, 20)
enemy = Soldier('enemy', 400, 200, 3, 2, 10)

# Step 3: Game Loop
run = True
while run:
    # Step 14: Set framerate
    clock.tick(FPS)

    draw_bg()

    player.update()
    # Step 8: Draw the player
    player.draw()

    # Update and draw groups
    bullet_group.update()
    bullet_group.draw(screen)

    # Update player actions
    if player.alive: # only update if player is alive
        if shoot:
            player.shoot()

        if player.in_air:
            player.update_action(2) # jump
        elif moving_left or moving_right:
            player.update_action(1) # run
        else:
            player.update_action(0) # idle

        player.move(moving_left, moving_right)

    enemy.ai()
    enemy.update()
    enemy.draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        # KEYBOARD PRESSES
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            # jump
            if event.key == pygame.K_w and player.alive:
                player.jump = True

            # Escape key escapes the game
            if event.key == pygame.K_ESCAPE:
                run = False

        # KEYBOARD BUTTON RELEASES
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False

    # Step 5: Update display
    pygame.display.update()

pygame.quit()