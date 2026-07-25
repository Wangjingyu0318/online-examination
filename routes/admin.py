from flask import Blueprint, request, jsonify, session
import sys
import os
import pandas as pd
import io
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import query, query_one, execute, execute_many

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ============================================================
# 工具函数：题目字段映射（数据库英文 → 前端中文）
# ============================================================
def question_to_frontend(q):
    """把数据库的题目转成前端需要的中文字段格式"""
    return {
        'id': q['id'],
        '题目编号': q['question_code'] or '',
        '题型': q['question_type'] or '',
        '题目分类': q['category'] or '',
        '知识点': q['knowledge_point'] or '',
        '难度': q['difficulty'],
        '题干': q['stem'] or '',
        '选项A': q['option_a'] or '',
        '选项B': q['option_b'] or '',
        '选项C': q['option_c'] or '',
        '选项D': q['option_d'] or '',
        '选项E': q['option_e'] or '',
        '选项F': q['option_f'] or '',
        '正确答案': q['correct_answer'] or '',
        '备选答案': q['alt_answer'] or '',
        '答案匹配方式': q['match_mode'] or '',
        '多选计分方式': q['multi_score_mode'] or '',
        '答案解析': q['explanation'] or '',
        '默认分值': q['default_score'],
        '是否用于考试': q['for_exam'] or '是',
        '是否用于练习': q['for_practice'] or '是',
        '标签': q['tags'] or '',
        '题目状态': q['status'] or '启用',
        '来源': q['source'] or '',
        '版本': float(q['version']) if q['version'] else 1.0,
        '备注': q['remark'] or ''
    }


def user_to_frontend(u):
    """把数据库的用户转成前端格式"""
    return {
        'id': u['id'],
        'name': u['name'] or '',
        'username': u['username'] or '',
        'unit': u['unit'] or '',
        'phone': u['phone'] or '',
        'idNumber': u['id_number'] or '',
        'status': u['status'] or '正常',
        'eligible': bool(u['eligible']),
        'role': u['role'] or 'student'
    }


# ============================================================
# 考试管理
# ============================================================
@admin_bp.route('/exams', methods=['GET'])
def get_exams():
    """获取所有考试列表"""
    exams = query("SELECT * FROM exams ORDER BY id DESC")
    return jsonify({'code': 0, 'data': exams})


@admin_bp.route('/exam/<int:exam_id>', methods=['GET'])
def get_exam(exam_id):
    """获取单个考试详情"""
    exam = query_one("SELECT * FROM exams WHERE id = %s", (exam_id,))
    if exam:
        return jsonify({'code': 0, 'data': exam})
    return jsonify({'code': 1, 'message': '考试不存在'})


@admin_bp.route('/exam', methods=['POST'])
def create_exam():
    """创建考试"""
    d = request.get_json()
    execute("""
        INSERT INTO exams (name, description, duration, total_score, question_count, start_time, end_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        d.get('name', ''),
        d.get('description', ''),
        d.get('duration', 60),
        d.get('total_score', 100),
        d.get('question_count', 50),
        d.get('start_time'),
        d.get('end_time'),
        d.get('status', '未开始')
    ))
    new_id = query_one("SELECT LAST_INSERT_ID() as id")['id']
    return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': new_id}})


@admin_bp.route('/exam/<int:exam_id>', methods=['PUT'])
def update_exam(exam_id):
    """更新考试"""
    d = request.get_json()
    rows = execute("""
        UPDATE exams SET name=%s, description=%s, duration=%s, total_score=%s, question_count=%s,
        start_time=%s, end_time=%s, status=%s WHERE id=%s
    """, (
        d.get('name', ''),
        d.get('description', ''),
        d.get('duration', 60),
        d.get('total_score', 100),
        d.get('question_count', 50),
        d.get('start_time'),
        d.get('end_time'),
        d.get('status', '未开始'),
        exam_id
    ))
    if rows:
        return jsonify({'code': 0, 'message': '更新成功'})
    return jsonify({'code': 1, 'message': '考试不存在'})


@admin_bp.route('/exam/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    """删除考试"""
    rows = execute("DELETE FROM exams WHERE id = %s", (exam_id,))
    if rows:
        return jsonify({'code': 0, 'message': '删除成功'})
    return jsonify({'code': 1, 'message': '考试不存在'})


# ============================================================
# 题库管理
# ============================================================
@admin_bp.route('/questions', methods=['GET'])
def get_questions():
    """获取所有题目列表（支持搜索和筛选）"""
    keyword = request.args.get('keyword', '').strip()
    question_type = request.args.get('type', '').strip()
    status = request.args.get('status', '').strip()

    sql = "SELECT * FROM questions WHERE 1=1"
    params = []

    if keyword:
        sql += " AND (question_code LIKE %s OR stem LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%'])

    if question_type:
        sql += " AND question_type = %s"
        params.append(question_type)

    if status:
        sql += " AND status = %s"
        params.append(status)

    sql += " ORDER BY id"

    questions = query(sql, params)
    result = [question_to_frontend(q) for q in questions]

    return jsonify({'code': 0, 'data': result})


@admin_bp.route('/questions/stats', methods=['GET'])
def get_questions_stats():
    """获取题库统计信息"""
    total = query_one("SELECT COUNT(*) as cnt FROM questions")['cnt']
    fill = query_one("SELECT COUNT(*) as cnt FROM questions WHERE question_type = '填空题'")['cnt']
    single = query_one("SELECT COUNT(*) as cnt FROM questions WHERE question_type = '单选题'")['cnt']
    multi = query_one("SELECT COUNT(*) as cnt FROM questions WHERE question_type = '多选题'")['cnt']
    judge = query_one("SELECT COUNT(*) as cnt FROM questions WHERE question_type = '判断题'")['cnt']

    return jsonify({
        'code': 0,
        'data': {
            'total': total,
            'fill': fill,
            'single': single,
            'multi': multi,
            'judge': judge
        }
    })


@admin_bp.route('/question/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """更新题目（编辑 / 启用禁用）"""
    d = request.get_json()

    # 前端传的是中文字段，转成英文
    update_fields = []
    params = []

    field_map = {
        '题目编号': 'question_code',
        '题型': 'question_type',
        '题目分类': 'category',
        '知识点': 'knowledge_point',
        '难度': 'difficulty',
        '题干': 'stem',
        '选项A': 'option_a',
        '选项B': 'option_b',
        '选项C': 'option_c',
        '选项D': 'option_d',
        '选项E': 'option_e',
        '选项F': 'option_f',
        '正确答案': 'correct_answer',
        '备选答案': 'alt_answer',
        '答案匹配方式': 'match_mode',
        '多选计分方式': 'multi_score_mode',
        '答案解析': 'explanation',
        '默认分值': 'default_score',
        '是否用于考试': 'for_exam',
        '是否用于练习': 'for_practice',
        '标签': 'tags',
        '题目状态': 'status',
        '备注': 'remark'
    }

    for cn_key, en_key in field_map.items():
        if cn_key in d:
            update_fields.append(f"{en_key} = %s")
            params.append(d[cn_key])

    if not update_fields:
        return jsonify({'code': 1, 'message': '没有可更新的字段'})

    params.append(question_id)
    sql = f"UPDATE questions SET {', '.join(update_fields)} WHERE id = %s"
    rows = execute(sql, params)

    if rows:
        return jsonify({'code': 0, 'message': '更新成功'})
    return jsonify({'code': 1, 'message': '题目不存在'})


@admin_bp.route('/question/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """删除题目"""
    rows = execute("DELETE FROM questions WHERE id = %s", (question_id,))
    if rows:
        return jsonify({'code': 0, 'message': '删除成功'})
    return jsonify({'code': 1, 'message': '题目不存在'})


# ============================================================
# CSV 上传和导入（题库）
# ============================================================
_upload_cache = []  # 全局缓存


@admin_bp.route('/questions/upload', methods=['POST'])
def upload_questions():
    """上传CSV文件，解析并返回预览数据"""
    if 'file' not in request.files:
        return jsonify({'code': 1, 'message': '未选择文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 1, 'message': '文件名为空'})

    if not file.filename.endswith('.csv'):
        return jsonify({'code': 1, 'message': '仅支持CSV格式'})

    try:
        content = file.read().decode('utf-8-sig')
        df = pd.read_csv(io.StringIO(content))

        required_cols = ['题目编号', '题型', '题干', '正确答案', '默认分值']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({'code': 1, 'message': f'CSV缺少必要列: {", ".join(missing)}'})

        type_counts = df['题型'].value_counts().to_dict()
        stats = {
            'total': len(df),
            'fill': type_counts.get('填空题', 0),
            'single': type_counts.get('单选题', 0),
            'multi': type_counts.get('多选题', 0),
            'judge': type_counts.get('判断题', 0)
        }

        rows = df.head(20).fillna('').to_dict('records')

        global _upload_cache
        _upload_cache = df.to_dict('records')

        return jsonify({
            'code': 0,
            'data': {
                'headers': df.columns.tolist(),
                'rows': rows,
                'stats': stats,
                'total': len(df)
            }
        })

    except Exception as e:
        return jsonify({'code': 1, 'message': f'解析失败: {str(e)}'})


@admin_bp.route('/questions/confirm', methods=['POST'])
def confirm_import():
    """确认导入预览的题目数据到数据库"""
    global _upload_cache
    questions_to_import = _upload_cache

    if not questions_to_import:
        return jsonify({'code': 1, 'message': '没有可导入的题目，请先上传CSV文件'})

    imported_count = 0
    values = []

    for q in questions_to_import:
        if not q.get('题目编号'):
            continue

        # 检查是否已存在（按题目编号去重）
        exists = query_one("SELECT id FROM questions WHERE question_code = %s", (q.get('题目编号'),))
        if exists:
            continue

        def clean(val):
            if pd.isna(val) if isinstance(val, float) else False:
                return ''
            return str(val) if val is not None else ''

        values.append((
            clean(q.get('题目编号')),
            clean(q.get('题型')),
            clean(q.get('题目分类')),
            clean(q.get('知识点')),
            int(q.get('难度', 3)) if q.get('难度') and not pd.isna(q.get('难度')) else 3,
            clean(q.get('题干')),
            clean(q.get('选项A')),
            clean(q.get('选项B')),
            clean(q.get('选项C')),
            clean(q.get('选项D')),
            clean(q.get('选项E')),
            clean(q.get('选项F')),
            clean(q.get('正确答案')),
            clean(q.get('备选答案')),
            clean(q.get('答案匹配方式')),
            clean(q.get('多选计分方式')),
            clean(q.get('答案解析')),
            int(q.get('默认分值', 2)) if q.get('默认分值') and not pd.isna(q.get('默认分值')) else 2,
            clean(q.get('是否用于考试')) or '是',
            clean(q.get('是否用于练习')) or '是',
            clean(q.get('标签')),
            clean(q.get('题目状态')) or '启用',
            clean(q.get('来源')),
            float(q.get('版本', 1.0)) if q.get('版本') and not pd.isna(q.get('版本')) else 1.0,
            clean(q.get('备注'))
        ))
        imported_count += 1

    if values:
        sql = """
            INSERT INTO questions (
                question_code, question_type, category, knowledge_point, difficulty,
                stem, option_a, option_b, option_c, option_d, option_e, option_f,
                correct_answer, alt_answer, match_mode, multi_score_mode,
                explanation, default_score, for_exam, for_practice, tags,
                status, source, version, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_many(sql, values)

    _upload_cache = []

    return jsonify({
        'code': 0,
        'message': f'成功导入 {imported_count} 道题目',
        'data': {'count': imported_count}
    })


# ============================================================
# 人员管理
# ============================================================
@admin_bp.route('/users', methods=['GET'])
def get_users():
    """获取所有人员列表（支持搜索和筛选）"""
    keyword = request.args.get('keyword', '').strip()
    unit = request.args.get('unit', '').strip()

    sql = "SELECT * FROM users WHERE role = 'student'"
    params = []

    if keyword:
        sql += " AND (name LIKE %s OR unit LIKE %s OR phone LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

    if unit:
        sql += " AND unit = %s"
        params.append(unit)

    sql += " ORDER BY id DESC"

    users = query(sql, params)
    result = [user_to_frontend(u) for u in users]

    return jsonify({'code': 0, 'data': result})


@admin_bp.route('/users/upload', methods=['POST'])
def upload_users():
    """上传人员CSV文件，解析并返回预览数据"""
    if 'file' not in request.files:
        return jsonify({'code': 1, 'message': '未选择文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 1, 'message': '文件名为空'})

    if not file.filename.endswith('.csv'):
        return jsonify({'code': 1, 'message': '仅支持CSV格式'})

    try:
        content = file.read().decode('utf-8-sig')
        df = pd.read_csv(io.StringIO(content))

        required_cols = ['姓名', '单位', '联系电话', '身份证号']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({'code': 1, 'message': f'CSV缺少必要列: {", ".join(missing)}'})

        rows = df.head(20).fillna('').to_dict('records')

        return jsonify({
            'code': 0,
            'data': {
                'headers': df.columns.tolist(),
                'rows': rows,
                'total': len(df),
                'users': df.fillna('').to_dict('records')
            }
        })

    except Exception as e:
        return jsonify({'code': 1, 'message': f'解析失败: {str(e)}'})


@admin_bp.route('/users/confirm', methods=['POST'])
def confirm_import_users():
    """确认导入人员到数据库"""
    data = request.get_json()
    if data is None or 'users' not in data:
        return jsonify({'code': 1, 'message': '缺少人员数据'})

    users_to_import = data.get('users', [])
    if not users_to_import:
        return jsonify({'code': 1, 'message': '没有可导入的人员'})

    imported_count = 0
    values = []

    for u in users_to_import:
        if not u.get('姓名'):
            continue

        id_number = u.get('身份证号', '')
        # 按身份证号去重
        exists = query_one("SELECT id FROM users WHERE id_number = %s", (id_number,))
        if exists:
            continue

        name = u.get('姓名', '')
        # 生成默认用户名（姓名拼音或简单处理，这里直接用姓名+序号太复杂，先用手机号当用户名）
        username = u.get('联系电话', '') or name

        values.append((
            username,
            '123456',  # 默认密码
            name,
            'student',
            u.get('单位', ''),
            u.get('联系电话', ''),
            id_number,
            '正常',
            1
        ))
        imported_count += 1

    if values:
        sql = """
            INSERT INTO users (username, password, name, role, unit, phone, id_number, status, eligible)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_many(sql, values)

    return jsonify({
        'code': 0,
        'message': f'成功导入 {imported_count} 名人员',
        'data': {'count': imported_count}
    })


# ============================================================
# 成绩管理
# ============================================================
@admin_bp.route('/scores', methods=['GET'])
def get_scores():
    """获取成绩列表（支持按考试筛选、关键词搜索）"""
    exam_id = request.args.get('exam_id', '').strip()
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()

    sql = "SELECT * FROM scores WHERE 1=1"
    params = []

    if exam_id:
        sql += " AND exam_id = %s"
        params.append(exam_id)

    if keyword:
        sql += " AND (user_name LIKE %s OR unit LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%'])

    if status:
        if status == '锁定':
            sql += " AND is_locked = 1"
        elif status == '未锁定':
            sql += " AND is_locked = 0"

    sql += " ORDER BY id DESC"

    scores = query(sql, params)

    # 转成前端兼容格式
    result = []
    for s in scores:
        result.append({
            'id': s['id'],
            'exam_id': s['exam_id'],
            'exam_name': s['exam_name'] or '',
            'user_id': s['user_id'],
            'name': s['user_name'] or '',
            'unit': s['unit'] or '',
            'score': s['score'],
            'total': s['total_score'],
            'correct_count': s['correct_count'],
            'wrong_count': s['wrong_count'],
            'submit_time': s['submit_time'].strftime('%Y-%m-%d %H:%M') if s['submit_time'] else '',
            'status': '锁定' if s['is_locked'] else '正常',
            'submitCount': 1 if s['submit_time'] else 0
        })

    return jsonify({'code': 0, 'data': result})


@admin_bp.route('/scores/stats', methods=['GET'])
def get_scores_stats():
    """获取成绩统计信息"""
    exam_id = request.args.get('exam_id', '').strip()

    sql = "SELECT COUNT(*) as total FROM scores"
    params = []
    if exam_id:
        sql += " WHERE exam_id = %s"
        params.append(exam_id)

    total = query_one(sql, params)['total']

    submitted_sql = "SELECT COUNT(*) as cnt FROM scores WHERE submit_time IS NOT NULL"
    if exam_id:
        submitted_sql += " AND exam_id = %s"
    submitted = query_one(submitted_sql, params)['cnt']

    unsubmitted = total - submitted

    # 平均分
    if submitted > 0:
        avg_sql = "SELECT AVG(score) as avg_score FROM scores WHERE submit_time IS NOT NULL"
        if exam_id:
            avg_sql += " AND exam_id = %s"
        avg_total = query_one(avg_sql, params)['avg_score']
        avg_total = round(float(avg_total), 1) if avg_total else 0
    else:
        avg_total = 0

    locked_sql = "SELECT COUNT(*) as cnt FROM scores WHERE is_locked = 1"
    if exam_id:
        locked_sql += " AND exam_id = %s"
    locked = query_one(locked_sql, params)['cnt']
    unlocked = submitted - locked

    return jsonify({
        'code': 0,
        'data': {
            'total': total,
            'submitted': submitted,
            'unsubmitted': unsubmitted,
            'avg_total': avg_total,
            'locked': locked,
            'unlocked': unlocked
        }
    })


@admin_bp.route('/scores/lock', methods=['POST'])
def lock_scores():
    """锁定全部成绩"""
    req_data = request.get_json() or {}
    exam_id = req_data.get('exam_id')

    if exam_id:
        rows = execute("UPDATE scores SET is_locked = 1 WHERE exam_id = %s AND submit_time IS NOT NULL", (exam_id,))
    else:
        rows = execute("UPDATE scores SET is_locked = 1 WHERE submit_time IS NOT NULL")

    return jsonify({
        'code': 0,
        'message': f'已锁定 {rows} 份成绩',
        'data': {'count': rows}
    })


@admin_bp.route('/score/<int:score_id>', methods=['PUT'])
def update_score(score_id):
    """更新单条成绩（人工调整分数等）"""
    d = request.get_json()

    update_fields = []
    params = []

    if 'score' in d:
        update_fields.append("score = %s")
        params.append(d['score'])
    if 'is_locked' in d:
        update_fields.append("is_locked = %s")
        params.append(1 if d['is_locked'] else 0)

    if not update_fields:
        return jsonify({'code': 1, 'message': '没有可更新的字段'})

    params.append(score_id)
    sql = f"UPDATE scores SET {', '.join(update_fields)} WHERE id = %s"
    rows = execute(sql, params)

    if rows:
        return jsonify({'code': 0, 'message': '更新成功'})
    return jsonify({'code': 1, 'message': '成绩记录不存在'})
