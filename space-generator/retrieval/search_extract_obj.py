# test_obj_loader.py - Test loading OBJ files from 3D-FUTURE dataset
import open3d as o3d
import numpy as np
import os
import re
import json
import shutil
from typing import Dict, List, Optional
import trimesh

class OBJLoaderTest:
    def __init__(self, root_path=None, clip_results_path="clip_rerank_results"):
        """
        Initialize the OBJ loader test
        
        Args:
            root_path: Root directory path containing layout.txt
            clip_results_path: Path to CLIP rerank results folder
        """
        if root_path is None:
            self.root_path = os.path.dirname(os.path.abspath(__file__))
        else:
            self.root_path = os.path.abspath(root_path)
            
        self.clip_results_path = clip_results_path
        self.layout_file_path = os.path.join(self.root_path, "layout.txt")
        self.output_path = os.path.join(self.root_path, "output", "individual_meshes")
        
        # 3D-FUTURE dataset paths
        self.dataset_paths = [
            "../../dataset/3D-FUTURE-model-part1",
            "../../dataset/3D-FUTURE-model-part2", 
            "../../dataset/3D-FUTURE-model-part3",
            "../../dataset/3D-FUTURE-model-part4"
	    ]
        
        # Create output directory
        os.makedirs(self.output_path, exist_ok=True)
        
        print(f"📁 Root path: {self.root_path}")
        print(f"📁 CLIP results path: {self.clip_results_path}")
        print(f"📁 Output path: {self.output_path}")
        
    def parse_layout_file(self):
        """Parse layout.txt to get object names"""
        objects = {}
        
        print(f"\n📖 Reading layout file: {self.layout_file_path}")
        
        if not os.path.exists(self.layout_file_path):
            print(f"❌ Layout file not found!")
            return objects
            
        with open(self.layout_file_path, 'r') as f:
            content = f.read()
            
        # First, extract object positions from the standard format
        position_pattern = r'(\w+):\s*\{\'position\':\s*\(([\d\w\.\(\), -]+)\),\s*\'width\':\s*([\d\.]+),\s*\'length\':\s*([\d\.]+)\}'
        
        positions = {}
        for match in re.finditer(position_pattern, content):
            obj_name = match.group(1).lower()
            if 'door' not in obj_name and 'window' not in obj_name:
                positions[obj_name] = {
                    'width': float(match.group(3)),
                    'length': float(match.group(4))
                }
        
        # Then, parse numbered blocks for object names (더 정확한 이름)
        pattern = re.compile(
            r'^\s*(\d+)[\.\)\-:\s]+\*\*([^*]+)\*\*[\s\S]*?(?=^\s*\d+[\.\)\-:\s]+\*\*|$\Z)',
            re.MULTILINE
        )
        
        numbered_objects = []
        for match in pattern.finditer(content):
            object_name = match.group(2).strip()
            numbered_objects.append(object_name)
            
        # Match numbered objects with position data
        if numbered_objects:
            print(f"📋 Found {len(numbered_objects)} numbered objects")
            for name in numbered_objects:
                key = name.lower().replace(' ', '_')
                # Try to find matching position data
                if key in positions:
                    objects[name] = positions[key]
                else:
                    # Try alternative matching (first word, etc.)
                    for pos_key in positions:
                        if pos_key in key or key in pos_key:
                            objects[name] = positions[pos_key]
                            break
        else:
            # Fallback to position keys if no numbered format found
            print("⚠️  No numbered format found, using position keys")
            for key, data in positions.items():
                objects[key] = data
                
        print(f"📊 Found {len(objects)} furniture objects: {list(objects.keys())}")
        return objects
        
    def get_object_ids_from_clip(self, object_name):
        """Get all object IDs from CLIP rerank results"""
        # Try different filename patterns
        possible_names = [
            object_name.lower().replace(' ', '_'),
            object_name.lower().replace(' ', '-'),
            object_name.lower(),
            object_name.lower().split()[0] if ' ' in object_name else object_name.lower()
        ]
        
        for name in possible_names:
            txt_file = os.path.join(self.clip_results_path, f"{name}_clip_top.txt")
            if os.path.exists(txt_file):
                try:
                    with open(txt_file, 'r') as f:
                        ids = [line.strip() for line in f.readlines() if line.strip()]
                        print(f"📎 Found {len(ids)} IDs for {object_name} (file: {name}_clip_top.txt)")
                        if len(ids) > 3:
                            print(f"   First 3 IDs: {ids[:3]}...")
                        else:
                            print(f"   IDs: {ids}")
                        return ids
                except Exception as e:
                    print(f"❌ Error reading CLIP results: {e}")
                    
        print(f"⚠️  No CLIP results found for {object_name} (tried: {possible_names})")
        return []
            
    def find_object_in_dataset(self, object_id):
        """Find object folder in 3D-FUTURE dataset"""
        for dataset_path in self.dataset_paths:
            obj_folder = os.path.join(dataset_path, object_id)
            if os.path.exists(obj_folder):
                print(f"  ✅ Found {object_id} in {os.path.basename(dataset_path)}")
                return obj_folder
                
        print(f"  ❌ Object {object_id} not found in any dataset")
        return None
        
    def find_obj_file(self, obj_folder):
        """Find the OBJ file in the folder"""
        # Priority order for OBJ files
        obj_names = [
            'normalized_model.obj',
            'normalized.obj', 
            'model_normalized.obj',
            'raw_model.obj',
            'model.obj'
        ]
        
        # First try priority names
        for obj_name in obj_names:
            obj_path = os.path.join(obj_folder, obj_name)
            if os.path.exists(obj_path):
                return obj_path, obj_name
                
        # If not found, look for any .obj file
        for file in os.listdir(obj_folder):
            if file.endswith('.obj'):
                return os.path.join(obj_folder, file), file
                
        return None, None
    
    
    def convert_obj_folder_to_glb(self, source_folder, output_glb_path):
        obj_path = os.path.join(source_folder, 'normalized_model.obj')
        if not os.path.exists(obj_path):
            print(f'❌ {obj_path} not found')
            return False
        try:
            mesh = trimesh.load(obj_path, force='mesh')
            mesh.export(output_glb_path)
            print(f"  💾 Saved glb to: {output_glb_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to convert {obj_path} to glb: {e}")
            return False

    
    def load_and_save_object(self, object_name, object_id, save_name):
        """Load OBJ file and save as GLB using trimesh, no file copying"""
        # 1. Find object folder
        obj_folder = self.find_object_in_dataset(object_id)
        if not obj_folder:
            return False

        obj_path = os.path.join(obj_folder, "normalized_model.obj")
        if not os.path.exists(obj_path):
            print(f"  ❌ normalized_model.obj not found in {obj_folder}")
            return False

        print(f"  📂 Loading from: {obj_path}")

        try:
            # (Open3D로 mesh info만 출력, 이후는 사용X)
            mesh = o3d.io.read_triangle_mesh(obj_path)
            if not mesh.has_vertices():
                print(f"  ❌ Mesh has no vertices!")
                return False
            vertices = np.asarray(mesh.vertices)
            triangles = np.asarray(mesh.triangles)
            print(f"  📊 Mesh stats: {len(vertices)} vertices, {len(triangles)} triangles")

            # Texture/material 존재여부 확인
            texture_path = os.path.join(obj_folder, "texture.png")
            mtl_path = os.path.join(obj_folder, "model.mtl")
            if os.path.exists(texture_path):
                print(f"  🎨 Found texture: texture.png")
            if os.path.exists(mtl_path):
                print(f"  📄 Found material: model.mtl")

            # 2. 바로 GLB로 저장 (복사없이)
            output_glb = os.path.join(self.output_path, f"{save_name}.glb")
            self.convert_obj_folder_to_glb(obj_folder, output_glb)  # 이 함수는 위에서 제공

            return True

        except Exception as e:
            print(f"  ❌ Error processing files: {e}")
            import traceback
            traceback.print_exc()
            return False

            
    def test_all_objects(self):
        """Test loading all objects from layout"""
        print("\n" + "="*60)
        print("🧪 TESTING OBJ LOADING FROM 3D-FUTURE DATASET")
        print("="*60)
        
        # Parse layout to get objects
        objects = self.parse_layout_file()
        
        if not objects:
            print("❌ No objects found in layout.txt")
            return
            
        # Results tracking
        results = {
            'success': [],
            'failed': [],
            'no_clip': []
        }
        
        # Test each object
        for obj_name in objects:
            print(f"\n🔍 Processing: {obj_name}")
            print("-" * 40)
            
            # Get CLIP results
            clip_ids = self.get_object_ids_from_clip(obj_name)
            
            if not clip_ids:
                results['no_clip'].append(obj_name)
                continue
                
            # Try first ID
            success = False
            for i, clip_id in enumerate(clip_ids[:3]):  # Try up to 3 IDs
                print(f"\n  Trying ID {i+1}: {clip_id}")
                save_name = f"{obj_name.replace(' ', '_')}_{i+1}_{clip_id}"
                if self.load_and_save_object(obj_name, clip_id, save_name):
                    results['success'].append(f"{obj_name} ({clip_id})")
                    success = True
                    break
                    
            if not success:
                results['failed'].append(obj_name)
                
        # Print summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"✅ Successfully loaded: {len(results['success'])} objects")
        for obj in results['success']:
            print(f"   - {obj}")
            
        if results['no_clip']:
            print(f"\n⚠️  No CLIP results: {len(results['no_clip'])} objects")
            for obj in results['no_clip']:
                print(f"   - {obj}")
                
        if results['failed']:
            print(f"\n❌ Failed to load: {len(results['failed'])} objects")
            for obj in results['failed']:
                print(f"   - {obj}")
                
        print(f"\n📁 Check output folder: {self.output_path}")
        
        # Save summary as JSON
        summary_file = os.path.join(self.output_path, "loading_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Summary saved to: {summary_file}")


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test OBJ loading from 3D-FUTURE dataset')
    parser.add_argument('--root', '-r', type=str, default="/data2/sumin/stylin/FlairGPT/Scene_Synthesis/Result_txt/layout",
                       help='Root directory path containing layout.txt')
    parser.add_argument('--clip-results', '-c', type=str,
                       default="/data2/sumin/stylin/FlairGPT/retrieval/clip_rerank_results",
                       help='Path to CLIP rerank results folder')
    
    args = parser.parse_args()
    
    # Run test
    tester = OBJLoaderTest(
        root_path=args.root,
        clip_results_path=args.clip_results
    )
    
    tester.test_all_objects()


if __name__ == "__main__":
    main()
