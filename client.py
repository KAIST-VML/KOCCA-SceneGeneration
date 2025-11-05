#!/usr/bin/env python3
"""
간단한 3D Scene Generation 클라이언트
사용법: python client.py "input_prompt" "save_dir" [iterations] [server_url]
"""

import sys
import requests
import time
import os
import argparse
from pathlib import Path


class SceneGenerationClient:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url.rstrip('/')
        
    def set_api_key(self, api_key):
        """OpenAI API 키 설정"""
        try:
            response = requests.post(
                f"{self.server_url}/api/set-api-key",
                json={"openai_api_key": api_key}
            )
            if response.status_code == 200:
                print("✅ API 키가 성공적으로 설정되었습니다.")
                return True
            else:
                print(f"❌ API 키 설정 실패: {response.json().get('detail', '알 수 없는 오류')}")
                return False
        except Exception as e:
            print(f"❌ API 키 설정 중 오류: {e}")
            return False
    
    def generate_scene(self, scene_descriptor, iterations=300):
        """씬 생성 요청"""
        try:
            response = requests.post(
                f"{self.server_url}/api/generate-scene",
                json={
                    "scene_descriptor": scene_descriptor,
                    "iterations": iterations
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"🚀 씬 생성 요청이 접수되었습니다. Task ID: {data['task_id']}")
                return data['task_id']
            else:
                error_msg = response.json().get('detail', '알 수 없는 오류')
                print(f"❌ 씬 생성 요청 실패: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ 요청 중 오류 발생: {e}")
            return None
    
    def wait_for_completion(self, task_id, check_interval=10):
        """작업 완료까지 대기"""
        print("⏳ 씬 생성 중...")
        
        while True:
            try:
                response = requests.get(f"{self.server_url}/api/status/{task_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data['status']
                    
                    print(f"📊 상태: {status}")
                    
                    # 단계별 상세 정보 출력
                    if 'steps' in data:
                        for step_name, step_info in data['steps'].items():
                            step_status = step_info['status']
                            step_progress = step_info['progress']
                            step_message = step_info['message']
                            
                            if step_status == 'processing':
                                print(f"  🔄 {step_name}: {step_message} ({step_progress}%)")
                            elif step_status == 'completed':
                                print(f"  ✅ {step_name}: 완료")
                            elif step_status == 'failed':
                                print(f"  ❌ {step_name}: 실패 - {step_message}")
                    
                    if status == 'completed':
                        print("🎉 씬 생성이 완료되었습니다!")
                        return True
                    elif status == 'failed':
                        error_msg = data.get('error', '알 수 없는 오류')
                        print(f"❌ 씬 생성 실패: {error_msg}")
                        return False
                    
                    time.sleep(check_interval)
                else:
                    print(f"❌ 상태 확인 실패: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ 상태 확인 중 오류: {e}")
                time.sleep(check_interval)
    
    def download_file(self, task_id, save_path):
        """GLB 파일 다운로드"""
        try:
            # 저장 디렉토리 생성
            save_dir = Path(save_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 파일 다운로드 중...")
            response = requests.get(f"{self.server_url}/download/{task_id}", stream=True)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ 파일이 성공적으로 저장되었습니다: {save_path}")
                return True
            else:
                print(f"❌ 파일 다운로드 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 파일 다운로드 중 오류: {e}")
            return False
    
    def check_server_health(self):
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.server_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"🟢 서버 상태: {data['status']}")
                print(f"   활성 작업: {data['active_tasks']}개")
                # api_key_status가 없어도 무시
                api_key_status = data.get('api_key_status', 'Unknown')
                print(f"   API 키 상태: {api_key_status}")
                return True
            else:
                print(f"🔴 서버 응답 오류: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"🔴 서버 연결 실패: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='3D Scene Generation Client')
    parser.add_argument('input_prompt', help='씬 설명 텍스트')
    parser.add_argument('save_dir', help='GLB 파일 저장 경로')
    parser.add_argument('--iterations', type=int, default=200, help='반복 횟수 (기본값: 300)')
    parser.add_argument('--server-url', default=os.getenv('SCENE_SERVER_URL', 'http://localhost:8000'), help='서버 URL')
    parser.add_argument('--api-key', default=os.getenv('OPENAI_API_KEY'), help='OpenAI API 키')
    parser.add_argument('--check-interval', type=int, default=10, help='상태 확인 간격 (초, 기본값: 10)')
    
    args = parser.parse_args()
    
    # 클라이언트 초기화
    client = SceneGenerationClient(args.server_url)
    
    print("🎨 3D Scene Generation Client")
    print(f"📝 씬 설명: {args.input_prompt}")
    print(f"💾 저장 경로: {args.save_dir}")
    print(f"🔄 반복 횟수: {args.iterations}")
    print(f"🌐 서버: {args.server_url}")
    print("-" * 50)
    
    # 서버 상태 확인
    if not client.check_server_health():
        print("❌ 서버에 연결할 수 없습니다.")
        sys.exit(1)
    
    # API 키 설정 (필요한 경우)
    api_key = args.api_key
    if api_key:
        if not client.set_api_key(api_key):
            print("❌ API 키 설정에 실패했습니다.")
            sys.exit(1)
    
    # 씬 생성 요청
    task_id = client.generate_scene(args.input_prompt, args.iterations)
    if not task_id:
        print("❌ 씬 생성 요청에 실패했습니다.")
        sys.exit(1)
    
    # 완료 대기
    if not client.wait_for_completion(task_id, args.check_interval):
        print("❌ 씬 생성에 실패했습니다.")
        sys.exit(1)
    
    # 파일 다운로드
    save_path = Path(args.save_dir) / f"scene_{task_id}.glb"
    if client.download_file(task_id, save_path):
        print(f"🎉 모든 작업이 완료되었습니다!")
        print(f"📁 GLB 파일 위치: {save_path}")
    else:
        print("❌ 파일 다운로드에 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()