from flask import Flask, render_template, jsonify, request
from notion_fetcher import get_notion_calendar_data, get_unassigned_cleaning_tasks, get_weekly_schedule, get_cleaner_options, get_all_cleaning_schedule
from notion_updater import assign_cleaner_to_date, DATABASE_ID, notion
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS 헤더 추가
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# 메인 페이지 보여주기
@app.route('/')
def dashboard():
    return render_template('dashboard.html')  # 'templates/' 폴더 안의 dashboard.html 파일을 불러옴

# 캘린더 데이터 API
@app.route('/api/calendar')
def calendar_data():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify(get_notion_calendar_data(year, month))

# 미배정 청소 일정 API
@app.route('/api/unassigned')
def unassigned_tasks():
    logger.debug("미배정 청소 일정 API 호출됨")
    tasks = get_unassigned_cleaning_tasks()
    logger.debug(f"미배정 청소 일정 개수: {len(tasks)}")
    logger.debug(f"API 응답 데이터: {tasks}")
    return jsonify(tasks)

# 주간 일정 API
@app.route('/api/weekly')
def weekly_schedule():
    return jsonify(get_weekly_schedule())

# 청소 담당자 배정 API
@app.route('/api/assign', methods=['POST'])
def assign_cleaner():
    data = request.json
    cleaning_date = data.get('date')
    cleaner_name = data.get('name')
    
    if not cleaning_date or not cleaner_name:
        return jsonify({"success": False, "message": "날짜와 이름이 필요합니다"}), 400
    
    # 배정 시도
    success = assign_cleaner_to_date(cleaning_date, cleaner_name)
    
    if success:
        # 배정 후 상태 확인
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "청소 일정",
                "date": {
                    "equals": cleaning_date
                }
            }
        )
        
        if response["results"]:
            page = response["results"][0]
            people = page["properties"].get("예약인원", {}).get("number", 0)
            status = page["properties"].get("상태", {}).get("status", {}).get("name", "")
            cleaner_items = page["properties"].get("청소 담당자", {}).get("multi_select", [])
            cleaner_count = len(cleaner_items) if cleaner_items else 0
            
            print(f"DEBUG - 배정 후: 날짜: {cleaning_date}, 인원: {people}, 담당자 수: {cleaner_count}, 상태: {status}")
            
            # 7명 이상이고 '청소 배정 필요' 상태인 경우 - 부분 배정 알림
            if people >= 7 and status == "청소 배정 필요":
                cleaner_names = [item.get("name", "") for item in cleaner_items]
                current_assigned = ", ".join(cleaner_names)
                return jsonify({
                    "success": True, 
                    "partial": True, 
                    "message": f"담당자가 1명 배정되었습니다({current_assigned}). 예약인원이 7명 이상이므로 추가 담당자 배정이 필요합니다."
                })
    
    return jsonify({"success": success})

# 청소 담당자 옵션 API
@app.route('/api/cleaners')
def cleaner_options():
    return jsonify(get_cleaner_options())

# 전체 청소 일정 API
@app.route('/api/all-schedules')
def all_schedules():
    sort_by_date = request.args.get('sort', 'asc') != 'desc'
    return jsonify(get_all_cleaning_schedule(sort_by_date))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"서버 시작: 포트 {port}, 디버그 모드 활성화")
    app.run(host="0.0.0.0", port=port, debug=True)
