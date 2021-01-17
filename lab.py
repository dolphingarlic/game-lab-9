"""6.009 Fall 2019 Lab 9 -- 6.009 Zoo"""

from math import acos
# NO OTHER IMPORTS ALLOWED!

class Constants:
    """
    A collection of game-specific constants.

    You can experiment with tweaking these constants, but
    remember to revert the changes when running the test suite!
    """
    # width and height of keepers
    KEEPER_WIDTH = 30
    KEEPER_HEIGHT = 30

    # width and height of animals
    ANIMAL_WIDTH = 30
    ANIMAL_HEIGHT = 30

    # width and height of food
    FOOD_WIDTH = 10
    FOOD_HEIGHT = 10

    # width and height of rocks
    ROCK_WIDTH = 50
    ROCK_HEIGHT = 50

    # thickness of the path
    PATH_THICKNESS = 30

    TEXTURES = {
        'rock': '1f5ff',
        'animal': '1f418',
        'SpeedyZookeeper': '1f472',
        'ThriftyZookeeper': '1f46e',
        'CheeryZookeeper': '1f477',
        'food': '1f34e'
    }

    FORMATION_INFO = {'SpeedyZookeeper':
                       {'price': 9,
                        'interval': 55,
                        'throw_speed_mag': 20},
                      'ThriftyZookeeper':
                       {'price': 7,
                        'interval': 45,
                        'throw_speed_mag': 7},
                      'CheeryZookeeper':
                       {'price': 10,
                        'interval': 35,
                        'throw_speed_mag': 2}}

    # Floating point precision leeway
    EPSILON = 1e-3


class NotEnoughMoneyError(Exception):
    """A custom exception to be used when insufficient funds are available
    to hire new zookeepers. You may leave this class as is."""
    pass

################################################################################
################################################################################

class Game:
    def __init__(self, game_info):
        """Initializes the game.

        `game_info` is a dictionary formatted in the following manner:
          { 'width': The width of the game grid.
            'height': The height of the game grid.
            'rocks': The set of tuple rock coordinates.
            'path_corners': An ordered list of coordinate tuples. The first
                            coordinate is the starting point of the path, the
                            last point is the end point (both of which lie on
                            the edges of the gameboard), and the other points
                            are corner ("turning") points on the path.
            'money': The money balance with which the player begins.
            'spawn_interval': The interval (in timesteps) for spawning animals
                              to the game.
            'animal_speed': The magnitude of the speed at which the animals move
                            along the path, in units of grid distance traversed
                            per timestep.
            'num_allowed_unfed': The number of animals allowed to finish the
                                 path unfed before the player loses.
          }
        """
        # Grid info
        self.width = game_info['width']
        self.height = game_info['height']
        # Formation info
        self.rocks = [Rock(i) for i in game_info['rocks']]
        self.animals = []
        self.keepers = []
        self.food = []
        # Path info
        self.path_corners = game_info['path_corners']
        # Player resource info
        self.money = game_info['money']
        self.num_allowed_remaining = game_info['num_allowed_unfed']
        # Animal behaviour info
        self.animal_speed = game_info['animal_speed']
        # Animal spawn info
        self.spawn_interval = game_info['spawn_interval']
        self.time_since_last_spawn = 0
        # Zookeeper spawn info
        self.nxt_keeper_variant = None
        self.awaiting_aim_dir = False

    def move_animal(self, animal):
        """Moves `animal` along the path and updates `animal.loc` and `animal.nxt_corner_idx` accordingly"""
        rem_dist = self.animal_speed
        for i in range(animal.nxt_corner_idx, len(self.path_corners)):
            # Pythagoras' theorem to get distance to corder
            dist_to_corner = sum((animal.loc[j] - self.path_corners[i][j]) ** 2 for j in range(2)) ** .5

            if dist_to_corner > rem_dist or i == len(self.path_corners) - 1:
                displacement = tuple( # Wow look I'm using physics definitions
                    0 if self.path_corners[i - 1][j] == self.path_corners[i][j]
                    else rem_dist if self.path_corners[i - 1][j] < self.path_corners[i][j]
                    else -rem_dist
                    for j in range(2)
                )
                # Update location
                animal.loc = tuple(animal.loc[j] + displacement[j] for j in range(2))
                animal.nxt_corner_idx = i
                return
            else:
                # Move to the next corner and decrease remaining distance to move
                rem_dist -= dist_to_corner
                animal.loc = self.path_corners[i]

    def render(self):
        """Renders the game in a form that can be parsed by the UI.

        Returns a dictionary of the following form:
          { 'formations': A list of dictionaries in any order, each one
                          representing a formation. The list should contain 
                          the formations of all animals, zookeepers, rocks, 
                          and food. Each dictionary has the key/value pairs:
                             'loc': (x, y), 
                             'texture': texture, 
                             'size': (width, height)
                          where `(x, y)` is the center coordinate of the 
                          formation, `texture` is its texture, and `width` 
                          and `height` are its dimensions. Zookeeper
                          formations have an additional key, 'aim_dir',
                          which is None if the keeper has not been aimed, or a 
                          tuple `(aim_x, aim_y)` representing a unit vector 
                          pointing in the aimed direction.
            'money': The amount of money the player has available.
            'status': The current state of the game which can be 'ongoing' or 'defeat'.
            'num_allowed_remaining': The number of animals which are still
                                     allowed to exit the board before the game
                                     status is `'defeat'`.
          }
        """
        formations = [{
            'loc': r.loc,
            'texture': r.texture,
            'size': (r.width, r.height),
            'aim_dir': r.aim_dir
        } for r in self.rocks + self.animals + self.keepers + self.food]

        return {
            'formations': formations,
            'money': self.money,
            'status': 'ongoing' if self.num_allowed_remaining >= 0 else 'defeat',
            'num_allowed_remaining': self.num_allowed_remaining
        }

    def handle_mouse(self, mouse):
        """Handles mouse input by determining whether to spawn a new keeper"""
        if mouse is not None:
            if type(mouse) is str: # First click
                self.nxt_keeper_variant = mouse
            elif self.nxt_keeper_variant is not None: # Second click
                if self.money < Constants.FORMATION_INFO[self.nxt_keeper_variant]['price']:
                    raise NotEnoughMoneyError()
                keeper = Keeper(mouse, self.nxt_keeper_variant)
                pos_is_good = True
                # Check whether the keeper intersects with rocks or other keepers
                for i in self.rocks + self.keepers:
                    if keeper.intersects(i):
                        pos_is_good = False
                        break
                # Also check intersections with the path
                for i in range(1, len(self.path_corners)):
                    path_seg = Formation(
                        tuple((self.path_corners[i][j] + self.path_corners[i - 1][j]) / 2 for j in range(2)),
                        Constants.PATH_THICKNESS + abs(self.path_corners[i][0] - self.path_corners[i - 1][0]),
                        Constants.PATH_THICKNESS + abs(self.path_corners[i][1] - self.path_corners[i - 1][1]),
                        'rock' # Temporary texture
                    )
                    if keeper.intersects(path_seg):
                        pos_is_good = False
                        break
                # Only create keeper if the position is good
                if pos_is_good:
                    self.money -= Constants.FORMATION_INFO[self.nxt_keeper_variant]['price']
                    self.keepers.append(keeper)
                    self.nxt_keeper_variant = None
                    self.awaiting_aim_dir = True
            elif self.awaiting_aim_dir and mouse != self.keepers[-1].loc: # Third **valid** click
                v_mag = sum((mouse[i] - self.keepers[-1].loc[i]) ** 2 for i in range(2)) ** .5
                self.keepers[-1].aim_dir = tuple((mouse[i] - self.keepers[-1].loc[i]) / v_mag for i in range(2))
                self.awaiting_aim_dir = False

    def timestep(self, mouse=None):
        """Simulates the evolution of the game by one timestep.

        In this order:
            (0. Do not take any action if the player is already defeated.)
            1. Compute any changes in formation locations, then remove any
                off-board formations.
            2. Handle any food-animal collisions, and remove the fed animals
                and eaten food.
            3. Throw new food if possible.
            4. Spawn a new animal from the path's start if needed.
            5. Handle mouse input, which is the integer coordinate of a player's
               click, the string label of a particular zookeeper type, or `None`.
            6. Redeem one unit money per animal fed this timestep.
            7. Check for the losing condition to update the game status if needed.
        """
        # Don't do anything if there are no lives left
        if self.num_allowed_remaining < 0:
            return

        # Move animals and remove those outside the grid
        to_remove = []
        for a in self.animals:
            self.move_animal(a)
            if not (0 <= a.loc[0] <= self.width and 0 <= a.loc[1] <= self.height):
                to_remove.append(a)
        self.num_allowed_remaining -= len(to_remove)
        self.animals = list(filter(lambda a: a not in to_remove, self.animals))
        # Move food and remove those outside the grid
        to_remove = []
        for f in self.food:
            f.loc = tuple(f.loc[i] + f.velocity[i] for i in range(2))
            if not (0 <= f.loc[0] <= self.width and 0 <= f.loc[1] <= self.height):
                to_remove.append(f)
        self.food = list(filter(lambda f: f not in to_remove, self.food))

        # Handle food-animal collisions
        animals_fed = list(filter(lambda a: any(a.intersects(f) for f in self.food), self.animals))
        food_eaten = list(filter(lambda f: any(f.intersects(a) for a in self.animals), self.food))
        self.animals = list(filter(lambda a: a not in animals_fed, self.animals))
        self.food = list(filter(lambda f: f not in food_eaten, self.food))

        # Throw new food if possible
        for k in self.keepers:
            if k.time_to_nxt_throw == 0:
                if k.aim_dir is not None and any(k.can_see(a) for a in self.animals):
                    self.food.append(Food(
                        k.loc,
                        tuple(k.info['throw_speed_mag'] * k.aim_dir[i] for i in range(2))
                    ))
                k.time_to_nxt_throw = k.info['interval']
            k.time_to_nxt_throw -= 1

        # Spawn a new animal from the path's start if possible
        if self.time_since_last_spawn == 0:
            self.animals.append(Animal(self.path_corners[0]))
            self.time_since_last_spawn = self.spawn_interval
        self.time_since_last_spawn -= 1

        # Handle mouse input
        self.handle_mouse(mouse)

        # Redeem one unit of money per animal fed this timestep
        self.money += len(animals_fed)


################################################################################
################################################################################

class Formation:
    def __init__(self, loc, width, height, texture):
        """Initializes a formation"""
        self.loc = loc
        self.width = width
        self.height = height
        self.texture = Constants.TEXTURES[texture]
        self.aim_dir = None
    
    def intersects(self, other):
        """Checks whether this formation intersects with another
        
        Two rectangles intersect if and only if their bounding rectangle's width and height is less
        than the sum of the widths and heights of the two rectangles
        """
        return (
            max(self.loc[0] + self.width / 2, other.loc[0] + other.width / 2) - 
            min(self.loc[0] - self.width / 2, other.loc[0] - other.width / 2) < self.width + other.width and
            max(self.loc[1] + self.height / 2, other.loc[1] + other.height / 2) - 
            min(self.loc[1] - self.height / 2, other.loc[1] - other.height / 2) < self.height + other.height
        )


class Rock(Formation):
    def __init__(self, loc):
        """Initializes a rock"""
        super().__init__(loc, Constants.ROCK_HEIGHT, Constants.ROCK_WIDTH, 'rock')


class Animal(Formation):
    def __init__(self, loc):
        """Initializes an animal"""
        super().__init__(loc, Constants.ANIMAL_WIDTH, Constants.ANIMAL_HEIGHT, 'animal')
        self.nxt_corner_idx = 1


def angle(v1, v2):
    """Calculates the angle (in radians) between two vectors"""
    return acos(
        (v1[0] * v2[0] + v1[1] * v2[1]) /
        (((v1[0] ** 2 + v1[1] ** 2) ** .5) * ((v2[0] ** 2 + v2[1] ** 2) ** .5))
    )


class Keeper(Formation):
    def __init__(self, loc, variant):
        """Initializes an animal"""
        assert variant in Constants.FORMATION_INFO
        super().__init__(loc, Constants.KEEPER_WIDTH, Constants.KEEPER_HEIGHT, variant)
        self.info = Constants.FORMATION_INFO[variant]
        self.time_to_nxt_throw = 1
    
    def can_see(self, animal):
        """Checks whether this keeper can see an animal"""
        rect_vectors = [
            (animal.loc[0] + animal.width / 2 - self.loc[0], animal.loc[1] + animal.height / 2 - self.loc[1]),
            (animal.loc[0] + animal.width / 2 - self.loc[0], animal.loc[1] - animal.height / 2 - self.loc[1]),
            (animal.loc[0] - animal.width / 2 - self.loc[0], animal.loc[1] - animal.height / 2 - self.loc[1]),
            (animal.loc[0] - animal.width / 2 - self.loc[0], animal.loc[1] + animal.height / 2 - self.loc[1]),
            (animal.loc[0] + animal.width / 2 - self.loc[0], animal.loc[1] + animal.height / 2 - self.loc[1])
        ]
        for i in range(4):
            theta1 = angle(rect_vectors[i], rect_vectors[i + 1])
            theta2 = angle(rect_vectors[i], self.aim_dir) + angle(rect_vectors[i + 1], self.aim_dir)
            if abs(theta1 - theta2) <= Constants.EPSILON:
                return True
        return False


class Food(Formation):
    def __init__(self, loc, velocity):
        """Initializes food and its velocity"""
        super().__init__(loc, Constants.FOOD_HEIGHT, Constants.FOOD_WIDTH, 'food')
        self.velocity = velocity


################################################################################
################################################################################

if __name__ == '__main__':
   pass
