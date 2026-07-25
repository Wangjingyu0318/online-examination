from flask import Blueprint, request, jsonify, session
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import query, query_one, execute
from datetime import datetime

student_bp = Blueprint('student', __name__, url_prefix='/api/student')


# ============================================================
# 练习记录
# ============================================================
@student_bp.route('/practice-records', methods=['GET'])
def get_practice_records():
    """获取当前用户的练习记录列表"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 1, 'message': '未登录'})

    user_id = user.get('id')
    records = query("""
        SELECT id, user_id, user_name, name, practice_type, category, time, total, correct, wrong, score, created_at
        FROM practice_records
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    # 转换字段名兼容前端
    result = []
    for r in records:
        result.append({
            'id': r['id'],
            'user_id': r['user_id'],
            'user_name': r['user_name'],
            'name': r['name'],
            'time': r['created_at'].strftime('%Y-%m-%d %H:%M') if r['created_at'] else '',
            'score': r['score'],
            'wrong': r['wrong'],
            'total': r['total'],
            'correct': r['correct']
        })

    return jsonify({'code': 0, 'data': result})


@student_bp.route('/practice-record', methods=['POST'])
def add_practice_record():
    """新增一条练习记录（练习提交后调用）"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 1, 'message': '未登录'})

    record_data = request.get_json()

    execute("""
        INSERT INTO practice_records (user_id, user_name, name, practice_type, category, time, total, correct, wrong, score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user.get('id'),
        user.get('name', ''),
        record_data.get('name', '随机练习'),
        record_data.get('practice_type', ''),
        record_data.get('category', ''),
        record_data.get('time', 0),
        record_data.get('total', 0),
        record_data.get('correct', 0),
        record_data.get('wrong', 0),
        record_data.get('score', 0)
    ))

    # 获取刚插入的ID
    new_id = query_one("SELECT LAST_INSERT_ID() as id")['id']

    return jsonify({
        'code': 0,
        'message': '记录已保存',
        'data': {'id': new_id}
    })


@student_bp.route('/practice-record/<int:record_id>', methods=['GET'])
def get_practice_record_detail(record_id):
    """获取单条练习记录详情"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 1, 'message': '未登录'})

    r = query_one("""
        SELECT * FROM practice_records WHERE id = %s AND user_id = %s
    """, (record_id, user.get('id')))

    if not r:
        return jsonify({'code': 1, 'message': '记录不存在'})

    result = {
        'id': r['id'],
        'user_id': r['user_id'],
        'user_name': r['user_name'],
        'name': r['name'],
        'time': r['created_at'].strftime('%Y-%m-%d %H:%M') if r['created_at'] else '',
        'score': r['score'],
        'wrong': r['wrong'],
        'total': r['total'],
        'correct': r['correct']
    }

    return jsonify({'code': 0, 'data': result})
