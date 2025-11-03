#!/usr/bin/env python3
# render_glb_interior.py - FIXED look_at_matrix

import os
import sys
import argparse
import numpy as np
import math

os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

import trimesh
import pyrender
from PIL import Image


def look_at_matrix_fixed(camera_pos, target_pos, up=[0, 0, 1]):
    """
    Look-at 변환 행렬 생성 - FIXED for Pyrender
    
    Args:
        camera_pos: 카메라 위치 [x, y, z]
        target_pos: 바라볼 지점 [x, y, z]
        up: 상향 벡터 [x, y, z]
    
    Returns:
        4x4 변환 행렬
    """
    camera_pos = np.array(camera_pos, dtype=np.float64)
    target_pos = np.array(target_pos, dtype=np.float64)
    up = np.array(up, dtype=np.float64)
    
    # Forward 벡터 (카메라에서 타겟으로)
    forward = target_pos - camera_pos
    forward_norm = np.linalg.norm(forward)
    
    if forward_norm < 1e-6:
        # 카메라와 타겟이 같은 위치
        mat = np.eye(4)
        mat[:3, 3] = camera_pos
        return mat
    
    forward = forward / forward_norm
    
    # 수직 케이스 처리
    dot_product = abs(np.dot(forward, up))
    
    if dot_product > 0.999:  # 거의 평행
        if abs(forward[0]) < 0.9:
            up = np.array([1, 0, 0], dtype=np.float64)
        else:
            up = np.array([0, 1, 0], dtype=np.float64)
    
    # Right 벡터
    right = np.cross(forward, up)
    right_norm = np.linalg.norm(right)
    
    if right_norm < 1e-6:
        # 다른 up 벡터 시도
        up = np.array([0, 1, 0], dtype=np.float64) if abs(forward[1]) < 0.9 else np.array([1, 0, 0], dtype=np.float64)
        right = np.cross(forward, up)
        right_norm = np.linalg.norm(right)
    
    right = right / right_norm
    
    # Up 벡터 재계산
    up_corrected = np.cross(right, forward)
    up_corrected = up_corrected / np.linalg.norm(up_corrected)
    
    # 🔥 Pyrender용 변환 행렬 구성
    # Pyrender는 OpenGL 좌표계를 사용: +X=right, +Y=up, -Z=forward
    mat = np.eye(4)
    mat[0, :3] = right
    mat[1, :3] = up_corrected
    mat[2, :3] = -forward  # 카메라는 -Z 방향을 바라봄
    mat[:3, 3] = camera_pos
    
    return mat

def render_glb_interior_view(glb_path, output_path, 
                             camera_position=None,
                             look_at=None,
                             resolution=(1920, 1080),
                             fov=60,
                             background_color=(255, 255, 255, 255)):
    """
    GLB 파일을 방 내부 시점으로 렌더링
    """
    
    print(f"📂 Loading GLB: {glb_path}")
    
    if not os.path.exists(glb_path):
        print(f"❌ File not found: {glb_path}")
        return False
    
    try:
        # GLB 로드
        scene_data = trimesh.load(glb_path)
        print(f"✅ GLB loaded successfully")
        
        # Pyrender scene 생성 - 🔥 ambient_light 줄임
        render_scene = pyrender.Scene(
            ambient_light=[0.05, 0.05, 0.05],  # 0.3 → 0.05로 줄임
            bg_color=background_color
        )
        
        # Scene에 mesh 추가
        if hasattr(scene_data, 'geometry'):
            print(f"📦 Scene contains {len(scene_data.geometry)} objects")
            for name, geom in scene_data.geometry.items():
                try:
                    mesh = pyrender.Mesh.from_trimesh(geom)
                    render_scene.add(mesh)
                    print(f"  ✓ Added: {name}")
                except Exception as e:
                    print(f"  ⚠️  Failed to add {name}: {e}")
        else:
            print(f"📦 Single mesh scene")
            mesh = pyrender.Mesh.from_trimesh(scene_data)
            render_scene.add(mesh)
        
        # Scene bounds 계산
        bounds = scene_data.bounds
        center = scene_data.centroid
        size = bounds[1] - bounds[0]
        
        print(f"📏 Scene info:")
        print(f"  Center: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
        print(f"  Size: {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}")
        
        # 카메라 위치 자동 설정
        if camera_position is None:
            camera_position = [
                bounds[0][0] + size[0] * 0.2,
                bounds[0][1] + size[1] * 0.2,
                bounds[0][2] + size[2] * 0.5
            ]
        
        if look_at is None:
            look_at = [
                center[0],
                center[1],
                bounds[0][2] + size[2] * 0.4
            ]
        
        print(f"📷 Camera setup:")
        print(f"  Position: ({camera_position[0]:.2f}, {camera_position[1]:.2f}, {camera_position[2]:.2f})")
        print(f"  Looking at: ({look_at[0]:.2f}, {look_at[1]:.2f}, {look_at[2]:.2f})")
        print(f"  FOV: {fov}°")
        
        # Perspective 카메라 생성
        camera = pyrender.PerspectiveCamera(
            yfov=np.radians(fov),
            aspectRatio=resolution[0] / resolution[1]
        )
        
        # 수정된 Look-at 변환 행렬 사용
        camera_pose = look_at_matrix_fixed(camera_position, look_at)
        
        # 디버깅: 카메라 포즈 확인
        print(f"  Camera pose matrix:")
        print(f"    Forward (Z): {-camera_pose[2, :3]}")
        print(f"    Right (X): {camera_pose[0, :3]}")
        print(f"    Up (Y): {camera_pose[1, :3]}")
        
        render_scene.add(camera, pose=camera_pose)
        
        # 조명 설정 - 🔥 모든 intensity 대폭 줄임
        # 1. 천장 조명
        ceiling_light = pyrender.PointLight(
            color=[1.0, 1.0, 0.95],
            intensity=20.0  # 100.0 → 20.0
        )
        ceiling_pos = np.array([
            [1, 0, 0, center[0]],
            [0, 1, 0, center[1]],
            [0, 0, 1, bounds[1][2] - 0.3],
            [0, 0, 0, 1]
        ])
        render_scene.add(ceiling_light, pose=ceiling_pos)
        
        # 2. 방향광
        window_light = pyrender.DirectionalLight(
            color=[1.0, 1.0, 1.0],
            intensity=0.5  # 3.0 → 0.5
        )
        window_pose = np.array([
            [1, 0, 0, 0],
            [0, 0.7, -0.7, 0],
            [0, 0.7, 0.7, 0],
            [0, 0, 0, 1]
        ])
        render_scene.add(window_light, pose=window_pose)
        
        # 3. Fill light
        fill_light = pyrender.PointLight(
            color=[1.0, 1.0, 1.0],
            intensity=10.0  # 30.0 → 10.0
        )
        fill_pos = np.array([
            [1, 0, 0, camera_position[0]],
            [0, 1, 0, camera_position[1]],
            [0, 0, 1, camera_position[2]],
            [0, 0, 0, 1]
        ])
        render_scene.add(fill_light, pose=fill_pos)
        
        # 렌더링
        print(f"🎨 Rendering {resolution[0]}x{resolution[1]} image...")
        renderer = pyrender.OffscreenRenderer(
            viewport_width=resolution[0],
            viewport_height=resolution[1]
        )
        
        color, depth = renderer.render(render_scene)
        
        # 이미지 저장
        print(f"💾 Saving image to: {output_path}")
        image = Image.fromarray(color)
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        image.save(output_path, quality=95, optimize=True)
        
        renderer.delete()
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Rendering complete!")
        print(f"   Output: {output_path}")
        print(f"   Size: {file_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='Render GLB file from interior view (FIXED)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('glb_file', help='Input GLB file path')
    parser.add_argument('-o', '--output', required=True, help='Output image path')
    parser.add_argument('-r', '--resolution', type=int, nargs=2, default=[1920, 1080], 
                       metavar=('WIDTH', 'HEIGHT'), help='Image resolution')
    parser.add_argument('--camera', type=float, nargs=3, metavar=('X', 'Y', 'Z'),
                       help='Camera position')
    parser.add_argument('--look-at', type=float, nargs=3, metavar=('X', 'Y', 'Z'),
                       help='Point to look at')
    parser.add_argument('--fov', type=float, default=60, help='Field of view in degrees')
    parser.add_argument('--bg-color', type=int, nargs=3, default=[255, 255, 255],
                       metavar=('R', 'G', 'B'), help='Background color RGB')
    
    args = parser.parse_args()
    
    bg_color = args.bg_color + [255]
    
    print(f"🖥️  Rendering mode: {os.environ.get('PYOPENGL_PLATFORM', 'default')}")
    print(f"\n{'='*60}")
    print(f"🏠 Starting Interior View Rendering (FIXED)")
    print(f"{'='*60}\n")
    
    success = render_glb_interior_view(
        glb_path=args.glb_file,
        output_path=args.output,
        camera_position=args.camera,
        look_at=args.look_at,
        resolution=tuple(args.resolution),
        fov=args.fov,
        background_color=tuple(bg_color)
    )
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 SUCCESS!")
    else:
        print("💥 FAILED!")
        sys.exit(1)
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()