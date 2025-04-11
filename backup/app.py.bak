from flask import Flask, render_template, jsonify, request
from notion_fetcher import get_notion_calendar_data, get_unassigned_cleaning_tasks, get_weekly_schedule, get_cleaner_options, get_all_cleaning_schedule
from notion_updater import assign_cleaner_to_date
import os

app = Flask(__name__)

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
    return jsonify(get_unassigned_cleaning_tasks())

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
    
    success = assign_cleaner_to_date(cleaning_date, cleaner_name)
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
    app.run(host="0.0.0.0", port=port, debug=False)
