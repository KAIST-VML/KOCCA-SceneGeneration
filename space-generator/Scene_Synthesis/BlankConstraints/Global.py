## All the Individual Object constraint functions are defined here
from Class_Structures import *
from shapely.geometry import Polygon

### Throughout, the sides of the objects are defined as follows:
# 'top' or 'back' of the object would be the headboard of a bed, or the back of a chair
# 'front' or 'bottom' of the object would be the foot of a bed, or the front of a wardrobe (the side with the doors)
# 'left' would be the left side of the object, when standing behind it
# 'right' would be the right side of the object, when standing behind it

def in_bounds(positions, room, weight = 15.0): 

    """ This function ensures that all objects are within the room. THIS SHOULD BE USED IN EVERY OPTIMISATION FUNCTION.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        weight: float, weight of the constraint
    """
    return

def no_overlap(positions, room):
    """ This function ensures that no objects overlap in the room. THIS SHOULD BE USED IN EVERY OPTIMISATION FUNCTION.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """

    return

def aligned(positions, room):
    """ ind_aligned is a function that penalises orientations that are not one of the cardinal directions.
        Since most furniture in a room is in one of the cardinal directions, we want to encourage this. 
        This constraint is quite week in order to not prevent rotations. This should be used in EVERR room.

        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """

    return

def balanced(positions, room):
    """ This function ensures that the room is balanced.
    
        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """
    return 