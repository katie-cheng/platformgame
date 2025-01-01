import pygame
import os
import random
import csv

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
SCROLL_THRESH = 200  # how close the player can get to the edge before scrolling
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21

level = 1
screen_scroll = 0
bg_scroll = 0

# Player action variables
moving_left = False
moving_right = False
shoot = False

# Load images

img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()

# Define colors
BG = (144, 201, 120)
RED = (255, 0, 0)

# Background images
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()

# Draw background with parallax effect
def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, (0, 0, 0), (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y, 150 * ratio, 20))

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
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0: # if I just shot, I need to wait before I can shoot again
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # Step 11: Reset movement variables
        screen_scroll = 0
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
            self.vel_y = -13
            self.jump = False
            self.in_air = True

        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10 # terminal velocity
        dy += self.vel_y

        #check for collision
        for tile in world.obstacle_list:
			#check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
				#if the ai has hit a wall then make it turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
			#check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#check if below the ground, i.e. jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
				#check if above the ground, i.e. falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        #check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0
                    
        # Step 13: Update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
				or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll

    def shoot(self):
        # method to shoot bullets, for ANY soldier, not just player
        if self.shoot_cooldown == 0 and self.ammo > 0: # have at least one bullet to shoot with
            self.shoot_cooldown = 20 # reset the cooldown
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction) # spawn bullet in front of the player's gun but not on top of the player so that it would take damage
            bullet_group.add(bullet)
            # reduce ammo
            self.ammo -= 1

    def ai(self):
        # Logic for enemy AI
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
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
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    # logic for AI to be moving
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1) # 1 for run animation
                    self.move_counter += 1
                    # update AI vision as enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    # if idling and counter is up, stop idling
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
        #scroll
        self.rect.x += screen_scroll

    def update_animation(self):
        # Step 14: Update animation
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            if self.action != 3 or self.frame_index < len(self.animation_list[self.action]) - 1:
                self.frame_index += 1
        # reset back to the start of the animation
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:  # Death animation stops at the last frame
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
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
        
        for tile in world.obstacle_list:
             if tile[1].colliderect(self.rect):
                self.kill()

        # check collision with characters with pygame spritecollide
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill() # kill the bullet if it collides with live player
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()

class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])
		#iterate through each value in level data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)
					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					elif tile >= 9 and tile <= 10:
						water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
						water_group.add(water)
					elif tile >= 11 and tile <= 14:
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)
					elif tile == 15: # create player
						player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20)
						health_bar = HealthBar(10, 10, player.health, player.health)
					elif tile == 16: # create enemies
						enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20)
						enemy_group.add(enemy)
					elif tile == 17: # create ammo box
						pass
					elif tile == 18: # create grenade box
						pass
					elif tile == 19: # create health box
						pass
					elif tile == 20: # create exit
						pass

		return player, health_bar

	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll
          
class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll
          
class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

# Create sprite groups
bullet_group = pygame.sprite.Group() # keeping all instances of a class together in a list
enemy_group = pygame.sprite.Group() 
water_group = pygame.sprite.Group() 
decoration_group = pygame.sprite.Group() 
exit_group = pygame.sprite.Group()

# Create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)

# Load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

world = World()
player, health_bar = world.process_data(world_data)

# Step 3: Game Loop
run = True
while run:
    # Step 14: Set framerate
    clock.tick(FPS)

    draw_bg()
    world.draw()

    player.update()
    # Step 8: Draw the player
    player.draw()
    health_bar.draw(player.health)

    # Spawn enemies in groups
    for enemy in enemy_group:
        enemy.ai()
        enemy.update()
        enemy.draw()

    # Update and draw groups
    bullet_group.update()
    decoration_group.update()
    water_group.update()
    exit_group.update()

    bullet_group.draw(screen)
    decoration_group.draw(screen)
    water_group.draw(screen)
    exit_group.update(screen)

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
        screen_scroll = player.move(moving_left, moving_right)
        bg_scroll -= screen_scroll

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