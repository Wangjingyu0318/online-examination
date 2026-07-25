from flask import Blueprint, request, jsonify, session
import json
import os
from datetime import datetime

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

# 数据文件路径（与admin共用）
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')


def load_data():
    """读取JSON数据"""
    if not os.path.exists(DATA_FILE):
        return {'exams': [], 'questions': [], 'users': [], 'scores': [], 'practice_records': []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 兼容旧数据，补充缺失字段
    if 'practice_records' not in data:
        data['practice_records'] = []
    if 'scores' not in data:
        data['scores'] = []

    return data


def save_data(data):
    """保存JSON数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 练习记录
# ============================================================
@student_bp.route('/practice-records', methods=['GET'])
def get_practice_records():
    """获取当前用户的练习记录列表"""
    # 从session获取当前用户
    user = session.get('user')
    if not user:
        return jsonify({'code': 1, 'message': '未登录'})

    user_id = user.get('id')
    data = load_data()
    records = data.get('practice_records', [])

    # 只返回当前用户的记录，按时间倒序
    user_records = [r for r in records if r.get('user_id') == user_id]
    user_records.sort(key=lambda x: x.get('time', ''), reverse=True)

    return jsonify({'code': 0, 'data': user_records})


@student_bp.route('/practice-record', methods=['POST'])
def add_practice_record():
    """新增一条练习记录（练习提交后调用）"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 1, 'message': '未登录'})

    record_data = request.get_json()
    data = load_data()
    records = data.get('practice_records', [])

    # 生成ID
    max_id = max([r.get('id', 0) for r in records]) if records else 0

    # 统计该用户对这套练习的第几次
    same_name = [r for r in records if r.get('user_id') == user.get('id') and r.get('name') == record_data.get('name')]
    count = len(same_name) + 1

    new_record = {
        'id': max_id + 1,
        'user_id': user.get('id'),
        'user_name': user.get('name', ''),
        'name': record_data.get('name', '随机练习'),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'count': count,
        'score': record_data.get('score', 0),
        'wrong': record_data.get('wrong', 0),
        'total': record_data.get('total', 0),
        'correct': record_data.get('correct', 0)
    }

    records.append(new_record)
    data['practice_records'] = records
    save_data(data)

    return jsonify({
        'code': 0,
        'message': '记录已保存',
        'data': {'id': new_record['id']}
    })


@student_bp.route('/practice-record/<int:record_id>', methods=['GET'])
def get_practice_record_detail(record_id):
    """获取单条练习记录详情"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 1, 'message': '未登录'})

    data = load_data()
    records = data.get('practice_records', [])

    for r in records:
        if r.get('id') == record_id and r.get('user_id') == user.get('id'):
            return jsonify({'code': 0, 'data': r})

    return jsonify({'code': 1, 'message': '记录不存在'})
