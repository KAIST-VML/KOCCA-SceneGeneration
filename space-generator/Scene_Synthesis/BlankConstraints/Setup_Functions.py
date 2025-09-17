import numpy as np
from Class_Structures import Object, Room, Region

def create_room(width, length):
    """ A function that creates an empty room.
        Inputs:
        width: float, width of the room (meters)
        length: float, length of the room (meters)
        Outputs:
        room: Room, an empty room with the specified dimensions
    """

    return

def create_fixed_object(room, name, width, length, wall, position = None):
    """ A function that creates an object.
        Inputs:
        room: Room for the object to be put in
        name: str, name of the object all lowercase. E.g. 'window'
        width: float, width of the object (m)
        length: float, length of the object (m)
        wall: wall for the object to be put on, one of 'north', 'east', 'south', 'west'
        position: float object (between 0 and 1) that determines where on the wall it is placed. E.g if wall is 'north', 
                  position might be 0.5, which means the object is at position (0.5*room.width, room.length).
    """

    return 


def remove_object(room, obj_index):
    """ A function that removes an object from the room.
        Inputs:
        room: Room, the room from which the object is to be removed
        obj_index: index of object to be removed 
    """
    return

def region_setup(room, name, index):

    """ A function that initialises the regions in a room.
        Inputs:
        room: Room, the room from which the object is to be removed
        name: str, the name of the region e.g 'sleeping'
        index: int, the index of the region (0, 1, 2, ...). First one must be 0, and the rest must be in order.
    """
    return

def create_moving_object(room, name, width, length, region_name, index):
    """ A function that creates an object.
        Inputs:
        room: Room for the object to be put in
        name: str, name of the object all lowercase. E.g. 'window'
        width: float, width of the object (m)
        length: float, length of the object (m)
        region_name: str, name of the region where the object is to be placed
        index: int, index of the object in the room's object list
    """
    return

def distance_point_from_line(p1, p2, p):
    """ Perpendicular distance of p from the line going from p1 to p2. 
        Args: 
        p1: tuple, point 1
        p2: tuple, point 2
        p: tuple, point to find distance from
        
    """
    return