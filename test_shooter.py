"""Comprehensive tests for shooter.py

Tests cover all classes and key functions:
- HealthBar: initialization and drawing
- Soldier: initialization, movement, shooting, AI, animation, death
- Bullet: initialization, movement, off-screen removal, collisions
- World: initialization, level data processing, drawing
- Decoration, Water, Exit: initialization and scroll updates
- draw_bg: background rendering
"""
import os
import pytest
import pygame
from unittest.mock import patch, MagicMock

import shooter


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _ensure_cwd():
    """Ensure the working directory is the repo root for image loading."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    original = os.getcwd()
    os.chdir(repo_dir)
    yield
    os.chdir(original)


@pytest.fixture()
def clean_groups():
    """Empty all sprite groups before and after the test."""
    shooter.bullet_group.empty()
    shooter.enemy_group.empty()
    shooter.water_group.empty()
    shooter.decoration_group.empty()
    shooter.exit_group.empty()
    yield
    shooter.bullet_group.empty()
    shooter.enemy_group.empty()
    shooter.water_group.empty()
    shooter.decoration_group.empty()
    shooter.exit_group.empty()


@pytest.fixture()
def mock_world():
    """Temporarily replace the global world with a lightweight mock."""
    original = shooter.world
    mock = MagicMock()
    mock.obstacle_list = []
    mock.level_length = 150
    shooter.world = mock
    yield mock
    shooter.world = original


@pytest.fixture()
def mock_player():
    """Temporarily replace the global player with a mock far off-screen."""
    original = shooter.player
    mock = MagicMock()
    mock.alive = False
    mock.rect = pygame.Rect(-5000, -5000, 1, 1)
    shooter.player = mock
    yield mock
    shooter.player = original


def make_soldier(char_type='player', x=200, y=200, scale=1.65, speed=5, ammo=20):
    """Helper to create a Soldier instance."""
    return shooter.Soldier(char_type, x, y, scale, speed, ammo)


# =========================================================================
# HealthBar Tests
# =========================================================================

class TestHealthBar:
    """Tests for the HealthBar class."""

    def test_init_stores_values(self):
        hb = shooter.HealthBar(10, 20, 100, 100)
        assert hb.x == 10
        assert hb.y == 20
        assert hb.health == 100
        assert hb.max_health == 100

    def test_init_partial_health(self):
        hb = shooter.HealthBar(0, 0, 50, 100)
        assert hb.health == 50
        assert hb.max_health == 100

    def test_draw_updates_health(self):
        hb = shooter.HealthBar(10, 10, 100, 100)
        hb.draw(75)
        assert hb.health == 75

    def test_draw_zero_health(self):
        hb = shooter.HealthBar(10, 10, 100, 100)
        hb.draw(0)
        assert hb.health == 0

    def test_draw_full_health(self):
        hb = shooter.HealthBar(10, 10, 100, 100)
        hb.draw(100)
        assert hb.health == 100

    def test_draw_renders_three_rectangles(self):
        hb = shooter.HealthBar(10, 10, 100, 100)
        with patch('pygame.draw.rect') as mock_rect:
            hb.draw(50)
            assert mock_rect.call_count == 3


# =========================================================================
# Soldier Tests
# =========================================================================

class TestSoldierInit:
    """Tests for Soldier.__init__."""

    def test_player_basic_attributes(self):
        s = make_soldier('player', 200, 200, 1.65, 5, 20)
        assert s.alive is True
        assert s.char_type == 'player'
        assert s.speed == 5
        assert s.ammo == 20
        assert s.start_ammo == 20
        assert s.shoot_cooldown == 0
        assert s.health == 100
        assert s.max_health == 100

    def test_player_movement_defaults(self):
        s = make_soldier()
        assert s.direction == 1
        assert s.vel_y == 0
        assert s.jump is False
        assert s.in_air is True
        assert s.flip is False

    def test_player_animation_defaults(self):
        s = make_soldier()
        assert s.frame_index == 0
        assert s.action == 0

    def test_player_rect_centered(self):
        s = make_soldier(x=300, y=400)
        assert s.rect.center == (300, 400)

    def test_player_dimensions(self):
        s = make_soldier()
        assert s.width == s.image.get_width()
        assert s.height == s.image.get_height()

    def test_enemy_attributes(self):
        s = make_soldier('enemy', 400, 300, 1.65, 2, 20)
        assert s.char_type == 'enemy'
        assert s.speed == 2
        assert s.idling is False
        assert s.idling_counter == 0
        assert s.move_counter == 0

    def test_animation_list_has_four_types(self):
        s = make_soldier()
        assert len(s.animation_list) == 4  # Idle, Run, Jump, Death

    def test_animation_frames_are_surfaces(self):
        s = make_soldier()
        for anim_type in s.animation_list:
            assert len(anim_type) > 0
            for frame in anim_type:
                assert isinstance(frame, pygame.Surface)

    def test_enemy_vision_rect(self):
        s = make_soldier('enemy')
        assert isinstance(s.vision, pygame.Rect)
        assert s.vision.width == 150
        assert s.vision.height == 20


class TestSoldierUpdate:
    """Tests for Soldier.update."""

    def test_decrements_cooldown(self):
        s = make_soldier()
        s.shoot_cooldown = 5
        s.update()
        assert s.shoot_cooldown == 4

    def test_cooldown_does_not_go_below_zero(self):
        s = make_soldier()
        s.shoot_cooldown = 0
        s.update()
        assert s.shoot_cooldown == 0

    def test_cooldown_from_one_to_zero(self):
        s = make_soldier()
        s.shoot_cooldown = 1
        s.update()
        assert s.shoot_cooldown == 0


class TestSoldierMove:
    """Tests for Soldier.move."""

    def test_move_left_sets_direction(self, mock_world):
        s = make_soldier()
        s.in_air = False
        s.move(True, False)
        assert s.flip is True
        assert s.direction == -1

    def test_move_right_sets_direction(self, mock_world):
        s = make_soldier()
        s.in_air = False
        s.move(False, True)
        assert s.flip is False
        assert s.direction == 1

    def test_stationary_no_horizontal_move(self, mock_world):
        s = make_soldier(x=300, y=300)
        s.in_air = False
        s.vel_y = 0
        initial_x = s.rect.x
        s.move(False, False)
        assert s.rect.x == initial_x  # no horizontal movement

    def test_gravity_applied(self, mock_world):
        s = make_soldier()
        assert s.vel_y == 0
        s.move(False, False)
        assert s.vel_y == shooter.GRAVITY

    def test_gravity_accumulates(self, mock_world):
        s = make_soldier()
        s.vel_y = 5.0
        s.move(False, False)
        assert s.vel_y == 5.0 + shooter.GRAVITY

    def test_terminal_velocity(self, mock_world):
        s = make_soldier()
        s.vel_y = 15  # above terminal velocity
        s.move(False, False)
        assert s.vel_y == 10

    def test_jump_sets_velocity(self, mock_world):
        s = make_soldier()
        s.jump = True
        s.in_air = False
        s.move(False, False)
        assert s.vel_y == -13 + shooter.GRAVITY
        assert s.jump is False
        assert s.in_air is True

    def test_cannot_jump_while_airborne(self, mock_world):
        s = make_soldier()
        s.jump = True
        s.in_air = True
        s.vel_y = 0
        s.move(False, False)
        # Only gravity applied, not jump velocity
        assert s.vel_y == shooter.GRAVITY

    def test_returns_screen_scroll(self, mock_world):
        s = make_soldier()
        result = s.move(False, False)
        assert isinstance(result, int)

    def test_player_bounded_left_edge(self, mock_world):
        s = make_soldier('player', x=5, y=200)
        s.rect.left = 0
        s.in_air = False
        s.vel_y = 0
        s.move(True, False)
        # Player should not go off left edge
        assert s.rect.left >= 0

    def test_player_bounded_right_edge(self, mock_world):
        s = make_soldier('player', x=shooter.SCREEN_WIDTH - 5, y=200)
        s.rect.right = shooter.SCREEN_WIDTH
        s.in_air = False
        s.vel_y = 0
        s.move(False, True)
        # Player should not go off right edge
        assert s.rect.right <= shooter.SCREEN_WIDTH

    def test_enemy_turns_on_x_collision(self):
        s = make_soldier('enemy', x=200, y=200, speed=2)
        s.direction = 1
        s.in_air = False

        original_world = shooter.world
        mock = MagicMock()
        # Obstacle directly to the right
        obstacle_rect = pygame.Rect(s.rect.right, s.rect.y, 45, 45)
        mock.obstacle_list = [(MagicMock(), obstacle_rect)]
        mock.level_length = 150
        shooter.world = mock

        s.move(False, True)
        assert s.direction == -1
        assert s.move_counter == 0

        shooter.world = original_world

    def test_y_collision_landing(self):
        s = make_soldier('player', x=200, y=200)
        s.vel_y = 5  # falling
        s.in_air = True

        original_world = shooter.world
        mock = MagicMock()
        # Ground tile just below the soldier
        ground_rect = pygame.Rect(
            s.rect.x - 10,
            s.rect.bottom + 3,
            s.rect.width + 20,
            shooter.TILE_SIZE,
        )
        mock.obstacle_list = [(MagicMock(), ground_rect)]
        mock.level_length = 150
        shooter.world = mock

        s.move(False, False)
        assert s.vel_y == 0
        assert s.in_air is False

        shooter.world = original_world

    def test_y_collision_head_bump(self):
        s = make_soldier('player', x=200, y=200)
        s.vel_y = -5  # jumping upward
        s.in_air = True

        original_world = shooter.world
        mock = MagicMock()
        # Ceiling tile just above the soldier
        ceiling_rect = pygame.Rect(
            s.rect.x - 10,
            s.rect.top - shooter.TILE_SIZE - 3,
            s.rect.width + 20,
            shooter.TILE_SIZE,
        )
        mock.obstacle_list = [(MagicMock(), ceiling_rect)]
        mock.level_length = 150
        shooter.world = mock

        s.move(False, False)
        assert s.vel_y == 0

        shooter.world = original_world


class TestSoldierShoot:
    """Tests for Soldier.shoot."""

    def test_shoot_creates_bullet(self, clean_groups):
        s = make_soldier()
        s.shoot_cooldown = 0
        s.ammo = 10
        s.shoot()
        assert s.ammo == 9
        assert s.shoot_cooldown == 20
        assert len(shooter.bullet_group) == 1

    def test_shoot_cooldown_prevents_fire(self, clean_groups):
        s = make_soldier()
        s.shoot_cooldown = 5
        s.ammo = 10
        s.shoot()
        assert s.ammo == 10
        assert len(shooter.bullet_group) == 0

    def test_shoot_no_ammo(self, clean_groups):
        s = make_soldier()
        s.shoot_cooldown = 0
        s.ammo = 0
        s.shoot()
        assert s.ammo == 0
        assert s.shoot_cooldown == 0
        assert len(shooter.bullet_group) == 0

    def test_shoot_direction_right(self, clean_groups):
        s = make_soldier()
        s.shoot_cooldown = 0
        s.ammo = 10
        s.direction = 1
        s.shoot()
        bullet = list(shooter.bullet_group)[0]
        assert bullet.direction == 1

    def test_shoot_direction_left(self, clean_groups):
        s = make_soldier()
        s.shoot_cooldown = 0
        s.ammo = 10
        s.direction = -1
        s.shoot()
        bullet = list(shooter.bullet_group)[0]
        assert bullet.direction == -1

    def test_multiple_shots_decrement_ammo(self, clean_groups):
        s = make_soldier()
        s.ammo = 5
        for _ in range(3):
            s.shoot_cooldown = 0
            s.shoot()
        assert s.ammo == 2
        assert len(shooter.bullet_group) == 3


class TestSoldierAI:
    """Tests for Soldier.ai (enemy AI behaviour)."""

    def test_ai_scrolls_enemy(self, mock_world):
        """AI always applies screen_scroll to enemy position."""
        original_player = shooter.player
        shooter.player = make_soldier('player', x=-5000, y=-5000)  # far away

        enemy = make_soldier('enemy', x=300, y=300)
        enemy.alive = True

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 5
        x_before_ai = enemy.rect.x
        enemy.ai()
        # The AI may also move the enemy, so just verify scroll was applied
        # by checking the net displacement includes the scroll offset.
        # For a dead-player scenario the AI still runs movement + scroll.
        # Simplest: confirm rect.x changed by at least the scroll amount direction.
        assert enemy.rect.x != x_before_ai  # enemy position was modified

        shooter.screen_scroll = original_scroll
        shooter.player = original_player

    def test_ai_does_nothing_when_dead(self, mock_world):
        """Dead enemy should not move (except scroll)."""
        original_player = shooter.player
        shooter.player = make_soldier('player', x=-5000, y=-5000)

        enemy = make_soldier('enemy', x=300, y=300)
        enemy.alive = False
        initial_x = enemy.rect.x

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 0
        enemy.ai()
        assert enemy.rect.x == initial_x

        shooter.screen_scroll = original_scroll
        shooter.player = original_player

    def test_ai_shoots_when_player_in_vision(self, mock_world, clean_groups):
        """Enemy should shoot when player is within vision rect."""
        original_player = shooter.player

        enemy = make_soldier('enemy', x=300, y=300, speed=2)
        enemy.alive = True
        enemy.shoot_cooldown = 0
        enemy.ammo = 10

        # Position player inside enemy's vision rect
        player = make_soldier('player', x=350, y=300)
        shooter.player = player
        enemy.vision = pygame.Rect(
            enemy.rect.centerx - 75,
            enemy.rect.centery - 10,
            150,
            20,
        )
        # Ensure the vision rect overlaps with player rect
        enemy.vision.center = (player.rect.centerx, player.rect.centery)

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 0
        enemy.ai()

        assert enemy.ammo == 9  # shot was fired
        assert enemy.action == 0  # idle while shooting

        shooter.screen_scroll = original_scroll
        shooter.player = original_player

    def test_ai_idling_counter_decrements(self, mock_world):
        """Idling counter should decrement while enemy is idling."""
        original_player = shooter.player
        shooter.player = make_soldier('player', x=-5000, y=-5000)

        enemy = make_soldier('enemy', x=300, y=300)
        enemy.alive = True
        enemy.idling = True
        enemy.idling_counter = 10
        # Place vision far from player so enemy doesn't shoot
        enemy.vision = pygame.Rect(-9000, -9000, 150, 20)

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 0
        enemy.ai()
        assert enemy.idling_counter == 9

        shooter.screen_scroll = original_scroll
        shooter.player = original_player

    def test_ai_stops_idling_when_counter_zero(self, mock_world):
        """Enemy should stop idling when counter reaches 0."""
        original_player = shooter.player
        shooter.player = make_soldier('player', x=-5000, y=-5000)

        enemy = make_soldier('enemy', x=300, y=300)
        enemy.alive = True
        enemy.idling = True
        enemy.idling_counter = 1
        enemy.vision = pygame.Rect(-9000, -9000, 150, 20)

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 0
        enemy.ai()
        assert enemy.idling is False

        shooter.screen_scroll = original_scroll
        shooter.player = original_player

    def test_ai_moves_when_not_idling(self, mock_world):
        """Enemy should move and update action to run when not idling."""
        original_player = shooter.player
        shooter.player = make_soldier('player', x=-5000, y=-5000)

        enemy = make_soldier('enemy', x=300, y=300)
        enemy.alive = True
        enemy.idling = False
        enemy.direction = 1
        enemy.vision = pygame.Rect(-9000, -9000, 150, 20)

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 0
        with patch('random.randint', return_value=0):  # prevent random idling
            enemy.ai()

        assert enemy.action == 1  # run animation
        assert enemy.move_counter != 0  # counter updated

        shooter.screen_scroll = original_scroll
        shooter.player = original_player

    def test_ai_reverses_at_move_counter_limit(self, mock_world):
        """Enemy reverses direction when move_counter exceeds TILE_SIZE."""
        original_player = shooter.player
        shooter.player = make_soldier('player', x=-5000, y=-5000)

        enemy = make_soldier('enemy', x=300, y=300)
        enemy.alive = True
        enemy.idling = False
        enemy.direction = 1
        enemy.move_counter = shooter.TILE_SIZE  # at the limit
        enemy.vision = pygame.Rect(-9000, -9000, 150, 20)

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 0
        with patch('random.randint', return_value=0):
            enemy.ai()

        assert enemy.direction == -1

        shooter.screen_scroll = original_scroll
        shooter.player = original_player


class TestSoldierAnimation:
    """Tests for Soldier animation methods."""

    def test_update_action_changes_action(self):
        s = make_soldier()
        s.action = 0
        s.frame_index = 3
        s.update_action(1)
        assert s.action == 1
        assert s.frame_index == 0

    def test_update_action_same_action_no_reset(self):
        s = make_soldier()
        s.action = 1
        s.frame_index = 3
        s.update_action(1)
        assert s.frame_index == 3  # unchanged

    def test_update_animation_advances_after_cooldown(self):
        s = make_soldier()
        s.action = 0
        s.frame_index = 0
        s.update_time = pygame.time.get_ticks() - 200  # well past cooldown
        s.update_animation()
        assert s.frame_index == 1

    def test_update_animation_no_advance_before_cooldown(self):
        s = make_soldier()
        s.action = 0
        s.frame_index = 0
        s.update_time = pygame.time.get_ticks()  # just now
        s.update_animation()
        assert s.frame_index == 0

    def test_animation_wraps_non_death(self):
        s = make_soldier()
        s.action = 0  # Idle
        num_frames = len(s.animation_list[0])
        # Set frame_index to last valid index so next advance wraps
        s.frame_index = num_frames - 1
        s.update_time = pygame.time.get_ticks() - 200
        s.update_animation()  # advances past end
        # The wrap check sets frame_index back to 0
        assert s.frame_index == 0  # wrapped

    def test_death_animation_stops_at_last_frame(self):
        s = make_soldier()
        s.action = 3  # Death
        last = len(s.animation_list[3]) - 1
        s.frame_index = last
        s.update_time = pygame.time.get_ticks() - 200
        s.update_animation()
        assert s.frame_index == last

    def test_death_animation_advances_to_last(self):
        s = make_soldier()
        s.action = 3
        s.frame_index = 0
        s.update_time = pygame.time.get_ticks() - 200
        s.update_animation()
        assert s.frame_index == 1

    def test_update_animation_sets_image(self):
        s = make_soldier()
        s.action = 0
        s.frame_index = 0
        s.update_animation()
        assert s.image is s.animation_list[0][0]


class TestSoldierCheckAlive:
    """Tests for Soldier.check_alive."""

    def test_alive_with_positive_health(self):
        s = make_soldier()
        s.health = 50
        s.check_alive()
        assert s.alive is True

    def test_dead_at_zero_health(self):
        s = make_soldier()
        s.health = 0
        s.check_alive()
        assert s.alive is False
        assert s.health == 0
        assert s.speed == 0
        assert s.action == 3

    def test_dead_with_negative_health(self):
        s = make_soldier()
        s.health = -20
        s.check_alive()
        assert s.alive is False
        assert s.health == 0

    def test_full_health_stays_alive(self):
        s = make_soldier()
        s.health = 100
        s.check_alive()
        assert s.alive is True
        assert s.speed == 5


class TestSoldierDraw:
    """Tests for Soldier.draw."""

    def test_draw_does_not_raise(self):
        """Verify draw executes without error on the dummy display."""
        s = make_soldier()
        # pygame.Surface.blit is a C-level method and cannot be patched,
        # so we just verify the call completes without raising.
        s.draw()


# =========================================================================
# Bullet Tests
# =========================================================================

class TestBulletInit:
    """Tests for Bullet.__init__."""

    def test_basic_init(self):
        b = shooter.Bullet(100, 200, 1)
        assert b.speed == 10
        assert b.rect.center == (100, 200)
        assert b.direction == 1

    def test_left_direction(self):
        b = shooter.Bullet(100, 200, -1)
        assert b.direction == -1

    def test_image_set(self):
        b = shooter.Bullet(100, 200, 1)
        assert isinstance(b.image, pygame.Surface)


class TestBulletUpdate:
    """Tests for Bullet.update."""

    def test_moves_right(self, mock_world, mock_player, clean_groups):
        b = shooter.Bullet(100, 200, 1)
        shooter.bullet_group.add(b)
        initial_x = b.rect.x
        b.update()
        assert b.rect.x == initial_x + 10

    def test_moves_left(self, mock_world, mock_player, clean_groups):
        b = shooter.Bullet(400, 200, -1)
        shooter.bullet_group.add(b)
        initial_x = b.rect.x
        b.update()
        assert b.rect.x == initial_x - 10

    def test_killed_offscreen_right(self, mock_world, mock_player, clean_groups):
        b = shooter.Bullet(shooter.SCREEN_WIDTH + 50, 200, 1)
        shooter.bullet_group.add(b)
        b.update()
        assert b not in shooter.bullet_group

    def test_killed_offscreen_left(self, mock_world, mock_player, clean_groups):
        b = shooter.Bullet(-50, 200, -1)
        shooter.bullet_group.add(b)
        b.update()
        assert b not in shooter.bullet_group

    def test_killed_on_obstacle(self, mock_player, clean_groups):
        original_world = shooter.world
        mock = MagicMock()
        obstacle_rect = pygame.Rect(195, 195, 50, 50)
        mock.obstacle_list = [(MagicMock(), obstacle_rect)]
        shooter.world = mock

        b = shooter.Bullet(200, 200, 1)
        shooter.bullet_group.add(b)
        b.update()
        assert b not in shooter.bullet_group

        shooter.world = original_world

    def test_damages_enemy(self, mock_world, mock_player, clean_groups):
        enemy = make_soldier('enemy', x=215, y=200)
        initial_health = enemy.health
        shooter.enemy_group.add(enemy)

        b = shooter.Bullet(enemy.rect.centerx, enemy.rect.centery, 1)
        shooter.bullet_group.add(b)
        b.update()

        assert enemy.health == initial_health - 25

    def test_does_not_damage_dead_enemy(self, mock_world, mock_player, clean_groups):
        enemy = make_soldier('enemy', x=215, y=200)
        enemy.alive = False
        initial_health = enemy.health
        shooter.enemy_group.add(enemy)

        b = shooter.Bullet(enemy.rect.centerx, enemy.rect.centery, 1)
        shooter.bullet_group.add(b)
        b.update()

        assert enemy.health == initial_health  # no damage to dead enemy

    def test_damages_player(self, mock_world, clean_groups):
        original_player = shooter.player
        player = make_soldier('player', x=215, y=200)
        player.alive = True
        initial_health = player.health
        shooter.player = player

        b = shooter.Bullet(player.rect.centerx, player.rect.centery, 1)
        shooter.bullet_group.add(b)
        b.update()

        assert player.health == initial_health - 5

        shooter.player = original_player

    def test_does_not_damage_dead_player(self, mock_world, clean_groups):
        original_player = shooter.player
        player = make_soldier('player', x=215, y=200)
        player.alive = False
        initial_health = player.health
        shooter.player = player

        b = shooter.Bullet(player.rect.centerx, player.rect.centery, 1)
        shooter.bullet_group.add(b)
        b.update()

        assert player.health == initial_health

        shooter.player = original_player


# =========================================================================
# World Tests
# =========================================================================

class TestWorldInit:
    """Tests for World.__init__."""

    def test_empty_obstacle_list(self):
        w = shooter.World()
        assert w.obstacle_list == []


class TestWorldProcessData:
    """Tests for World.process_data."""

    def _make_empty_data(self, rows=shooter.ROWS, cols=shooter.COLS):
        return [[-1] * cols for _ in range(rows)]

    def test_sets_level_length(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data(cols=100)
        # Need at least one player tile (15) for process_data to return
        data[5][10] = 15
        player, hb = w.process_data(data)
        assert w.level_length == 100

    def test_obstacle_tiles_0_to_8(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data()
        data[5][10] = 15  # player
        # Place obstacles
        for tile_id in range(9):
            data[14][tile_id] = tile_id
        player, hb = w.process_data(data)
        assert len(w.obstacle_list) == 9

    def test_water_tiles(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data()
        data[5][10] = 15  # player
        data[14][0] = 9   # water
        data[14][1] = 10  # water
        player, hb = w.process_data(data)
        assert len(shooter.water_group) == 2

    def test_decoration_tiles(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data()
        data[5][10] = 15  # player
        data[14][0] = 11  # decoration
        data[14][1] = 12  # decoration
        data[14][2] = 13  # decoration
        data[14][3] = 14  # decoration
        player, hb = w.process_data(data)
        assert len(shooter.decoration_group) == 4

    def test_creates_player(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data()
        data[5][10] = 15
        player, hb = w.process_data(data)
        assert isinstance(player, shooter.Soldier)
        assert player.char_type == 'player'

    def test_creates_health_bar(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data()
        data[5][10] = 15
        player, hb = w.process_data(data)
        assert isinstance(hb, shooter.HealthBar)

    def test_creates_enemies(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data()
        data[5][10] = 15  # player
        data[10][20] = 16  # enemy
        data[10][30] = 16  # enemy
        player, hb = w.process_data(data)
        assert len(shooter.enemy_group) == 2

    def test_ignores_negative_tiles(self, clean_groups):
        w = shooter.World()
        data = self._make_empty_data()
        data[5][10] = 15  # player
        # All other tiles are -1 by default
        player, hb = w.process_data(data)
        assert len(w.obstacle_list) == 0
        assert len(shooter.water_group) == 0
        assert len(shooter.decoration_group) == 0


class TestWorldDraw:
    """Tests for World.draw."""

    def test_draw_does_not_raise(self):
        """Verify World.draw executes without error."""
        w = shooter.World()
        surface = pygame.Surface((45, 45))
        rect = pygame.Rect(100, 100, 45, 45)
        w.obstacle_list = [(surface, rect)]

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 0
        # pygame.Surface.blit is a C-level method and cannot be patched,
        # so we verify the call completes without raising.
        w.draw()
        shooter.screen_scroll = original_scroll

    def test_draw_applies_scroll(self):
        w = shooter.World()
        surface = pygame.Surface((45, 45))
        rect = pygame.Rect(100, 100, 45, 45)
        w.obstacle_list = [(surface, rect)]

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 10
        initial_x = rect[0]
        w.draw()
        assert rect[0] == initial_x + 10
        shooter.screen_scroll = original_scroll


# =========================================================================
# Decoration Tests
# =========================================================================

class TestDecoration:
    """Tests for the Decoration class."""

    def test_init(self):
        img = pygame.Surface((30, 30))
        d = shooter.Decoration(img, 100, 200)
        assert isinstance(d.rect, pygame.Rect)
        assert d.image is img

    def test_rect_position(self):
        img = pygame.Surface((30, 30))
        d = shooter.Decoration(img, 100, 200)
        expected_x = 100 + shooter.TILE_SIZE // 2
        expected_y = 200 + (shooter.TILE_SIZE - img.get_height())
        assert d.rect.midtop == (expected_x, expected_y)

    def test_update_applies_scroll(self):
        img = pygame.Surface((30, 30))
        d = shooter.Decoration(img, 100, 200)
        initial_x = d.rect.x

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 7
        d.update()
        assert d.rect.x == initial_x + 7
        shooter.screen_scroll = original_scroll


# =========================================================================
# Water Tests
# =========================================================================

class TestWater:
    """Tests for the Water class."""

    def test_init(self):
        img = pygame.Surface((30, 30))
        w = shooter.Water(img, 100, 200)
        assert isinstance(w.rect, pygame.Rect)
        assert w.image is img

    def test_rect_position(self):
        img = pygame.Surface((30, 30))
        w = shooter.Water(img, 100, 200)
        expected_x = 100 + shooter.TILE_SIZE // 2
        expected_y = 200 + (shooter.TILE_SIZE - img.get_height())
        assert w.rect.midtop == (expected_x, expected_y)

    def test_update_applies_scroll(self):
        img = pygame.Surface((30, 30))
        w = shooter.Water(img, 100, 200)
        initial_x = w.rect.x

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = 3
        w.update()
        assert w.rect.x == initial_x + 3
        shooter.screen_scroll = original_scroll


# =========================================================================
# Exit Tests
# =========================================================================

class TestExit:
    """Tests for the Exit class."""

    def test_init(self):
        img = pygame.Surface((30, 30))
        e = shooter.Exit(img, 100, 200)
        assert isinstance(e.rect, pygame.Rect)
        assert e.image is img

    def test_rect_position(self):
        img = pygame.Surface((30, 30))
        e = shooter.Exit(img, 100, 200)
        expected_x = 100 + shooter.TILE_SIZE // 2
        expected_y = 200 + (shooter.TILE_SIZE - img.get_height())
        assert e.rect.midtop == (expected_x, expected_y)

    def test_update_applies_scroll(self):
        img = pygame.Surface((30, 30))
        e = shooter.Exit(img, 100, 200)
        initial_x = e.rect.x

        original_scroll = shooter.screen_scroll
        shooter.screen_scroll = -4
        e.update()
        assert e.rect.x == initial_x - 4
        shooter.screen_scroll = original_scroll


# =========================================================================
# draw_bg Tests
# =========================================================================

class TestDrawBg:
    """Tests for the draw_bg function."""

    def test_draw_bg_does_not_raise(self):
        """Verify draw_bg executes without error on the dummy display."""
        # pygame.Surface methods (fill/blit) are C-level and cannot be patched.
        # We verify the function runs to completion instead.
        shooter.draw_bg()

    def test_draw_bg_uses_background_images(self):
        """Verify the background image variables exist and are Surfaces."""
        assert isinstance(shooter.sky_img, pygame.Surface)
        assert isinstance(shooter.mountain_img, pygame.Surface)
        assert isinstance(shooter.pine1_img, pygame.Surface)
        assert isinstance(shooter.pine2_img, pygame.Surface)


# =========================================================================
# Module-Level Constants Tests
# =========================================================================

class TestConstants:
    """Tests for module-level constants."""

    def test_screen_dimensions(self):
        assert shooter.SCREEN_WIDTH == 800
        assert shooter.SCREEN_HEIGHT == 720

    def test_gravity(self):
        assert shooter.GRAVITY == 0.75

    def test_scroll_thresh(self):
        assert shooter.SCROLL_THRESH == 200

    def test_grid_dimensions(self):
        assert shooter.ROWS == 16
        assert shooter.COLS == 150

    def test_tile_size(self):
        assert shooter.TILE_SIZE == shooter.SCREEN_HEIGHT // shooter.ROWS

    def test_tile_types(self):
        assert shooter.TILE_TYPES == 21

    def test_fps(self):
        assert shooter.FPS == 60

    def test_colors(self):
        assert shooter.BG == (144, 201, 120)
        assert shooter.RED == (255, 0, 0)
