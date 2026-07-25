from flask import Blueprint, request, jsonify, session
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import query_one

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    登录接口
    考生登录：提交 name, unit, phone, idNumber
    管理员登录：提交 username, password
    """
    data = request.get_json()

    # ============================================================
    # 考生登录
    # ============================================================
    if data.get('role') == 'student':
        name = data.get('name', '').strip()
        unit = data.get('unit', '').strip()
        phone = data.get('phone', '').strip()
        id_number = data.get('idNumber', '').strip()

        # 校验：四个字段都不能为空
        if not all([name, unit, phone, id_number]):
            return jsonify({'code': 1, 'message': '请完整填写所有字段'})

        # 从数据库查考生
        user = query_one("""
            SELECT * FROM users 
            WHERE name = %s AND unit = %s AND phone = %s AND id_number = %s 
            AND role = 'student' AND status = '正常'
        """, (name, unit, phone, id_number))

        if user and user['eligible']:
            # 登录成功，保存session
            session['user'] = {
                'id': user['id'],
                'role': 'student',
                'name': user['name'],
                'unit': user['unit'],
                'phone': user['phone'],
                'idNumber': user['id_number']
            }
            return jsonify({'code': 0, 'message': '登录成功', 'data': {'role': 'student'}})
        else:
            return jsonify({'code': 1, 'message': '考生信息校验失败，请检查填写内容'})

    # ============================================================
    # 管理员登录
    # ============================================================
    elif data.get('role') == 'admin':
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'code': 1, 'message': '请输入账号和密码'})

        # 从数据库查管理员
        user = query_one("""
            SELECT * FROM users 
            WHERE username = %s AND password = %s AND role = 'admin' AND status = '正常'
        """, (username, password))

        if user:
            session['user'] = {
                'id': user['id'],
                'role': 'admin',
                'username': user['username'],
                'name': user['name']
            }
            return jsonify({'code': 0, 'message': '登录成功', 'data': {'role': 'admin'}})
        else:
            return jsonify({'code': 1, 'message': '账号或密码错误'})

    else:
        return jsonify({'code': 1, 'message': '请选择登录身份'})
