#!/usr/bin/env python3
# batch_render_four_walls.py - 4개 벽에서 방 안을 바라보는 뷰

import os
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

import sys
import argparse
import numpy as np
from pathlib import Path
import trimesh

from render import render_glb_interior_view


class FourWallsRenderer:
    def __init__(self, glb_path, output_dir):
        self.glb_path = glb_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📦 Loading GLB: {glb_path}")
        scene = trimesh.load(glb_path)
        
        bounds = scene.bounds
        self.center = scene.centroid
        self.size = bounds[1] - bounds[0]
        self.bounds = bounds
        
        # 방의 실제 좌표
        self.room_x_min, self.room_y_min, self.room_z_min = bounds[0]
        self.room_x_max, self.room_y_max, self.room_z_max = bounds[1]
        self.room_width = self.room_x_max - self.room_x_min
        self.room_length = self.room_y_max - self.room_y_min
        self.room_height = self.room_z_max - self.room_z_min
        
        print(f"🏠 Room info:")
        print(f"   Size: {self.room_width:.2f} x {self.room_length:.2f} x {self.room_height:.2f}")
        print(f"   X range: {self.room_x_min:.2f} ~ {self.room_x_max:.2f}")
        print(f"   Y range: {self.room_y_min:.2f} ~ {self.room_y_max:.2f}")
        print(f"   Z range: {self.room_z_min:.2f} ~ {self.room_z_max:.2f}")
        print(f"   Center: ({self.center[0]:.2f}, {self.center[1]:.2f}, {self.center[2]:.2f})")
    
    def render_view(self, name, camera_pos, look_at, fov=70, resolution=(1920, 1080)):
        """직접 render_glb_interior_view 함수 호출"""
        output_path = self.output_dir / f"render_{name}.png"
        
        print(f"\n🎬 Rendering {name}...")
        print(f"   📷 Camera: ({camera_pos[0]:.2f}, {camera_pos[1]:.2f}, {camera_pos[2]:.2f})")
        print(f"   👁️  Looking at: ({look_at[0]:.2f}, {look_at[1]:.2f}, {look_at[2]:.2f})")
        print(f"   📐 FOV: {fov}°")
        print(f"   📏 Resolution: {resolution[0]}x{resolution[1]}")
        
        success = render_glb_interior_view(
            glb_path=self.glb_path,
            output_path=str(output_path),
            camera_position=list(camera_pos),
            look_at=list(look_at),
            resolution=resolution,
            fov=fov
        )
        
        if success:
            print(f"   ✅ Saved: {output_path}")
            return str(output_path)
        else:
            print(f"   ❌ Failed")
            return None

    def render_top_view(self):
        """탑뷰 - 위에서 아래로 (정사각형)"""
        camera_height = self.room_z_max + max(self.room_width, self.room_length) * 0.5
        
        return self.render_view(
            "01_top_view",
            camera_pos=[
                self.center[0],
                self.center[1],
                camera_height
            ],
            look_at=self.center,
            fov=65,
            resolution=(1080, 1080)  # 정사각형 해상도
        )
    
    def render_from_back_wall(self):
        """뒤쪽 벽에서 앞쪽을 바라보는 뷰"""
        eye_height = self.room_z_min + 1.6
        wall_offset = 0.15
        look_depth = 0.7
        
        return self.render_view(
            "02_from_back_wall",
            camera_pos=[
                self.center[0],
                self.room_y_max - self.room_length * wall_offset,
                eye_height
            ],
            look_at=[
                self.center[0],
                self.room_y_max - self.room_length * look_depth,
                eye_height - 0.3
            ],
            fov=75
        )
    
    def render_all(self):
        """모든 뷰 렌더링"""
        print("\n" + "=" * 60)
        print("🎬 STARTING RENDERING")
        print("=" * 60)
        
        results = []
        
        # 1. 탑뷰
        print("\n📸 TOP VIEW")
        top = self.render_top_view()
        if top:
            results.append(top)
        
        # 2. 뒤쪽 벽
        print("\n📸 BACK WALL VIEW")
        back = self.render_from_back_wall()
        if back:
            results.append(back)
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("✅ RENDERING COMPLETE!")
        print("=" * 60)
        print(f"📸 Total: {len(results)} images")
        
        print(f"\n📂 Files:")
        for img in results:
            print(f"   - {Path(img).name}")
        
        print(f"\n📁 Output directory: {self.output_dir}")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Render room from top view and back wall view'
    )
    parser.add_argument(
        '--glb', '-g',
        required=True,
        help='Path to GLB file'
    )
    parser.add_argument(
        '--output', '-o',
        default='renders_2views',
        help='Output directory (default: renders_2views)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.glb):
        print(f"❌ GLB file not found: {args.glb}")
        sys.exit(1)
    
    try:
        renderer = FourWallsRenderer(args.glb, args.output)
        results = renderer.render_all()
        
        if results:
            print("\n🎉 All rendering completed successfully!")
        else:
            print("\n⚠️  No images were rendered")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()