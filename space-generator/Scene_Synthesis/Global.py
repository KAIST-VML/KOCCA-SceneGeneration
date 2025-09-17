## All the Individual Object constraint functions are defined here
from Class_Structures import *
from shapely.geometry import Polygon
from Individual import *

@safe_execution
def in_bounds(positions, room, weight = 10): 

    """ This function ensures that all objects are within the room. This should be used in every objective function.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """
    val = 0
    objs = room.moving_objects
    for i in range(len(room.moving_objects)):
        x, y, theta = get_position(positions, room, i)
        cs = corners(x, y, theta, objs[i].width, objs[i].length)
        for corner in cs: 
            val += (max(0, corner[0] - room.width)**2 + max(0, corner[1] - room.length)**2)
            val += (max(0, -corner[0])**2 + max(0, -corner[1])**2)
        
    return weight * val 

@safe_execution
def no_overlap(positions, room, weight = 5):
    """ This function ensures that no objects overlap in the room. This should be used in every objective function. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """

    val = 0
    objs = room.moving_objects
    indices = [i for i in range(len(room.moving_objects))]
        
    doors = room.find_all('door')
    door_polygons = [] 
    for door in doors: 
        door_corners = []
        if door.position[2] == 0:
            door_corners += [[door.position[0] - door.width, door.position[1]]]
            door_corners += [[door.position[0] + door.width, door.position[1]]]
            door_corners += [[door.position[0] + door.width, door.position[1] + door.width]]
            door_corners += [[door.position[0] - door.width, door.position[1] + door.width]]
        elif door.position[2] == np.pi/2:
            door_corners += [[door.position[0], door.position[1] - door.width]]
            door_corners += [[door.position[0] - door.width, door.position[1] - door.width]]
            door_corners += [[door.position[0] - door.width, door.position[1] + door.width]]
            door_corners += [[door.position[0], door.position[1] + door.width]]
        elif door.position[2] == np.pi:
            door_corners += [[door.position[0] + door.width, door.position[1]]]
            door_corners += [[door.position[0] + door.width, door.position[1] - door.width]]
            door_corners += [[door.position[0] - door.width, door.position[1] - door.width]]
            door_corners += [[door.position[0] - door.width, door.position[1]]]
        elif door.position[2] == 3*np.pi/2:
            door_corners += [[door.position[0], door.position[1] + door.width]]
            door_corners += [[door.position[0] + door.width, door.position[1] + door.width]]
            door_corners += [[door.position[0] + door.width, door.position[1] - door.width]]
            door_corners += [[door.position[0], door.position[1] - door.width]]

        door_poly = Polygon(door_corners)
        door_polygons += [door_poly]
        
    for i in indices:
        
        obj_i = objs[i]

        x_i, y_i, theta_i = get_position(positions, room, i)

        corners_i = corners(x_i, y_i, theta_i, obj_i.width, obj_i.length)
        if nan_check(corners_i):
            continue

        poly1 = Polygon(corners_i)

        for j in indices:
            if j <= i: 
                continue

            x_j, y_j, theta_j = get_position(positions, room, j)
            obj_j = objs[j]
            corners_j = corners(x_j, y_j, theta_j, obj_j.width, obj_j.length)
            if nan_check(corners_j):
                continue
            
            poly2 = Polygon(corners_j)
            intersection = poly1.intersection(poly2)
            
            if intersection.area > 0:
                x = np.array([[i, j] for i, j in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                lengths = np.roll(x, -1, axis = 0) - x
                lengths = np.linalg.norm(lengths, axis = 1)
                val += sum(lengths**2)
        
        for door in door_polygons:
            intersection = poly1.intersection(door)
            if intersection.area > 0:
                x = np.array([[i, j] for i, j in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                lengths = np.roll(x, -1, axis = 0) - x
                lengths = np.linalg.norm(lengths, axis = 1)
                val += 100*sum(lengths**2)

    return weight * val 

@safe_execution
def aligned(positions, room):
    """ aligned is a function that penalises orientations that are not one of the cardinal directions.
        Since most furniture in a room is in one of the cardinal directions, we want to encourage this. 
        This constraint is quite week in order to not prevent rotations. This should be used in all rooms.
        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """

    val = 0
    for i in range(len(positions)//3):
        theta = positions[3*i + 2]
        val += (np.sin(2*theta)**2)/5
    return val

@safe_execution
def balanced(positions, room):

    """ This function ensures that the room is balanced.
    
        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """
    
    if positions.shape[0] == 3: 
        return 0
    objs = room.moving_objects
    room_x, room_y = room.width/2, room.length/2
    av_x, av_y = 0.0, 0.0
    total_weight = 0.0
    for i in range(len(objs)):
        x, y, theta = get_position(positions, room, i)
        weight = objs[i].width * objs[i].length
        total_weight += weight
        av_x += weight * x
        av_y += weight * y
    
    av_x /= total_weight
    av_y /= total_weight

    val = (av_x - room_x)**2 + (av_y - room_y)**2
    return val 


def wall_attraction(positions, room): 
    """ This function is a very weak constraint that attracts the objects to near the walls 
        in order to prevent 'floating' objects - objects that are placed in the middle of the room. 
        This should be used in all rooms.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """

    objs = room.moving_objects
    val = 0
    for i in range(len(objs)):
        x, y, theta = get_position(positions, room, i)
        width, length = objs[i].width, objs[i].length
        half_diag = np.sqrt(width**2 + length**2)/2
        val += 0.05 * ind_near_wall(positions, room, i, half_diag + 0.5)

    return val 





                
















