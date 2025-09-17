# composition.py - Standardized version
import bpy
import os
import sys
import numpy as np
import re
from mathutils import Vector, Euler
import math

class SceneLayoutManager:
    def __init__(self, root_path=None):
        """
        Initialize the scene layout manager with standardized folder structure
        
        Expected folder structure:
        root_path/
        ├── layout.txt
        ├── background_color.txt
        ├── objects/
        │   ├── bed/
        │   │   ├── normalized_model.obj
        │   │   ├── model.mtl
        │   │   └── texture.png
        │   ├── wardrobe/
        │   │   └── ...
        │   └── desk/
        │       └── ...
        └── output/
            └── scene.blend (generated)
        
        Args:
            root_path: Root directory path. If None, uses script directory.
        """
        # Determine root path
        if root_path is None:
            # Use the directory where this script is located
            self.root_path = os.path.dirname(os.path.abspath(__file__))
        else:
            self.root_path = os.path.abspath(root_path)
            
        print(f"Using root path: {self.root_path}")
        
        # Set up standardized paths
        self.objects_path = os.path.join(self.root_path, "objects")
        self.layout_file_path = os.path.join(self.root_path, "layout.txt")
        self.background_color_path = os.path.join(self.root_path, "background_color.txt")
        self.output_path = os.path.join(self.root_path, "output")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        # Validate required files
        self.validate_structure()
        
        # Parse configuration files
        self.layout_data = self.parse_layout_file()
        self.background_colors = self.parse_background_colors()
        
    def validate_structure(self):
        """Validate that required files and folders exist"""
        required_paths = [
            (self.layout_file_path, "layout.txt"),
            (self.objects_path, "objects/ folder")
        ]
        
        missing = []
        for path, name in required_paths:
            if not os.path.exists(path):
                missing.append(name)
                
        if missing:
            print(f"❌ Missing required files/folders: {', '.join(missing)}")
            print(f"Expected structure in: {self.root_path}")
            print("Required:")
            print("  - layout.txt")
            print("  - objects/ folder")
            print("Optional:")
            print("  - background_color.txt")
            sys.exit(1)
        else:
            print("✅ Folder structure validated")
    
    def parse_layout_file(self):
        """Parse the layout text file and extract room and object information"""
        layout_data = {
            'room_width': None,
            'room_length': None,
            'objects': {},
            'style': None,
            'prompt': None
        }
        
        print(f"📖 Reading layout file: {self.layout_file_path}")
        
        with open(self.layout_file_path, 'r') as f:
            content = f.read()
            
        # Extract room dimensions
        room_width_match = re.search(r'room_width:\s*(\d+(?:\.\d+)?)', content)
        room_length_match = re.search(r'room_length:\s*(\d+(?:\.\d+)?)', content)
        
        if room_width_match:
            layout_data['room_width'] = float(room_width_match.group(1))
        if room_length_match:
            layout_data['room_length'] = float(room_length_match.group(1))
            
        # Extract prompt
        prompt_match = re.search(r'prompt:\s*(.+)', content)
        if prompt_match:
            layout_data['prompt'] = prompt_match.group(1)
            
        # Extract objects
        object_pattern = r'(\w+):\s*\{\'position\':\s*\(([\d\w\.\(\), -]+)\),\s*\'width\':\s*([\d\.]+),\s*\'length\':\s*([\d\.]+)\}'
        
        for match in re.finditer(object_pattern, content):
            obj_name = match.group(1)
            
            # Parse position tuple
            position_str = match.group(2)
            pos_numbers = re.findall(r'np\.float64\(([\d\.-]+)\)|(\d+(?:\.\d+)?)', position_str)
            position = []
            for num_match in pos_numbers:
                if num_match[0]:  # np.float64 format
                    position.append(float(num_match[0]))
                elif num_match[1]:  # regular float format
                    position.append(float(num_match[1]))
            
            if len(position) >= 3:
                layout_data['objects'][obj_name] = {
                    'position': (position[0], position[1], position[2]),
                    'width': float(match.group(3)),
                    'length': float(match.group(4))
                }
                
        # Extract style description
        style_match = re.search(r'style:\s*(.+)', content, re.DOTALL)
        if style_match:
            layout_data['style'] = style_match.group(1).strip()
            
        print(f"📊 Parsed {len(layout_data['objects'])} objects from layout")
        return layout_data
    
    def parse_background_colors(self):
        """Parse background color file and extract floor and wall colors"""
        colors = {
            'floor_color': (0.8, 0.6, 0.4, 1.0),  # Default light oak
            'wall_color': (0.6, 0.7, 0.6, 1.0)    # Default sage green
        }
        
        if not os.path.exists(self.background_color_path):
            print(f"⚠️  Background color file not found: {self.background_color_path}")
            print("Using default colors")
            return colors
            
        try:
            with open(self.background_color_path, 'r') as f:
                content = f.read()
                
            # Extract floor color
            floor_match = re.search(r'floor color\s*:\s*\(([\d\.\s,]+)\)', content)
            if floor_match:
                color_values = [float(x.strip()) for x in floor_match.group(1).split(',')]
                if len(color_values) >= 3:
                    colors['floor_color'] = tuple(color_values[:4])  # Take up to 4 values (RGBA)
                    
            # Extract wall color
            wall_match = re.search(r'wall color\s*:\s*\(([\d\.\s,]+)\)', content)
            if wall_match:
                color_values = [float(x.strip()) for x in wall_match.group(1).split(',')]
                if len(color_values) >= 3:
                    colors['wall_color'] = tuple(color_values[:4])  # Take up to 4 values (RGBA)
                    
            print(f"🎨 Loaded colors - Floor: {colors['floor_color']}, Wall: {colors['wall_color']}")
            
        except Exception as e:
            print(f"❌ Error parsing background colors: {e}")
            print("Using default colors")
            
        return colors
    
    def clear_scene(self):
        """Clear all objects from the current scene"""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
    def create_room(self):
        """Create the room with floor and walls, including door and window openings"""
        width = self.layout_data['room_width']
        length = self.layout_data['room_length']
        height = 3.0  # Standard room height
        wall_thickness = 0.1
        
        # Create floor
        self.create_floor(width, length)
        
        # Create walls with openings
        self.create_walls_with_openings(width, length, height, wall_thickness)
        
        print(f"🏠 Created room: {width}m x {length}m x {height}m")
        
    def create_floor(self, width, length):
        """Create the floor with specified color"""
        bpy.ops.mesh.primitive_plane_add(size=1, location=(width/2, length/2, 0))
        floor = bpy.context.active_object
        floor.name = "Room_Floor"
        floor.scale = (width, length, 1)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Apply floor material
        floor_mat = bpy.data.materials.new(name="Floor_Material")
        floor_mat.use_nodes = True
        bsdf = floor_mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = self.background_colors['floor_color']
        bsdf.inputs['Roughness'].default_value = 0.3
        floor.data.materials.append(floor_mat)
        
    def create_walls_with_openings(self, width, length, height, wall_thickness):
        """Create walls with door and window openings"""
        wall_positions = {
            'back': (width/2, length + wall_thickness/2, height/2, (width + 2*wall_thickness, wall_thickness, height)),
            'front': (width/2, -wall_thickness/2, height/2, (width + 2*wall_thickness, wall_thickness, height)),
            'left': (-wall_thickness/2, length/2, height/2, (wall_thickness, length, height)),
            'right': (width + wall_thickness/2, length/2, height/2, (wall_thickness, length, height))
        }
            
        for wall_name, (x, y, z, scale) in wall_positions.items():
            wall = self.create_single_wall(f"Room_Wall_{wall_name.title()}", x, y, z, scale)
            self.create_wall_openings(wall, wall_name, width, length, height)
            
    def create_single_wall(self, name, x, y, z, scale):
        """Create a single wall"""
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        wall = bpy.context.active_object
        wall.name = name
        wall.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Apply wall material
        wall_mat = bpy.data.materials.new(name=f"{name}_Material")
        wall_mat.use_nodes = True
        wall_bsdf = wall_mat.node_tree.nodes["Principled BSDF"]
        wall_bsdf.inputs['Base Color'].default_value = self.background_colors['wall_color']
        wall_bsdf.inputs['Roughness'].default_value = 0.8
        wall.data.materials.append(wall_mat)
        
        return wall
        
    def create_wall_openings(self, wall, wall_direction, room_width, room_length, room_height):
        """Create openings in walls for doors and windows"""
        openings = self.get_openings_for_wall(wall_direction, room_width, room_length)
        
        if not openings:
            return
            
        for opening in openings:
            self.cut_opening_in_wall(opening, wall_direction, room_width, room_length, room_height)
        
    def get_openings_for_wall(self, wall_direction, room_width, room_length):
        """Get door and window openings for a specific wall"""
        openings = []
        
        for obj_name, obj_data in self.layout_data['objects'].items():
            if 'door' in obj_name.lower() or 'window' in obj_name.lower():
                opening_type = 'door' if 'door' in obj_name.lower() else 'window'
                pos_x, pos_y, rotation = obj_data['position']
                width = obj_data['width']
                
                wall_for_opening = self.determine_wall_for_opening(pos_x, pos_y, room_width, room_length)
                
                if wall_for_opening == wall_direction:
                    openings.append({
                        'type': opening_type,
                        'position': (pos_x, pos_y),
                        'width': width,
                        'height': 2.1 if opening_type == 'door' else 1.2,
                        'bottom_height': 0 if opening_type == 'door' else 1.0
                    })
                    
        return openings
        
    def determine_wall_for_opening(self, pos_x, pos_y, room_width, room_length):
        """Determine which wall an opening belongs to based on its position"""
        tolerance = 0.2
        
        if abs(pos_y) < tolerance:
            return 'front'
        elif abs(pos_y - room_length) < tolerance:
            return 'back'
        elif abs(pos_x) < tolerance:
            return 'left'
        elif abs(pos_x - room_width) < tolerance:
            return 'right'
        else:
            distances = {
                'front': pos_y,
                'back': room_length - pos_y,
                'left': pos_x,
                'right': room_width - pos_x
            }
            return min(distances, key=distances.get)
            
    def cut_opening_in_wall(self, opening, wall_direction, room_width, room_length, room_height):
        """Cut an opening in the wall mesh using boolean operations"""
        wall_thickness = 0.1
        
        pos_x, pos_y = opening['position']
        opening_width = opening['width']
        opening_height = opening['height']
        opening_bottom = opening['bottom_height']
        
        # Determine cutter position based on wall direction
        if wall_direction == 'front':
            cutter_pos = (pos_x, -wall_thickness/2, opening_bottom + opening_height/2)
            cutter_scale = (opening_width, wall_thickness + 0.02, opening_height)
        elif wall_direction == 'back':
            cutter_pos = (pos_x, room_length + wall_thickness/2, opening_bottom + opening_height/2)
            cutter_scale = (opening_width, wall_thickness + 0.02, opening_height)
        elif wall_direction == 'left':
            cutter_pos = (-wall_thickness/2, pos_y, opening_bottom + opening_height/2)
            cutter_scale = (wall_thickness + 0.02, opening_width, opening_height)
        elif wall_direction == 'right':
            cutter_pos = (room_width + wall_thickness/2, pos_y, opening_bottom + opening_height/2)
            cutter_scale = (wall_thickness + 0.02, opening_width, opening_height)
        else:
            return
        
        # Create cutter cube
        bpy.ops.mesh.primitive_cube_add(size=1, location=cutter_pos)
        cutter = bpy.context.active_object
        cutter.scale = cutter_scale
        cutter.name = f"{opening['type']}_cutter"
        
        # Get the wall object
        wall_name = f"Room_Wall_{wall_direction.title()}"
        wall = bpy.data.objects.get(wall_name)
        
        if wall:
            # Add boolean modifier to wall
            bool_mod = wall.modifiers.new(name=f"{opening['type']}_opening", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = cutter
            
            # Apply modifier
            bpy.context.view_layer.objects.active = wall
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            
            # Delete cutter object
            bpy.context.view_layer.objects.active = None
            bpy.ops.object.select_all(action='DESELECT')
            cutter.select_set(True)
            bpy.ops.object.delete(use_global=False)
            
            print(f"🚪 Created {opening['type']} opening on {wall_direction} wall")
        else:
            # Delete cutter since we couldn't use it
            bpy.ops.object.select_all(action='DESELECT')
            cutter.select_set(True)
            bpy.ops.object.delete(use_global=False)
            
    def load_object(self, object_id, obj_data):
        """Load a 3D object from its folder and place it in the scene"""
        obj_folder = os.path.join(self.objects_path, object_id)
        
        if not os.path.exists(obj_folder):
            print(f"❌ Object folder not found: {obj_folder}")
            return self.create_placeholder(object_id, obj_data)
            
        obj_file = os.path.join(obj_folder, 'normalized_model.obj')
        
        if not os.path.exists(obj_file):
            # Fallback to any .obj file
            for file in os.listdir(obj_folder):
                if file.endswith('.obj'):
                    obj_file = os.path.join(obj_folder, file)
                    print(f"⚠️  normalized_model.obj not found for {object_id}, using {file}")
                    break
        
        if not os.path.exists(obj_file):
            print(f"❌ No .obj file found for {object_id}")
            return self.create_placeholder(object_id, obj_data)
            
        # Store existing objects
        existing_objects = set(obj.name for obj in bpy.data.objects)
        
        # Import the object
        print(f"📦 Loading {object_id} from {os.path.basename(obj_file)}")
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.import_scene.obj(filepath=obj_file, use_split_objects=False, use_split_groups=False)
        
        # Get newly imported objects
        new_objects = [obj for obj in bpy.data.objects if obj.name not in existing_objects]
        
        if not new_objects:
            print(f"❌ No new objects were imported from {obj_file}")
            return self.create_placeholder(object_id, obj_data)
            
        # Process the imported object
        imported_obj = self.process_imported_object(new_objects, object_id, obj_data, obj_folder)
        
        return imported_obj
    
    def process_imported_object(self, new_objects, object_id, obj_data, obj_folder):
        """Process and position the imported object"""
        # Select and join multiple objects if needed
        bpy.ops.object.select_all(action='DESELECT')
        for obj in new_objects:
            obj.select_set(True)
        
        bpy.context.view_layer.objects.active = new_objects[0]
        
        if len(new_objects) > 1:
            bpy.ops.object.join()
        
        imported_obj = bpy.context.active_object
        imported_obj.name = f"{object_id}_furniture"
        
        # Fix texture paths and material properties
        self.fix_texture_paths(imported_obj, obj_folder)
        
        # Apply transformations (keeping original logic)
        self.apply_object_transformations(imported_obj, obj_data, object_id)
        
        return imported_obj
        
    def apply_object_transformations(self, imported_obj, obj_data, object_id):
        """Apply scaling, rotation, and positioning to the imported object"""
        # Reset and apply initial rotation
        imported_obj.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        
        # Initial mesh orientation
        imported_obj.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        bpy.context.view_layer.update()
        
        # Calculate scaling
        bbox = imported_obj.bound_box
        current_width = max([v[0] for v in bbox]) - min([v[0] for v in bbox])
        current_length = max([v[1] for v in bbox]) - min([v[1] for v in bbox])
        current_height = max([v[2] for v in bbox]) - min([v[2] for v in bbox])
        
        target_width = obj_data['width']
        target_length = obj_data['length']
        target_height = obj_data.get('height', current_height)
        
        # Apply scaling
        scale_x = target_width / current_width if current_width > 0 else 1
        scale_y = target_length / current_length if current_length > 0 else 1
        scale_z = max(scale_x, scale_y)  # Keep proportional height
        
        imported_obj.scale = (scale_x, scale_y, scale_z)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.context.view_layer.update()
        
        # Apply Z rotation
        final_z_rot = 2 * math.pi - obj_data['position'][2]
        imported_obj.rotation_euler = (0, 0, final_z_rot)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        bpy.context.view_layer.update()
        
        # Position object at floor center
        self.position_object_at_floor_center(imported_obj, obj_data)
        
    def position_object_at_floor_center(self, imported_obj, obj_data):
        """Position object so its bottom center aligns with the target position"""
        bpy.context.view_layer.update()
        bbox = imported_obj.bound_box
        
        # Calculate bounding box center and minimum Z
        min_x = min([v[0] for v in bbox])
        max_x = max([v[0] for v in bbox])
        min_y = min([v[1] for v in bbox])
        max_y = max([v[1] for v in bbox])
        min_z = min([v[2] for v in bbox])
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Move object origin to bottom center
        imported_obj.location.x -= center_x
        imported_obj.location.y -= center_y
        imported_obj.location.z -= min_z
        
        # Apply target position
        imported_obj.location.x += obj_data['position'][0]
        imported_obj.location.y += obj_data['position'][1]
        
        bpy.context.view_layer.update()
    
    def fix_texture_paths(self, obj, obj_folder):
        """Fix texture paths and material properties for imported materials"""
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                material = mat_slot.material
                
                # Fix texture paths
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        if not os.path.exists(bpy.path.abspath(node.image.filepath)):
                            # Try to find texture.png in object folder
                            texture_path = os.path.join(obj_folder, 'texture.png')
                            if os.path.exists(texture_path):
                                node.image.filepath = texture_path
                                node.image.reload()
                                print(f"  ✅ Fixed texture path: texture.png")
                            else:
                                # Try other common texture names
                                for tex_name in ['texture.jpg', 'diffuse.png', 'diffuse.jpg']:
                                    tex_path = os.path.join(obj_folder, tex_name)
                                    if os.path.exists(tex_path):
                                        node.image.filepath = tex_path
                                        node.image.reload()
                                        print(f"  ✅ Found texture: {tex_name}")
                                        break
                
                # Fix material properties to prevent glowing
                bsdf = None
                for node in material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        bsdf = node
                        break
                
                if bsdf:
                    # Reset problematic properties
                    bsdf.inputs['Emission'].default_value = (0.0, 0.0, 0.0, 1.0)  # No emission
                    bsdf.inputs['Metallic'].default_value = 0.0                    # Non-metallic
                    bsdf.inputs['Roughness'].default_value = 0.7                   # Reasonable roughness
                    bsdf.inputs['Specular'].default_value = 0.3                    # Reduced specular
                    
                    # Adjust overly bright colors
                    current_color = bsdf.inputs['Base Color'].default_value
                    if sum(current_color[:3]) > 2.0:
                        bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
                        print(f"  ⚡ Adjusted overly bright material")
    
    def create_placeholder(self, name, obj_data):
        """Create a placeholder cube for objects that can't be loaded"""
        position = obj_data['position']
        width = obj_data['width']
        length = obj_data['length']
        
        # Object height estimates
        height_map = {
            'bed': 0.6,
            'wardrobe': 2.0,
            'desk': 0.75,
        }
        height = height_map.get(name, 1.0)
        
        bpy.ops.mesh.primitive_cube_add(location=(position[0], position[1], height/2))
        placeholder = bpy.context.active_object
        placeholder.name = f"{name}_placeholder"
        placeholder.scale = (width, length, height)
        placeholder.rotation_euler = (0, 0, position[2])
        
        # Create placeholder material
        mat = bpy.data.materials.new(name=f"{name}_placeholder_material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.9, 0.5, 0.5, 1.0)  # Red placeholder
        placeholder.data.materials.append(mat)
        
        print(f"📦 Created placeholder for {name}")
        return placeholder
        
    def setup_camera_and_lighting(self):
        """Setup camera and lighting for the scene"""
        width = self.layout_data['room_width']
        length = self.layout_data['room_length']
        
        # Add camera
        camera_location = (width/2 + 3, -3, 4)
        bpy.ops.object.camera_add(location=camera_location)
        camera = bpy.context.active_object
        camera.rotation_euler = (1.1, 0, 0.785)  # Point towards room center
        bpy.context.scene.camera = camera
        
        # Add sun light
        bpy.ops.object.light_add(type='SUN', location=(width/2, length/2, 5))
        sun = bpy.context.active_object
        sun.data.energy = 1.5
        sun.rotation_euler = (-0.5, -0.5, 0)
        
        # Add area light for softer shadows
        bpy.ops.object.light_add(type='AREA', location=(width/2, length/2, 2.8))
        area_light = bpy.context.active_object
        area_light.data.energy = 30
        area_light.data.size = 3
        area_light.rotation_euler = (math.radians(180), 0, 0)  # Point downward
        
        print("📸 Camera and lighting setup complete")
        
    def setup_scene(self):
        """Main function to set up the entire scene"""
        print("=" * 50)
        print("🎬 BLENDER SCENE SETUP START")
        print("=" * 50)
        
        # Clear existing scene
        self.clear_scene()
        
        # Print layout info
        print(f"\n🏠 Room Layout:")
        print(f"   Size: {self.layout_data['room_width']}m x {self.layout_data['room_length']}m")
        print(f"   Floor color: {self.background_colors['floor_color']}")
        print(f"   Wall color: {self.background_colors['wall_color']}")
        
        print(f"\n📦 Objects in layout:")
        for name, data in self.layout_data['objects'].items():
            obj_type = "🚪 Door/Window" if ('door' in name.lower() or 'window' in name.lower()) else "🪑 Furniture"
            print(f"   {obj_type} {name}: pos={data['position']}, size={data['width']}x{data['length']}")
        
        # Create room
        self.create_room()
        
        # Load furniture objects (skip doors/windows)
        furniture_objects = [name for name in self.layout_data['objects'].keys() 
                           if 'door' not in name.lower() and 'window' not in name.lower()]
        
        print(f"\n🪑 Loading furniture: {furniture_objects}")
        for obj_name in furniture_objects:
            if obj_name in self.layout_data['objects']:
                try:
                    self.load_object(obj_name, self.layout_data['objects'][obj_name])
                except Exception as e:
                    print(f"❌ Could not load {obj_name}: {e}")
                    self.create_placeholder(obj_name, self.layout_data['objects'][obj_name])
                    
        # Setup camera and lighting
        self.setup_camera_and_lighting()
        
        # Save the scene
        output_file = os.path.join(self.output_path, "scene.blend")
        bpy.ops.wm.save_as_mainfile(filepath=output_file)
        
        # Final summary
        print("\n" + "=" * 50)
        print("✅ SCENE SETUP COMPLETE")
        print("=" * 50)
        print("📁 Output saved to:")
        print(f"   {output_file}")
        print(f"\n📊 Final scene contains:")
        for obj in bpy.data.objects:
            icon = "🏠" if "Room" in obj.name else "💡" if obj.type == 'LIGHT' else "📸" if obj.type == 'CAMERA' else "🪑"
            print(f"   {icon} {obj.name} ({obj.type})")


def main():
    """Main execution function"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Blender scene from layout data')
    parser.add_argument('--root', '-r', type=str, default=None,
                       help='Root directory path (default: script directory)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    # Only parse known args to avoid conflicts with Blender's arguments
    args, unknown = parser.parse_known_args()
    
    try:
        # Create and setup the scene
        layout_manager = SceneLayoutManager(root_path=args.root)
        layout_manager.setup_scene()
        
        print("\n🎉 SUCCESS: Scene generation completed!")
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()