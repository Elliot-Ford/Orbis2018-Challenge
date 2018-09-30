from PythonClientAPI.game.PointUtils import *
from PythonClientAPI.game.Entities import FriendlyUnit, EnemyUnit, Tile
from PythonClientAPI.game.Enums import Team
from PythonClientAPI.game.World import World
from PythonClientAPI.game.TileUtils import TileUtils

class PlayerAI:

    def __init__(self):
        ''' Initialize! '''
        self.turn_count = 0             # game turn count
        self.target = None              # target to send unit to!
        self.outbound = True            # is the unit leaving, or returning?
        self.out_count = 0

    def do_move(self, world, friendly_unit, enemy_units):
        '''
        This method is called every turn by the game engine.
        Make sure you call friendly_unit.move(target) somewhere here!

        Below, you'll find a very rudimentary strategy to get you started.
        Feel free to use, or delete any part of the provided code - Good luck!

        :param world: world object (more information on the documentation)
            - world: contains information about the game map.
            - world.path: contains various pathfinding helper methods.
            - world.util: contains various tile-finding helper methods.
            - world.fill: contains various flood-filling helper methods.

        :param friendly_unit: FriendlyUnit object
        :param enemy_units: list of EnemyUnit objects
        '''

        # increment turn count
        self.turn_count += 1

        if self.outbound:
            self.out_count += 1

        # if unit is dead, stop making moves.
        if friendly_unit.status == 'DISABLED':
            print("Turn {0}: Disabled - skipping move.".format(str(self.turn_count)))
            self.target = None
            self.outbound = True
            return

        invader_target = \
            self._territory_check(world, friendly_unit, enemy_units)

        # if unit reaches the target point, reverse outbound boolean and
        #  set target back to None
        if self.target is not\
                None and \
                friendly_unit.position == self.target.position:
            # Reached the target
            if not self.outbound or world.is_edge(self.target.position):
                # If inbound or we're at the edge, go outbound
                self.outbound = not self.outbound
            self.target = None

        if self.should_flee(world, friendly_unit):
            # Flee has the highest priority
            self.outbound = False
            self.target = None



        # if outbound and no target set, set target as the closest
        # capturable tile at least 1 tile away from your
        # territory's edge.
        if self.outbound and self.target is None:
            # Neutral expand case
            # TODO: try to figure out this one
            edges = [tile for tile in world.util.get_friendly_territory_edges()]
            avoid = []
            for edge in edges:
                avoid += [pos for pos in world.get_neighbours(edge.position).values()]

            neighbours = []
            target = None
            target_distance = 0
            for i in range(3):
                temp_target = world.util.get_closest_capturable_territory_from(friendly_unit.position, avoid)
                neighbours.append(temp_target)
                avoid.append(temp_target)

            for tile in neighbours:
                distance = world.path.get_taxi_cab_distance(friendly_unit.position, tile.position)
                if target is None:
                    target = tile
                    target_distance = distance
                else:
                    if distance <= 5 and target_distance <= 5:
                        if target_distance >= distance:
                            pass
                        else:
                            target = tile
                    elif distance <= 5 < target_distance:
                        target = tile
                    elif target_distance <= 5 < distance:
                        pass
                    else:
                        if target_distance >= distance:
                            target = tile
                        else:
                            pass

            print(str(target))
            print(str(target_distance))
            self.target = target

        elif self.outbound and self.target is None and \
                invader_target is not None:
            # Invader case
            self.target = invader_target
        # else if inbound and no target set, set target as the closest friendly tile
        elif not self.outbound and self.target is None:
            # just to catch the target being None error
            self.target = world.util.get_closest_friendly_territory_from(friendly_unit.position, None)
        print(self.target.position)
        print(friendly_unit.position)
        print(friendly_unit.snake)
        # set next move as the next point in the path to target
        next_move = world.path.get_shortest_path(friendly_unit.position, self.target.position, friendly_unit.snake)[0]

        # move!
        friendly_unit.move(next_move)
        print("Turn {0}: currently at {1}, making {2} move to {3}.".format(
            str(self.turn_count),
            str(friendly_unit.position),
            'outbound' if self.outbound else 'inbound',
            str(self.target.position)
        ))

    def _territory_check(self, world, friendly_unit, enemy_units):
        """
        Determines whether or not to return to the territory in pursuit
        of an enemy
        :param self: reference to class
        :type self: PlayerAI
        :param friendly_unit: reference to the friendly_unit
        :type friendly_unit: FriendlyUnit
        :param enemy_units:
        :type: enemy_units: EnemyUnit
        :return: The target of an enemy.
        :rtype: bool
        """
        ret = None
        lowest_found_distance = 900

        for enemy_unit in enemy_units:
            if enemy_unit.snake in friendly_unit.territory:

                closest_eu_territory_to_eu = \
                    world.utils.get_closest_territory_by_team(
                        enemy_unit.position, enemy_unit.team)

                head_distance_to_safety = world.path.\
                    get_taxi_cab_distance(enemy_unit.position,
                                          closest_eu_territory_to_eu)

                closest_eu_body_to_f = world.utils.\
                    get_closest_body_by_team(friendly_unit.position,
                                             enemy_unit.team)

                avoid = [i.snake for i
                         in enemy_units if i != enemy_unit] + \
                        friendly_unit.body

                friendly_distance_to_enemy_unit: int = len(
                    world.path.get_shortest_path(friendly_unit.position,
                                                 closest_eu_body_to_f,
                                                 avoid))

                if (head_distance_to_safety >
                        friendly_distance_to_enemy_unit):
                    if (not lowest_found_distance or
                            friendly_distance_to_enemy_unit <
                            lowest_found_distance):
                        ret = closest_eu_body_to_f
        return ret


    def get_friendly_territory_target(self, world, friendly_unit):
        return world.util.get_closest_friendly_territory_from(
            friendly_unit.position, None)

    def get_enemy_body_target(self, world, friendly_unit, enemy_units):
        avoid = friendly_unit.snake + [i.position for i in enemy_units]
        enemy_body = world.util.get_closest_enemy_body_from(
            friendly_unit.position, avoid)
        enemy_head_to_body_dis = world.path. \
            get_taxi_cab_distance(world.util.
                                  get_closest_enemy_head_from(
            enemy_body, friendly_unit.position))
        friendly_head_to_body_dis = world.path. \
            get_taxi_cab_distance(friendly_unit.position, enemy_body)

        if enemy_head_to_body_dis > friendly_head_to_body_dis:
            return enemy_body
        else:
            return None

    VISION_THRESHOLD = 4

    def should_flee(self, world, friendly_unit):
        closeset_enemy = world.util.get_closest_enemy_head_from(
            friendly_unit.position, []).position
        distance_from_enemy = world.path.get_taxi_cab_distance(
            friendly_unit.position, closeset_enemy)
        distance_from_home = world.path.get_taxi_cab_distance(
            self.get_friendly_territory_target(world, friendly_unit).
                position,
            friendly_unit.position)

        if distance_from_enemy < distance_from_home + self.\
                VISION_THRESHOLD:
            return True
        else:
            return False

