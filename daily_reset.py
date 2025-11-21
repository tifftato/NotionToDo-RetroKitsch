import os
import json
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# --- 설정 ---
# GitHub Secrets에서 가져올 값들
NOTION_TOKEN = os.environ['NOTION_KEY']
NOTION_DB_ID = "2b28c5bdbe91803caa65ed21de8fc4e5" # Backlog용 DB ID
FIREBASE_CREDENTIALS = os.environ['FIREBASE_ADMIN_JSON'] # 관리자 열쇠 내용

# --- 1. Firebase 접속 (관리자 모드) ---
cred_dict = json.loads(FIREBASE_CREDENTIALS)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://notion-todo-retrokitsch-default-rtdb.asia-southeast1.firebasedatabase.app'
})

def create_notion_page(text, is_priority):
    """노션에 페이지를 생성하는 함수"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 이모지 설정 (중요하면 별, 아니면 빗자루)
    icon = "⭐" if is_priority else "🧹"
    
    data = {
        "parent": {"database_id": NOTION_DB_ID},
        "icon": {"emoji": icon},
        "properties": {
            "Name": { # 데이터베이스의 제목 속성 이름이 'Name' 또는 '이름'인지 확인하세요
                "title": [{"text": {"content": text}}]
            },
            "Status": { # 상태 속성이 있다면
                "select": {"name": "Backlog"} # 'Backlog'라는 옵션이 있어야 함
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"❌ Notion Error: {response.text}")
    else:
        print(f"✅ Notion Archived: {text}")

def midnight_cleaner():
    print("🌙 자정의 청소부가 활동을 시작합니다...")
    ref = db.reference('tasks')
    snapshot = ref.get()
    
    if not snapshot:
        print("🧹 위젯이 이미 깨끗합니다.")
        return

    moved_count = 0
    
    for key, val in snapshot.items():
        text = val.get('text', 'No Text')
        completed = val.get('completed', False)
        priority = val.get('priority', False)
        
        # 완료되지 않은 일은 노션으로 대피!
        if not completed:
            print(f"📦 이동 중: {text}")
            create_notion_page(text, priority)
            moved_count += 1
        
        # 위젯에서는 모두 삭제 (완료된 것도 삭제)
        ref.child(key).delete()
        
    print(f"✨ 청소 완료! {moved_count}개의 할 일을 노션으로 옮겼습니다.")

if __name__ == '__main__':
    midnight_cleaner()
