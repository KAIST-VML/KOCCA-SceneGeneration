## All the Individual Object constraint functions are defined here
from Class_Structures import *
from shapely.geometry import Polygon

### Throughout, the sides of the objects are defined as follows:
# 'back' of the object would be the headboard of a bed, or the back of a chair
# 'front' of the object would be the foot of a bed, or the front of a wardrobe (the side with the doors)
# 'left' would be the left side of the object, when standing behind it
# 'right' would be the right side of the object, when standing behind it

def ind_next_to_wall(positions, room, object_index):
    """ This function ensures an object is next to a wall in a room. Specifically the back of the object. 
        Example constraint: "The tv should be against a wall."    
    
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list)
        
    """

    return


def ind_near_wall(positions, room, object_index, side = 'back', max_dist = 0.5):
    """ This function ensures an object is near to a wall in a room (within a specific distance, NOT next to).
        The specific side of the object will be used. If no side is given, the back of the object will be used.
                
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        side: string, one of 'back', 'front', 'left', 'right'  defines which side of the object to check e.g back of bed 
        max_dist: float, maximum distance the object should be from the wall
    """
        
    
    return 
    
def ind_close_to_fixed_object(positions, room, object_index, fixed_object_type, side = None, max_dist = 0.5):
    """ The function ind_close_to_fixed_object is used for 3 purposes: 
            1) an object should be next to a window (fixed_object_type = 'window')
            2) an object should be next to a door (fixed_object_type = 'door')
            3) an object should be next a socket (fixed_object_type = 'socket')
        
        If side is given, the specific side of the object will be used.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        fixed_object_type: string, type of fixed object to check. One of 'window', 'door', 'socket'
        side: string, one of 'back' (for things like headboard of bed, or back of bookshelf), 'front' (for things like foot of bed or front of bookshelf), 'left', 'right', defines which side of the object to check e.g back of bed 
        max_dist: float, maximum distance between the object and the fixed object to be considered close to it. Please write this as a float e.g. 2.0. 
    """

    return

def ind_away_from_fixed_object(positions, room, object_index, fixed_object_type, min_dist = 2.0):
    """ This function is used for 3 purposes: 
            1) an object should be away from a window (fixed_object_type = 'window')
            2) an object should be away from a door (fixed_object_type = 'door')
            3) an object should be away from a socket (fixed_object_type = 'socket')
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        fixed_object_type: string, type of fixed object to check. One of 'window', 'door', 'socket'
        min_dist: float, minimum distance between the object and the fixed object to be considered away from it. Please write this as a float, e.g. 2.0. 
    """

    return

def ind_accessible(positions, room, object_index, sides, min_dist = None):
    """ This function ensures that an object is accessible from given sides. It can also ensure that 
        there is nothing too close to a given side of an object (e.g. if there needs to be clearance around something). 
        If no sides are given, the front side is used. If min_dist is given, then this function 
        will act as a clearance constraint. If you want all the sides to be accesible, sides = ['front', 'back', 'left', 'right'].
    
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        sides: a list of strings, each one one of 'front', 'left', 'right', defines which side of the object to check
        min_dist: float (optional), minimum distance clearance for the object on the sides given. Please write this as a float, e.g. 1.0.
    """
    
    return

def ind_central(positions, room, object_index, both = False):
    """ This function ensures that an object is centrally placed in the room. 
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        both: bool (optional), if True, then the object should be placed centrally in both x and y. For example for a bed, this would be False, 
              but for a dining table, it should be True.
    """

    return


def ind_not_block_fixed_object(positions, room, object_index, fixed_object_type):

    """ This function is used for 2 purposes: 
            1) an object does not block a window (fixed_object_type = 'window')
            2) an object does not block a door (fixed_object_type = 'door')
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        fixed_object_type: string, type of fixed object to check. E.g one of 'window', 'door', 'plug'
    """

    return

def ind_under_window(positions, room, object_index):

    """ This function ensures that the object will be placed underneath a window.
        For example, you might want a desk or a dresser below (but not blocking) a window. You would NOT use this for any 
        objects that would be tall, for example a wardrobe or a fridge. Example constraint "The desk should be under the window", 
        "The desk should look out the window". Don't use with ind_not_block_fixed_object for a window and the same object. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """ 

    return

def ind_facing_into_room(positions, room, object_index):
    """ ind_facing_into_room is a function that ensures and object faces into the center of the room. 
        E.g. an armchair might face into the room.

        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        
    """
    return

def ind_in_region(positions, room, object_index, region_name, weight = 5.0):
    """ This function ensures that an object is in a given region. This should NOT be used with the optimize_primary_objects function.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        region_name: string, name of the region for the object to be in 
        weight: float, weight of the constraint
    """

    return 


def ind_not_against_wall(positions, room, object_index, min_dist = 0.5):

    """ ind_not_against_wall is a function that ensures an object is not against a wall. 
        For example "the rug should not be touching the wall" or "the dining table should not be against the wall". 

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        min_dist: float, minimum distance the object should be from the wall. Please write this as a float, e.g. 2.0. 
    """

    return 

def ind_in_corner(positions, room, object_index, side = 'back', max_dist = 0.5):
    """ This function can be used to ensure that an object is placed into a corner. 
        The back of the object will always be placed closest to the corner. 

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        max_dist: float, maximum distance the object should be from the wall
    """
    return









                
















