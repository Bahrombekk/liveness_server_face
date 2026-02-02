import random

DIRECTIONS = ["LEFT", "RIGHT", "UP", "DOWN"]

def new_challenge():
    return random.choice(DIRECTIONS)

def is_centered(yaw, pitch):
    """Yuz to'g'ri markazda turganini tekshirish"""
    return abs(yaw) < 15 and abs(pitch) < 12

def check(challenge, yaw, pitch):
    """Challenge bajarilganini tekshirish"""
    thresholds = {
        "LEFT": yaw < -20,
        "RIGHT": yaw > 20,
        "UP": pitch < -12,
        "DOWN": pitch > 12
    }
    return thresholds.get(challenge, False)
