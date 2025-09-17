## All the Individual Object constraint functions are defined here
from Class_Structures import *
from shapely.geometry import Polygon

## Sides of Objects 
# - Options for sides: 'front', 'back', 'left', 'right'. 
# All the code is for 2D positioning, so if there is something to do with the 'top' of the object normally ignore it. 
# - 'front' is the side of the object that is the front like the side of a wardrobe with doors, or the foot of the bed. This would never be placed against a wall. 
# - 'back' is the back of an object like the headboard of a bed, or the back of a sofa. 
# -'left' and 'right' are the sides of the object, like the left side of a bed or the right side of a sofa. These are from the perspective of standing behind the object. 

def TR(x, y, theta, w, l):
    return (x + w/2 * np.cos(theta) + l/2 * np.sin(theta), y + w/2 * np.sin(theta) - l/2 * np.cos(theta))

def TL(x, y, theta, w, l):
    return (x - w/2 * np.cos(theta) + l/2 * np.sin(theta), y - w/2 * np.sin(theta) - l/2 * np.cos(theta))

def BR(x, y, theta, w, l):
    return (x + w/2 * np.cos(theta) - l/2 * np.sin(theta), y + w/2 * np.sin(theta) + l/2 * np.cos(theta))

def BL(x, y, theta, w, l):
    return (x - w/2 * np.cos(theta) - l/2 * np.sin(theta), y - w/2 * np.sin(theta) + l/2 * np.cos(theta))

def corners(x, y, theta, w, l):
    return [TL(x, y, theta, w, l), TR(x, y, theta, w, l), BR(x, y, theta, w, l), BL(x, y, theta, w, l)]

def safe_execution(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            #print(f"An error occurred: {e}, function: {func.__name__}")
            return 0.0
    return wrapper

def nan_check(points):
    for point in points:  
        if np.isnan(point[0]) or np.isnan(point[1]):
            return True
    return False

def positions_index(room, object_index): 

    if len(room.fm_indices) == 0: 
        return 3*object_index
    else: 
        new_index = 1 * object_index
        for i in range(len(room.fm_indices)):
            ind = room.fm_indices[i]
            if ind < object_index: 
                new_index -= 1
        return 3*new_index
    
def get_position(positions, room, object_index):
    if object_index in room.fm_indices: 
        x, y, theta = room.moving_objects[object_index].position
    else: 
        index = positions_index(room, object_index)
        x, y, theta = positions[index:index+3]
    return x, y, theta

@safe_execution 
def ind_next_to_wall(positions, room, object_index, side = 'back'):
    """ This function ensures an object is next to a wall in a room. 
        The specific side of the object will be used. If no side is given, the back of the object will be used.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        side: string, one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of the object to check e.g back of bed 
    """

    x, y, theta = get_position(positions, room, object_index)
    cs = np.array(corners(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)) # TL, TR, BR, BL
    distances =  np.zeros((4, 4)) # each row a different corner, each column a different wall 
    sides = [[0, 1], [2, 3], [0, 3], [1, 2]]
    for i in range(4):
        distances[i, :] = np.array([(cs[i][1] - room.length)**2, (cs[i][0] - room.width)**2, cs[i][1]**2, cs[i][0]**2])

    distances = np.sqrt(distances)
    side_distances = np.zeros_like(distances) # columns: N, E, S, W, rows: back, top, left, right
    for i in range(4):
        side_distances[i, :] = distances[sides[i][0], :] + distances[sides[i][1], :]

    val = 0 

    if side == "top" or side == "back":
        wall = np.argmin(side_distances[0, :])
        ds = side_distances[:, wall]
        # distance of side to north or south, x side of corner 1 to east or west 
        val += (min(side_distances[0, 0], side_distances[0, 2]) * min(side_distances[0, 1], side_distances[0, 3]))
        val += max(ds[0] - ds[1], 0.0)**2 + max(ds[0] - ds[2], 0.0)**2 + max(ds[0] - ds[3], 0.0)**2
    elif side == "bottom" or side == "front":
        wall = np.argmin(side_distances[1, :])
        ds = side_distances[:, wall]
        val += (min(side_distances[1, 0], side_distances[1, 2]) * min(side_distances[1, 1], side_distances[1, 3]))
        val += max(ds[1] - ds[0], 0.0)**2 + max(ds[1] - ds[2], 0.0)**2 + max(ds[1] - ds[3], 0.0)**2
    elif side == "left":
        wall = np.argmin(side_distances[2, :])
        ds = side_distances[:, wall]
        val += (min(side_distances[2, 0], side_distances[2, 2]) * min(side_distances[2, 1], side_distances[2, 3]))
        val += max(ds[2] - ds[0], 0.0)**2 + max(ds[2] - ds[1], 0.0)**2 + max(ds[2] - ds[3], 0.0)**2
    elif side == "right":
        wall = np.argmin(side_distances[3, :])
        ds = side_distances[:, wall]
        val += (min(side_distances[3, 0], side_distances[3, 2]) * min(side_distances[3, 1], side_distances[3, 3]))
        val += max(ds[3] - ds[0], 0.0)**2 + max(ds[3] - ds[1], 0.0)**2 + max(ds[3] - ds[2], 0.0)**2
    else: 
        ## Assume side is meant to be back, 
        return ind_next_to_wall(positions, room, object_index, side = 'back') 
    
    return 2*val

@ safe_execution
def ind_near_wall(positions, room, object_index, max_dist = 0.5):
    """ This function ensures an object is near to a wall in a room. 
        The specific side of the object will be used. If no side is given, the back of the object will be used.
                
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        side: string, one of 'back', 'front', 'left', 'right', defines which side of the object to check e.g back of bed 
        max_dist: float, maximum distance the object should be from the wall
    """
        
    x, y, theta = get_position(positions, room, object_index)
    cs = np.array(corners(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)) # TL, TR, BR, BL
    distances =  np.zeros((4, 4))
    sides = [[0, 1], [2, 3], [0, 3], [1, 2]]
    for i in range(4):
        distances[i, :] = np.array([(cs[i][1] - room.length)**2, (cs[i][0] - room.width)**2, cs[i][1]**2, cs[i][0]**2])

    distances = np.sqrt(distances)
    side_distances = np.zeros_like(distances) # columns: N, E, S, W, rows: top, bottom, left, right
    for i in range(4):
        side_distances[i, :] = (distances[sides[i][0], :] + distances[sides[i][1], :])/2

    val = 0 
    wall = np.argmin(side_distances[0, :])
    ds = side_distances[:, wall]
    val += min(max_dist - np.min(ds), 0.0)**2
    val += max(ds[0] - ds[1], 0.0)**2 + max(ds[0] - ds[2], 0.0)**2 + max(ds[0] - ds[3], 0.0)**2
    
    return val

@ safe_execution
def ind_in_corner(positions, room, object_index, side = 'back', max_dist = 0.5):
    """ This function can be used to ensure that an object is placed into a corner. 
        The back of the object will always be placed closest to the corner. 

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        max_dist: float, maximum distance the object should be from the wall
    """

    x, y, theta = get_position(positions, room, object_index)
    cs = np.array(corners(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)) # TL, TR, BR, BL
    distances =  np.zeros((4, 4)) # each row a different corner, each column a different room corner 
    room_corners = [[0, 0], [0, room.length], [room.width, 0], [room.width, room.length]]
    sides = [[0, 1], [2, 3], [0, 3], [1, 2]]
    for i in range(4):
        for j in range(4): 
            distances[i, j] = (cs[i][0] - room_corners[j][0])**2 + (cs[i][1] - room_corners[j][1])**2

    distances = np.sqrt(distances)
    side_distances = np.zeros_like(distances) # columns: N, E, S, W, rows: back, front, left, right
    for i in range(4):
        side_distances[i, :] = (distances[sides[i][0], :] + distances[sides[i][1], :])/2
    
    ## want to minimise the distance of the back corners to the corner of the room.
    room_corner = np.argmin(side_distances[0, :]) 
    val = 0
    val += min(max_dist - side_distances[0, room_corner], 0.0)**2  # two back corners should be equally close
    val += (distances[0, room_corner] - distances[1, room_corner])**2# back side should be closer than any other side
    val += min(side_distances[1, room_corner] + side_distances[2, room_corner] + side_distances[3, room_corner] - 3*side_distances[0, room_corner], 0.0)**2 # back side should be less than max_dist away from the corner

    return val 


@safe_execution   
def ind_close_to_fixed_object(positions, room, object_index, fixed_object_type, side = None, max_dist = 0.5):
    """ This function ensures an object is next to a fixed object in a room. 
        If side is given, the specific side of the object will be used.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        fixed_object_type: string, type of fixed object to check. One of 'window', 'door', 'socket'
        side: string, one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of the object to check
    """

    x, y, theta = get_position(positions, room, object_index)
    cs = np.array(corners(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)) # TR, BR, TL, BL
    if side == "top" or side == "back":
        cs = [cs[0], cs[1]]
    elif side == "bottom" or side == "front":
        cs = [cs[2], cs[3]]
    elif side == "left":
        cs = [cs[0], cs[3]]
    elif side == "right":
        cs = [cs[1], cs[2]]
    
    f_objs = room.find_all(fixed_object_type)
    if len(f_objs) == 0: 
        return 0.0
    if side: 
        dist = np.inf
        point = [(cs[0][0] + cs[1][0])/2, (cs[0][1] + cs[1][1])/2]
        for i in range(len(f_objs)):
            f_obj = f_objs[i]
            new_dist = (point[0] - f_obj.position[0])**2 + (point[1] - f_obj.position[1])**2
            if new_dist < dist: 
                dist = new_dist
        return max(dist - max_dist**2, 0.0)
    else:
        distances = np.zeros((len(f_objs), 4)) # corners to the objects
        for i in range(len(f_objs)):
            for j in range(4): 
                distances[i, j] = (cs[j][0] - f_objs[i].position[0])**2 + (cs[j][1] - f_objs[i].position[1])**2
        return max(min(distances.flatten()) - max_dist**2, 0.0)

@safe_execution
def ind_away_from_fixed_object(positions, room, object_index, fixed_object_type, min_dist = 2):
    """ This function ensures an object is not near to a fixed object in a room. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        fixed_object_type: string, type of fixed object to check. One of 'window', 'door', 'plug'
        min_dist: float, minimum distance between the object and the fixed object to be considered away from it 
    """
    x, y, _ = get_position(positions, room, object_index)
    w, l = room.moving_objects[object_index].width, room.moving_objects[object_index].length
    half_diag = np.sqrt((w/2)**2 + (l/2)**2)
    f_objs = room.find_all(fixed_object_type)
    if len(f_objs) == 0:
        return 0.0
    
    distances = np.zeros(len(f_objs))
    for i in range(len(f_objs)):
        f_obj = f_objs[i]
        distances[i] = max(0.0, (min_dist + half_diag) - np.sqrt(((x - f_obj.position[0])**2 + (y - f_obj.position[1])**2)))**2
     
    val = sum(distances)
    
    return 0.8*val

@safe_execution
def ind_accessible(positions, room, object_index, sides = [], min_dist = None):
    """ This function ensures that an object is accessible from given sides. 
        If no sides are given, all the sides will be used. If min_dist is given, then this function 
        will act as a clearance constraint. If you want all the sides to be accesible, sides = ['top', 'bottom', 'left', 'right'].
    
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        sides: a list of strings, each one one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of the object to check
        min_dist: float, minimum distance of clearance there should be on the sides. 
    """
    
    val = 0.0 # initialise output value 

    obj = room.moving_objects[object_index]
    rug_names = ['rug', 'mat', 'Rug', 'Mat', 'RUG', 'MAT', 'carpet', 'Carpet']
    for i in range(len(rug_names)): 
        if rug_names[i] in obj.name:
            return 0.0
    
    x, y, theta = get_position(positions, room, object_index)
    TL, TR, BR, BL = corners(x, y, theta, obj.width, obj.length)
    polys = []
    if min_dist: 
        distance = min_dist
    else: 
        distance = min(1, np.max([obj.width, obj.length, 0.5]))

    def project(point1, point2, distance = distance):
        direction = np.array([point1[0] - point2[0], point1[1] - point2[1]])
        direction /= np.linalg.norm(direction)
        return [point1[0], point1[1]] + distance * direction
    
    def wall_bounds(point):
        if point[0] < 0 or point[0] > room.width or point[1] < 0 or point[1] > room.length:
            return min(0.0, point[0])**2 + min(0.0, point[1])**2 + max(0.0, point[0] - room.width)**2 + max(0.0, point[1] - room.length)**2
        return 0.0
    
    if sides == []: 
        sides = ['front']

    if sides == ['sides']: 
        sides = ['left', 'right']
    
    for i in range(len(sides)): 

        if sides[i] == 'long':
            if obj.width > obj.length:
                val = np.random.randn()
                if val > 0: 
                    sides[i] = 'left'
                else: 
                    sides[i] = 'right'
            else: 
                sides[i] = 'front'
        elif sides[i] == 'short':
            if obj.width > obj.length:
                sides[i] = 'front'
            else: 
                sides[i] = 'left'
        
    for side in sides: 
        if side == 'top' or side == 'back':
            new_pointL = project(TL, BL)
            new_pointR = project(TR, BR)
            if nan_check([new_pointL, new_pointR]):
                continue
            polys += [Polygon([TL, TR, new_pointR, new_pointL])]
            val += wall_bounds(new_pointL) + wall_bounds(new_pointR)
        elif side == 'bottom' or side == 'front':
            new_pointL = project(BL, TL) 
            new_pointR = project(BR, TR)
            if nan_check([new_pointL, new_pointR]):
                continue
            polys += [Polygon([new_pointL, new_pointR, BR, BL])]
            val += wall_bounds(new_pointL) + wall_bounds(new_pointR)
        elif side == 'left':
            new_pointT = project(TL, TR)
            new_pointB = project(BL, BR)
            if nan_check([new_pointT, new_pointB]):
                continue
            polys += [Polygon([TL, new_pointT, new_pointB, BL])]
            val += wall_bounds(new_pointT) + wall_bounds(new_pointB)
        elif side == 'right':
            new_pointT = project(TR, TL)
            new_pointB = project(BR, BL)
            if nan_check([new_pointT, new_pointB]):
                continue
            polys += [Polygon([new_pointT, TR, BR, new_pointB])]
            val += wall_bounds(new_pointT) + wall_bounds(new_pointB)
        else: 
            ## If no side is given or a side is incorrect, assume accessible from the front 
            return ind_accessible(positions, room, object_index, ['front'])
    
    for poly in polys:
        for i in range(len(room.moving_objects)):
            if i == object_index:
                continue

            rug = 0
            for name in rug_names: 
                if name in room.moving_objects[i].name:
                    rug = 1
                    continue
            if rug == 1:
                continue

            x, y, theta = get_position(positions, room, i)
            poly2 = Polygon(corners(x, y, theta, room.moving_objects[i].width, room.moving_objects[i].length))
            intersection = poly.intersection(poly2)
            if intersection.area > 1e-3:
                x = np.array([[i, j] for i, j in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                lengths = np.roll(x, -1, axis = 0) - x
                lengths = np.linalg.norm(lengths, axis = 1)
                val += sum(lengths**2)   

        for i in range(len(room.fixed_objects)):
            if room.fixed_objects[i].name != 'door':
                continue
            else: 
                poly2 = Polygon(room.fixed_objects[i].corners())
                intersection = poly.intersection(poly2)
                if intersection.area > 1e-3:
                    x = np.array([[i, j] for i, j in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                    lengths = np.roll(x, -1, axis = 0) - x
                    lengths = np.linalg.norm(lengths, axis = 1)
                    val += 5*sum(lengths**2)

    return 3*val

@safe_execution
def ind_central(positions, room, object_index, both = False):
    """ This function ensures that an object is centrally placed in the room. 
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        both: bool (optional), if True, then the object should be placed centrally in both x and y. For example for a bed, this would be False, 
              but for a dining table, it should be True..
    """

    ## want the position to be in the middle 1/3 of x or the middle 1/3 of y
    lower_x, upper_x = room.width/3, 2*room.width/3
    lower_y, upper_y = room.length/3, 2*room.length/3
    mid_x, mid_y = room.width/2, room.length/2

    x, y, theta = get_position(positions, room, object_index)
    if both: 
        val = min(x - lower_x, 0.0)**2 + min(upper_x - x, 0.0)**2 + min(y - lower_y, 0.0)**2 + min(upper_y - y, 0.0)**2 + 0.01*((x - mid_x)**2 + (y - mid_y)**2)
    else: 
        val = (min(x - lower_x, 0.0) + min(upper_x - x, 0.0))*(min(y - lower_y, 0.0) + min(upper_y - y, 0.0))

    val += (np.sin(2*theta)**2)/5
    return val

@safe_execution
def ind_in_region(positions, room, object_index, region_name, weight = 5):
    """ This function ensures that an object is in a given region. 
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        region_name: string, name of the region for the object to be in 
    """
    regions = room.regions
    region_index = room.find_region_index(region_name)
    if region_index == None: 
        ## check both uppercase
        if " " in region_name: 
            region_name2 = region_name.split(" ")[0].capitalize() + " " + region_name.split(" ")[1].capitalize()
        ## check both uppercase
            region_name3 = region_name.split(" ")[0].lower() + " " + region_name.split(" ")[1].lower()
        ## check uppercase first, lower case second
            region_name4 = region_name.split(" ")[0].capitalize() + " " + region_name.split(" ")[1].lower()
        for r in regions: 
            if r.name == region_name2 or r.name == region_name3 or r.name == region_name4:
                region_index = regions.index(r)
                break
        if region_index == None:
            return 0.0
    
    x, y, _ = get_position(positions, room, object_index)
    r_dist = np.sqrt((regions[region_index].x - x)**2 + (regions[region_index].y - y)**2)
    value = 0 
    for i in range(len(regions)):
        if i == region_index:
            continue
        else:
            value += min(np.sqrt((regions[i].x - x)**2 + (regions[i].y - y)**2) - r_dist, 0.0)**2
    return weight*value

@safe_execution
def ind_not_block_fixed_object(positions, room, object_index, fixed_object_type):

    """ This function ensures that an object does not block a fixed object in the room. 
        E.g. a wardrobe shouldn't block a window.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        fixed_object_type: string, type of fixed object to check. E.g one of 'window', 'door', 'plug'
    """

    val = 0
    fixed_objects = room.find_all(fixed_object_type)
    x, y, theta = get_position(positions, room, object_index)
    obj = room.moving_objects[object_index]
    cs = corners(x, y, theta, obj.width, obj.length)
    poly = Polygon(cs)

    for obj in fixed_objects: 
        if obj.name == 'window':
            x, y, theta = obj.position
            cs = obj.corners()
            poly_fixed = Polygon(cs)
            intersection = poly.intersection(poly_fixed)
            if intersection.area > 1e-3:
                x = np.array([[i, j] for i, j in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                lengths = np.roll(x, -1, axis = 0) - x
                lengths = np.linalg.norm(lengths, axis = 1)
                val += sum(lengths**2)  
        elif obj.name == 'door':
            door_corners = obj.corners()
            poly_fixed = Polygon(door_corners)
            intersection = poly.intersection(poly_fixed)
            if intersection.area > 1e-3:
                x = np.array([[i, j] for i, j in zip(intersection.exterior.xy[0], intersection.exterior.xy[1])])
                lengths = np.roll(x, -1, axis = 0) - x
                lengths = np.linalg.norm(lengths, axis = 1)
                val += sum(lengths**2)  

        else: 
            return 0.0
                
    return val

@safe_execution
def ind_under_window(positions, room, object_index):

    """ This function ensures that the object (object_index) will be placed underneath a window.
        For example, you might want a desk or a dresser below (but not blocking) a window. You would not use this for any 
        objects that would be tall, for example a wardrobe or a fridge.
        
        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
    """ 

    x, y, _ = get_position(positions, room, object_index)
    windows = room.find_all('window')
    min_dist = np.inf
    for window in windows: 
        distance = (window.position[0] - x)**2 + (window.position[1] - y)**2 
        if distance < min_dist: 
            min_dist = distance

    return min_dist

@safe_execution
def ind_facing_into_room(positions, room, object_index):
    """ ind_facing_into_room is a function that ensures and object faces into the center of the room. 
        E.g. an armchair might face into the room.

        Args: 
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        
    """
    val = 0
    x, y, theta = get_position(positions, room, object_index)
    bl = BL(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)
    tl = TL(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)

    direction1 = np.array([room.width/2 - x, room.length/2 - y])
    direction1 /= np.linalg.norm(direction1)

    direction2 = np.array([bl[0] - tl[0], bl[1] - tl[1]])
    direction2 /= np.linalg.norm(direction2)

    angle = np.arccos(np.dot(direction1, direction2))
    val += max(0.0, angle - np.pi/4)**2

    return val 

@safe_execution
def ind_not_against_wall(positions, room, object_index, min_dist = 0.2):

    """ ind_not_against_wall is a function that ensures and object is not against a wall. 
        For example, you might not want a rug against a wall, or a dining table. 

        Args:
        positions: list of floats, x, y, theta values for all objects in the room
        room: rectangular Room object
        object_index: int, index of the object in the room's object list
        side: string, one of 'top' or 'back', 'bottom' or 'front', 'left', 'right', defines which side of the object to check e.g back of bed   
        min_dist: float, minimum distance the object should be from the wall 
    """
    val = 0.0
    x, y, theta = get_position(positions, room, object_index)
    cs = np.array(corners(x, y, theta, room.moving_objects[object_index].width, room.moving_objects[object_index].length)) # TL, TR, BR, BL
    distances =  np.zeros((4, 4)) # each row a different corner, each column a different wall 

    for i in range(4):
        distances[i, :] = np.array([(cs[i][1] - room.length)**2, (cs[i][0] - room.width)**2, cs[i][1]**2, cs[i][0]**2])

    distances = np.sqrt(distances.flatten())
    distances = np.where(distances > min_dist, 0.0, (distances - min_dist)**2)
    val = 10*sum(distances)
    return val







                
















