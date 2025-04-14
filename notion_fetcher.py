from notion_client import Client
from datetime import datetime, timedelta
import calendar
import os

# Notion API Token과 Database ID를 환경 변수에서 가져오거나 기본값 사용
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "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")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "1b66b54dd16f8051a7beeed441be3c17")

notion = Client(auth=NOTION_TOKEN)

day_map = {
    "Monday": "(월)", "Tuesday": "(화)", "Wednesday": "(수)",
    "Thursday": "(목)", "Friday": "(금)", "Saturday": "(토)", "Sunday": "(일)"
}

def get_korean_date(date_obj):
    weekday = date_obj.strftime('%A')
    korean_day = day_map.get(weekday, weekday)
    return f"{date_obj.year % 100}년 {date_obj.month}월 {date_obj.day}일 {korean_day}"

def get_cleaning_messages():
    result_text = "[자동 메세지]\n🧼 청소 담당자분이 배정되지 않은 일정 목록입니다.\n"

    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "상태",
            "status": {
                "equals": "청소 배정 필요"
            }
        }
    )

    for page in response["results"]:
        props = page["properties"]
        date_data = props.get("청소 일정", {}).get("date")
        if not date_data or not date_data.get("start"):
            continue

        try:
            date = datetime.fromisoformat(date_data["start"])
            people = props.get("예약인원", {}).get("number", 0)
            formatted = f"{get_korean_date(date)}, 예약자 수는 {people}명 입니다."
            result_text += formatted + "\n"
        except Exception as e:
            print("⚠️ 날짜 파싱 오류:", e)

    result_text += "\n[청소 캘린더 확인하기] : http://bit.ly/43rPfOu"
    return result_text.strip()

# 청소 담당자 목록 가져오기
def get_cleaner_options():
    try:
        # 데이터베이스 속성 정보 가져오기
        database = notion.databases.retrieve(database_id=DATABASE_ID)
        
        # '청소 담당자' 속성 찾기
        cleaner_property = database.get("properties", {}).get("청소 담당자", {})
        
        # 선택 옵션 가져오기
        cleaner_options = []
        if cleaner_property.get("type") == "multi_select":
            options = cleaner_property.get("multi_select", {}).get("options", [])
            for option in options:
                cleaner_options.append({
                    "id": option.get("id"),
                    "name": option.get("name"),
                    "color": option.get("color")
                })
        
        return cleaner_options
    except Exception as e:
        print(f"⚠️ 청소 담당자 목록 가져오기 오류: {e}")
        return []

# 캘린더용 노션 데이터 가져오기
def get_notion_calendar_data(year=None, month=None):
    if not year or not month:
        now = datetime.now()
        year = now.year
        month = now.month
    
    # 해당 월의 시작일과 마지막 날짜 계산
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # 노션 데이터베이스 쿼리
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "and": [
                {
                    "property": "청소 일정",
                    "date": {
                        "on_or_after": first_day.date().isoformat()
                    }
                },
                {
                    "property": "청소 일정",
                    "date": {
                        "on_or_before": last_day.date().isoformat()
                    }
                }
            ]
        }
    )
    
    # 결과 포맷팅
    calendar_data = {}
    for page in response["results"]:
        props = page["properties"]
        date_data = props.get("청소 일정", {}).get("date")
        if not date_data or not date_data.get("start"):
            continue
            
        try:
            date = datetime.fromisoformat(date_data["start"])
            date_key = date.strftime('%Y-%m-%d')
            
            cleaner_items = props.get("청소 담당자", {}).get("multi_select", [])
            cleaner_names = [item.get("name", "") for item in cleaner_items if item.get("name")]
            cleaner_name = ", ".join(cleaner_names) if cleaner_names else "미지정"
            
            status = props.get("상태", {}).get("status", {}).get("name", "")
            people = props.get("예약인원", {}).get("number", 0)
            
            calendar_data[date_key] = {
                "day": date.day,
                "cleaner": cleaner_name,
                "status": status,
                "people": people,
                "page_id": page["id"]
            }
        except Exception as e:
            print(f"⚠️ 캘린더 데이터 파싱 오류: {e}")
    
    return {
        "year": year,
        "month": month,
        "data": calendar_data
    }

# 미배정 청소 일정 가져오기
def get_unassigned_cleaning_tasks():
    print("\n===== 미배정 청소 일정 가져오기 시작 =====")
    print(f"노션 TOKEN 체크: {NOTION_TOKEN[:5]}...")
    print(f"노션 DATABASE_ID 체크: {DATABASE_ID}")
    
    # 노션 API 필터 정보 확인
    filter_json = {
        "property": "청소 담당자",
        "multi_select": {
            "is_empty": True
        }
    }
    print(f"사용하는 필터: {filter_json}")
    
    try:
        # 먼저 모든 상태값 확인을 위한 쿼리
        print("전체 데이터베이스 항목 조회 중...")
        all_response = notion.databases.query(
            database_id=DATABASE_ID,
            page_size=100  # 최대 100개 항목 가져오기
        )
        
        print(f"전체 데이터베이스 항목 개수: {len(all_response['results'])}")
        
        # 상태 프로퍼티 분석
        all_statuses = {}
        for page in all_response["results"]:
            status_obj = page["properties"].get("상태", {})
            status_type = status_obj.get("type", "없음")
            
            if status_type == "status":
                status_name = status_obj.get("status", {}).get("name", "없음")
                if status_name in all_statuses:
                    all_statuses[status_name] += 1
                else:
                    all_statuses[status_name] = 1
            else:
                print(f"⚠️ 예상치 못한 상태 프로퍼티 형식: {status_type}")
        
        print(f"데이터베이스 내 모든 상태값 분포: {all_statuses}")
        
        # 필터링된 쿼리 실행
        print("'청소 배정 필요' 상태이면서 담당자가 없는 항목 조회 중...")
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter=filter_json,
            sorts=[
                {
                    "property": "청소 일정",
                    "direction": "ascending"
                }
            ]
        )
        
        print(f"노션 API 응답: 총 {len(response['results'])}개 일정 조회됨")
        
        tasks = []
        for page in response["results"]:
            props = page["properties"]
            date_data = props.get("청소 일정", {}).get("date")
            if not date_data or not date_data.get("start"):
                continue
                
            try:
                date_str = date_data["start"]
                date = datetime.fromisoformat(date_str)
                people = props.get("예약인원", {}).get("number", 0)
                
                # 이미 배정된 담당자 정보 확인
                cleaner_items = props.get("청소 담당자", {}).get("multi_select", [])
                cleaner_names = [item.get("name", "") for item in cleaner_items if item.get("name")]
                current_assigned = ", ".join(cleaner_names) if cleaner_names else ""
                
                status = props.get("상태", {}).get("status", {}).get("name", "")
                
                page_id = page["id"]
                print(f"미배정 항목: {get_korean_date(date)}, 인원: {people}명, 담당자: {current_assigned}, 상태: {status}, ID: {page_id[:8]}...")
                
                tasks.append({
                    "date": date_str,
                    "formatted_date": get_korean_date(date),
                    "people": people,
                    "page_id": page_id,
                    "current_assigned": current_assigned
                })
            except Exception as e:
                print(f"⚠️ 미배정 일정 파싱 오류: {e}")
        
        print(f"최종 미배정 일정 개수: {len(tasks)}개")
        print("===== 미배정 청소 일정 가져오기 완료 =====\n")
        return tasks
    except Exception as e:
        print(f"❌ 노션 API 호출 오류: {e}")
        print(f"오류 세부 정보: {str(e)}")
        print("===== 미배정 청소 일정 가져오기 실패 =====\n")
        return []

# 주간 일정 가져오기
def get_weekly_schedule():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # 이번 주 월요일
    end_of_week = start_of_week + timedelta(days=6)  # 이번 주 일요일
    end_of_next_week = end_of_week + timedelta(days=7)  # 다음 주 일요일
    
    # 이번 주 일정
    this_week = get_week_schedule(start_of_week, end_of_week)
    
    # 다음 주 일정
    next_week = get_week_schedule(end_of_week + timedelta(days=1), end_of_next_week)
    
    return {
        "this_week": this_week,
        "next_week": next_week
    }

# 특정 기간의 일정 가져오기 (주간 일정 헬퍼 함수)
def get_week_schedule(start_date, end_date):
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "and": [
                {
                    "property": "청소 일정",
                    "date": {
                        "on_or_after": start_date.date().isoformat()
                    }
                },
                {
                    "property": "청소 일정",
                    "date": {
                        "on_or_before": end_date.date().isoformat()
                    }
                }
            ]
        },
        sorts=[
            {
                "property": "청소 일정",
                "direction": "ascending"
            }
        ]
    )
    
    schedule = []
    for page in response["results"]:
        props = page["properties"]
        date_data = props.get("청소 일정", {}).get("date")
        if not date_data or not date_data.get("start"):
            continue
            
        try:
            date = datetime.fromisoformat(date_data["start"])
            people = props.get("예약인원", {}).get("number", 0)
            
            cleaner_items = props.get("청소 담당자", {}).get("multi_select", [])
            cleaner_names = [item.get("name", "") for item in cleaner_items if item.get("name")]
            cleaner_name = ", ".join(cleaner_names) if cleaner_names else "미지정"
            
            status = props.get("상태", {}).get("status", {}).get("name", "")
            
            schedule.append({
                "date": date_data["start"],
                "formatted_date": get_korean_date(date),
                "people": people,
                "cleaner": cleaner_name,
                "status": status,
                "page_id": page["id"],
                "completed": status == "완료"
            })
        except Exception as e:
            print(f"⚠️ 주간 일정 파싱 오류: {e}")
    
    return schedule

# 모든 청소 일정 가져오기
def get_all_cleaning_schedule(sort_by_date=True):
    response = notion.databases.query(
        database_id=DATABASE_ID,
        sorts=[
            {
                "property": "청소 일정",
                "direction": "ascending" if sort_by_date else "descending"
            }
        ]
    )
    
    schedule = []
    for page in response["results"]:
        props = page["properties"]
        date_data = props.get("청소 일정", {}).get("date")
        if not date_data or not date_data.get("start"):
            continue
            
        try:
            date = datetime.fromisoformat(date_data["start"])
            people = props.get("예약인원", {}).get("number", 0)
            
            cleaner_items = props.get("청소 담당자", {}).get("multi_select", [])
            cleaner_names = [item.get("name", "") for item in cleaner_items if item.get("name")]
            cleaner_name = ", ".join(cleaner_names) if cleaner_names else "미지정"
            
            status = props.get("상태", {}).get("status", {}).get("name", "")
            
            schedule.append({
                "date": date_data["start"],
                "formatted_date": get_korean_date(date),
                "people": people,
                "cleaner": cleaner_name,
                "status": status,
                "page_id": page["id"],
                "completed": status == "완료"
            })
        except Exception as e:
            print(f"⚠️ 청소 일정 파싱 오류: {e}")
    
    return schedule
