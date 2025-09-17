import numpy as np 
from Class_Structures import * 
from shapely.geometry import Polygon

### Throughout, the sides of the objects are defined as follows:
# 'top' or 'back' of the object would be the headboard of a bed, or the back of a chair
# 'front' or 'bottom' of the object would be the foot of a bed, or the front of a wardrobe (the side with the doors)
# 'left' would be the left side of the object, when standing behind it
# 'right' would be the right side of the object, when standing behind it


def io_next_to(positions, room, object1_index, object2_index, side1 = None, side2 = None):
    ## DO NOT USE THIS WITH io_surround, IT WILL BE REDUNDANT OR CONTRADICTORY.
    """ This function ensures that two objects are next to each other in a room. 
        This should only be used when necessary e.g. for nightstands and a bed, or a desk and desk chair. 
        This should not be used for dining chairs around a table or similar relationship, for that use io_surround.
        If side1 is given, the specific side of object1 will be used. If side2 is given, 
        the specific side of object2 will be used. E.g. the 'front' of the chair should be next to the 'front' of the desk. 
        If no side is given, then any of the sides will be used.
        
        Args:
        room: rectangular Room object
        object1: Object object
        object2: Object object
        side1: string, one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of object1 to use
        side2: string, one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of object2 to use
    """
    return

def io_away_from(positions, room, object1_index, object2_index, min_dist = 2.0):
    """ This function ensures that two objects are away from each other in a room.
        For example, a bed should be away from a desk. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
        min_dist: float, minimum distance between the two objects. Please write this as a float, e.g. 2.0.

    """
    return

def io_near(positions, room, object1_index, object2_index, max_dist = 3.0):
    """ This function ensures that two objects are within a certain distance to each other. 
        They are not necessarily next to each other, but they are close. This might be for a bookshelf 
        and an armchair, or a mirror and a wardrobe. 
        
        Args:
        room: rectangular Room object
        object1_index: Object object
        object2_index: Object object
        max_dist: furthest distance between the two objects. Please write this as a float, e.g. 3.0.

    """
    return 

def io_parallel(positions, room, object1_index, object2_index, center_object_info = None, max_dist = 2.0):
    """ This function ensures that two objects have the same orientation in a room.
        That is, that they are parallel to each other. It does not handle distance, so if 
        proximity is important, please combine this function with io_near, or io_next to, or even io_between. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room 
    """
    return

def io_facing(positions, room, object1_index, object2_index, both = False):
    """ This function ensures that object1 is facing object2 in a room. 
        If both is True, then object2 will also be facing object1.
        For example, a sofa and tv should face each other, so in that instance both would be True.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
        both: bool, if True, object2 will also be facing object1
    """
    return

def io_infront(positions, room, object1_index, object2_index, dist = 0.8, parallel = False):
    """ This function ensures that object1 is in front of object2 (both moving_objects i.e. not windows or doors).
        E.g a coffee table should be in front of a sofa. 

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, Object object
        object2_index: int, Object object
        dist: float, desired distance between two objects. E.g. if its a sofa and a coffee table, the distance should be around 0.8m, 
                                                            if its a sofa and a fireplace, the distance should be around 2m/2.5m.
        parallel: bool, if True, object1 will be parallel to object2. This would be used for a coffee table in front of a sofa, 
                    but not for a sofa in front of a fireplace.
    """

    return

def io_perp(positions, room, object1_index, object2_index, center_object_index = None):
    """ This function ensures that two objects are aligned in a room perpendicularly. 
        If center is given, the objects will be aligned about that point. For example, 
        a sofa and chair might be aligned perpendicularly about a coffee table or a side table. Or a chair at the head of the table 
        might be aligned perpendicularly with the chairs closest to it on the sides of the table. 

        
        Args:

        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
        center_object_index: int, index of object in room.moving_objects to be used as the pivot for the alignment (e.g. a coffee table or a table)
    """

    return

def io_surround(positions, room, central_object_index, object_indices):
    ## IF YOU USE THIS FUNCTON, DO NOT ALSO USE "IO_NEXT_TO" AS IT WILL BE REDUNDANT OR CONTRADICTORY. 
    """ This function ensures that central_object is surrounded by all the objects in object_indices.
        This would be used for chairs around a dining table. This should NOT be combined with io_next_to, as that would be redundant or 
        it would contradict. 

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        central_object_index: int, Object object
        object_indices: list of ints, indices of Object objects
    """

    return

def io_not_facing(positions, room, object1_index, object2_index):
    """ This function ensures that object1 is NOT facing object2 in a room.
        For example, a bed should not face a mirror.         
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
    """
    return 

def io_between(positions, room, object1_index, object2_index, object3_index): 
    """ This function ensures that object1 is in between the two objects object2 and object3. 
        This would be used for something like a side table being between two chairs, or maybe a bed being between two nightstands. 
        Or even a nightstand going between two beds.
        
        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room (** this is the object that will go in between the other two objects)
        object2_index: int, index of object2 in the room
        object3_index: int, index of object3 in the room
    """
    return 