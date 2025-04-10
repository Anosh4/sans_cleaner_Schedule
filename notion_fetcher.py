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
        if cleaner_property.get("type") == "select":
            options = cleaner_property.get("select", {}).get("options", [])
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
            
            cleaner = props.get("청소 담당자", {}).get("select", {})
            cleaner_name = cleaner.get("name", "미지정") if cleaner else "미지정"
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
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "상태",
            "status": {
                "equals": "청소 배정 필요"
            }
        },
        sorts=[
            {
                "property": "청소 일정",
                "direction": "ascending"
            }
        ]
    )
    
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
            
            tasks.append({
                "date": date_str,
                "formatted_date": get_korean_date(date),
                "people": people,
                "page_id": page["id"]
            })
        except Exception as e:
            print(f"⚠️ 미배정 일정 파싱 오류: {e}")
    
    return tasks

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
            cleaner = props.get("청소 담당자", {}).get("select", {})
            cleaner_name = cleaner.get("name", "미지정") if cleaner else "미지정"
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
            cleaner = props.get("청소 담당자", {}).get("select", {})
            cleaner_name = cleaner.get("name", "미지정") if cleaner else "미지정"
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
