import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.spatial import Voronoi, voronoi_plot_2d
import scipy as sp
import sys
from shapely.geometry import Polygon, Point
from Individual import get_position
import matplotlib.colors as mcolors
import matplotlib.lines as lines

def TR(x, y, theta, w, l):
    return (x + w/2 * np.cos(theta) + l/2 * np.sin(theta), y + w/2 * np.sin(theta) - l/2 * np.cos(theta))

def TL(x, y, theta, w, l):
    return (x - w/2 * np.cos(theta) + l/2 * np.sin(theta), y - w/2 * np.sin(theta) - l/2 * np.cos(theta))

def BR(x, y, theta, w, l):
    return (x + w/2 * np.cos(theta) - l/2 * np.sin(theta), y + w/2 * np.sin(theta) + l/2 * np.cos(theta))

def BL(x, y, theta, w, l):
    return (x - w/2 * np.cos(theta) - l/2 * np.sin(theta), y - w/2 * np.sin(theta) + l/2 * np.cos(theta))

def corners(x, y, theta, w, l): # TL, TR, BR, BL
    return [TL(x, y, theta, w, l), TR(x, y, theta, w, l), BR(x, y, theta, w, l), BL(x, y, theta, w, l)]


def cost(positions, room, points, weights): 

    intersection = 0
    rug_names = ['rug', 'mat', 'Rug', 'Mat', 'RUG', 'MAT', 'carpet', 'Carpet']
    for i in range(len(room.moving_objects)): 
        rug = False
        for name in rug_names: 
            if name in room.moving_objects[i].name:
                rug = True
                break
        if rug: 
            continue 
        x, y, theta = get_position(positions, room, i)
        cs = corners(x, y, theta, room.moving_objects[i].width, room.moving_objects[i].length)
        poly = Polygon(cs)
        for j in range(points.shape[0]): 
            if poly.contains(Point(points[j, :])): 
                intersection += weights[j]*poly.exterior.distance(Point(points[j, :]))**2

    return intersection

class Object:

    def __init__(self, name, width, length, region = None, index = None, position = (0, 0, 0), tertiary = False):
        """ Initialization of an object in a scene. 
            Inputs: 
            name: str, name of the object all lowercase
            width: float, width of the object
            length: float, length of the object
            index : int, index of the object in the room's object list (optional, only used for moving_objects)
            position: tuple (x, y, theta), where x, y are the coordinates of the center of the 
                      object and theta is the orientation of the object in radians.
            tertiary: string, one of "wall", "floor", "table", "ceiling" (optional, only used for tertiary_objects) which determines the type of teriary object
        """

        self.position = position
        self.name = name
        self.width = width 
        self.length = length
        self.index = index
        if region: 
            self.region = region
        else: 
            self.region = None
        
        if tertiary: 
            self.tertiary = tertiary 

    def TR(self):
        x, y, theta = self.position
        return TR(x, y, theta, self.width, self.length)

    def TL(self):  
        x, y, theta = self.position
        return TL(x, y, theta, self.width, self.length)

    def BR(self):
        x, y, theta = self.position
        return BR(x, y, theta, self.width, self.length)

    def BL(self):
        x, y, theta = self.position
        return BL(x, y, theta, self.width, self.length)
    
    def corners(self):

        if self.name != 'door' and self.name != 'window':
            return [self.TL(), self.TR(), self.BR(), self.BL()]
        elif self.name == 'door': 
            if self.position[2] == 0: 
                BL = [self.position[0] - 0.2, self.position[1] - 0.2]
                BR = [self.position[0] + self.width + 0.2, self.position[1] - 0.2]
                TR = [self.position[0] + self.width + 0.2, self.position[1] + self.width + 0.2]
                TL = [self.position[0] - 0.2, self.position[1] + self.width + 0.2]    
            elif self.position[2] == np.pi/2:
                BL = [self.position[0] + 0.2, self.position[1] - 0.2]
                BR = [self.position[0] + 0.2, self.position[1] + self.width + 0.2]
                TR = [self.position[0] - self.width - 0.2, self.position[1] + self.width + 0.2]
                TL = [self.position[0] - self.width - 0.2, self.position[1] - 0.2]
            elif self.position[2] == np.pi:
                BL = [self.position[0] + 0.2, self.position[1]]
                BR = [self.position[0] - self.width - 0.2, self.position[1]]
                TR = [self.position[0] - self.width - 0.2, self.position[1] - self.width - 0.2]
                TL = [self.position[0] + 0.2, self.position[1] - self.width - 0.2]
            elif self.position[2] == 3*np.pi/2:
                BL = [self.position[0] - 0.2, self.position[1] + 0.2]
                BR = [self.position[0] - 0.2, self.position[1] - self.width - 0.2]
                TR = [self.position[0] + self.width + 0.2, self.position[1] - self.width - 0.2]
                TL = [self.position[0] + self.width + 0.2, self.position[1] + 0.2]

            return [TL, TR, BR, BL]
        else: 
            return corners(self.position[0], self.position[1], self.position[2], self.width + 0.1, 1)

    
    def back_corners(self):
        return [self.TL(), self.TR()]
    
class Region: 
    def __init__(self, name, x, y, index):

        """ Initialization of a region in a scene. 
            Inputs: 
            name: str, name of the object all lowercase
            x: float, x-coordinate of the center of the region
            y: float, y-coordinate of the center of the region
        """

        self.name = name
        self.x = x
        self.y = y
        self.index = index

class Room: 

    def __init__(self, width, length, fixed_objects = []):

        self.width = width
        self.length = length
        self.fixed_objects = fixed_objects
        self.moving_objects = []
        self.fm_indices = []
        self.center = (width/2, length/2)
        self.regions = []
        self.tertiary_objects = []

    def find_region_index(self, region_name):

        """ Finds a region in the room by name.
            Inputs:
            region_name: str, name of the region
            Outputs:
            region: Region, the region object
        """

        for region in self.regions:
            if region_name in region.name or region.name in region_name:
                return region.index

        print("No region with this name is in the room.")    
        return None
    
    def find(self, name):
        for obj in self.fixed_objects + self.moving_objects:
            if obj.name == name:
                return obj
        return None
    
    def find_all(self, name):
        objects = []
        for obj in self.fixed_objects + self.moving_objects:
            if obj.name == name:
                objects.append(obj)
        return objects
    
    def count(self, name):
        counter = 0
        for obj in self.fixed_objects + self.moving_objects:
            if obj.name == name:
                counter += 1
        return counter
    
    
    def draw(self, draw_regions = False, buffers = False, ax = None, level = 2, arrows = False, key = False):

        """ Draws the room with all the objects in it."""
        show = True
        if ax is None and not key: 
            show = False
            fig, ax = plt.subplots(figsize = (10, 10))
            ax.set_xlim(-1, self.width + 1)
            ax.set_ylim(-1, self.length + 1)
            ax.set_aspect('equal')
            ax.grid(linestyle = '--')
        
        elif ax is None and key: 
            show = False
            fig, ax = plt.subplots(figsize = (10, 10))
            ax.set_xlim(-2, self.width + 1)
            ax.set_ylim(-1, self.length + 1)
            ax.set_aspect('equal')
            ax.grid(linestyle = '--')
        
        def lighten_color(color, amount=0.5):
            # Convert color to RGB
            try:
                c = mcolors.cnames[color]
            except KeyError:
                c = color
            c = mcolors.to_rgb(c)
    
            # Blend with white
            return mcolors.to_rgba([(1.0 - amount) * x + amount for x in c])

        # Draw the room
        rect = patches.Rectangle((0, 0), self.width, self.length, linewidth=2, edgecolor='black', facecolor='none', label='_nolegend_')
        ax.add_patch(rect)
        
        if draw_regions:
            eps = sys.float_info.epsilon

            def in_box(towers, bounding_box):
                return np.logical_and(np.logical_and(bounding_box[0] <= towers[:, 0],
                                            towers[:, 0] <= bounding_box[1]),
                            np.logical_and(bounding_box[2] <= towers[:, 1],
                                            towers[:, 1] <= bounding_box[3]))
            def voronoi(towers, bounding_box):
                # Select towers inside the bounding box
                i = in_box(towers, bounding_box)
                # Mirror points
                points_center = towers[i, :]
                points_left = np.copy(points_center)
                points_left[:, 0] = bounding_box[0] - (points_left[:, 0] - bounding_box[0])
                points_right = np.copy(points_center)
                points_right[:, 0] = bounding_box[1] + (bounding_box[1] - points_right[:, 0])
                points_down = np.copy(points_center)
                points_down[:, 1] = bounding_box[2] - (points_down[:, 1] - bounding_box[2])
                points_up = np.copy(points_center)
                points_up[:, 1] = bounding_box[3] + (bounding_box[3] - points_up[:, 1])
                points = np.append(points_center,
                                np.append(np.append(points_left,
                                                    points_right,
                                                    axis=0),
                                            np.append(points_down,
                                                    points_up,
                                                    axis=0),
                                            axis=0),
                                axis=0)
                # Compute Voronoi
                vor = sp.spatial.Voronoi(points)
                # Filter regions
                regions = []
                for region in vor.regions:
                    flag = True
                    for index in region:
                        if index == -1:
                            flag = False
                            break
                        else:
                            x = vor.vertices[index, 0]
                            y = vor.vertices[index, 1]
                            if not(bounding_box[0] - eps <= x and x <= bounding_box[1] + eps and
                                bounding_box[2] - eps <= y and y <= bounding_box[3] + eps):
                                flag = False
                                break
                    if region != [] and flag:
                        regions.append(region)
                vor.filtered_points = points_center
                vor.filtered_regions = regions
                return vor
            
            # Collect points for Voronoi diagram
            points = np.array([[region.x, region.y] for region in self.regions])
            colors = plt.cm.viridis(np.linspace(0, 1, len(points)))

            # Plot the points
            for i, point in enumerate(points):
                ax.plot(point[0], point[1], 'o', markersize=10, color=colors[i], label= self.regions[i].name)
                #ax.text(point[0], point[1], self.regions[i].name, fontsize=10)

            # Extracting handles and labels
            handles, labels = ax.get_legend_handles_labels()

            # Creating the legend
            ax.legend(handles, labels, title="Regions")

            # Plot Voronoi diagram
            vor = voronoi(points, np.array([0, self.width, 0, self.length]))
            for point_index, region_index in enumerate(vor.point_region):
                if point_index >= len(self.regions):
                    break
                region = vor.regions[region_index]
                if len(region) > 0:
                    polygon = [vor.vertices[i] for i in region]
                    for vert in polygon:
                        if vert[0] < 0:
                            vert[0] = 0
                        if vert[0] > self.width:
                            vert[0] = self.width
                        if vert[1] < 0:
                            vert[1] = 0
                        if vert[1] > self.length:
                            vert[1] = self.length
                    ax.fill(*zip(*polygon), color=colors[point_index], alpha=0.2)
        
        if buffers: 
            for obj in self.fixed_objects: 
                if obj.name == 'door' or obj.name == 'window': 
                    cs = np.array(obj.corners()).reshape(4, 2)
                    bottom_left = [np.min(cs[:, 0]), np.min(cs[:, 1])]
                    top_right = [np.max(cs[:, 0]), np.max(cs[:, 1])]
                    w, l = top_right[0] - bottom_left[0], top_right[1] - bottom_left[1]
                    rect = patches.Rectangle(bottom_left, w, l, linewidth=2, edgecolor='#2fb8c4', facecolor='#2fb8c4', alpha = 0.3)
                    ax.add_patch(rect)

        # Draw the objects
        if self.moving_objects:
            for obj in self.moving_objects:
                rectangle = patches.Rectangle(obj.position[:2]  - np.array([obj.width/2, obj.length/2]), obj.width, obj.length, linewidth=2, edgecolor='none', facecolor='none', angle=np.rad2deg(obj.position[2]), rotation_point='center')
                ax.add_patch(rectangle)
                line, = plt.plot([], [], label=obj.name)  # Create an invisible line

                if level == 0 or level == 2: 
                    rectangle.set_edgecolor(line.get_color())  # Use the line's color for the rectangle
                else: 
                    rectangle.set_edgecolor(lighten_color(line.get_color(), 0.5))

                cs = np.array(obj.corners()) # TL, TR, BR, BL
                front_mid = 3*((cs[2, :] + cs[3, :]) / 2 - obj.position[:2])/4
                if (level == 2 or level == 0) and not key:
                    ax.text(obj.position[0] - 0.5*front_mid[0], obj.position[1]-0.5*front_mid[1], obj.name, fontsize=12)
                elif (level == 2 or level == 0) and key:
                    ax.text(obj.position[0] - 0.5*front_mid[0], obj.position[1]-0.5*front_mid[1], str(obj.index), fontsize=12) 

                if (arrows and level == 2) or (arrows and level == 0): 
                    ax.arrow(obj.position[0]-0.5*front_mid[0], obj.position[1]- 0.5*front_mid[1], front_mid[0], front_mid[1], head_width=0.1, head_length=0.1, fc=line.get_color(), ec=line.get_color())
                
                if not arrows: 
                    cs = obj.back_corners()
                    for corner in cs:
                        ax.plot(corner[0], corner[1], color = line.get_color(), marker = 'o')
            if key and level == 0: 
                handles = []
                for i in range(len(self.moving_objects)):
                    custom_text = lines.Line2D([], [], color='none', marker='None', linestyle='None', label= str(i) + ": " + self.moving_objects[i].name)
                    handles += [custom_text]
                # Add custom handles to the legend
                ax.legend(handles = handles, loc='upper left', title="Objects")


        # Draw the objects
        if self.tertiary_objects:
            for obj in self.tertiary_objects:
                rectangle = patches.Rectangle(obj.position[:2]  - np.array([obj.width/2, obj.length/2]), obj.width, obj.length, linewidth=2, edgecolor='none', facecolor='none', angle=np.rad2deg(obj.position[2]), rotation_point='center')
                ax.add_patch(rectangle)
                cs = np.array(obj.corners()) # TL, TR, BR, BL
                front_mid = 3*((cs[2, :] + cs[3, :]) / 2 - obj.position[:2])/4
                left_mid = 3*((cs[3, :] + cs[0, :]) / 2 - obj.position[:2])/4
                if level == 2 or level == 1: 
                    rectangle.set_edgecolor('b')  # Use the line's color for the rectangle
                else:
                    rectangle.set_edgecolor(lighten_color('b', 0.8))
                if (level == 2 or level == 1) and not key:
                    ax.text(obj.position[0] - 0.5*front_mid[0], obj.position[1]-0.5*front_mid[1], obj.name, fontsize=12)
                elif (level == 2 or level == 1) and key: 
                    ax.text(obj.position[0] + 0.5*left_mid[0], obj.position[1]+0.5*left_mid[1], str(obj.index + len(self.moving_objects)), fontsize=12)
                if (arrows and level == 2) or (arrows and level == 1): 
                    ax.arrow(obj.position[0]-0.5*front_mid[0], obj.position[1]- 0.5*front_mid[1], front_mid[0], front_mid[1], head_width=0.1, head_length=0.1, fc='b', ec='b')
                if not arrows and (level == 2 or level == 1): 
                    cs = obj.back_corners()
                    for corner in cs:
                        ax.plot(corner[0], corner[1], color = 'b', marker = 'o')

                if key and (level == 1): 
                    handles = []
                    for i in range(len(self.tertiary_objects)):
                        custom_text = lines.Line2D([], [], color='b', marker='None', linestyle='None', label= str(i + len(self.moving_objects)) + ": " + self.tertiary_objects[i].name)
                        handles += [custom_text]
                    # Add custom handles to the legend
                    ax.legend(handles = handles, loc='upper left', title="Objects")
        
        if key and level == 2: 
            handles = []
            for i in range(len(self.moving_objects)):
                custom_text = lines.Line2D([], [], color='none', marker='None', linestyle='None', label= str(i) + ": " + self.moving_objects[i].name)
                handles += [custom_text]
            for i in range(len(self.tertiary_objects)): 
                custom_text = lines.Line2D([], [], color='b', marker='None', linestyle='None', label= str(i + len(self.moving_objects)) + ": " + self.tertiary_objects[i].name)
                handles += [custom_text]
            # Add custom handles to the legend
            ax.legend(handles = handles, loc='upper left', title="Objects")

        if self.fixed_objects:
            for obj in self.fixed_objects:
                if obj.name == 'window':
                    rect = patches.Rectangle(obj.position[:2] - np.array([obj.width/2, obj.length/2]), obj.width, obj.length, linewidth=5, edgecolor='r', facecolor='none', angle=np.rad2deg(obj.position[2]), rotation_point='center')
                    ax.add_patch(rect)
                elif obj.name == 'door':
                    wedge = patches.Wedge(center=obj.position[:2], r=obj.width, 
                                            theta1=np.rad2deg(obj.position[2]), theta2=np.rad2deg(obj.position[2]) + 90, linewidth=3, edgecolor='r', facecolor='none')
                    ax.add_patch(wedge)

                elif obj.name == 'socket' or obj.name == 'plug' or obj.name == 'electrical plug':
                    x, y = obj.position[:2]
                    ax.plot([x - 0.05, x + 0.05], [y - 0.05, y + 0.05], color='red', linewidth=2)
                    ax.plot([x - 0.05, x + 0.05], [y + 0.05, y - 0.05], color='red', linewidth=2)

        if show: 
            plt.show()
        
        return