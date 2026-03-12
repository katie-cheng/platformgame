"""Pytest configuration for shooter.py tests.

Sets up headless pygame environment and imports the shooter module
with the game loop patched to exit immediately.
"""
import os
import sys

# Set up headless pygame drivers BEFORE any pygame import
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
from unittest.mock import patch

# Change to repo directory so relative image/level paths resolve correctly
_repo_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_repo_dir)

# Ensure repo dir is on sys.path
if _repo_dir not in sys.path:
    sys.path.insert(0, _repo_dir)

# Initialize pygame so we can create surfaces for mocks
pygame.init()
pygame.display.set_mode((800, 720))

# Wrap the real pygame.image.load to fix case-sensitivity issues
# (e.g. 'img/Background/' in code vs 'img/background/' on disk)
_real_load = pygame.image.load
_dummy_surface = pygame.Surface((10, 10)).convert_alpha()


def _patched_load(path, *args, **kwargs):
    """Try loading the image as-is; on failure try a case-fixed path."""
    try:
        return _real_load(path, *args, **kwargs)
    except FileNotFoundError:
        fixed = path.replace('Background', 'background')
        try:
            return _real_load(fixed, *args, **kwargs)
        except FileNotFoundError:
            return _dummy_surface.copy()


# Import shooter with:
#  - patched image loader for case-insensitive paths
#  - QUIT event so the game loop exits after one iteration
#  - patched pygame.quit so pygame stays active for tests
with patch('pygame.image.load', side_effect=_patched_load):
    with patch('pygame.event.get',
               return_value=[pygame.event.Event(pygame.QUIT)]):
        with patch('pygame.quit'):
            import shooter
