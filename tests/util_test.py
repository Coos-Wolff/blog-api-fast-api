import random

RANDOM_INT_MIN = 0
RANDOM_INT_MAX = 100_000_000

def create_user_id():
    return random.randint(RANDOM_INT_MIN, RANDOM_INT_MAX)