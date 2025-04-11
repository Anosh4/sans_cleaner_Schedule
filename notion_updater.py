from notion_client import Client
import os

# Notion API Token과 Database ID를 환경 변수에서 가져오거나 기본값 사용
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "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")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "1b66b54dd16f8051a7beeed441be3c17")

notion = Client(auth=NOTION_TOKEN)

def assign_cleaner_to_date(cleaning_date: str, cleaner_name: str):
    print(f"\n======= 청소 담당자 배정 시작: {cleaning_date}, {cleaner_name} =======")
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "and": [
                {"property": "청소 일정", "date": {"equals": cleaning_date}},
                {"property": "상태", "status": {"equals": "청소 배정 필요"}}
            ]
        }
    )

    if not response["results"]:
        print("❌ 해당 날짜에 청소 배정 필요 일정이 없습니다.")
        return False

    page_id = response["results"][0]["id"]
    
    # 예약인원 확인
    people_count = response["results"][0]["properties"].get("예약인원", {}).get("number", 0)
    print(f"예약인원: {people_count}명")
    
    # 기존 청소 담당자 확인
    current_cleaners = response["results"][0]["properties"].get("청소 담당자", {}).get("multi_select", [])
    cleaner_names = [cleaner["name"] for cleaner in current_cleaners] if current_cleaners else []
    print(f"기존 담당자: {cleaner_names}")
    
    # 중복 배정 방지
    if cleaner_name in cleaner_names:
        print(f"❌ {cleaner_name} 님은 이미 배정되어 있습니다.")
        return False
    
    # 기존 담당자가 있으면 추가, 없으면 새로 설정
    if cleaner_names:
        cleaner_names.append(cleaner_name)
        multi_select_items = [{"name": name} for name in cleaner_names]
    else:
        multi_select_items = [{"name": cleaner_name}]
    
    print(f"배정 후 담당자: {[item['name'] for item in multi_select_items]}")
    
    # 예약인원이 7명 미만이고 이미 담당자가 있는 경우 중복 배정 방지
    if people_count < 7 and len(cleaner_names) > 1:
        print(f"❌ 예약인원이 7명 미만인 경우 청소 담당자는 1명만 배정 가능합니다.")
        return False
    
    # 예약인원이 7명 이상이어도 담당자가 2명을 초과하는 경우 배정 방지
    if len(multi_select_items) > 2:
        print(f"❌ 청소 담당자는 최대 2명까지만 배정 가능합니다.")
        return False

    # 상태 업데이트 조건 설정
    # 7명 이상 예약이면 2명이 모두 배정되었을 때만 '예약됨' 상태로 변경
    new_status = "예약됨"
    if people_count >= 7 and len(multi_select_items) < 2:
        new_status = "청소 배정 필요"  # 아직 2명 다 배정되지 않았으므로 상태 유지
        print(f"⚠️ 7명 이상 예약인데 담당자가 {len(multi_select_items)}명이므로 '청소 배정 필요' 상태 유지")
    else:
        print(f"✓ 상태를 '예약됨'으로 변경합니다. 예약인원: {people_count}, 담당자 수: {len(multi_select_items)}")

    # 업데이트 실행 - 한번에 모든 속성 업데이트
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "청소 담당자": {"multi_select": multi_select_items},
                "상태": {"status": {"name": new_status}}
            }
        )
        print(f"✅ {cleaning_date}에 {cleaner_name} 님 배정 완료, 상태: {new_status}")
        
        # 업데이트 확인
        check_response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "청소 일정",
                "date": {
                    "equals": cleaning_date
                }
            }
        )
        
        if check_response["results"]:
            updated_status = check_response["results"][0]["properties"].get("상태", {}).get("status", {}).get("name", "")
            print(f"✓ 업데이트 후 상태 확인: {updated_status}")
            
            # 상태가 의도한 대로 변경되지 않았을 경우 다시 시도
            if updated_status != new_status:
                print(f"⚠️ 상태가 원하는 대로 변경되지 않았습니다. 다시 시도합니다.")
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        "상태": {"status": {"name": new_status}}
                    }
                )
                print(f"✓ 상태 재업데이트 시도: {new_status}")
        
        return True
    except Exception as e:
        print(f"❌ 업데이트 중 오류 발생: {e}")
        return False
