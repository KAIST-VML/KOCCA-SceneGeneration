## All the Individual Object constraint functions are defined here
from Class_Structures import *
from shapely.geometry import Polygon, Point
from shapely import distance
from Individual import * 
from Setup_Functions import *
from Global import * 
from scipy.optimize import minimize 

def t_valid(positions, room): 

    """ This function ensures that the tertiary objects ae placed in a valid way.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """

    total_val = 0
    objs = room.tertiary_objects
    doors = room.find_all('door')
    door_polygons = [] 
    for door in doors: 
        door_corners = door.corners()
        door_poly = Polygon(door_corners)
        door_polygons += [door_poly]
    
    windows = room.find_all('window')
    window_polygons = []
    for window in windows:
        window_corners = window.corners()
        window_poly = Polygon(window_corners)
        window_polygons += [window_poly]
       
    for i in range(len(objs)):

        obj_i = objs[i]
        typ = obj_i.tertiary
        w, l = objs[i].width, objs[i].length
        x, y, theta = positions[3*i: 3*i + 3]
        
        ## in bounds
        cs = corners(x, y, theta, w, l)
        for corner in cs: 
            total_val += 100*(max(0, corner[0] - room.width)**2 + max(0, corner[1] - room.length)**2)
            total_val += 100*(max(0, -corner[0])**2 + max(0, -corner[1])**2)

        ## no overlap with doors or windows
        if nan_check(cs):
            continue

        poly1 = Polygon(cs)
        for door in door_polygons: ## all objects must not intersect doors
            intersection = poly1.intersection(door)
            if intersection.area > 0:
                z = np.array([[l, m] for l, m in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                lengths = np.roll(z, -1, axis = 0) - z
                lengths = np.linalg.norm(lengths, axis = 1)
                total_val += 100*sum(lengths**2)
        
        if typ == 'wall': # wall objects must not intersect windows 
            for window in window_polygons:
                intersection = poly1.intersection(window)
                if intersection.area > 0:
                    z = np.array([[l, m] for l, m in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                    lengths = np.roll(z, -1, axis = 0) - z
                    lengths = np.linalg.norm(lengths, axis = 1)
                    total_val += 500*sum(lengths**2)

        ## Wall objects must be on the wall
        if typ == 'wall':
            product = ((x - l/2)**2 + (theta - 3*np.pi/2)**2) # west wall, x = 0, theta = 3pi/2
            product *= ((room.length - l/2 - y)**2 + (theta - np.pi)**2) # north wall, y = room.length, theta = pi
            product *= ((room.width - x - l/2)**2 + (theta - np.pi/2)**2) # east wall, x = room.width, theta = pi/2
            product *= ((y - l/2)**2 + theta**2) # south wall, y = 0, theta = 0
            total_val += product
            
        #Check for overlap of the same kinds of objects 
        for j in range(i + 1, len(objs)):
            if objs[j].tertiary == typ: # only check the same type of object 

                x_j, y_j, theta_j = positions[3*j: 3*j + 3]
                obj_j = objs[j]
                corners_j = corners(x_j, y_j, theta_j, obj_j.width, obj_j.length)
                if nan_check(corners_j):
                    continue
                
                poly2 = Polygon(corners_j)
                intersection = poly1.intersection(poly2)
                
                if intersection.area > 0:
                    z = np.array([[l, m] for l, m in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                    lengths = np.roll(z, -1, axis = 0) - z
                    lengths = np.linalg.norm(lengths, axis = 1)
                    total_val += sum(lengths**2)

        # aligned
        total_val += (np.sin(2*theta)**2)/5
        
    return 5 * total_val
 

def rug_under_central(positions, room, tertiary_index, object_index):

    """ This function ensures that the rug is placed under the central object. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        rug_index: int, index of the rug object in the room.tertiary_objects list
        object_index: int, index of the central object in the room.moving_objects list
    """ 

    if room.tertiary_objects[tertiary_index].tertiary != 'floor':
        return 0
    
    x, y, _ = room.moving_objects[object_index].position
    rug_x, rug_y, _ = positions[3*tertiary_index: 3*tertiary_index + 3]
    return (x - rug_x)**2 + (y - rug_y)**2 

def rug_under_central_forward(positions, room, tertiary_index, object_index): 

    """ This function ensures that the rug is placed under the central object, oriented correctly, and moved slightly forward. 
        This would be used for a rug that is placed under a bed, for example.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        rug_index: int, index of the rug object in the room.tertiary_objects list
        object_index: int, index of the central object in the room.moving_objects list
    """

    if room.tertiary_objects[tertiary_index].tertiary != 'floor':
        return 0
    
    x, y, theta = room.moving_objects[object_index].position
    rug_x, rug_y, rug_theta = positions[3*tertiary_index: 3*tertiary_index + 3]
    tl, tr, br, bl = corners(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)
    forward_direction = [br[0] - tr[0], br[1] - tr[1]] 
    mid_x, mid_y = x + 0.5*forward_direction[0], y + 0.5*forward_direction[1]

    ### want the longer side of the rug to be oriented with the front side of the object 
    tl2, tr2, br2, bl2 = corners(rug_x, rug_y, rug_theta, room.tertiary_objects[tertiary_index].width, room.tertiary_objects[tertiary_index].length)
    if room.tertiary_objects[tertiary_index].width >= room.tertiary_objects[tertiary_index].length:
        direction_1 = [br2[0] - bl2[0], br2[1] - bl2[1]] # rug longer side
    else: 
        direction_1 = [tr2[0] - br2[0], tr2[1] - br2[1]] # rug longer side
    
    direction_2 = [tr[0] - tl[0], tr[1] - tl[1]] # object longer side
    direction_1 = direction_1/np.linalg.norm(direction_1)
    direction_2 = direction_2/np.linalg.norm(direction_2)

    angle_between = np.arccos(np.dot(direction_1, direction_2))
    
    return (rug_x - mid_x)**2 + (rug_y - mid_y)**2 + angle_between**2

def on_top_central(positions, room, tertiary_index, other_index): 

    """ This function ensures that the tertiary object is placed on top of the central object.
        This would be used for placing a table lamp on top of a nightstand, for example. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
        other_index: int, index of the central object in the room.moving_objects list
    """

    if room.tertiary_objects[tertiary_index].tertiary != 'table':
        return 0

    x, y, theta = room.moving_objects[other_index].position
    object_x, object_y, object_theta = positions[3*tertiary_index: 3*tertiary_index + 3]
    w, l = room.tertiary_objects[tertiary_index].width, room.tertiary_objects[tertiary_index].length
    val = (object_x - x)**2 + (object_y - y)**2 + ((object_theta%(2*np.pi)) - (theta%(2*np.pi)))**2

    return val

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

    if room.tertiary_objects[tertiary_index].tertiary != 'table':
        return 0
    
    x, y, theta = room.moving_objects[other_index].position
    object_x, object_y, object_theta = positions[3*tertiary_index: 3*tertiary_index + 3]
    w, l = room.tertiary_objects[tertiary_index].width, room.tertiary_objects[tertiary_index].length

    tl, tr, br, bl = corners(x, y, theta, room.moving_objects[other_index].width, room.moving_objects[other_index].length)

    if corner == 'tl': 
        position = (np.array(tl) + np.array([x, y]))/2

    elif corner == 'tr':
       position = (np.array(tr) + np.array([x, y]))/2
    
    elif corner == 'bl':
        position = (np.array(bl) + np.array([x, y]))/2

    elif corner == 'br': 
        position = (np.array(br) + np.array([x, y]))/2
    
    else: 
        return on_top_corner(positions, room, tertiary_index, other_index, corner = 'tl')

    val = (object_x - position[0])**2 + (object_y - position[1])**2
    poly1 = Polygon([tl, tr, br, bl])

    cs = corners(object_x, object_y, object_theta, w, l)
    poly2 = Polygon(cs)

    intersection = poly1.intersection(poly2)

    if intersection.area != poly2.area and intersection.area > 0: 
        # if any of the corners are off the object add a penalty 
        for corner in cs: 
            if not poly1.contains(Point(corner)):
                d = distance(Point(corner), poly1)
                val += d**2
    
    return val 


def on_wall_near(positions, room, tertiary_index, other_index): 

    """ This function ensures that the tertiary object is placed on the wall near the central object.
        This would be used for placing a painting on the wall near a dining table, for example.

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        tertiary_index: int, index of the tertiary object in the room.tertiary_objects list
        other_index: int, index of the central object in the room.moving_objects list
    """

    if room.tertiary_objects[tertiary_index].tertiary != 'wall':
        return 0

    val = 0
    x, y, _ = room.moving_objects[other_index].position
    object_x, object_y, object_theta = positions[3*tertiary_index: 3*tertiary_index + 3]
    w, l = room.tertiary_objects[tertiary_index].width, room.tertiary_objects[tertiary_index].length
    product = ((object_x - l/2)**2 + (object_theta - 3*np.pi/2)**2) # west wall, x = 0, theta = 3pi/2
    product *= ((room.length - l/2 - object_y)**2 + (object_theta - np.pi)**2) # north wall, y = room.length, theta = pi
    product *= ((room.width - object_x - l/2)**2 + (object_theta - np.pi/2)**2) # east wall, x = room.width, theta = pi/2
    product *= ((object_y - l/2)**2 + object_theta**2) # south wall, y = 0, theta = 0
    #val -= 5*product

    wall_distances = [x**2, (room.width - x)**2, y**2, (room.length - y)**2]
    wall_1 = np.argmin(wall_distances[:2])
    wall_2 = np.argmin(wall_distances[2:]) + 2
    
    distance = np.sqrt((object_x - x)**2 + (object_y - y)**2)
    val += distance**2

    ## on wall (must be on the wall)
    obj_wall_distances = [(object_x - l/2)**2, (room.width - l/2 - object_x)**2, (object_y - l/2)**2, (room.length - l/2 - object_y)**2]
    angles = [((object_theta%(2*np.pi)) - 3*np.pi/2)**2, ((object_theta%(2*np.pi)) - np.pi/2)**2, (object_theta%(2*np.pi))**2, ((object_theta%(2*np.pi)) - np.pi)**2]
    product = (obj_wall_distances[wall_1] + angles[wall_1])*(obj_wall_distances[wall_2] + angles[wall_2])
    val += product * 100

    return val 

def on_wall_in_region(positions, room, tertiary_index, region_name): 

    if room.tertiary_objects[tertiary_index].tertiary != 'wall':
        return 0

    region_names = [region.name for region in room.regions]
    if region_name not in region_names:
        return 0

    val = 0
    region_index = room.find_region_index(region_name)
    object_x, object_y, object_theta = positions[3*tertiary_index: 3*tertiary_index + 3]
    reg_x, reg_y = room.regions[region_index].x, room.regions[region_index].y
    reg_dist = np.sqrt((object_x - reg_x)**2 + (object_y - reg_y)**2)

    for i in range(len(room.regions)): 
        if i != region_index: 
            region_x, region_y = room.regions[i].x, room.regions[i].y
            dist = np.sqrt((object_x - region_x)**2 + (object_y - region_y)**2)
            val += max(0, reg_dist - dist)**2
    return val

def center_ceiling(positions, room, tertiary_index): 

    if room.tertiary_objects[tertiary_index].tertiary != 'ceiling':
        return 0
    
    x, y, theta = positions[3*tertiary_index: 3*tertiary_index + 3]
    val = (x - room.width/2)**2 + (y - room.length/2)**2
    return val

def ceiling_above(positions, room, tertiary_index, other_index): 

    if room.tertiary_objects[tertiary_index].tertiary != 'ceiling':
        return 0
    
    x, y, theta = room.moving_objects[other_index].position
    object_x, object_y, object_theta = positions[3*tertiary_index: 3*tertiary_index + 3]
    val = (object_x - x)**2 + (object_y - y)**2
    return val