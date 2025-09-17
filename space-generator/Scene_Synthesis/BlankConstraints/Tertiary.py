## All the Individual Object constraint functions are defined here
from Class_Structures import *
from shapely.geometry import Polygon, Point
from shapely import distance
from Individual import * 
from Setup_Functions import *
from Global import * 
from scipy.optimize import minimize 
 

def rug_under_central(positions, room, rug_index, object_index):

    """ This function ensures that the rug is placed under the central object. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        rug_index: int, index of the rug object in the room.tertiary_objects list
        object_index: int, index of the central object in the room.moving_objects list
    """ 

    return

def rug_under_central_forward(positions, room, rug_index, object_index): 

    """ This function ensures that the rug is placed under the central object, oriented correctly, and moved slightly forward. 
        This would be used for a rug that is placed under a bed, for example.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        rug_index: int, index of the rug object in the room.tertiary_objects list
        object_index: int, index of the central object in the room.moving_objects list
    """
    return

def on_top_central(positions, room, tertiary_index, other_index): 

    """ This function ensures that the tertiary object is placed on top of the central object.
        This would be used for placing a table lamp on top of a nightstand, for example. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
        other_index: int, index of the central object in the room.moving_objects list
    """
    return

def on_top_corner(positions, room, tertiary_index, other_index, corner = 'tl'): 

    """ This function ensures that the tertiary object is placed on top of the central object, at a specific corner.
        This would be used for placing a lamp on the top left corner of a desl, for example.

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
        other_index: int, index of the central object in the room.moving_objects list
        corner: str, corner of the central object where the tertiary object should be placed. Options are 'tl', 'tr', 'bl', 'br'
    """

    return

def on_wall_near(positions, room, tertiary_index, other_index): 

    """ This function ensures that the tertiary object is placed on the wall near the central object.
        This would be used for placing a painting on the wall near a dining table, for example.

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
        other_index: int, index of the central object in the room.moving_objects list
    """

    return

def on_wall_in_region(positions, room, tertiary_index, region_name): 
    """ This function is used to place a tertiary object on the wall in a specific region of the room.
        This would be used for placing a painting on the wall in the living region, for example.

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
        region_name: str, name of the region where the tertiary object should be placed (e.g. 'living', 'dining', 'bedroom')
        """
    return

def center_ceiling(positions, room, tertiary_index): 

    """ This function ensures that the tertiary object is placed in the center of the ceiling.
        This would be used for placing a chandelier/ceiling light in the center of the room.

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
    """
    return

def ceiling_above(positions, room, tertiary_index, other_index): 
    """ This function ensures that the tertiary object is placed on the ceiling above the central object.
        This would be used for placing a ceiling fan above a bed, or a chandelier above a dining table for example.

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
        other_index: int, index of the central object in the room.moving_objects list
    """
    return