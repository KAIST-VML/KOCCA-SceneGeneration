from Setup_Functions import *
from Class_Structures import *
from Individual import * 
from InterObject import * 
from Global import * 
import openai
from openai.types import Completion, CompletionChoice, CompletionUsage
import os
import requests
from dotenv import load_dotenv
from scipy.optimize import minimize, Bounds, NonlinearConstraint
from functools import partial 
from scipy.spatial import Voronoi, voronoi_plot_2d, ConvexHull
from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt
from matplotlib.path import Path
from shapely import Polygon, Point


def draw_medial_axis(room, points, weights): 

    fig, ax = plt.subplots(figsize = (10, 10))
    ax.set_xlim(-1, room.width + 1)
    ax.set_ylim(-1, room.length + 1)
    ax.set_aspect('equal')
    ax.grid(linestyle = '--')
    ax.scatter(points[:, 0], points[:, 1], c = weights)
    room.draw(ax = ax)
    return 


def medial_axis(room, draw = False):

    final_points = []

    # Draw the room
    rect = patches.Rectangle((0, 0), room.width, room.length, linewidth=2, edgecolor='black', facecolor='none', label='_nolegend_')

    points = []
    cs = rect.get_corners()
    num_points = int(np.ceil(2 * (5 * room.width + 5 * room.length)))
    for i in range(num_points):
        points.append(cs[0] + (cs[1] - cs[0]) * i / num_points)  # Bottom side
        points.append(cs[1] + (cs[2] - cs[1]) * i / num_points)  # Right side
        points.append(cs[2] + (cs[3] - cs[2]) * i / num_points)  # Top side
        points.append(cs[3] + (cs[0] - cs[3]) * i / num_points)  # Left side
    final_points.append(points)

    rug_names = ['rug', 'mat', 'Rug', 'Mat', 'RUG', 'MAT', 'carpet', 'Carpet']
    # Draw the objects
    if room.moving_objects:
        for obj in room.moving_objects:
            rug = False
            for name in rug_names: 
                if name in obj.name:
                    rug = True
                    break
            if rug: 
                continue 
            cs_tup = obj.corners()
            cs = [np.array(i) for i in cs_tup]
            points = []
            num_points = int(np.ceil(2 * (5 * obj.width + 5 * obj.length)))
            for i in range(num_points):
                points.append(cs[0] + (cs[1] - cs[0]) * i / num_points)  # Bottom side
                points.append(cs[1] + (cs[2] - cs[1]) * i / num_points)  # Right side
                points.append(cs[2] + (cs[3] - cs[2]) * i / num_points)  # Top side
                points.append(cs[3] + (cs[0] - cs[3]) * i / num_points)  # Left side
            
            points = np.array(points)
            final_points.append(points)

    if room.fixed_objects:
        for obj in room.fixed_objects:
            if obj.name == 'door':

                wedge = patches.Wedge(center=obj.position[:2], r=obj.width, 
                                        theta1=np.rad2deg(obj.position[2]), theta2=np.rad2deg(obj.position[2]) + 90, linewidth=3, edgecolor='r', facecolor='none')
                
                points = wedge.get_path().vertices
                if obj.position[2] == 0:
                    points = [i for i in points if np.isclose(i[1], 0)]
                    points = np.unique(points, axis = 0)
                    min_x, max_x = sorted([i[0] for i in points])
                    crit = lambda x: np.isclose(x[1], 0) and (min_x < x[0]) and (x[0] < max_x)
                    crit2 = lambda x: np.isclose(x[1], 0)
                elif obj.position[2] == np.pi/2:
                    points = [i for i in points if np.isclose(i[0], room.width)]
                    points = np.unique(points, axis = 0)
                    min_y, max_y = sorted([i[1] for i in points])
                    crit = lambda x: np.isclose(x[0], room.width) and( min_y < x[1]) and (x[1] < max_y ) 
                    crit2 = lambda x: np.isclose(x[0], room.width) 
                elif obj.position[2] == np.pi:
                    points = [i for i in points if np.isclose(i[1], room.length)]
                    points = np.unique(points, axis = 0)
                    min_x, max_x = sorted([i[0] for i in points])
                    crit = lambda x: np.isclose(x[1], room.length) and (min_x < x[0]) and (x[0] < max_x)
                    crit2 = lambda x: np.isclose(x[1], room.length)
                elif obj.position[2] == 3*np.pi/2:
                    points = [i for i in points if np.isclose(i[0], 0)]
                    points = np.unique(points, axis = 0)
                    min_y, max_y = sorted([i[1] for i in points])
                    crit = lambda x: np.isclose(x[0], 0) and (min_y < x[1]) and (x[1] < max_y ) 
                    crit2 = lambda x: np.isclose(x[0], 0)
                final_points.append(points)

    final_points = np.concatenate(final_points)

    door_points = []
    for point in final_points:
        if crit(point):
            door_points += [point]
            final_points = np.delete(final_points, np.where(np.all(final_points == point, axis = 1)), axis = 0)
    vor = Voronoi(final_points)

    new_edges = []
    new_ridge_points = []
    max_distances = []

    ## find the door ridge 
    ridge_points = vor.ridge_points
    for i in range(len(ridge_points)): 
        edge = ridge_points[i]
        p1, p2 = vor.points[edge]
        if crit2(p1) and crit2(p2) and np.linalg.norm(p1 - p2) > 0.4:
            new_edges.append(vor.ridge_vertices[i])
            new_ridge_points.append(vor.ridge_points[i])

    for i in range(len(vor.ridge_vertices)): 
        edge = vor.ridge_vertices[i]
        remove = False
        p1 = vor.vertices[edge[0]]
        p2 = vor.vertices[edge[1]]
        if (edge[0] == -1 or edge[1] == -1):
            continue
        if p1[0] < 0 or p2[0] < 0 or p1[1] < 0 or p2[1] < 0:
            continue
        if p1[0] > room.width or p1[1] > room.length or p2[0] > room.width or p2[1] > room.length:
            continue
        for obj in room.moving_objects:
            rug = False
            for name in rug_names: 
                if name in obj.name:
                    rug = True
                    break
            if rug:
                continue
            poly = Polygon(obj.corners())
            if any([poly.contains(Point(vor.vertices[v])) for v in edge]):
                remove = True
                break

        if remove: 
            continue
        

        regions = [j for j in range(len(vor.regions)) if edge[0] in vor.regions[j] and edge[1] in vor.regions[j]]
        region_vs = [[], []]
        for j in range(2): 
            region_vs[j] = [v for v in vor.regions[regions[j]] if v != edge[0] and v != edge[1]]

        dists = []
        for j in range(len(region_vs[0])): 
            for k in range(len(region_vs[1])):
                dists.append(np.linalg.norm(vor.vertices[region_vs[0][j]] - vor.vertices[region_vs[1][k]]))
        if np.any(np.array(dists) < 1e-8): 
            continue 
        else: 
            max_distances.append(np.min(dists))
            new_edges.append(edge)  
            new_ridge_points.append(vor.ridge_points[i])  

    new_vor = Voronoi(final_points)
    new_vor.vertices = vor.vertices
    new_vor.regions = vor.regions
    new_vor.ridge_vertices = new_edges
    new_vor.ridge_points = new_ridge_points

    if draw:
        fig, ax = plt.subplots(figsize = (10, 10))
        voronoi_plot_2d(new_vor, ax=ax, show_points=True, show_vertices=False, line_colors='gray')

    return new_vor, max_distances


def find_corners(points): 

    c_inds =[]
    neighbour_inds = []
    for i in range(points.shape[0]): 
        dists = np.linalg.norm(points - points[i], axis = 1)
        inds = [j for j in np.where(dists < 0.15)[0] if j != i]
        neighbours = points[inds]
        ds = []
        for n in neighbours:
            direction = n - points[i]
            if np.isnan(direction[0]/np.linalg.norm(direction)) or np.isnan(direction[1]/np.linalg.norm(direction)):
                continue
            ds += [direction / np.linalg.norm(direction)]
        for j in range(len(ds) - 1): 
            angles = np.arccos(np.clip(np.dot(ds[j+1:], ds[j]), -1, 1))
            if (np.any(np.isclose(angles, np.pi/2)) or np.any(np.isclose(angles, -np.pi/2))):
                neighbour_inds += [inds]
                c_inds.append(i)
                break
    
    copy_inds = c_inds.copy()
    for ind in range(len(copy_inds)): 
        num = 0
        new_ind = copy_inds[ind]
        neighbours = points[neighbour_inds[ind]]
        diff = (neighbours - points[new_ind])/np.linalg.norm(points[new_ind] - neighbours, axis = 1)[:, None]
        for i in range(diff.shape[0]): 
            new_diff = np.dot(np.concatenate([diff[:i], diff[i + 1:]]), diff[i])
            if not np.any(new_diff < -0.9):
                num += 1
        if num == len(neighbours): 
            c_inds.remove(new_ind)
    
    corner1 = np.argmin(points[:, 0] + points[:, 1])
    corner2 = np.argmax(points[:, 0] + points[:, 1])
    corner3 = np.argmax(points[:, 0] - points[:, 1])
    corner4 = np.argmin(points[:, 0] - points[:, 1])
    if corner1 not in c_inds: 
        c_inds.append(corner1)
    if corner2 not in c_inds:
        c_inds.append(corner2)
    if corner3 not in c_inds:
        c_inds.append(corner3)
    if corner4 not in c_inds:
        c_inds.append(corner4)

    return c_inds


def path_points(room): 

    vor, _ = medial_axis(room)
    vor_points = vor.points
    all_points = []
    weights = []

    c_inds = find_corners(vor_points)
    corner_points = vor_points[c_inds]

    for i in range(len(vor.ridge_vertices)): 
        mid_points = []
        edge = vor.ridge_vertices[i]
        # fill in any gaps
        if np.linalg.norm(vor.vertices[edge[0]] - vor.vertices[edge[1]]) > 0.15: 
            points = np.linspace(vor.vertices[edge[0]], vor.vertices[edge[1]], 25)
            verts = [i.tolist() for i in vor.vertices]
            vor.vertices = np.array(verts + points.tolist())
            mid_points = points

        min_index = np.argmin([vor.vertices[edge[0]][0], vor.vertices[edge[1]][0]])
        other_index = 1 - min_index
        direction = vor.vertices[edge[other_index]] - vor.vertices[edge[min_index]]
        if abs(np.linalg.norm(direction)) < 1e-6: 
            direction = direction / 1e-6
        else:
            direction = direction / np.linalg.norm(direction)
        perpendicular_direction = np.array([direction[1], - direction[0]])
        perpendicular_direction = perpendicular_direction / np.linalg.norm(perpendicular_direction)

        NUM = 7
        ws = np.hstack((np.linspace(1, NUM//2, NUM//2),np.linspace(NUM//2 + 1, 1, NUM//2 + 1)))
        
        if len(mid_points) > 0: 
            for point in mid_points: 
                mid_point = point
                dists = np.linalg.norm(corner_points - mid_point, axis = 1)
                x = np.linspace(mid_point[0] - 0.3 * perpendicular_direction[0], mid_point[0] + 0.3 * perpendicular_direction[0], NUM)
                y = np.linspace(mid_point[1] - 0.3 * perpendicular_direction[1], mid_point[1] + 0.3 * perpendicular_direction[1], NUM)
                for i in range(NUM): 
                    all_points.append([x[i], y[i]])

        else: 
            
            mid_point = (vor.vertices[edge[0]] + vor.vertices[edge[1]]) / 2
            dists = np.linalg.norm(corner_points - mid_point, axis = 1)
            if np.any(dists < 0.3): 
                continue

            x = np.linspace(mid_point[0] - 0.3 * perpendicular_direction[0], mid_point[0] + 0.3 * perpendicular_direction[0], NUM)
            y = np.linspace(mid_point[1] - 0.3 * perpendicular_direction[1], mid_point[1] + 0.3 * perpendicular_direction[1], NUM)
            for xi, yi in zip(x, y):
                all_points.append([xi, yi])
        
            
    all_points = np.array(all_points)
    weights = ws.tolist() * (all_points.shape[0]//NUM)

    return all_points, weights



def pathway_cost(room): 

    points, weights = path_points(room)
    draw_medial_axis(room, points, weights)
    intersection = 0
    for i in range(len(room.moving_objects)): 

        obj_i = room.moving_objects[i]
        x, y, theta = obj_i.position
        cs = corners(x, y, theta, obj_i.width, obj_i.length)
        poly = Polygon(cs)
        for j in range(points.shape[0]): 
            if poly.contains(Point(points[j, :])): 
                intersection += weights[j]*poly.exterior.distance(Point(points[j, :]))**2

    return intersection


def OOB(room): 
    
    val = 0
    num_objects = len(room.moving_objects) + len(room.tertiary_objects)
    room_poly = Polygon([(0, 0), (0, room.length) , (room.width, room.length), (room.width, 0)])
    x, y = room_poly.exterior.xy
    for i in range(num_objects): 
        if i < len(room.moving_objects):
            obj_i = room.moving_objects[i]
        else: 
            obj_i = room.tertiary_objects[i - num_objects]
        obj_poly = Polygon(obj_i.corners())
        if obj_poly.intersection(room_poly).area < obj_poly.area: 
            val += obj_poly.area - obj_poly.intersection(room_poly).area
    return 100 *  val / (room.width * room.length)

def OOR(room): 

    windows = room.find_all('window')
    window_polygons = []
    for window in windows:
        window_corners = window.corners()
        window_poly = Polygon(window_corners)
        window_polygons += [window_poly]

    doors = room.find_all('door')
    door_polygons = [] 
    for door in doors: 
        door_corners = door.corners()
        door_poly = Polygon(door_corners)
        door_polygons += [door_poly]
    
    val = 0
    # Primary + Secondary 
    num_objs = len(room.moving_objects)
    for i in range(num_objs): 
        obj_i = room.moving_objects[i]
        poly_i = Polygon(obj_i.corners())

        for door in door_polygons: ## all objects must not intersect doors
            intersection = poly_i.intersection(door)
            if intersection.area > 0:
                val += intersection.area
                
        for j in range(i + 1, num_objs): 
            obj_j = room.moving_objects[j]
            poly_j = Polygon(obj_j.corners())
            if poly_j.intersection(poly_i).area > 0: 
                val += poly_j.intersection(poly_i).area



    #Tertiary
    num_tertiary_objs = len(room.tertiary_objects)
    for i in range(num_tertiary_objs): 
        obj_i = room.tertiary_objects[i]
        poly_i = Polygon(obj_i.corners())
        typ_i = obj_i.tertiary

        for door in door_polygons: ## all objects must not intersect doors
            intersection = poly_i.intersection(door)
            if intersection.area > 0:
                val += intersection.area

        if typ_i == 'wall': # wall objects must not intersect windows 
            for window in window_polygons:
                intersection = poly_i.intersection(window)
                if intersection.area > 0:
                    val += intersection.area

        for j in range(i + 1, num_tertiary_objs): 
            obj_j = room.tertiary_objects[j]
            if not typ_i == obj_j.tertiary:
                continue
            else:
                poly_j = Polygon(obj_j.corners())
                intersection = poly_j.intersection(poly_i)
                if intersection.area > 0: 
                    val += intersection.area

    

    return 100 * val / (room.width * room.length)
