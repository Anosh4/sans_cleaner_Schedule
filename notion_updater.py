from notion_client import Client
import os

# Notion API Token과 Database ID를 환경 변수에서 가져오거나 기본값 사용
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "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")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "1b66b54dd16f8051a7beeed441be3c17")

notion = Client(auth=NOTION_TOKEN)

def assign_cleaner_to_date(cleaning_date: str, cleaner_name: str):
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

    notion.pages.update(
        page_id=page_id,
        properties={
            "청소 담당자": {"select": {"name": cleaner_name}},
            "상태": {"status": {"name": "예약됨"}}
        }
    )
    print(f"✅ {cleaning_date}에 {cleaner_name} 님 배정 완료")
    return True
