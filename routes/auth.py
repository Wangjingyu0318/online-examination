from flask import Blueprint, request, jsonify, session

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

        # 校验默认考生信息
        if (name == 'student' and
            unit == 'company' and
            phone == '111111' and
            id_number == '123456'):
            # 登录成功，保存session
            session['user'] = {
                'role': 'student',
                'name': name,
                'unit': unit,
                'phone': phone,
                'idNumber': id_number
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

        if username == '111111' and password == '123456':
            session['user'] = {
                'role': 'admin',
                'username': username
            }
            return jsonify({'code': 0, 'message': '登录成功', 'data': {'role': 'admin'}})
        else:
            return jsonify({'code': 1, 'message': '账号或密码错误'})

    else:
        return jsonify({'code': 1, 'message': '请选择登录身份'})