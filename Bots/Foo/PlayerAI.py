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
        self.mission = False            # is the unit on the mission of reaching a certain target?

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

        # if unit is dead, stop making moves.
        if friendly_unit.status == 'DISABLED':
            print("Turn {0}: Disabled - skipping move.".format(str(self.turn_count)))
            self.target = None
            self.outbound = True
            self.mission = False
            return

        invader_target = \
            self._territory_check(world, friendly_unit, enemy_units)

        possible_target = \
            self._vision_decision(world, friendly_unit, enemy_units)

        if invader_target is not None:
        # If there's an invader
            self.target = invader_target
            self.outbound = False
            self.mission = True
            # If there's an invader and we deem it necessary to attack, then this is the highest priority,
            # and this will overwrite previous target instruction.

        # TODO: take the possible_target as a Tuple:
        #     - the first index is 0(expand), 1(attack) and 2(flee)
        #     - the second index is the target position, which is also a Tuple
        else:
            if self.target is not None and friendly_unit.position == self.target:
            # If there's a target and we reached the target.
                # TODO: a) Expand case:
                    #     self.outbound, do not change
                    #     self.mission, do not change
                    #     self.target = None
                # TODO: b) Invader or Flee case:
                    #     self.outbound = True
                    #     self.mission = False
                    #     self.target = None
                # TODO: c) Attack case:
                    #     self.outbound = False
                    #     self.mission = False
                    #     self.target, updated as the cloest territory

            if self.target is not None and friendly_unit.position != self.target:
            # If there's a target and we havn't reached the target.
            # we want to be wary of whether we need to flee.
                # TODO: check enemy head to see if we need to overwrite our target and flee.
                    #     self.outbound = False
                    #     self.mission = False
                    #     self.target, updated as the cloest territory
                # else just pass

            elif self.target is None:
            # If target is None, then we want to check our vision.
                # TODO: a) Flee case:
                    #     self.outbound = False
                    #     self.mission = False
                    #     self.target = current target from vision
                # TODO: b) Attack case:
                    #     self.outbound = True
                    #     self.mission = True
                    #     self.target = current target from vision
                # TODO: c) Expand case:
                    #     self.outbound = True
                    #     self.mission = False
                    #     self.target = current target from vision


        # TODO: Restructure the move function.

        # if unit reaches the target point, reverse outbound boolean and
        #  set target back to None
        if self.target is not None and friendly_unit.position == self.target.position:
            self.outbound = not self.outbound
            self.target = None

        if self.target is not None and self.outbound is False:
            pass
            # If the target is not None and we decide to flee back to our territory,
            # we want to stick with our original target.

        # if outbound and no target set, set target as the closest
        # capturable tile at least 1 tile away from your
        # territory's edge.

        if self.outbound and self.target is None and \
                invader_target is None:
            self.target = possible_target

            edges = [tile for tile in
                     world.util.get_friendly_territory_edges()]
            avoid = []
            for edge in edges:
                avoid += [pos for pos in world.get_neighbours(edge.position).values()]
            self.target = world.util.get_closest_capturable_territory_from(friendly_unit.position, avoid)

        elif self.outbound and self.target is None and \
                invader_target is not None:
            self.target = invader_target
        # else if inbound and no target set, set target as the closest friendly tile
        elif not self.outbound and self.target is None:
            print("Heading Home!")
            self.target = world.util.get_closest_friendly_territory_from(friendly_unit.position, None)

        # set next move as the next point in the path to target
        next_move = world.path.get_shortest_path(friendly_unit.position,
                                                 self.target.position,
                                                 friendly_unit.snake)[0]

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

    def _vision_decision(self, world, friendly_unit, enemy_units):
        """
            The vision for this snake. It should send a signal to the action function when an enemy enters our sight.
        One of the two cases might then occur:
                a) An enemy body is in sight, then we want to expand our sight before moving away. we will decide to
            attack the enemy, if not then we return 0 as to ignore the enemy;
                b) An enemy head is in sight, then we immediately return to our territory through the shortest path to
            conservatively expand without risking being killed.

        @type world: World object
        @type friendly_unit: FriendlyUnit object
        @type enemy_units: EnemyUnit objects
            - this is a list of EnemyUnit objects (which means it's info about all the other three snakes)

        @rtype: Tuple
            (int, Tuple(position))
            - this integer can be 0(no enemy), 1(sees enemy body) or 2(sees enemy head)
            - this tuple of position is the move I want to go towards
        """
        # our safety threshold is 5, plus 4 for the vision, therefore our vision is 9 tiles away from our snake

        # in the do nothing condition, I need to return which neutral tile I'm going towards;
        # in the enemy body condition, I need to return which enemy body tile I'm going towards;
        # in the enemy head condition, I need to return which territory tile I'm going back to.

        # If sees enemy head, flee:
        if self._check_enemy_head(world, friendly_unit, enemy_units):
            self.outbound = False
            return None
        # Else if sees enemy body, attack:
        # elif self._check_enemy_body(world, friendly_unit):
        #     return self._check_enemy_body(world, friendly_unit)[1]
        # # Else, move one more tile:
        # else:
        #     return self._get_neutral_path(world, friendly_unit)

    def _check_enemy_head(self, world, friendly_unit, enemy_units):
        """
            This is a helper function for _vision_decision to check if there is an enemy head in our sight
            so that we'll turn back towards our territory.

        @type world: World object
        @type friendly_unit: FriendlyUnit object
        @type enemy_units: EnemyUnit objects
        @rtype: boolean
            - this determines whether there is a threatening enemy head
        """
        for enemy in enemy_units:
            avoid = [i.snake for i
                     in enemy_units if i != enemy] + \
                    [friendly_unit.body]
            if world.path.get_taxi_cab_distance(enemy.position,
                                                friendly_unit.position) \
                    == world.path.\
                    get_taxi_cab_distance(friendly_unit.position, world.util.get_closest_friendly_territory_from(
                    friendly_unit.position, avoid).position) + 4:
                return True
                # Return true if we find one enemy head entered our sight.
        return False
        # Return false if we find no enemy head within our sight.

    def _check_enemy_body(self, world, friendly_unit):
        """
            This is a helper function for _vision_decision to check if there is an enemy body within
            our safety threshold so that we can go attack it.

        @type world: World object
        @type friendly_unit: FriendlyUnit object
        @rtype: Tuple
            - the target position
        """
        enemy_body = world.util.get_closest_enemy_body_from(friendly_unit.position, friendly_unit.snake)
        distance = world.path.get_taxi_cab_distance(enemy_body.position, friendly_unit.position)
        if distance <= 5:
            return enemy_body.position
            # Return true if we find one enemy body that's attackable within our safety threshold.
        else:
            return None
            # Return false if we do not find any enemy body that's attackable within our safety threshold.

    def _get_neutral_path(self, world, friendly_unit):
        """
            This is a helper function for _vision_decision to get a neutral position to travel to.

        @type world: World object
        @type friendly_unit: FriendlyUnit object
        @rtype: Tuple
            - this tuple is the position we want to move into
        """
        neighbours = world.get_neighbours(friendly_unit.position)
        back_up_position = None
        back_up_distance = 500
        delete_list = []
        for direction in neighbours.keys():
            target_tile = world.util.get_closest_friendly_territory_from(neighbours[direction], friendly_unit.snake)
            distance = world.path.get_taxi_cab_distance(target_tile.position, neighbours[direction])
            if neighbours[direction] in friendly_unit.snake:
                delete_list.append(direction)
                # Make sure the dictionary of possible moves does not include the snake's own body.
            elif distance > 5:
                if back_up_position is None:
                    back_up_position = neighbours[direction]
                else:
                    if back_up_distance > distance:
                        back_up_position = neighbours[direction]
                        back_up_distance = distance
                # The back up is in case there is no short enough path left.
                delete_list.append(direction)
                # Make sure the dictionary of possible moves does not make the snake exit the safety threshold region.
