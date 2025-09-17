import numpy as np 
from Class_Structures import * 
from shapely.geometry import Polygon
from Individual import *
from Global import * 

@safe_execution
def io_next_to(positions, room, object1_index, object2_index, side1 = None, side2 = None):
    """ The function next_to ensures that two objects are next to each other in a room. 
        This function should only be used when two objects need to be next to each other, 
        e.g. a chair next to a desk, a bed next to a nightstand, a sofa next to side table. 

        Args:
        room: rectangular Room object
        object1: Object object
        object2: Object object
        side1: optional string, one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of object1 to use
        side2: optional string, one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of object2 to use
    """
    val = 0

    obj1 = room.moving_objects[object1_index]
    obj2 = room.moving_objects[object2_index]

    x1, y1, theta1 = get_position(positions, room, object1_index)
    x2, y2, theta2 = get_position(positions, room, object2_index)

    cs1 = np.array(corners(x1, y1, theta1, obj1.width, obj1.length)) # TL, TR, BR, BL
    cs2 = np.array(corners(x2, y2, theta2, obj2.width, obj2.length)) # TL, TR, BR, BL

    if side1: 
        if side1 == 'top' or side1 == 'back':
            point1, point2 = cs1[0], cs1[1] # TL, TR
        elif side1 == 'bottom' or side1 == 'front':
            point1, point2 = cs1[2], cs1[3] # BR, BL
        elif side1 == 'left':
            point1, point2 = cs1[0], cs1[3] # TL, BL
        elif side1 == 'right':
            point1, point2 = cs1[1], cs1[2] # TR, BR
        else:
            return io_next_to(positions, room, object1_index, object2_index, side2 = side2)
    if side2: 
        if side2 == 'top' or side2 == 'back':
            point3, point4 = cs2[0], cs2[1]
        elif side2 == 'bottom' or side2 == 'front':
            point3, point4 = cs2[2], cs2[3]
        elif side2 == 'left':
            point3, point4 = cs2[0], cs2[3]
        elif side2 == 'right':
            point3, point4 = cs2[1], cs2[2]
        else:
            return io_next_to(positions, room, object1_index, object2_index, side1 = side1)
        
    if side1 and side2:

        ### if two sides are given, we want the two sides to be parallel, as well as the two objects to be close to each other
        ### Want it to not matter if the centers are close per se, more that the sides are close (perpendicular distance between the two lines?)
        direction1 = np.array([point2[0] - point1[0], point2[1] - point1[1]]) # side1
        direction2 = np.array([point4[0] - point3[0], point4[1] - point3[1]]) # side2

        angle_diff = np.arccos(np.clip(np.dot(direction1, direction2)/(max(np.linalg.norm(direction1), 1e-6)*max(np.linalg.norm(direction2), 1e-6)), -1, 1))
        val += 2 * np.sin(angle_diff)**2

        if np.linalg.norm(direction1) > np.linalg.norm(direction2):
            point5 = np.array([(point3[0] + point4[0]) / 2, (point3[1] + point4[1]) / 2]) # point on the shorter side
            point6 = np.array([(point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2]) # point on the longer side
            dim_shorter = np.linalg.norm(direction2)
            direction3 = np.array([point5[0] - point1[0], point5[1] - point1[1]])
            direction4 = np.array([point5[0] - point2[0], point5[1] - point2[1]])
            t = np.dot(direction1, direction3)/np.linalg.norm(direction1)
            direction5 = direction1
        else: 
            point5 = np.array([(point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2]) # point on the shorter side
            point6 = np.array([(point3[0] + point4[0]) / 2, (point3[1] + point4[1]) / 2]) # point on the longer side
            dim_shorter = np.linalg.norm(direction1)
            direction3 = np.array([point5[0] - point3[0], point5[1] - point3[1]])
            direction4 = np.array([point5[0] - point4[0], point5[1] - point4[1]])
            t = np.dot(direction2, direction3)/np.linalg.norm(direction2)
            direction5 = direction2
        if t < 0: 
            val += np.linalg.norm(direction3)**2 + (t)**2 + 0.1 * np.linalg.norm(point5 - point6)**2
        elif t > 1: 
            val += np.linalg.norm(direction4)**2 + (t - 1)**2 + 0.1 * np.linalg.norm(point5 - point6)**2
        else:
            #val += 0.01 * np.linalg.norm(point5 - point6)**2
            distance = np.linalg.norm(np.cross(direction5, direction3)) / np.linalg.norm(direction5)
            val += distance**2
        if (side1 == 'front' and side2 == 'front') or (side1 == 'front' and side2 == 'back') or (side1 == 'back' and side2 == 'front') or (side1 == 'back' and side2 == 'back'):
            val += 10*np.linalg.norm(point5 - point6)**2
        if np.linalg.norm(t*direction5) < dim_shorter/2: 
            val += 10*(dim_shorter/2 - np.linalg.norm(t*direction5))**2
        elif np.linalg.norm((1 - t)*direction5) < dim_shorter/2:
            val += 10*(dim_shorter/2 - np.linalg.norm((1 - t)*direction5))**2
        else: 
            distance = np.linalg.norm(np.cross(direction5, direction3)) / np.linalg.norm(direction5)
            val += distance**2
    
    if side1 and not side2:
        min_side_dist = np.inf
        sides = ['front', 'back', 'left', 'right']
        for i in range(4): 
            side_value = io_next_to(positions, room, object1_index, object2_index, side1 = side1, side2 = sides[i])
            min_side_dist = min(min_side_dist, side_value)
        val += min_side_dist
                
        return val 
    
    if side2 and not side1:     
        min_side_dist = np.inf
        sides = ['front', 'back', 'left', 'right']
        for i in range(4): 
            side_value = io_next_to(positions, room, object1_index, object2_index, side1 = sides[i], side2 = side2)
            min_side_dist = min(min_side_dist, side_value)
        val += min_side_dist

        return val 
    if not side2 and not side1: 
        ### If no sides are given, we want the two objects to be close to each other as possible from any direction
        ### Want the distance between the two objects to be minimized but also to not be overlapping 

        distance = np.linalg.norm(np.array([x1, y1]) - np.array([x2, y2]))
        val += distance**2

    return 2*val 


@safe_execution
def io_away_from(positions, room, object1_index, object2_index, min_dist = 2):
    """ The function p_away_from ensures that two objects are away from each other in a room.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room

    """
    x1, y1, _ = get_position(positions, room, object1_index)
    x2, y2, _ = get_position(positions, room, object2_index)

    distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    return np.exp(min_dist - distance)

@safe_execution
def io_near(positions, room, object1_index, object2_index, max_dist = 3.0):
    """ The function next_to ensures that two objects are within a certain distance to each other. 
        They are not necessarily next to each other, but they are close.
        
        Args:
        room: rectangular Room object
        object1_index: Object object
        object2_index: Object object
        max_dist: furthest distance between the two objects. Please write this as a float, e.g. 3.0.

    """

    x1, y1, _ = get_position(positions, room, object1_index)
    x2, y2, _ = get_position(positions, room, object2_index)

    distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    return min(max_dist - distance, 0.0)**2

@safe_execution
def io_parallel(positions, room, object1_index, object2_index):
    """ The function p_parallel ensures that two objects have the same orientation in a room.
        That is, that they are parallel to each other. It does not handle distance, so if 
        proximity is important, please combine this function with p_near, or p_next to, or even p_between. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in  roomthe
    """
    _, _, theta1 = get_position(positions, room, object1_index)
    _, _, theta2 = get_position(positions, room, object2_index)
     
    return ((theta1%(2*np.pi)) - (theta2%(2*np.pi)))**2  

@safe_execution
def io_facing(positions, room, object1_index, object2_index, both = False):
    """ The function facing ensures that object1 is facing object2 in a room.
        If both is True, then object2 will also be facing object1.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
    """
    val = 0.0

    object1, object2 = room.moving_objects[object1_index], room.moving_objects[object2_index]
    x1, y1, theta1 = get_position(positions, room, object1_index)
    x2, y2, theta2 = get_position(positions, room, object2_index)

    cs1 = np.array(corners(x1, y1, theta1, object1.width, object1.length))# TL, TR, BR, BL
    tl1, tr1, br1, bl1 = cs1
    dir1 = np.array([bl1[0] - tl1[0], bl1[1] - tl1[1]])
    dir1 /= np.linalg.norm(dir1)

    distances = np.linalg.norm(cs1 - np.array([x2, y2]), axis = 1) 
    ## want front right to be closer than back right, and front left to be closer than back left 
    val += max(0.0, distances[3] - distances[0])**2 + max(0.0, distances[2] - distances[1])**2
    ## Line 1 goes from front left corner onward, line 2 goes from front right corner 
    ## distance of object2 from line1
    dist1 = abs((bl1[1] - tl1[1])*x2 - (bl1[0] - tl1[0])*y2 + bl1[0]*tl1[1] - bl1[1]*tl1[0])/np.sqrt((bl1[0] - tl1[0])**2 + (bl1[1] - tl1[1])**2)
    ## distance of object2 from line2
    dist2 = abs((br1[1] - tr1[1])*x2 - (br1[0] - tr1[0])*y2 + br1[0]*tr1[1] - br1[1]*tr1[0])/np.sqrt((br1[0] - tr1[0])**2 + (br1[1] - tr1[1])**2)
    ## distance between the two lines is width, therefore want dist1 + dist2 = width 
    val += (dist1 + dist2 - object1.width)**2
    if both: 
        val += io_facing(positions, room, object2_index, object1_index)
        cs2 = np.array(corners(x2, y2, theta2, object2.width, object2.length))# TL, TR, BR, BL
        dir2 = np.array([cs2[3][0] - cs2[0][0], cs2[3][1] - cs2[0][1]])
        dir2 /= np.linalg.norm(dir2)
        val += (np.dot(dir1, dir2) + 1)**2
    return val 

@safe_execution
def io_under_central(positions, room, object1_index, object2_index):
    """ The function under ensures that object1 (a rug) is underneath object2 (any moving_object) and centered.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
    """

    ## Under basically means that their positions are the same.
    x1, y1, theta1 = get_position(positions, room, object1_index)
    x2, y2, theta2 = get_position(positions, room, object2_index)

    val = ((x1 - x2)**2 + (y1 - y2)**2  + ((theta1%(2*np.pi)) - (theta2%(2*np.pi)))**2)
    return val 

@safe_execution
def io_on(positions, room, object1_index, object2_index):
    """ The function p_on ensures that object1 is on top of object2 (a rug) but does not ensure that it is centered.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
    """

    obj2 = room.moving_objects[object2_index]   
 
    ## Under basically means that their positions are the same.
    obj1 = room.moving_objects[object1_index] 
    x1, y1, theta1 = get_position(positions, room, object1_index)
    x2, y2, theta2 = get_position(positions, room, object2_index)
    cs1 = corners(x1, y1, theta1, obj1.width, obj1.length)
    cs2 = corners(x2, y2, theta2, obj2.width, obj2.length)
    poly1 = Polygon(cs1)
    poly2 = Polygon(cs2)

    intersection = poly1.intersection(poly2)
    if intersection.area == poly1.area: 
        return 0.0

    lengths2 = np.roll(np.array(cs1), -1, axis = 0) - np.array(cs1)
    total_lengths = sum(np.linalg.norm(lengths2, axis = 1)**2)
    cs1 = np.array(cs1).reshape(-1, 2)
    cs2 = np.array(cs2).reshape(-1, 2)
    if intersection.area == 0: 
        dists = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                dists[i, j] = np.linalg.norm(cs1[i] - cs2[j])
        return np.min(dists) * total_lengths
    
    else: 
        x = np.array([[i, j] for i, j in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
        lengths1 = np.roll(x, -1, axis = 0) - x
        lengths1 = np.linalg.norm(lengths1, axis = 1)
        lengths_on_rug = sum(lengths1**2)
    
        return total_lengths - lengths_on_rug

@safe_execution
def io_infront(positions, room, object1_index, object2_index, dist = 0.8, parallel = False):
    """ The function p_infront ensures that object1 is in front of object2 (both moving_objects i.e. not windows or doors). E.g a coffee table should be in front of a sofa....

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, Object object
        object2_index: int, Object object
        dist: float, desired distance between two objects. E.g. if its a sofa and a coffee table, the distance should be around 0.8m, 
                                                            if its a sofa and a fireplace, the distance should be around 2m/2.5m.
    """

    ## want object1 position to be in front of object2 position in the frame of object2
    x1, y1, theta1 = get_position(positions, room, object1_index)
    x2, y2, theta2 = get_position(positions, room, object2_index)

    obj1 = room.moving_objects[object1_index]
    obj2 = room.moving_objects[object2_index]

    cs2 = corners(x2, y2, theta2, obj2.width, obj2.length) # TL, TR, BR, BL
    mid_front = np.array([(cs2[2][0] + cs2[3][0])/2, (cs2[2][1] + cs2[3][1])/2])
    mid2front = np.array([mid_front[0] - x2, mid_front[1] - y2])
    mid2front /= np.linalg.norm(mid2front)

    projection = mid_front + (dist + min(obj1.width, obj1.length)/2) * mid2front
    val = (projection[0] - x1)**2 + (projection[1] - y1)**2 
    if parallel == True: 
        val += 3*((theta1%(2*np.pi) - (theta2%(2*np.pi)))**2)
    return 4*val

@safe_execution
def io_perp(positions, room, object1_index, object2_index, center_object_index = None):
    """ The function p_perp ensures that two objects are aligned in a room perpendicularly. 
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

    val = 0.0
    obj1, obj2 = room.moving_objects[object1_index], room.moving_objects[object2_index]
    x1, y1, theta1 = get_position(positions, room, object1_index)
    x2, y2, theta2 = get_position(positions, room, object2_index)

    cs1 = np.array(corners(x1, y1, theta1, obj1.width, obj1.length))# TL, TR, BR, BL
    cs2 = np.array(corners(x2, y2, theta2, obj2.width, obj2.length))

    mid_front1 = (cs1[2, :] + cs1[3, :])/2
    mid_front2 = (cs2[2, :] + cs2[3, :])/2

    dir1 = (cs1[3, :] - cs1[0, :])/np.linalg.norm(cs1[3, :] - cs1[0, :])
    dir2 = (cs2[3, :] - cs2[0, :])/np.linalg.norm(cs2[3, :] - cs2[0, :])

    ### Find t1, and t2 (intersection line lengths - want there to be a right angled triangle between each object)
    BA = mid_front2 - mid_front1
    t1 = np.dot(np.array([dir2[1], -dir2[0]]), BA) / np.dot(np.array([dir2[1], -dir2[0]]), dir1)
    t2 = np.dot(np.array([dir1[1], -dir1[0]]), BA) / np.dot(np.array([dir2[1], -dir2[0]]), dir1)
    
    if not center_object_index:
        lim = np.sqrt((0.8*obj1.width)**2 + (0.8*obj2.width)**2)
        val += (np.linalg.norm(BA) - np.sqrt(t1**2 + t2**2))**2 
        val += min(0.0, t1)**2 + min(0.0, t2)**2 # t1 and t2 should be bigger than 0 
        val += min(0.0, lim - np.sqrt(t1**2+ t2**2))**2 # t1 and t2 should not be too big
        val += ((max((theta1%(2*np.pi)), (theta2%(2*np.pi))) - min((theta1%(2*np.pi)), (theta2%(2*np.pi)))) - np.pi/2)**2 ## thetas should be pi/2 apart
    else: 
        center_obj = room.moving_objects[center_object_index]
        lim = np.sqrt((center_obj.width)**2 + (center_obj.length)**2)
        x3, y3, theta3 = positions[3*center_object_index:3*center_object_index + 3]
        val += min(0.0, t1)**2 + min(0.0, t2)**2 # t1 and t2 should be bigger than 0 
        val += (np.linalg.norm(BA) - np.sqrt((t1**2 + t2**2)))**2 ## mid_front1, mid_front2, and intersection point should make a right angled triangle 
        C = np.array([x1, y1]) + t1 * dir1 
        val += (C[0] - x3)**2 + (C[1] - y3)**2 # C should be the center of the center object
        val += min(0.0, lim - np.sqrt(t1**2+ t2**2))**2 # t1 and t2 should not be too big
        val += ((max((theta1%(2*np.pi)), (theta2%(2*np.pi))) - min((theta1%(2*np.pi)), (theta2%(2*np.pi)))) - np.pi/2)**2 ## thetas should be pi/2 apart
    return val

@safe_execution
def io_surround(positions, room, central_object_index, object_indices):
    """ The function p_surroudn ensures that central_object is surrounded by all the objects in object_indices.
        This would be used for chairs around a dining table.

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        central_object_index: int, Object object
        object_indices: list of ints, indices of Object objects
    """

    val = 0

    center_obj = room.moving_objects[central_object_index]
    center_x, center_y, center_theta = center_obj.position

    other_length = room.moving_objects[object_indices[0]].length 
    other_width = room.moving_objects[object_indices[0]].width

    pos = np.array(positions).reshape(-1, 3)
    indices = [positions_index(room, i)//3 for i in object_indices]
    pos = pos[indices, :]

    center_of_mass = np.mean(pos[:, :2], axis = 0)
    val += (center_of_mass[0] - center_x)**2 + (center_of_mass[1] - center_y)**2 # center of mass of all the objects


    ## Need to check if any of the sides are too close to walls. 
    cs = corners(center_x, center_y, center_theta, center_obj.width, center_obj.length) # TL, TR, BR, BL
    sides = [[cs[0], cs[1]],  [cs[2], cs[3]], [cs[1], cs[2]], [cs[3], cs[0]]] # back, front, right, left
    wall_distances = np.zeros((4, 4)) # each row is a side, each column is a wall
    lengthways = []
    widthways = []
    for i in range(4): 
        side1, side2 = sides[i]
        side1_distances = 0.5 * np.array([side1[0]**2, side1[1]**2, (room.width - side1[0])**2, (room.length - side1[1])**2])
        side2_distances = 0.5 * np.array([side2[0]**2, side2[1]**2, (room.width - side2[0])**2, (room.length - side2[1])**2])
        if np.abs(np.min(side1_distances) - np.min(side2_distances)) < 0.1: 
            lengthways.append(i)
        else:
            widthways.append(i)

        wall_distances[i,:] = (side1_distances + side2_distances)

    wall_distances = np.min(wall_distances, axis = 1)
    sides = ['back', 'front', 'right', 'left']
    inds = []

    for i in lengthways: 
        if wall_distances[i] >= 0.05 + other_length: 
            inds.append(i)
    for i in widthways: 
        if wall_distances[i] >= 0.05 + other_width/2: 
            inds.append(i)
    sides = [sides[i] for i in inds]
    obj_per_sides = [[] for i in range(len(sides))]
    num = len(object_indices) // len(sides)
    remaining = len(object_indices) % len(sides)
    
    for i in range(num): 
        for j in range(len(sides)*i, len(sides)*(i+1)):
            obj_per_sides[j%len(sides)].append(object_indices[j])
            val += 3*io_next_to(positions, room, object_indices[j], central_object_index, side1 = 'front', side2 = sides[j%len(sides)])
    
    new_sides = []
    index = len(sides)*num
    if center_obj.width >= center_obj.length:
        if 'back' in sides: 
            new_sides.append('back')
        if 'front' in sides:
            new_sides.append('front')
        if 'left' in sides:
            new_sides.append('left')
        if 'right' in sides:
            new_sides.append('right')
    else: 
        if 'left' in sides:
            new_sides.append('left')
        if 'right' in sides:
            new_sides.append('right')
        if 'back' in sides:
            new_sides.append('back')
        if 'front' in sides:
            new_sides.append('front')
    for i in range(remaining):
        obj_per_sides[i].append(object_indices[index + i])
        val += 3*io_next_to(positions, room, object_indices[index + i], central_object_index, side1 = 'front', side2 = new_sides[i])
        
    for side in obj_per_sides: 
        if len(side) == 1:
            val += io_facing(positions, room, side[0], central_object_index, False)
    val += no_overlap(positions, room)
    return val


@safe_execution
def io_not_facing(positions, room, object1_index, object2_index):
    """ The function facing ensures that object1 is NOT facing object2 in a room.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room
        object2_index: int, index of object2 in the room
    """
    val = 0.0

    object1 = room.moving_objects[object1_index]
    x1, y1, theta1 = get_position(positions, room, object1_index)
    x2, y2, theta2 = get_position(positions, room, object2_index)

    cs1 = np.array(corners(x1, y1, theta1, object1.width, object1.length))# TL, TR, BR, BL
    tl1, tr1, br1, bl1 = cs1
    dir1 = np.array([bl1[0] - tl1[0], bl1[1] - tl1[1]])
    dir1 /= np.linalg.norm(dir1)

    ## Line 1 goes from front left corner onward, line 2 goes from front right corner 
    ## distance of object2 from line1
    dist1 = abs((bl1[1] - tl1[1])*x2 - (bl1[0] - tl1[0])*y2 + bl1[0]*tl1[1] - bl1[1]*tl1[0])/np.sqrt((bl1[0] - tl1[0])**2 + (bl1[1] - tl1[1])**2)
    ## distance of object2 from line2
    dist2 = abs((br1[1] - tr1[1])*x2 - (br1[0] - tr1[0])*y2 + br1[0]*tr1[1] - br1[1]*tr1[0])/np.sqrt((br1[0] - tr1[0])**2 + (br1[1] - tr1[1])**2)
    ## distance between the two lines is width, therefore want dist1 + dist2 > width 
    val += min((dist1 + dist2) - object1.width, 0.0)**2
    return val 

@safe_execution
def io_between(positions, room, object1_index, object2_index, object3_index): 
    
    """ The function p_between ensures that object1 is in between the two objects object2 and object3 (specifically 
        between the left and right side of the two objects).  
        This would be used for something like a side table being between two chairs, or a bed being between two nightstands. 
        This is not used for something like a dining table between two chairs, as the chairs are not side by side. It is also 
        not used for a coffee table between a sofa and a tv, as the sofa and tv are not side by side.
        Or even a nightstand going between two beds. This can be used instead of two p_next_to functions, or in conjunction with them.
        
        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object1_index: int, index of object1 in the room (** this is the object that will go in between the other two objects)
        object2_index: int, index of object2 in the room
        object3_index: int, index of object3 in the room
        sides: list of two strings, either ['left', 'right'] or ['front', 'front']. ['left', 'right'] would be used to place an object in between the 
                left and right sides of the other objects (e.g. a bed between 2 nighstands) and ['front', 'front'] would be used to place an object in between the
                front sides of the other objects (e.g. for a coffee table between a sofa and a tv/fireplace. )
    """


    vali1 = io_next_to(positions, room, object1_index, object2_index, side1 = 'left', side2 = 'right')
    valj1 = io_next_to(positions, room, object1_index, object3_index, side1 = 'right', side2 = 'left')
    val1 = vali1 + valj1

    vali2 = io_next_to(positions, room, object1_index, object2_index, side1 = 'right', side2 = 'left')
    valj2 = io_next_to(positions, room, object1_index, object3_index, side1 = 'left', side2 = 'right')
    val2 = vali2 + valj2

    return min(val1, val2)

