# Alec Mai and Scott Xu
# MegaMan_Final.py
# This is our FSE, our own version of MegaMan. The goal of the game is to complete all of the levels.
# From the main menu:
#   The start button takes the user to the tutorial level.
#   The level select button leads to a level select screen to select the current and previously completed levels.
#       There is also a save button to save the user's score and progress to the 'saves' folder.
#   The load button loads in the saved score and level reached from a file.
#   The high scores button shows the top 10 high scores.
#   The credits button shows the credits screen.
# Each level consists of multiple stages connected by doors.
# We have three basic enemies, two bosses, and four types of consumables.
# In game the user controls the player character using the arrow keys and spacebar.
# When the final level is completed there are fireworks to congratulate the user.
# There are also sound effects and music throughout the game.

from tkinter import *
from tkinter import filedialog
from pygame import *
from random import *
from math import *
from time import clock
from glob import glob

root = Tk()
root.withdraw()
init()
mixer.init()
bitfont20 = font.Font("Munro.ttf", 20)
bitfont40 = font.Font("Munro.ttf", 40)
bitfont120 = font.Font("Munro.ttf", 120)

#######################################################################
# classes

# user controlled character
# arrow keys to move and jump
# spacebar to shoot
class character:
    def __init__(self, x, y, health = 10, lazer = False, jumpboost = False):
        self.picNum = 0  # which image index to use
        self.direction = 'standR'  # state and direction
        self.pic = playerPics[self.direction][self.picNum] # image for current frame
        self.w, self.h = self.pic.get_size()
        self.x, self.y = x, y
        self.onground = False # whether or not the player is touching the ground
        self.vy = 0 # change in y (for jumping and falling)
        self.atkFrames = 0  # number of frames to show attacking animation
        self.warmUp = 0  # number of frames needed to attack again
        self.invFrames = 0  # number of frames in which the player cannot take more damage
        self.health = health
        self.jumpboost = jumpboost # whether or not the player has the jumpboost powerup
        self.lazer = lazer # whether or not the player has the lazer powerup
        self.lazerSoundOffset = 0 # used to delay each lazer sound

    def move(self):  # move player based on which keys are pressed
        if self.invFrames <= 0:
            self.invFrames = 0

            # move player horizontally
            if moves['left'] and not moves['right']:
                self.x -= 4
                if self.onground:
                    self.picNum += 1
                    self.direction = 'walkL'
                else:
                    self.direction = 'jumpL'
            elif moves['right'] and not moves['left']:
                self.x += 4
                if self.onground:
                    self.picNum += 1
                    self.direction = 'walkR'
                else:
                    self.direction = 'jumpR'
            else:
                if self.onground:
                    self.picNum = 0
                    self.direction = 'stand' + self.direction[-1]
                else:
                    self.direction = 'jump' + self.direction[-1]
                    
            # check for collisions
            self.rect = Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)
            for wall in walls: # stationary platforms
                if self.rect.colliderect(wall):
                    if self.x < wall.right+wall.w/2:  # moved to the right
                        self.x = wall.left - self.w // 2 - 1
                    else:
                        self.x = wall.right + self.w // 2 + 1
            for p in platforms: # moving platforms
                pRect = Rect(p.x, p.y, p.w, 20)
                if self.rect.colliderect(pRect):
                    if self.x < p.x:  # moved to the right
                        self.x = pRect.left - self.w // 2 - 1
                    elif self.x > p.x + p.w:
                        self.x = pRect.right + self.w // 2 + 1

            # move player vertically
            if moves['up'] and self.onground:  # only can jump if on ground
                playerJumpSound.play()
                self.direction = 'jump' + self.direction[-1]
                moves['up'] = False
                self.onground = False
                if self.jumpboost:
                    self.vy = -6
                else:
                    self.vy = -5
            self.y += self.vy

            # check for collisions
            self.rect = Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)
            for wall in walls: # stationary platforms
                if self.rect.colliderect(wall):
                    if self.y <= wall.top + wall.h//2:  # moved down
                        if 'jump' in self.direction:
                            self.picNum = min(self.picNum + 1, 4)
                        self.y = wall.top - self.h // 2 - 1
                        self.onground = True
                        self.vy = 0
                    else:
                        self.y = wall.bottom + self.h // 2 + 1
                        self.vy = 0
            for p in platforms: # moving platforms
                pRect = Rect(p.x, p.y, p.w, 20)
                if self.rect.colliderect(pRect):
                    if self.y <= p.y:  # moved down
                        if 'jump' in self.direction:
                            self.picNum = min(self.picNum + 1, 4)
                        self.y = pRect.top - self.h // 2 - 1
                        self.onground = True
                        self.vy = 0
                    elif self.y >= p.y + 20:
                        self.y = pRect.bottom + self.h // 2 + 1
                        if self.vy < 0:
                            self.vy = 0

        else:
            self.invFrames -= 1

        # player shoots
        if moves['atk']:
            self.shoot()
        else: # lock y position of all lasers
            for lazer in lazers:
                lazer[2] = True

        self.check_ground()
        self.animate()

    def check_ground(self): # check if player is on the ground or a platform
        self.fallRect = Rect(self.x - self.w // 2, self.y - self.h // 2 + 2, self.w, self.h) # projected next location of the player
        if not any([self.fallRect.colliderect(wall) for wall in walls]) and not any([self.fallRect.colliderect(Rect(p.x, p.y, p.w, 20)) for p in platforms]):
            self.onground = False

        if not self.onground:
            self.direction = 'jump' + self.direction[-1]
            if self.vy < 0: # image for player jumping up
                self.picNum = 3
            else: # image for player falling down
                self.picNum = 4
            self.vy += 0.1
    
    def animate(self): # animates all character actions
        if self.atkFrames > 0 or moves['atk']: # animate player shooting
            self.picNum %= len(playerPics['atk' + self.direction])
            self.pic = Surface(playerPics['atk' + self.direction][self.picNum].get_size()).convert()
            self.pic.blit(playerPics['atk' + self.direction][self.picNum], (0, 0))
            self.atkFrames -= 1
        else: # animate player not without shooting
            self.picNum %= len(playerPics[self.direction])
            self.pic = Surface(playerPics[self.direction][self.picNum].get_size()).convert()
            self.pic.blit(playerPics[self.direction][self.picNum], (0, 0))

        if self.invFrames > 0: # player flashes when taking damage
            self.cover = Surface((self.pic.get_width(), self.pic.get_height())).convert()
            self.tint = (255, 255, 255)
            self.cover.set_alpha((5 - (self.invFrames % 5)) * 50) # white cover becomes more and more opaque
            self.cover.fill(self.tint)
            self.pic.blit(self.cover, (0, 0))
        self.pic.set_colorkey(self.pic.get_at((0, 0)))

        if self.warmUp > 0:
            self.warmUp -= 1

    def shoot(self): # player shooting
        if self.warmUp == 0 and not self.lazer:
            self.atkFrames = 15  # show 15 frames of attacking
            self.warmUp = 15  # wait at least 15 frames before shooting again
            if self.direction[-1] == 'R':
                projectiles.append([self.x + self.w // 2, self.y - 7, 5, 0, 'bullet'])
                playerShotSound.play()
            else:
                projectiles.append([self.x - self.w // 2, self.y - 7, -5, 0, 'bullet'])
                playerShotSound.play()
            moves['atk'] = False

        elif self.lazer: # can hold space bar when shooting laser

            # staggers the lazerSound so that it does not drown out the other sounds 
            self.lazerSoundOffset += 1
            if self.lazerSoundOffset % 9 == 0:
                playerLazerSound.play()

            if self.direction[-1] == 'R':
                lazers.append([self.x + self.w // 2 - 13, self.y - 4, False, self.direction[-1]]) # shoots lazer to the right
            else:
                lazers.append([self.x - self.w // 2 - 30, self.y - 4, False, self.direction[-1]]) # shoots lazer to the left

    def show_death(self): # show the player's death and game over
        self.direction = 'death' + self.direction[-1]
        for i in range(len(playerPics[self.direction])):
            self.pic = playerPics[self.direction][i]
            self.w, self.h = self.pic.get_size()
            grey = 255-i*255/len(playerPics[self.direction]) # background goes from white to black
            screen.fill((grey, grey, grey))
            screen.blit(gameOverText, (400 - gameOverText.get_width()//2, 100 - gameOverText.get_height()//2))
            screen.blit(self.pic, (self.x - self.w // 2 - offset, self.y - self.h // 2 + 3))
            display.flip()
            time.wait(1000)

# rolling enemy
# rolls to player if player enters its sight-rect (field of view)
class armadillo:
    def __init__(self, x, y, direction, sight):
        # the following variables are the same as in the character class
        self.x, self.y = x, y
        self.direction = direction
        self.picNum = 0
        self.pic = armadilloPics[self.direction][self.picNum]
        self.w, self.h = self.pic.get_size()
        self.warmup = 0
        self.health = 2

        # the following variables are unique to the armadillo
        self.sight = sight  # rect which the armadillo can detect the player
        self.rolling = False # holds whether or not the armadillo is rolling

    def look(self): # checking if player in range; if rolling, continue rolling
        if self.warmup == 0:
            if not self.rolling:
                if choice([0] * 49 + [1]) == 1: # randomly turn left and right
                    if self.direction == 'right':
                        self.direction = 'left'
                    else:
                        self.direction = 'right'

                self.checkplayer()
            if self.rolling:
                self.roll()
            else:
                self.picNum = 0
        else:
            self.warmup -= 1

        self.pic = armadilloPics[self.direction][self.picNum]
        self.w, self.h = self.pic.get_size()

    def checkplayer(self):  # check if player is in sight
        if self.direction == 'left':
            self.sightRect = Rect(self.sight.left, self.sight.top, self.x - self.sight.left, self.sight.height)
        else:
            self.sightRect = Rect(self.x, self.sight.top, self.sight.right - self.x, self.sight.height)
        if self.sightRect.collidepoint(player.x, player.y):
            armadilloDashSound.play()
            self.rolling = True

    def roll(self):  # roll toward player
        if self.direction == 'right':
            self.x += 7
        else:
            self.x -= 7

        if not self.sight.collidepoint(self.x, self.y): # check if armadillo has reached the boundary of its sight rect
            if self.direction == 'right':
                self.x = self.sight.right
            else:
                self.x = self.sight.left
            self.rolling = False
            self.warmup = 30
            
        self.picNum += 1
        if self.picNum > 7:
            self.picNum = 4

# stationary enemy
# shoots a cannonball in a parabolic arc towards the player if the player is in front of the cannon
class cannon:
    def __init__(self, x, y, direction):
        # the following variables are the same as in the character class
        self.x, self.y = x, y
        self.direction = direction
        self.picNum = 0
        self.pic = cannonPics[self.direction][self.picNum]
        self.w, self.h = self.pic.get_size()
        self.warmup = 0
        self.health = 10

    def shoot(self): # shoot if player is in range
        if self.warmup == 0:

            # see the file 'readme_cannon.pdf' for clarification
            
            if player.y > self.y:
                self.ballvy = -5 # vy of cannonball
            else:
                self.ballvy = -1*((self.y-player.y+125)/5)**0.5
            
            self.dy = 5*self.ballvy*(self.ballvy-0.1) # vertical distance from cannon's position to vertex
            
            if self.direction == 'left':
                self.ballapex = quadratic(self.y-player.y, -2*player.x*self.dy-2*self.x*(self.y-self.dy-player.y), player.x**2*self.dy+self.x**2*(self.y-self.dy-player.y))
                # possible x-coordinates of vertex
            else:
                # Note: (self.x, self.y) is the top left corner of the cannon.
                # Adding to self.x when the cannon is facing right makes cannonballs look like they are coming from the cannon
                self.ballapex = quadratic(self.y-player.y, -2*(player.x)*self.dy-2*(self.x+22)*(self.y-self.dy-player.y), player.x**2*self.dy+(self.x+22)**2*(self.y-self.dy-player.y))

            for apex in self.ballapex: # we want the vertex horizontally between the player and the cannon so the ball hits the player while coming down
                if self.direction == 'left' and player.x < apex < self.x:
                    # the ball moves -10*self.ballvy times to hit the vertex
                    # so, we divide the horizontal distance from the cannon to the vertex by -10*self.ballvy
                    self.ballvx = (apex-self.x)/(-10*self.ballvy) # vx of cannonball
                    projectiles.append([self.x, self.y, self.ballvx, self.ballvy, 'cannonball'])
                    cannonShotSound.play()
                    self.warmup = 60
                    break # shoot only once
                elif self.direction == 'right' and self.x < apex < player.x:
                    self.ballvx = (apex-(self.x+22))/(-10*self.ballvy)
                    projectiles.append([self.x+22, self.y, self.ballvx, self.ballvy, 'cannonball'])
                    cannonShotSound.play()
                    self.warmup = 60
                    break
        else:
            self.warmup -= 1
            if self.warmup >= 40:
                self.picNum = (self.picNum + 1) % 20
            self.pic = cannonPics[self.direction][self.picNum]

# walking and shooting enemy
# randomly jumps to shoot and hide in shell
class met:
    def __init__(self, x, y, direction, boss=False):
        # the following variables are the same as in the character class
        self.x, self.y = x, y
        self.vy = 0
        self.direction = direction
        self.picNum = 0
        self.health = 1
        self.pic = metPics[self.direction][self.picNum]
        self.onground = True
        self.w, self.h = 30, 35

        # the following variables are unique to the met class
        self.boss = boss # if the met is scaled up or not
        self.picW, self.picH = self.pic.get_size() # width and height of the met's image
        if self.boss: # enlarge the met & increase met health
            self.w *= 4
            self.h *= 4
            self.picW *= 4
            self.picH *= 4
            self.pic = transform.scale(self.pic, (self.picW, self.picH))
            self.health = 10

    def move(self):  # this moves the met
        if self.onground:
            if self.picNum <= 3:  # in shell
                if choice([0] * 24 + [1] * 1) == 1: # chance of getting up and moving
                    self.picNum += 1
            elif self.picNum <= 15:  # getting up
                self.picNum += 1
            elif self.picNum <= 31:  # walk
                self.picNum += 1
                self.rect = Rect(self.x - self.w // 2, self.y - self.h, self.w, self.h)

                # move horizontally
                if self.direction == 'left':
                    self.x -= 2
                else:
                    self.x += 2

                for wall in walls:  # check for collisons
                    if self.rect.colliderect(wall):
                        if self.x < wall.right + wall.w / 2:  # moved to the right
                            self.x = wall.left - self.w // 2 - 1
                            self.direction = 'left'
                        else:
                            self.x = wall.right + self.w // 2 + 1
                            self.direction = 'right'

                self.onground = self.check_ground(self.x, self.y, self.w)
                if self.picNum == 31:  # chance of staying walking or jumping and shooting
                    if choice([0] * 1 + [1] * 9) == 1:
                        self.picNum = 16
            elif self.picNum <= 52:  # jump and shoot
                self.picNum += 1
                self.y += (self.picNum - 43) * 0.4
                if self.picNum == 43:
                    self.shoot()
            else:  # go back into shell
                self.picNum += 1

            if self.picNum == 68: # restart animation
                self.picNum = 0
                self.direction = choice(['left', 'right'])

        else:
            # move vertically (falling) and check for collisions
            self.y += self.vy
            self.vy += 0.1
            if self.check_ground(self.x, self.y, self.w):
                self.vy = 0
                self.onground = True
                self.picNum = 16
            else:
                self.picNum = 32

        self.pic = metPics[self.direction][self.picNum]
        self.picW, self.picH = self.pic.get_size()

        if self.boss:
            self.picW *= 4
            self.picH *= 4
            self.pic = transform.scale(self.pic, (self.picW, self.picH))

    def check_ground(self, x, y, w):  # check if met is touching the ground
        for wall in walls:
            if Rect(x - w // 2, y, w, 2).colliderect(wall):
                self.y = wall.top
                return True
        else:
            return False

    def shoot(self):  # shoot at player
        metShotSound.play()
        mshot_ang = atan2(player.y - self.y + self.h // 2, player.x - self.x)
        if self.boss: # shoots a bigger projectile
            projectiles.append([self.x, self.y - self.h // 2, 3 * cos(mshot_ang), 3 * sin(mshot_ang), 'bigmetshot'])
        else:
            projectiles.append([self.x, self.y - self.h // 2, 3 * cos(mshot_ang), 3 * sin(mshot_ang), 'metshot'])

class movePlatform: # vertically and horizontally moving platforms
    def __init__(self, x, y, w, space, type):
        self.x, self.y = x, y
        self.w = w
        self.space = space # the movement area of the platform
        self.type = type # either horizontallly or vertically moving
        if self.type == 'H':
            self.direction = 'right' # which direction the platform moves
        else:
            self.direction = 'up'
        self.picNum = 0
        self.pic = Surface((self.w, 20)).convert()
        self.pic.set_colorkey((0, 0, 0, 0)) # set background of platform to to be clear
        for i in range(0, self.w, 20): # blits the number of platform blocks into pic
            self.pic.blit(blockPics['platform'], (i, 0))


    def move(self): # move based on type
        if self.type == 'H':
            self.moveH()
        else:
            self.moveV()

    def moveH(self): # move horizontally
        playerRect = Rect(player.x - player.w // 2, player.y + player.h // 2 - 2, player.w, 4)
        self.playercollide = playerRect.colliderect(Rect(self.x, self.y, self.w, 20))

        # also move player if player on platform; check if boundary is reached
        if self.direction == 'right':
            self.x += 2
            if self.playercollide:
                player.x += 2
            while self.x + self.w > self.space.right:
                self.x -= 1
                if self.playercollide:
                    player.x -= 1
                self.direction = 'left'
        else:
            self.x -= 2
            if self.playercollide:
                player.x -= 2
            while self.x < self.space.left:
                self.x += 1
                if self.playercollide:
                    player.x += 1
                self.direction = 'right'


    def moveV(self): # move vertically
        playerRect = Rect(player.x - player.w // 2, player.y + player.h // 2 - 2, player.w, 4)
        self.playercollide = playerRect.colliderect(Rect(self.x, self.y, self.w, 20))

        # also move player if player on platform; check if boundary is reached
        if self.direction == 'down':
            self.y += 1.5
            while self.y + 20 > self.space.bottom:
                self.y -= 1
                self.direction = 'up'
            if self.playercollide:
                player.y = self.y - player.h//2
        else:
            self.y -= 1.5
            while self.y < self.space.top:
                self.y += 1
                self.direction = 'down'
            if self.playercollide:
                player.y = self.y - player.h//2

# final enemy
# randomly flies between predetermined spots
# has two attacks:
#   charges player if player is on same level
#   slashes when player not in range of charge, slash produces a shockwave projectile
class finalBoss:
    def __init__(self, x, y, health = 20, direction = 'L'):
        # the following variables are the same as in the character class
        self.x = x # middle of boss
        self.y = y # bottom of boss
        self.direction = 'stand'+direction
        self.picNum = 0
        self.pic = bossPics[self.direction][self.picNum]
        self.w, self.h = self.pic.get_size()
        self.health = health

    def move(self): # chooses or continues an action
        if 'charge' in self.direction:
            self.charge()
        elif 'slash' in self.direction:
            self.slash()
        elif 'fly' in self.direction:
            self.fly()
        else: # standing
            if choice([1] + [0]*99) == 1: # chance of flying to a new position
                self.chooseAtkPos()
                self.direction = 'fly' + self.direction[-1]
            elif choice([1] + [0]*49) == 1: # chance of attacking
                if self.y >= player.y-41 and player.y >= self.y-76:  # check if player in range of charge
                    if player.x > self.x:
                        self.direction = 'charge' + 'R'
                    else:
                        self.direction = 'charge' + 'L'
                    bossChargeSound.play()
                else:
                    if player.x > self.x:
                        self.direction = 'slash' + 'R'
                    else:
                        self.direction = 'slash' + 'L'
                    bossSlashSound.play()

        self.picNum %= len(bossPics[self.direction])
        self.pic = bossPics[self.direction][self.picNum]
        self.w, self.h = self.pic.get_size()

    def chooseAtkPos(self): # determine a position to fly to
        self.choices = [pos for pos in bossAtkPos if pos[1]!=self.y] # list of possible positions
        self.newx, self.newy = choice([pos for pos in bossAtkPos if pos[1]!=self.y])
        if self.newx > self.x: # determine which direction to fly
            self.direction = 'flyR'
        else:
            self.direction = 'flyL'

    def fly(self): # move towards determined position
        self.picNum += 1
        if hypot(self.newy-self.y, self.newx-self.x) <= 5: # jump to position if close enough
            self.x, self.y = self.newx, self.newy
            self.direction = 'stand' + self.direction[-1]
        else:
            self.ang = atan2(self.newy-self.y, self.newx-self.x)
            self.x += 5 * cos(self.ang)
            self.y += 5 * sin(self.ang)

    def charge(self): # charge towards player
        self.picNum += 1

        if self.direction[-1] == 'R':
            self.x += 10
        else:
            self.x -= 10

        if self.picNum == 24: # keeps charging if not past player
            if self.direction[-1] == 'R' and self.x < player.x:
                self.picNum = 10
            elif self.direction[-1] == 'L' and self.x > player.x:
                self.picNum = 10

        # keeps the boss picture index within range and from charging off-screen
        if self.picNum >= len(bossPics[self.direction]) or self.x < 100 or self.x > 700:
            self.footRect = Rect(self.x - self.w // 2, self.y - self.h // 2 + 2, self.w, self.h) # bottom section of the boss
            # checks if the boss is standing on a block
            if not any([self.footRect.colliderect(wall) for wall in walls]): # if not, flies to another position
                self.chooseAtkPos()
                self.direction = 'fly' + self.direction[-1]
            else:
                self.direction = 'stand' + self.direction[-1]

    def slash(self): # slashes and shoots a shockwave towards the player
        self.picNum += 1

        if self.picNum == 20: # shoots once
            self.ang = atan2(player.y-self.y, player.x-self.x) # direction from boss to player
            self.shockvx, self.shockvy = 5*cos(self.ang), 5*sin(self.ang)
            # determine orientation and spawn point of shockwave
            if -3*pi/4 <= self.ang < -pi/4:
                projectiles.append([self.x - 30, self.y - self.h - 18, self.shockvx, self.shockvy, 'shockwaveN'])
            elif -pi/4 <= self.ang < pi/4:
                projectiles.append([self.x + self.w // 2, self.y - 59, self.shockvx, self.shockvy, 'shockwaveE'])
            elif pi/4 <= self.ang < 3*pi/4:
                projectiles.append([self.x - 30, self.y, self.shockvx, self.shockvy, 'shockwaveS'])
            else:
                projectiles.append([self.x - self.w // 2 - 18, self.y - 59, self.shockvx, self.shockvy, 'shockwaveW'])

        if self.picNum >= len(bossPics[self.direction]):
            self.direction = 'stand' + self.direction[-1]

#######################################################################
# functions

def quadratic(a, b, c): # returns real solutions to a*(x**2) + b*x + c = 0 in a list
    if a == b == 0:
        return []
    elif a == 0:
        # linear equation
        return [-c/b]
    else:
        d = b**2-4*a*c
        if d > 0:
            return [(-b-d**0.5)/(2*a), (-b+d**0.5)/(2*a)]
        elif d == 0:
            return [-b/(2*a)]
        else:
            return []


def updatePlayer(player, enemies, projectiles, consumables, screen):  # animate player and check for damage
    player.move()
    hitbox = Rect(player.x - player.w // 2 + 10, player.y - player.h // 2 + 10, player.w - 20, player.h - 20)
    remove = [] # projectiles that hit the player

    for armadillo in enemies['armadillos']: # check if hit by rolling armadillo
        if player.invFrames == 0:
            if armadillo.rolling:
                armaRect = Rect(armadillo.x - armadillo.w // 2, armadillo.y - armadillo.h // 2, armadillo.w, armadillo.h)
                if hitbox.colliderect(armaRect):
                    player.health = max(0, player.health - 2)
                    player.invFrames = 30
                    player.jumpboost = False
                    player.lazer = False

    for b in enemies['finalBoss']: # check if hit by charging boss
        if player.invFrames == 0:
            if 'charge' in b.direction:
                chargeRect = Rect(b.x - b.w // 2, b.y - b.h, b.w, b.h)
                if hitbox.colliderect(chargeRect):
                    player.health = max(0, player.health - 2)
                    player.invFrames = 30
                    player.jumpboost = False
                    player.lazer = False

    for i in range(len(projectiles)): # check if hit by projectile
        if projectiles[i][-1] != 'bullet':
            ball = projectiles[i]
            if ball[-1] == 'cannonball':
                ballRect = Rect(ball[0], ball[1], 14, 14)
            if ball[-1] == 'metshot':
                ballRect = Rect(ball[0], ball[1], 14, 14)
            if ball[-1] == 'bigmetshot':
                ballRect = Rect(ball[0], ball[1], 52, 52)
            if ball[-1] in ['shockwaveE', 'shockwaveW']:
                ballRect = Rect(ball[0], ball[1], 18, 59)
            if ball[-1] in ['shockwaveN', 'shockwaveS']:
                ballRect = Rect(ball[0], ball[1], 59, 18)

            if hitbox.colliderect(ballRect): # take damage
                if player.invFrames == 0:
                    if ball[-1] == 'cannonball':
                        player.health = max(0, player.health - 2)
                    if ball[-1] == 'metshot':
                        player.health = max(0, player.health - 1)
                    if ball[-1] == 'bigmetshot':
                        player.health = max(0, player.health - 4)
                    if 'shockwave' in ball[-1]:
                        player.health = max(0, player.health - 2)
                    player.invFrames = 20
                    player.jumpboost = False
                    player.lazer = False
                remove.insert(0, i)

    for i in remove: # remove projectiles that hit the player
        del projectiles[i]

    screen.blit(player.pic, (player.x - player.pic.get_width() // 2, player.y - player.pic.get_height() // 2 + 3))
    checkConsumables(consumables, hitbox, levelScreen)


def updateHealth(h, screen): # blit hearts to show player's health
    # each heart shown = 2 health
    for i in range(0, 10, 2):
        if i + 2 <= h:
            index = 'full'
        elif i + 1 <= h:
            index = 'half'
        else:
            index = 'empty'
        screen.blit(heartPics[index], (10 + 23 * i, 10))


def updateArmadillos(armadillos, projectiles, lazers, offset, screen): # animate armadillos that are on the screen and check for damage
    global score
    remove = [] # projectiles that hit the armadillo
    dead = [] # dead armadillos

    for i in range(len(armadillos)): # check if player is hit by a player projectile (similar to player)
        armadillo = armadillos[i]
        if not armadillo.rolling: # cannot take damage while rolling
            hitbox = Rect(armadillo.x - armadillo.w // 2, armadillo.y - armadillo.h // 2, armadillo.w, armadillo.h)
            for j in range(len(projectiles)):
                projectile = projectiles[j]
                if projectile[-1] == 'bullet':
                    hitRect = Rect(projectile[0], projectile[1], 9, 7)
                    if hitbox.colliderect(hitRect):
                        armadillo.health -= 1
                        remove.insert(0, j)
            for lazer in lazers:
                lazerRect = Rect(lazer[0], lazer[1], 50, 7)
                if hitbox.colliderect(lazerRect):
                    armadillo.health -= 0.1  # because the lazer hits them every frame
                    break

        if armadillo.health <= 0: # remove dead armadillos
            score += 50
            dead.insert(0, i)
            deadEnemies.append([armadillo.x - 16, armadillo.y - 16, 0])
            enemyDeathSound.play()
        else:
            if offset - 25 <= armadillo.x <= offset + 825: # only animate armadillos that are on-screen
                armadillo.look()
            screen.blit(armadillo.pic, (armadillo.x - armadillo.w // 2, armadillo.y - armadillo.h // 2))

    for i in dead: # remove dead armadillos
        del armadillos[i]
    for i in remove: # remove player projectiles that hit
        del projectiles[i]

def updateMets(mets, projectiles, lazers, offset, screen): # animate mets that are on the screen and check for damage
    # this is almost exactly the same as the 'updateArmadillos' function -- met.move() instead of armadillo.look()
    global score
    remove = []
    dead = []
    for i in range(len(mets)):
        met = mets[i]
        hitbox = Rect(met.x - met.picW // 2, met.y - met.picH, met.picW, met.picH)
        for j in range(len(projectiles)):
            projectile = projectiles[j]
            if projectile[-1] == 'bullet':
                hitRect = Rect(projectile[0], projectile[1], 9, 7)
                if hitbox.colliderect(hitRect):
                    if met.picNum > 3:
                        met.health -= 1
                        remove.insert(0, j)
                    elif met.boss:
                        remove.insert(0, j)
        for lazer in lazers:
            lazerRect = Rect(lazer[0], lazer[1], 50, 7)
            if hitbox.colliderect(lazerRect):
                if met.picNum > 3:
                    met.health -= 0.1
                break

        if met.health <= 0:
            if met.boss:
                score += 250
                deadBosses.append([met.x-56, met.y-met.h//2-55, 0, 'met'])
            else:
                score += 10
                deadEnemies.append([met.x-16, met.y-met.h//2-16, 0])
            dead.insert(0, i)
            enemyDeathSound.play()
        else:
            if offset - 25 <= met.x <= offset + 825:
                met.move()
            screen.blit(met.pic, (met.x - met.picW // 2, met.y - met.picH + 1))
    for i in dead:
        del mets[i]
    for i in remove:
        del projectiles[i]


def updateCannons(cannons, projectiles, lazers, offset, screen): # animate cannons that are on the screen and check for damage
    # this is almost exactly the same as the 'updateArmadillos' function -- cannon.shoot() instead of armadillo.look()
    global score
    remove = []
    dead = []
    for i in range(len(cannons)):
        cannon = cannons[i]
        hitbox = Rect(cannon.x, cannon.y, cannon.w, cannon.h)
        for j in range(len(projectiles)):
            projectile = projectiles[j]
            if projectile[-1] == 'bullet':
                hitRect = Rect(projectile[0], projectile[1], 9, 7)
                if hitbox.colliderect(hitRect):
                    cannon.health -= 1
                    remove.insert(0, j)
        for lazer in lazers:
            lazerRect = Rect(lazer[0], lazer[1], 50, 7)
            if hitbox.colliderect(lazerRect):
                cannon.health -= 0.1
                break

        if cannon.health <= 0:
            score += 100
            dead.insert(0, i)
            deadEnemies.append([cannon.x + 2, cannon.y + 12, 0])
            enemyDeathSound.play()
        else:
            if offset - 25 <= cannon.x <= offset + 825:
                cannon.shoot()
            screen.blit(cannon.pic, (cannon.x, cannon.y))
    for i in dead:
        del cannons[i]
    for i in remove:
        del projectiles[i]

def updateFinalBoss(bosses, projectiles, lazers, screen):
    # this is almost exactly the same as the 'updateArmadillos' function -- boss.move() instead of armadillo.look()
    global score
    remove = []
    dead = []
    for i in range(len(bosses)):
        boss = bosses[i]
        hitbox = Rect(boss.x - boss.w // 2, boss.y - boss.h, boss.w, boss.h)
        for j in range(len(projectiles)):
            projectile = projectiles[j]
            if projectile[-1] == 'bullet':
                hitRect = Rect(projectile[0], projectile[1], 9, 7)
                if hitbox.colliderect(hitRect):
                    boss.health -= 1
                    remove.insert(0, j)
        for lazer in lazers:
            lazerRect = Rect(lazer[0], lazer[1], 50, 7)
            if hitbox.colliderect(lazerRect):
                boss.health -= 0.1
                break

        if boss.health <= 0:
            score += 1000
            dead.insert(0, i)
            for i in range(10):
                deadEnemies.append([boss.x - randint(-boss.w//2, boss.w//2), boss.y - randint(0, boss.h), 0-i*15])
                enemyDeathSound.play()
        else:
            boss.move()
            screen.blit(boss.pic, (boss.x - boss.w // 2, boss.y - boss.h))
    for i in dead:
        del bosses[i]
    for i in remove:
        del projectiles[i]


def updateEnemies(enemies, projectiles, lazers, offset, screen): # call all enemy update functions (neatness)
    updateArmadillos(enemies['armadillos'], projectiles, lazers, offset, screen)
    updateMets(enemies['mets'], projectiles, lazers, offset, screen)
    updateCannons(enemies['cannons'], projectiles, lazers, offset, screen)
    updateFinalBoss(enemies['finalBoss'], projectiles, lazers, screen)


def updateProjectiles(projectiles, levelScreen, screen): # move projectiles
    offscreen = [] # holds projectiles that are off-screen
    for i in range(len(projectiles)):
        projectiles[i][0] += projectiles[i][2]
        projectiles[i][1] += projectiles[i][3]
        if projectiles[i][-1] == 'cannonball': # only cannonballs move parabolically
            projectiles[i][3] += 0.1
        if projectiles[i][0] < offset-25 or projectiles[i][0] > offset+25 + screen.get_width() or projectiles[i][1] > screen.get_height()+25 or projectiles[i][1] < 0 and projectiles[i][-1] != 'cannonball':
            # cannonballs will come back down
            offscreen.insert(0, i)

    for i in offscreen: # removes projectiles that are off-screen
        del projectiles[i]
    for projectile in projectiles:
        levelScreen.blit(shotPics[projectile[-1]], (projectile[0], projectile[1]))


def updateLazers(lazers, levelScreen, screen): # move lasers shot by player
    offscreen = []
    for i in range(len(lazers)):
        # all lazers are in the form of [x, y, locked (bool), direction]
        if lazers[i][-1] == 'R':
            lazers[i][0] += 10
        else:
            lazers[i][0] -= 10
        if lazers[i][0] < offset-25 or lazers[i][0] > offset+25 + screen.get_width() or lazers[i][1] < 0-25 or lazers[i][1] > screen.get_height()+25:
            offscreen.insert(0, i)
        if lazers[i][-1] != player.direction[-1]:
            lazers[i][2] = True
        if not lazers[i][2]:
            lazers[i][1] = player.y - 4

    for i in offscreen:
        del lazers[i]
    for lazer in lazers:
        levelScreen.blit(shotPics['lazer'], (lazer[0], lazer[1]))


def checkConsumables(consumables, hitbox, screen): # animate power-ups and check if player has collected one
    remove = [] # hold consumables that have been collected
    for i in range(len(consumables)):
        consumable = consumables[i]
        if hitbox.colliderect(Rect(consumable[:4])):
            if consumable[-1] == 'healthfull':
                healthUpSound.play()
                player.health = 10
            elif consumable[-1] == 'healthboost':
                healthUpSound.play()
                player.health = min(10, player.health + 2)
            elif consumable[-1] == 'jumpboost':
                powerUpSound.play()
                player.jumpboost = True
            elif consumable[-1] == 'lazer':
                powerUpSound.play()
                player.lazer = True
            remove.insert(0, i)

    for i in remove: # remove consumables that have been collected
        del consumables[i]
    for consumable in consumables:
        screen.blit(consumePics[consumable[-1]][consumable[4]], (consumable[:2]))
        consumable[4] = (consumable[4] + 1) % 84


def updatePlatforms(platforms, screen): # move and blit platforms
    for p in platforms:
        p.move()
        screen.blit(p.pic, (p.x, p.y))


def levelInterpret(level, background): # convert a list of strings into a level
    armRects = [] # 20 by 20 Rects in which the current armadillo is confined
    platWH = 0 # width of current horizontally-moving platform
    platPosH = [] # [x, y] position of current horizontally-moving platform
    platSpaceH = [] # Rects in which the current horizontally-moving platform is confined
    platWV = 0 # width of current vertically-moving platform
    platPosV = [] # [x, y] position of current vertically-moving platform
    platSpaceV = [] # Rects in which the current vertically-moving platform is confined

    for i in range(len(level)):
        for j in range(len(level[i])):
            block = level[i][j]

            if block in ['U', 'G', 'B', 'S', 'W']: # stationary blocks
                if block == 'U':
                    background.blit(blockPics['upground'],(j*20,i*20))
                elif block == 'G':
                    background.blit(blockPics['ground'], (j * 20, i * 20))
                elif block == 'B':
                    background.blit(blockPics['brick'], (j * 20, i * 20))
                elif block == 'S':
                    background.blit(blockPics['smooth_rock'], (j * 20, i * 20))
                elif block == 'W':
                    background.blit(blockPics['weird_tile'], (j * 20, i * 20))
                walls.append(Rect(j*20,i*20, 20,20))

            if block in ['P', 'p']: # horizontally-moving platform represented by a string of upper and lower case p's
                # "P" represents the platform, padded with "p"s that define how far left and right the platform can move
                if block == 'P':
                    platWH += 20
                    if not platPosH:
                        platPosH = [j*20, i*20]
                platSpaceH.append(Rect(j*20, i*20, 20, 20))
            else:
                if platPosH:
                    platforms.append(movePlatform(platPosH[0], platPosH[1], platWH, platSpaceH[0].unionall(platSpaceH[1:]), 'H'))
                    platWH = 0
                    platPosH = []
                    platSpaceH = []

            if block == 'V': # vertically-moving platform represented by a string of upper case V's
                platWV += 20
                if not platPosV:
                    platPosV = [j*20, (i+1)*20]
                platSpaceV.append(Rect(j * 20, i * 20, 20, 20))
                if len(platSpaceV) == 1: # above and below the leftmost "V" are "v"s that define how high and low the platform can move
                    platI, platJ = i - 1, j
                    while platI >= 0 and level[platI][platJ] in ['V', 'v']:
                        platSpaceV.append(Rect(platJ * 20, platI * 20, 20, 20))
                        platI -= 1
                    platI, platJ = i + 1, j
                    while platI < len(level) and level[platI][platJ] in ['V', 'v']:
                        platSpaceV.append(Rect(platJ * 20, platI * 20, 20, 20))
                        platI += 1
            else:
                if platPosV:
                    platforms.append(movePlatform(platPosV[0], platPosV[1], platWV, platSpaceV[0].unionall(platSpaceV[1:]), 'V'))
                    platWV = 0
                    platPosV = []
                    platSpaceV = []

            if block == 'd': # start door
                startPoint = [j*20, i*20-20]

            if block == 'D': # end door
                endPoint = [j*20, i*20-20]

            # enemies
            if block in ['A', 'a']: # armadillos - same idea as horizontally-moving platforms but with A's instead of P's
                if block == 'A':
                    armx, army = j*20, i*20
                armRects.append(Rect(j*20,i*20-20, 20,40))
            else:
                if armRects:
                    enemies['armadillos'].append(armadillo(armx, army+12, 'left', armRects[0].unionall(armRects[1:])))
                    armRects = []

            if block == 'M':
                enemies['mets'].append(met(j*20, i*20+20, 'left'))

            if block == 'm': # boss met
                enemies['mets'].append(met(j*20, i*20+20, 'left', boss=True))

            if block == 'C':
                enemies['cannons'].append(cannon(j*20, i*20-30, 'left'))
            if block == 'c':
                enemies['cannons'].append(cannon(j*20, i*20-30, 'right'))

            if block == 'F':
                enemies['finalBoss'].append(finalBoss(j * 20 + 10, i * 20 + 20))
            if block == 'X':
                bossAtkPos.append((j*20+10, i*20+20))

            # consumables
            if block == 'H':
                consumables.append([j*20, i*20, 20, 20, 0, 'healthfull'])
            if block == 'h':
                consumables.append([j*20, i*20, 20, 20, 0, 'healthboost'])
            if block == 'J':
                consumables.append([j*20, i*20, 20, 20, 0, 'jumpboost'])
            if block == 'L':
                consumables.append([j*20, i*20, 20, 20, 0, 'lazer'])

    doorPos.extend(startPoint + endPoint)
    background.blit(blockPics['start_door'], (startPoint[0], startPoint[1]))
    background.blit(blockPics['end_door'], (endPoint[0], endPoint[1]))


def clear_level(): # reset level variables
    global walls, platforms, projectiles, lazers, consumables, enemies, deadEnemies, doorPos, bossAtkPos, start_time
    walls = []
    platforms = []
    projectiles = []
    lazers = []
    consumables = []
    enemies = {'armadillos': [], 'cannons': [], 'mets': [], 'finalBoss': []}
    deadEnemies = []
    doorPos = []
    bossAtkPos = []
    start_time = clock()


def fadeIn(screen, fps): # fade into a new screen
    screencopy = screen.copy()
    fadeSurface = Surface((800, 600)).convert()
    for i in range(int(fps*2)):
        fadeSurface.set_alpha(255 - i/(fps*2)*255) # cover gets lighter (based on fps to prevent lag)
        screen.blit(screencopy, (0, 0))
        screen.blit(fadeSurface, (0, 0))
        display.flip()
    screen.blit(screencopy, (0, 0))

def fadeOut(screen, fps): # fade out of a screen
    screencopy = screen.copy()
    fadeSurface = Surface((800, 600)).convert()
    for i in range(int(fps*2)):
        fadeSurface.set_alpha(i/(fps*2)*255) # cover gets darker (based on fps to prevent lag)
        screen.blit(screencopy, (0, 0))
        screen.blit(fadeSurface, (0, 0))
        display.flip()

def backgroundMusic(musicType): # musicType is the music to be played
    if musicType == 'menu':
        mixer.music.load("music/MainMenuMusic.ogg")
    elif musicType == 'game':
        mixer.music.load("music/RegularStageMusic.ogg")
    elif musicType == 'boss':
        mixer.music.load("music/FinalBossMusic.ogg")
    mixer.music.set_volume(0.2)
    mixer.music.play(-1)

#######################################################################
# uploading images

consumePics = {'healthfull': [],
               'healthboost': [],
               'jumpboost': [],
               'lazer': []} # images of power-ups

for i in range(12):
    consumePics['healthfull'].extend([image.load('consumables/heartItem/heartItem' + str(i) + '.png')] * 7)
    consumePics['jumpboost'].extend([image.load('consumables/bootItem/bootItem' + str(i) + '.png')] * 7)
    consumePics['lazer'].extend([image.load('consumables/lazerItem/lazerItem' + str(i) + '.png')] * 7)
    consumePics['healthboost'].extend([image.load('consumables/halfheartItem/halfheartItem' + str(i) + '.png')] * 7)

blockPics = {'brick': image.load('tiles/brick.png'),
             'ground': image.load('tiles/ground.png'),
             'upground': image.load('tiles/upground.png'),
             'platform': image.load('tiles/platform.png'),
             'start_door': image.load('tiles/start door.png'),
             'end_door': image.load('tiles/end door.png'),
             'weird_tile': image.load('tiles/green tile.png'),
             'smooth_rock': image.load('tiles/ceramic.png')}# images of blocks

# player
playerPics = {'standL': [], 'standR': [],
              'walkL': [], 'walkR': [],
              'jumpL': [], 'jumpR': [],
              'atkstandL': [], 'atkstandR': [],
              'atkwalkL': [], 'atkwalkR': [],
              'atkjumpL': [], 'atkjumpR': [],
              'deathL': [], 'deathR': []}  # image for every possible position for the player
# uploading images and horizontally reflecting them
playerPics['standR'].append(image.load('megaman sprite/stand_right/stand_right0.png'))
playerPics['standL'].append(transform.flip(playerPics['standR'][0], True, False))
playerPics['atkstandR'].append(image.load('megaman sprite/atkstand_right/atkstand_right0.png'))
playerPics['atkstandL'].append(transform.flip(playerPics['atkstandR'][0], True, False))
for i in range(10):
    playerPics['walkR'].extend([image.load('megaman sprite/run_right/run_right' + str(i) + '.png')] * 4)
    playerPics['atkwalkR'].extend([image.load('megaman sprite/atkrun_right/atkrun_right' + str(i) + '.png')] * 4)
for right in playerPics['walkR']:
    playerPics['walkL'].append(transform.flip(right, True, False))
for right in playerPics['atkwalkR']:
    playerPics['atkwalkL'].append(transform.flip(right, True, False))
for i in range(6):
    playerPics['jumpR'].extend([image.load('megaman sprite/jump_right/jump_right' + str(i) + '.png')])
    playerPics['atkjumpR'].extend([image.load('megaman sprite/atkjump_right/atkjump_right' + str(i) + '.png')])
for right in playerPics['jumpR']:
    playerPics['jumpL'].append(transform.flip(right, True, False))
for right in playerPics['atkjumpR']:
    playerPics['atkjumpL'].append(transform.flip(right, True, False))
for i in range(5):
    playerPics['deathR'].extend([image.load('megaman sprite/death/death' + str(i) + '.png')])
for right in playerPics['deathR']:
    playerPics['deathL'].append(transform.flip(right, True, False))

# hearts (player health)
heartPics = {'full': image.load('hearts/heart_full.png'),
             'half': image.load('hearts/heart_half.png'),
             'empty': image.load('hearts/heart_empty.png')} # images of hearts

# armadillo
armadilloPics = {'left': [], 'right': []} # image for every possible position for armadillos
# uploading images and horizontally reflecting them
for i in range(8):
    armadilloPics['left'].append(image.load('armadillo_left/armadillo_left' + str(i) + '.png'))
for left in armadilloPics['left']:
    armadilloPics['right'].append(transform.flip(left, True, False))

# cannon
cannonPics = {'left': [], 'right': []} # image for every possible position for cannons
# uploading images and horizontally reflecting them
for i in range(4):
    cannonPics['left'].extend([image.load('cannon_left/cannon_left' + str(i) + '.png')] * 5)
for left in cannonPics['left']:
    cannonPics['right'].append(transform.flip(left, True, False))

# met
metPics = {'left': [], 'right': []} # image for every possible position for mets
# play through each action at a different speed
for i in range(8):
    if i == 4 or i == 5:
        multiplier = 8
    elif i == 6:
        multiplier = 32
    else:
        multiplier = 4
    metPics['left'].extend([image.load('met/met' + str(i) + '.png')] * multiplier)
# horizontally reflecting met images
for left in metPics['left']:
    metPics['right'].append(transform.flip(left, True, False))

# final boss
bossPics = {'standL': [], 'standR': [],
            'flyL': [], 'flyR': [],
            'slashL': [], 'slashR': [],
            'chargeL': [], 'chargeR': []} # image for every possible position for boss
# uploading images and horizontally reflecting them
bossPics['standR'].append(image.load('boss/stand/stand0.png'))
bossPics['standL'].append(transform.flip(bossPics['standR'][0], True, False))
for i in range(4):
    bossPics['flyR'].extend([image.load('boss/fly/fly' + str(i) + '.png')] * 5)
for i in bossPics['flyR']:
    bossPics['flyL'].append(transform.flip(i, True, False))
for i in range(8):
    bossPics['slashR'].extend([image.load('boss/slash/slash' + str(i) + '.png')] * 5)
for i in bossPics['slashR']:
    bossPics['slashL'].append(transform.flip(i, True, False))
for i in range(6):
    bossPics['chargeR'].extend([image.load('boss/charge/charge' + str(i) + '.png')] * 5)
for i in bossPics['chargeR']:
    bossPics['chargeL'].append(transform.flip(i, True, False))

# this is for when an enemy dies
explosionPics = []
bossExplosionPics = {'met': []}
for i in range(7):
    explosionPics.extend([image.load('explosion/explosion' + str(i) + '.png')] * 3)
    bossExplosionPics['met'].extend([transform.scale(image.load('explosion/explosion' + str(i) + '.png'), (124,124))] * 5)

# projectiles and laser
shotPics = {'bullet': image.load('projectiles/bullet.png'),
            'cannonball': image.load('projectiles/cannonball.png'),
            'metshot': image.load('projectiles/metshot.png'),
            'bigmetshot': transform.scale(image.load('projectiles/metshot.png'), (52,52)),
            'lazer': image.load('projectiles/lazer.png')}  # images of projectiles and laser beams
# loads shockwave of different orientations
for i in ['N', 'E', 'S', 'W']:
    shotPics['shockwave' + i] = image.load('projectiles/shockwave'+i+'.png')

# fireworks
fireworkPics = {}
for i in ['Blue', 'Green', 'Orange', 'Purple', 'Red', 'Yellow']:
    fireworkPics[i] = []
    for j in range(14):
        fireworkPics[i].extend([image.load('fireworks/firework' + i + '/' + 'firework' + i + str(j) + '.png')] * 1) # 35

# images for menus
logo = image.load("menu graphics/MegamanLogo.png")
stars = image.load('menu graphics/menuBackground.png')
arrowLeft = image.load("menu graphics/arrowLeft.png")
arrowRight = image.load("menu graphics/arrowRight.png")
lockPic = image.load("menu graphics/lock.png")

#######################################################################
# screens, images, text

# main menu
menuScreen = Surface((800, 600))
menuScreen.blit(transform.scale(stars, (800, 600)), (0, 0))
menuScreen.blit(transform.scale(logo, (700, 300)), (50, 10))

start_text = bitfont40.render('START', 0, (255, 255, 255, 255)) # start button
startRect = Rect(400-start_text.get_width()//2-10, 315, 20+start_text.get_width(), 10+start_text.get_height())
menuScreen.blit(start_text, (400-start_text.get_width()//2, 320))

level_text = bitfont40.render('LEVEL SELECT', 0, (255, 255, 255, 255)) # level select button
levelRect = Rect(400-level_text.get_width()//2-10, 365, 20+level_text.get_width(), 10+level_text.get_height())
menuScreen.blit(level_text, (400-level_text.get_width()//2, 370))

load_text = bitfont40.render('LOAD', 0, (255, 255, 255, 255)) # load progress button
loadRect = Rect(400-load_text.get_width()//2-10, 415, 20+load_text.get_width(), 10+load_text.get_height())
menuScreen.blit(load_text, (400-load_text.get_width()//2, 420))

scores_text = bitfont40.render('HIGH SCORES', 0, (255, 255, 255, 255)) # high scores button
scoresRect = Rect(400-scores_text.get_width()//2-10, 465, 20+scores_text.get_width(), 10+scores_text.get_height())
menuScreen.blit(scores_text, (400-scores_text.get_width()//2, 470))

credits_text = bitfont40.render('CREDITS', 0, (255, 255, 255, 255)) # credits button
creditRect = Rect(400-credits_text.get_width()//2-10, 515, 20+credits_text.get_width(), 10+credits_text.get_height())
menuScreen.blit(credits_text, (400-credits_text.get_width()//2, 520))


# back button (used in more than one screen)
back_text = bitfont40.render('BACK', 0, (255, 255, 255, 255))
backRect = Rect(700-back_text.get_width()//2, 550-back_text.get_height()//2, 20+back_text.get_width(), 20+back_text.get_height())


# level selection
selectionScreen = Surface((800, 600))
selectionScreen.blit(transform.scale(stars, (800, 600)), (0, 0))
selectionScreen.blit(level_text, (400-level_text.get_width()//2, 20))

levelNames = ['TUTORIAL', 'OPENER', 'DODGE', 'FOREST', 'METS', 'MAZE', 'PLATFORMS', 'JUMP', 'FINAL'] # name of each level
levelTextColours = [(0, 0, 0, 255), (0, 0, 0, 255), (0, 0, 0, 255), (0, 0, 0, 255), (0, 0, 0, 255), (255, 255, 255, 255), (0, 0, 0, 255), (0, 0, 0, 255), (255, 255, 255, 255)]
    # colour (for score and time left) for each level

# each level is a folder of stages
    # each stage is [letter].txt, with its corresponding background image [letter].png

levelRects = [] # buttons for each level
for i in range(3): # arrange level buttons
    for j in range(3):
        level_name = bitfont40.render(levelNames[i*3+j], 0, (255, 255, 255, 255))
        namex, namey = 200+j*200, 150+i*150
        levelRects.append(Rect(namex-level_name.get_width()//2-10, namey-level_name.get_height()//2-10, 20+level_name.get_width(), 20+level_name.get_height()))
        selectionScreen.blit(level_name, (namex-level_name.get_width()//2, namey-level_name.get_height()//2))

# level files
levels = [] # where levels[level][stage] is a file name
levelBackgroundPics = [] # where levelBackgroundPics[level][stage] is an image
for name in levelNames: #load in levels
    levels.append(glob('levels/'+name+'/*.txt'))
    stagePics = []
    for l in levels[-1]:
        stage = l[:-4].split('\\')[-1] # needs to be .split('/') on Mac
        stagePics.append(image.load('levels/'+name+'/'+stage+'.png'))
    levelBackgroundPics.append(stagePics)

selectionScreen.blit(back_text, (710-back_text.get_width()//2, 560-back_text.get_height()//2)) # back button

save_text = bitfont40.render('SAVE', 0, (255, 255, 255, 255)) # save progress button
saveRect = Rect(710-save_text.get_width()//2-10, 15, 20+save_text.get_width(), 10+save_text.get_height())
selectionScreen.blit(save_text, (710-save_text.get_width()//2, 20))

# credits
creditScreen = Surface((800, 600))
creditScreen.blit(transform.scale(stars, (800, 600)), (0, 0))
creditScreen.blit(back_text, (710-back_text.get_width()//2, 560-back_text.get_height()//2))

creditScreen_text = ['Alec Mai & Scott Xu', 'Teacher: Mr. McKenzie', 'ICS3U FSE', '2016 - 2017']
for i in range(len(creditScreen_text)):
    credit_text = bitfont40.render(creditScreen_text[i], 0, (255, 255, 255, 255))
    creditScreen.blit(credit_text, (400-credit_text.get_width()//2, 50 + 50*i))

#save score screen
scoreScreen = Surface((800,600))
scoreScreen.blit(transform.scale(stars, (800, 600)), (0, 0))

yes_text = bitfont40.render('SAVE', 0, (255, 255, 255, 255)) # save button
yesRect = Rect(300-yes_text.get_width()//2-10, 345, 20+yes_text.get_width(), 10+yes_text.get_height())
scoreScreen.blit(yes_text, (300-yes_text.get_width()//2, 350))

no_text = bitfont40.render('CANCEL', 0, (255, 255, 255, 255)) # cancel button
noRect = Rect(500-no_text.get_width()//2-10, 345, 20+no_text.get_width(), 10+no_text.get_height())
scoreScreen.blit(no_text, (500-no_text.get_width()//2, 350))

saveas_text = bitfont40.render('ENTER NAME:', 0, (255, 255, 255, 255))
scoreScreen.blit(saveas_text, (400-saveas_text.get_width()//2, 200))

#highscore screen
highscoreScreen = Surface((800,600))
highscoreScreen.blit(transform.scale(stars, (800, 600)), (0, 0))

highscore_text = bitfont40.render('HIGH SCORES', 0, (255, 255, 255, 255))
highscoreScreen.blit(highscore_text, (400-highscore_text.get_width()//2, 50))

highscoreScreen.blit(back_text, (710-back_text.get_width()//2, 560-back_text.get_height()//2)) # back button

#game over text
gameOverText = bitfont120.render('GAME OVER', 0, (200, 20, 20, 255))

#level complete text
levelCompleteText = bitfont120.render('LEVEL COMPLETE', 0, (255, 255, 255, 255))

#game complete text
winScreen = Surface((800, 600))
winText = bitfont120.render('GAME COMPLETE', 0, (255, 255, 255, 255))
winScreen.blit(winText, (400-winText.get_width()//2, 300-winText.get_height()//2))

#######################################################################
# sounds

# player sounds
playerShotSound = mixer.Sound("sound effects/Player Shot.wav")
playerShotSound.set_volume(0.4)
playerJumpSound = mixer.Sound("sound effects/Player Jump.wav")
playerJumpSound.set_volume(0.4)
playerLazerSound = mixer.Sound("sound effects/Lazer Sound.wav")
playerLazerSound.set_volume(0.4)

# enemy sounds
metShotSound = mixer.Sound("sound effects/Met Shot.wav")
metShotSound.set_volume(0.2)
cannonShotSound = mixer.Sound("sound effects/Cannon Shot.wav")
armadilloDashSound = mixer.Sound("sound effects/Armadillo Dash.wav")
bossSlashSound = mixer.Sound("sound effects/Boss Slash.wav")
bossSlashSound.set_volume(0.4)
bossChargeSound = mixer.Sound("sound effects/Boss Charge.wav")
bossChargeSound.set_volume(0.4)

# consumable sounds
healthUpSound = mixer.Sound("sound effects/Player Health Up.wav")
healthUpSound.set_volume(0.3)
powerUpSound = mixer.Sound("sound effects/Power Up.wav")
powerUpSound.set_volume(0.3)

# misc sounds
enemyDeathSound = mixer.Sound("sound effects/Enemy Death.wav")
enemyDeathSound.set_volume(0.5)
fireworkSound = mixer.Sound("sound effects/Firework.wav")
doorSound = mixer.Sound("sound effects/Door Sound.wav")

#######################################################################
# game music

#music starts at main menu
mixer.music.load("music/MainMenuMusic.ogg")
mixer.music.set_volume(0.2)
mixer.music.play(-1)

#######################################################################
# level and game data

moves = {'up': False, 'right': False, 'left': False, 'atk': False, 'enter': False}  # which keys are pressed (atk = space bar)
offset = 0 # offset of screen to move with player

walls = [] # Rects that the player cannot pass through
platforms = [] # moving platforms
projectiles = []  # all of the form [x, y, vx, vy, type]
lazers = []  # in the form of [x, y, locked (bool), direction] -- locked is whether or not the y-coord of the laser is fixed
consumables = []  # of the form [x, y, width, height, picNum, type]
enemies = {'armadillos': [], 'cannons': [], 'mets': [], 'finalBoss': []}  # stores all enemies
deadEnemies = [] # all of the form [x, y, picNum]
deadBosses = [] # all of the form [x, y, picNum]
doorPos = [] # x of start, y of start, x of end, y of end
bossAtkPos = [] # where the final boss can fly to
fireworks = [] # all of the form [x, y, colour, picNum, scale]
start_time = clock()

score = 0 # hold player socre
progress = 9 # holds furthest level player has reached
currentMusic = 'menu' # holds music that is playing
player_dead = False # holds whether or not the player is dead
newStage = False # holds whether or not the player has between a stage
current_level, current_stage = 0, 0 # holds what level, stage player is on
current_screen = 'menu' # holds what screen the user is on
saveName = '' # holds the user's save name for saving score

click, release = False, False # mouse status
#######################################################################
# game loop

screen = display.set_mode((800, 600))
running = True
myClock = time.Clock()

while running:
    for evt in event.get():
        if evt.type == QUIT:
            running = False

        if evt.type == KEYDOWN:
            try:
                if evt.key == K_UP and player.onground: # can only jump if player on ground
                    moves['up'] = True
                if evt.key == K_RIGHT:
                    moves['right'] = True
                if evt.key == K_LEFT:
                    moves['left'] = True
                if evt.key == K_SPACE:
                    moves['atk'] = True
                if evt.key == K_RETURN:
                    moves['enter'] = True
            except:
                pass

            if current_screen == 'save_score':
                try:
                    if evt.key == K_BACKSPACE: # typing save name
                        saveName = saveName[:-1]
                    elif len(saveName) < 10: # character limit of 10
                        saveName += evt.unicode
                except:
                    pass

        if evt.type == KEYUP:
            try:
                if evt.key == K_UP:
                    moves['up'] = False
                if evt.key == K_RIGHT:
                    moves['right'] = False
                if evt.key == K_LEFT:
                    moves['left'] = False
                if evt.key == K_SPACE:
                    moves['atk'] = False
                if evt.key == K_RETURN:
                    moves['enter'] = False
            except:
                pass

        if evt.type == MOUSEBUTTONDOWN:
            if evt.button == 1:
                click = True

        if evt.type == MOUSEBUTTONUP:
            if evt.button == 1:
                release = True

    mx, my = mouse.get_pos() # position of mouse on screen

    if current_screen == 'menu':

        if currentMusic != 'menu': # changes music
            currentMusic = 'menu'
            backgroundMusic(currentMusic)

        screen.blit(menuScreen, (0, 0))
        if startRect.collidepoint(mx, my):
            #shows selected
            screen.blit(arrowLeft, (startRect.left-18, startRect.top+7))
            screen.blit(arrowRight, (startRect.right - 6, startRect.top + 7))
            if click: # begins game at tutorial
                current_level, current_stage = 0, 1
                #loads level
                level_file = open(levels[current_level][current_stage-1])
                level = level_file.read().strip().split('\n')
                levelBackground = Surface((20 * max([len(i) for i in level]), 600))
                for i in range(0, levelBackground.get_width(), levelBackgroundPics[current_level][current_stage-1].get_width()):
                    levelBackground.blit(levelBackgroundPics[current_level][current_stage-1], (i, 0))

                clear_level()
                levelInterpret(level, levelBackground)
                player = character(doorPos[0] + 5, doorPos[1]) # spawn player
                current_screen = 'game'
                newStage = True

        if levelRect.collidepoint(mx,my):
            # shows selected
            screen.blit(arrowLeft, (levelRect.left-18, levelRect.top+7))
            screen.blit(arrowRight, (levelRect.right - 6, levelRect.top + 7))
            if click: # levelselect
                current_screen = 'levelSelect'

        if loadRect.collidepoint(mx,my):
            # shows selected
            screen.blit(arrowLeft, (loadRect.left-18, loadRect.top+7))
            screen.blit(arrowRight, (loadRect.right - 6, loadRect.top + 7))
            if click: # load file
                result = filedialog.askopenfilename()
                try:
                    loadfile = open(result)
                    score, progress = map(int, loadfile.readline().split(","))
                except:
                    pass

        if scoresRect.collidepoint(mx,my):
            # shows selected
            screen.blit(arrowLeft, (scoresRect.left-18, scoresRect.top+7))
            screen.blit(arrowRight, (scoresRect.right - 6, scoresRect.top + 7))
            if click: # scores
                current_screen = 'high_scores'

        if creditRect.collidepoint(mx,my):
            # shows selected
            screen.blit(arrowLeft, (creditRect.left-18, creditRect.top+7))
            screen.blit(arrowRight, (creditRect.right - 6, creditRect.top + 7))
            if click: # credits
                current_screen = 'credits'

    elif current_screen == 'levelSelect':

        if currentMusic != 'game': # changes music
            currentMusic = 'game'
            backgroundMusic(currentMusic)

        screen.blit(selectionScreen, (0,0))
        if backRect.collidepoint(mx, my):
            # shows selected
            screen.blit(arrowLeft, (backRect.left - 18, backRect.top + 12))
            screen.blit(arrowRight, (backRect.right - 6, backRect.top + 12))
            if click:
                current_screen = 'menu'

        if saveRect.collidepoint(mx, my):
            # shows selected
            screen.blit(arrowLeft, (saveRect.left - 18, saveRect.top + 7))
            screen.blit(arrowRight, (saveRect.right - 6, saveRect.top + 7))
            if click:
                result = filedialog.asksaveasfilename().split('/')[-1]
                if result: # saves progress
                    savefile = open('saves/'+result+'.txt', "w")
                    savefile.write("%d,%d" % (score, progress))
                    savefile.close()

        for i in range(len(levelRects)):
            if levelRects[i].collidepoint((mx, my)):
                if i <= progress:
                    # shows selected
                    screen.blit(arrowLeft, (levelRects[i].left - 18, levelRects[i].top + 12))
                    screen.blit(arrowRight, (levelRects[i].right - 6, levelRects[i].top + 12))
                    if click:
                        #loads level
                        current_level, current_stage = i, 1
                        level_file = open(levels[current_level][current_stage-1])
                        level = level_file.read().strip().split('\n')
                        levelBackground = Surface((20 * max([len(i) for i in level]), 600))
                        for i in range(0, levelBackground.get_width(), levelBackgroundPics[current_level][current_stage-1].get_width()):
                            levelBackground.blit(levelBackgroundPics[current_level][current_stage-1], (i, 0))
                        clear_level()
                        levelInterpret(level, levelBackground)
                        player = character(doorPos[0] + 5, doorPos[1])
                        current_screen = 'game'
                        newStage = True
                        break

                else:
                    # shows selected
                    screen.blit(lockPic, (levelRects[i].left - 30, levelRects[i].top + 12))
                    screen.blit(lockPic, (levelRects[i].right - 2, levelRects[i].top + 12))

    elif current_screen == 'credits':

        if currentMusic != 'menu': # changes music
            currentMusic = 'menu'
            backgroundMusic(currentMusic)

        screen.blit(creditScreen, (0,0))
        if backRect.collidepoint(mx, my):
            screen.blit(arrowLeft, (backRect.left - 18, backRect.top + 12))
            screen.blit(arrowRight, (backRect.right - 6, backRect.top + 12))
            if click:
                current_screen = 'menu'

    elif current_screen == 'game':

        if currentMusic != 'game'  and len(enemies['finalBoss']) == 0: # changes music
            currentMusic = 'game'
            backgroundMusic(currentMusic)
        elif currentMusic != 'boss' and len(enemies['finalBoss']) != 0: # changes music
            currentMusic = 'boss'
            backgroundMusic(currentMusic)

        levelScreen = levelBackground.copy()
        # updates
        updatePlatforms(platforms, levelScreen)
        updateProjectiles(projectiles, levelScreen, screen)
        updateLazers(lazers, levelScreen, screen)
        updateEnemies(enemies, projectiles, lazers, offset, levelScreen)
        updatePlayer(player, enemies, projectiles, consumables, levelScreen)

        # removes dead enemies
        remove = []
        for i in range(len(deadEnemies)):
            d = deadEnemies[i]
            if d[2] >= 0:
                levelScreen.blit(explosionPics[d[2]], (d[0], d[1]))
            d[2] += 1
            if d[2] >= len(explosionPics):
                remove.insert(0, i)
        for i in remove:
            del deadEnemies[i]

        # removes dead bosses
        remove = []
        for i in range(len(deadBosses)):
            d = deadBosses[i]
            levelScreen.blit(bossExplosionPics[d[3]][d[2]], (d[0], d[1]))
            d[2] += 1
            if d[2] >= len(bossExplosionPics[d[3]]):
                remove.insert(0, i)
        for i in remove:
            del deadBosses[i]

        # update offset of screen
        offset = max(player.x - screen.get_width() // 2, 0)
        offset = min(offset, levelBackground.get_width() - screen.get_width())
        screen.blit(levelScreen, (0 - offset, 0))

        updateHealth(player.health, screen)

        # show time left and score
        score = min(score, 99999)
        timetext = bitfont20.render('Time', 0, levelTextColours[current_level])
        screen.blit(timetext, (screen.get_size()[0] - (timetext.get_size()[0] + 30), 20))
        timeleft = int(120 + start_time - clock())
        timelefttext = bitfont20.render('%d:%02d' % (timeleft // 60, timeleft % 60), 0, levelTextColours[current_level])
        screen.blit(timelefttext, (screen.get_size()[0] - (timetext.get_size()[0] + 30), 40))
        scoreword = bitfont20.render('Score', 0, levelTextColours[current_level])
        screen.blit(scoreword, (screen.get_size()[0] - (timetext.get_size()[0] + 30), 70))
        scoretext = bitfont20.render('%05d' % (score), 0, levelTextColours[current_level])
        screen.blit(scoretext, (screen.get_size()[0] - (timetext.get_size()[0] + 30), 90))

        if newStage:
            fadeIn(screen, fps)
            newStage = False

        # player losses/dies
        if player.health <= 0 or timeleft <= 0:
            player.show_death()
            fadeOut(screen, fps)
            player_dead = True
            current_screen = 'save_score'
            continue

        # player completes a stage
        endDoor = Rect(doorPos[2], doorPos[3], 20, 40)
        playerRect = Rect(player.x - 10, player.y - 10, 20, 20)
        # player must defeat all bosses to complete a stage
        if endDoor.colliderect(playerRect) and len(enemies['finalBoss']) == 0 and not any([met.boss for met in enemies['mets']]):
            if moves['enter']:
                doorSound.play()
                score += timeleft//5 # increase score based on time left
                fadeOut(screen, fps)
                current_stage += 1
                # reach end of level
                if current_stage > len(levels[current_level]):
                    if current_level == progress:
                        progress += 1
                        if progress == 9: # player beat last level
                            fadeOut(screen, fps)
                            clear_level()
                            current_screen = 'fireworks'
                    else:
                        screen.blit(transform.scale(stars, (800, 600)), (0, 0))
                        screen.blit(levelCompleteText, (400 - levelCompleteText.get_width()//2, 300 - levelCompleteText.get_height()//2))
                        fadeIn(screen, fps)
                        time.wait(1500)
                        current_screen = 'levelSelect'
                else:
                    # load next stage
                    newStage = True
                    level_file = open(levels[current_level][current_stage-1])
                    level = level_file.read().strip().split('\n')
                    levelBackground = Surface((20 * max([len(i) for i in level]), 600))
                    for i in range(0, levelBackground.get_width(), levelBackgroundPics[current_level][current_stage-1].get_width()):
                        levelBackground.blit(levelBackgroundPics[current_level][current_stage-1], (i, 0))
                    clear_level()
                    levelInterpret(level, levelBackground)
                    player = character(doorPos[0] + 5, doorPos[1], health = player.health, lazer = player.lazer, jumpboost = player.jumpboost)

        time.wait(10)

    elif current_screen == 'save_score':

        if currentMusic != 'menu': # changes music
            currentMusic = 'menu'
            backgroundMusic(currentMusic)

        screen.blit(scoreScreen, (0, 0))
        savename_text = bitfont40.render(saveName, 0, (255, 255, 255, 255))
        screen.blit(savename_text, (400 - savename_text.get_width() // 2, 275))
        
        if yesRect.collidepoint(mx,my):
            # shows selected
            screen.blit(arrowLeft, (yesRect.left-18, yesRect.top+7))
            screen.blit(arrowRight, (yesRect.right - 6, yesRect.top + 7))
            if click and saveName: # add score to 'highscores.txt'
                file = open('highscores.txt')
                highscores = [[int(score), name] for (score, name) in [x.split() for x in file.read().strip().split("\n") if x]]
                highscores.append([score, saveName])
                highscores.sort(reverse=True)
                try:
                    file = open('highscores.txt', 'w')
                    for i in range(min(len(highscores), 10)):
                        file.write('%d %s\n' % (highscores[i][0], highscores[i][1]))
                    file.close()
                except:
                    continue

                if player_dead: # reset progress if player dies
                    progress = 1
                    score = 0
                    player_dead = False
                    
                current_screen = 'menu'
                saveName = ''

        # doesn't save score
        elif noRect.collidepoint(mx, my):
            # shows selected
            screen.blit(arrowLeft, (noRect.left - 18, noRect.top + 7))
            screen.blit(arrowRight, (noRect.right - 6, noRect.top + 7))

            if click: # reset progress if player dies
                if player_dead:
                    progress = 1
                    score = 0
                    player_dead = False

                current_screen = 'menu'
                saveName = ''

    elif current_screen == 'high_scores':

        if currentMusic != 'menu': # changes music
            currentMusic = 'menu'
            backgroundMusic(currentMusic)

        screen.blit(highscoreScreen, (0,0))

        # loads high scores
        file = open('highscores.txt')
        highscores = [[int(score), name] for (score, name) in [x.split() for x in file.read().strip().split("\n") if x]]
        highscores.sort(reverse=True)

        # displays top 10 scores
        for i in range(min(len(highscores), 10)):
            rank_text = bitfont40.render(str(i + 1) + '. ', 0, (255, 255, 255, 255))
            screen.blit(rank_text, (175, 100 + 45 * i))

            name_text = bitfont40.render(highscores[i][1], 0, (255, 255, 255, 255))
            screen.blit(name_text, (225, 100 + 45 * i))

            score_text = bitfont40.render('%05d' % min(highscores[i][0], 99999), 0, (255, 255, 255, 255))
            screen.blit(score_text, (500, 100 + 45 * i))

        if backRect.collidepoint(mx, my): # back button
            # shows selected
            screen.blit(arrowLeft, (backRect.left - 18, backRect.top + 12))
            screen.blit(arrowRight, (backRect.right - 6, backRect.top + 12))
            if click:
                current_screen = 'menu'

    elif current_screen == 'fireworks':
        # blits fireworks for some time
        screen.blit(winScreen, (0, 0))

        # show fireworks and remove when finished
        remove = []
        for i in range(len(fireworks)):
            f = fireworks[i]
            firePic = fireworkPics[f[2]][int(f[3])]
            screen.blit(transform.scale(firePic, (int(firePic.get_width()*f[4]), int(firePic.get_height()*f[4]))), (f[0], f[1]))
            f[3] += 10/fps
            if f[3] >= len(fireworkPics[f[2]]):
                remove.insert(0, i)
        for i in remove:
            del fireworks[i]

        # randomly add new fireworks
        if choice([1] + [0]*99) == 1:
            fireworkScale = choice([1, 1.5, 2, 2.5, 3])
            fireworks.append([randint(-50, 750), randint(-50, 550), choice(['Blue', 'Green', 'Orange', 'Purple', 'Red', 'Yellow']), 0, fireworkScale])
            fireworkSound.play()

        #time limit of fireworks
        timeleft = int(15 + start_time - clock())
        if timeleft <= 0:
            fadeOut(screen, fps)
            current_screen = 'save_score'

    display.flip()

    myClock.tick()
    fps = myClock.get_fps()
    display.set_caption("MEGAMAN || FPS: %d" % fps)
    fps = min(fps, 100) # prevents slow fading in/out

    click, release = False, False

quit()
