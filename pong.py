# pylint: disable=no-member

import os, sys
import pygame
import getpass
import random
from pygame.locals import *
from pygame.compat import geterror

DEFAULT_PONGPLATE_SIZE = (20, 100)
DEFAULT_SCREEN_PADDING = 18

main_dir = os.path.split(os.path.abspath(__file__))[0]

def get_resource_path(relative_path):
    return relative_path
    result = ""
    try:
        result = os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        result = relative_path
    return result

def randcolor(min = 100, max = 255):
    return (random.randint(min, max), random.randint(min, max), random.randint(min, max))

def load_sound(name):
    class NoneSound:
        def play(self):
            pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(main_dir, "sounds", name)
    print(fullname)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error:
        print(f"Cannot load sound: {str(fullname)}")
        raise SystemExit(str(geterror()))
    return sound

def play_random(sound_list):
    rand_seed = len(sound_list) - 1
    sound_list[random.randint(0, rand_seed)].play()

class Screendef:
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height

    def get_resolution(self):
        return (self.width, self.height)

    def get_left_pong(self):
        return (DEFAULT_SCREEN_PADDING, round(self.height / 2) - round(DEFAULT_PONGPLATE_SIZE[1] / 2))

    def get_right_pong(self):
        return (self.width - DEFAULT_PONGPLATE_SIZE[0] - DEFAULT_SCREEN_PADDING, round(self.height / 2) - round(DEFAULT_PONGPLATE_SIZE[1] / 2))

    def get_ball(self):
        return (round(self.width / 2), round(self.height / 2))

default_screen = Screendef()

def rand_pos(screen=default_screen):
    return (random.randint(0, screen.width), random.randint(0, screen.height))

def randomize_stars(starlist):
    for star in starlist:
        if random.randint(0, 1) == 1:
            star.randomize()

class Player:
    all_players = []
    maxscore = 10

    def __init__(self, name=getpass.getuser(), plate=None):
        occurences = Player.all_players.count(name)
        postfix = ""
        if (occurences > 0):
            postfix = f" ({occurences})"

        self.name = name + postfix
        Player.all_players.append(self.name)
        self.plate = plate
        self.score = 0

    def __del__(self):
        Player.all_players.remove(self.name)

class Pongplate:
    step = 8

    def __init__(self, placement="left", color=(255, 255, 255)):
        l_placement = placement.lower()
        
        if l_placement == "right":
            self.default_pos = default_screen.get_right_pong()
        else:
            self.default_pos= default_screen.get_left_pong()
        
        self.y_pos = self.default_pos[1]
        self.x_pos = self.default_pos[0]
        self.rect = pygame.Rect(self.default_pos, DEFAULT_PONGPLATE_SIZE)
        self.color = color
    
    def move(self, direction):
        l_direction = direction.lower()
        been_moved = False
        
        if l_direction == "down":
            lower_border = default_screen.height - DEFAULT_PONGPLATE_SIZE[1]
            if self.y_pos < lower_border:
                self.y_pos += Pongplate.step
                if self.y_pos > lower_border:
                    self.y_pos = lower_border
                been_moved = True
        elif l_direction == "up":
            if self.y_pos > 0:
                self.y_pos -= Pongplate.step
                if self.y_pos < 0:
                    self.y_pos = 0
                been_moved = True
        
        if been_moved:
            if l_direction == "down":
                self.rect.move_ip(0, Pongplate.step)
            elif l_direction == "up":
                self.rect.move_ip(0, -Pongplate.step)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def new_color(self):
        self.color = randcolor()

    def default(self):
        self.y_pos = self.default_pos[1]
        self.x_pos = self.default_pos[0]
        self.color = randcolor()
        self.rect = pygame.Rect(self.default_pos, DEFAULT_PONGPLATE_SIZE)

class Pongball:
    def __init__(self, size=15, maxspeed=10, color=(255, 255, 255)):
        self.default_pos = default_screen.get_ball()
        self.size = size
        self.x_pos = self.default_pos[0] - round(self.size / 2)
        self.y_pos = self.default_pos[1] - round(self.size / 2)
        self.color = color
        self.maxspeed = maxspeed
        self.rect = pygame.Rect(self.default_pos, (self.size, self.size))
        self.colliding = False
        self.wcolliding = False
        self.gone_side = None
        self.new_speed()

    def new_speed(self):
        self.x_speed = random.randint(-self.maxspeed, self.maxspeed)

        if self.x_speed == 0:
            self.x_speed = round(self.maxspeed / 2)

        negative = random.randint(-1, 1)
        if negative == 0: negative = 1

        self.y_speed = (self.maxspeed - abs(self.x_speed)) * negative

    def move(self, pongplates=None):
        self.colliding = False
        self.wcolliding = False

        self.x_pos += self.x_speed
        self.y_pos += self.y_speed
        self.rect.move_ip(self.x_speed, self.y_speed)

        if self.y_pos <= 0 or self.y_pos >= default_screen.height - self.size:
            self.y_speed = -self.y_speed
            self.wcolliding = True

        for pongplate in pongplates:
            xcollisionleft = self.x_pos <= pongplate.x_pos + DEFAULT_PONGPLATE_SIZE[0] and self.x_pos >= pongplate.x_pos
            xcollisionright = self.x_pos + self.size <= pongplate.x_pos + DEFAULT_PONGPLATE_SIZE[0] and self.x_pos + self.size >= pongplate.x_pos
            xcollision = xcollisionleft or xcollisionright
            ycollision = self.y_pos <= pongplate.y_pos + DEFAULT_PONGPLATE_SIZE[1] and self.y_pos >= pongplate.y_pos

            if xcollision and ycollision:
                self.colliding = True
                relative_pos = self.y_pos - pongplate.y_pos
                percentage = (relative_pos / DEFAULT_PONGPLATE_SIZE[1]) - 0.5
                self.y_speed = round(self.maxspeed * percentage)
                if self.x_speed > 0:
                    self.x_speed = (self.maxspeed - abs(self.y_speed)) * -1
                elif self.x_speed < 0:
                    self.x_speed = self.maxspeed - abs(self.y_speed)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def is_gone(self):
        self.gone_side = None
        if self.x_pos < -self.size:
            self.gone_side = "left"
            return True
        elif self.x_pos > default_screen.width:
            self.gone_side = "right"
            return True
        return False

    def new_color(self):
        self.color = randcolor()

    def default(self):
        self.x_pos = self.default_pos[0] - round(self.size / 2)
        self.y_pos = self.default_pos[1] - round(self.size / 2)
        self.color = randcolor()
        self.rect = pygame.Rect(self.default_pos, (self.size, self.size))
        self.colliding = False
        self.wcolliding = False
        self.gone_side = None
        self.new_speed()

class Decostar:
    def __init__(self, position=None, color=None):
        if color is None:
            color = randcolor()
        if position is None:
            position = rand_pos()
        self.color = color
        self.position = position
    
    def randomize(self):
        self.color = randcolor()
        self.position = rand_pos()

    def draw(self, surface):
        surface.set_at(self.position, self.color)

def main():
    #pygame.mixer.pre_init(44100, 16, 2, 4096)
    pygame.init()
    pygame.mixer.init()

    playscreen = pygame.display.set_mode(default_screen.get_resolution())
    pygame.display.set_caption(" 💵 Pong 💵 ")

    background_color = (0, 0, 0)
    
    current_bg_color = [
        background_color[0],
        background_color[1],
        background_color[2]
    ]
   
    background = pygame.Surface(playscreen.get_size())
    background = background.convert()
    background.fill(background_color)

    playscreen.blit(background, (0, 0))
    pygame.display.flip()

    clock = pygame.time.Clock()

    hitsounds = [
        load_sound(get_resource_path("hitsound1.ogg")),
        load_sound(get_resource_path("hitsound2.ogg"))
    ]

    wallsounds = [
        load_sound(get_resource_path("wallsound1.ogg")),
        load_sound(get_resource_path("wallsound2.ogg"))
    ]

    decostar_count = 200
    decostars = []
    for i in range(decostar_count):
        newstar = Decostar()
        decostars.append(newstar)

    leftpong = Pongplate("left", randcolor())
    rightpong = Pongplate("right", randcolor())
    rightplayer = Player(plate = rightpong)
    leftplayer = Player("Guest", leftpong)

    players = [leftplayer, rightplayer]
    pongplates = [leftpong, rightpong]

    pongball = Pongball(maxspeed = 12, color = randcolor())

    print(f"\nWelcome to Pong, {getpass.getuser()}!")

    pygame.mixer.music.load(get_resource_path("./sounds/bgsound.ogg"))
    pygame.mixer.music.play(-1)

    pygame.time.set_timer(pygame.USEREVENT, 20)
    initial_freeze = True
    going = True
    while going:
        clock.tick(60)

        if current_bg_color[0] > 0: 
            current_bg_color[0] -= 1
            if current_bg_color[0] < 0: current_bg_color[0] = 0 
        if current_bg_color[1] > 0: 
            current_bg_color[1] -= 3
            if current_bg_color[1] < 0: current_bg_color[1] = 0
        if current_bg_color[2] > 0: 
            current_bg_color[2] -= 1
            if current_bg_color[2] < 0: current_bg_color[2] = 0

        if pongball.is_gone():
            if pongball.gone_side == "right":
                rightplayer.score += 1
            elif pongball.gone_side == "left":
                leftplayer.score += 1

            for player in players:
                if player.score >= Player.maxscore:
                    going = False
                    print("-"*30)
                    print("Score:")
                    for finalplayer in players:
                        print(f"{finalplayer.name} scored {finalplayer.score} points")
                    print("-"*30)
                    print(f"WINNER: {player.name}\n")

            if going:
                play_random(wallsounds)
                pongball.default()
                for pongplate in pongplates:
                    pongplate.default()
                initial_freeze = True

        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                randomize_stars(decostars)

            if event.type == pygame.QUIT:
                going = False
            elif event.type == pygame.KEYDOWN:
                initial_freeze = False

        held_keys = pygame.key.get_pressed()
        
        if held_keys[pygame.K_UP]:
            rightpong.move("up")
        elif held_keys[pygame.K_DOWN]:
            rightpong.move("down")
        
        if held_keys[pygame.K_w]:
            leftpong.move("up")
        elif held_keys[pygame.K_s]:
            leftpong.move("down")

        if not initial_freeze:
            pongball.move(pongplates)

        if pongball.colliding:
            pongball.new_color()
            leftpong.new_color()
            rightpong.new_color()
            new_bg_color = randcolor(20, 75)
            current_bg_color = [new_bg_color[0], new_bg_color[1], new_bg_color[2]]
            play_random(hitsounds)
        elif pongball.wcolliding:
            play_random(wallsounds)

        background.fill((current_bg_color[0], current_bg_color[1], current_bg_color[2]))
        playscreen.blit(background, (0, 0))

        for decostar in decostars:
            decostar.draw(playscreen)

        leftpong.draw(playscreen)
        rightpong.draw(playscreen)
        pongball.draw(playscreen)
        pygame.display.flip()

    pygame.mixer.music.stop()
    pygame.mixer.music.load(get_resource_path("./sounds/endsound.ogg"))
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy() == True:
        continue

    print(f"Goodbye, {getpass.getuser()}!\nCome back for more Pong later\n")
    pygame.quit()

if __name__ == "__main__":
    main()
