from flask import Blueprint, request, jsonify, session
import json
import os
import pandas as pd

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================
# 数据存储：用JSON文件模拟数据库
# ============================================================
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')


def load_data():
    """读取JSON数据"""
    if not os.path.exists(DATA_FILE):
        return {'exams': [], 'questions': [], 'users': [], 'scores': []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 兼容旧数据，补充缺失字段
    if 'scores' not in data:
        data['scores'] = []
    if 'practice_records' not in data:
        data['practice_records'] = []

    # 统一清理 NaN 值（转为空字符串），避免前端JSON.parse失败
    def clean_nan(obj):
        if isinstance(obj, dict):
            return {k: clean_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_nan(item) for item in obj]
        elif isinstance(obj, float) and pd.isna(obj):
            return ''
        return obj

    return clean_nan(data)


def save_data(data):
    """保存JSON数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 考试管理
# ============================================================
@admin_bp.route('/exams', methods=['GET'])
def get_exams():
    """获取所有考试列表"""
    data = load_data()
    return jsonify({'code': 0, 'data': data.get('exams', [])})


@admin_bp.route('/exam/<int:exam_id>', methods=['GET'])
def get_exam(exam_id):
    """获取单个考试详情"""
    data = load_data()
    for exam in data.get('exams', []):
        if exam.get('id') == exam_id:
            return jsonify({'code': 0, 'data': exam})
    return jsonify({'code': 1, 'message': '考试不存在'})


@admin_bp.route('/exam', methods=['POST'])
def create_exam():
    """创建考试"""
    exam_data = request.get_json()
    data = load_data()
    exams = data.get('exams', [])

    # 生成ID
    max_id = max([e.get('id', 0) for e in exams]) if exams else 0
    exam_data['id'] = max_id + 1
    exams.append(exam_data)
    data['exams'] = exams
    save_data(data)
    return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': exam_data['id']}})


@admin_bp.route('/exam/<int:exam_id>', methods=['PUT'])
def update_exam(exam_id):
    """更新考试"""
    new_data = request.get_json()
    data = load_data()
    exams = data.get('exams', [])

    for i, exam in enumerate(exams):
        if exam.get('id') == exam_id:
            new_data['id'] = exam_id
            exams[i] = new_data
            data['exams'] = exams
            save_data(data)
            return jsonify({'code': 0, 'message': '更新成功'})

    return jsonify({'code': 1, 'message': '考试不存在'})


@admin_bp.route('/exam/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    """删除考试"""
    data = load_data()
    exams = data.get('exams', [])
    new_exams = [e for e in exams if e.get('id') != exam_id]

    if len(new_exams) == len(exams):
        return jsonify({'code': 1, 'message': '考试不存在'})

    data['exams'] = new_exams
    save_data(data)
    return jsonify({'code': 0, 'message': '删除成功'})

# ============================================================
# 题库管理
# ============================================================
@admin_bp.route('/questions', methods=['GET'])
def get_questions():
    """获取所有题目列表（支持搜索和筛选）"""
    data = load_data()
    questions = data.get('questions', [])

    # 获取查询参数
    keyword = request.args.get('keyword', '').strip()
    question_type = request.args.get('type', '').strip()
    status = request.args.get('status', '').strip()

    # 关键词搜索（题目编号 + 题干）
    if keyword:
        questions = [q for q in questions if keyword in str(q.get('题目编号', '')) or keyword in str(q.get('题干', ''))]

    # 题型筛选
    if question_type:
        questions = [q for q in questions if str(q.get('题型', '')) == question_type]

    # 状态筛选
    if status:
        questions = [q for q in questions if str(q.get('题目状态', '')) == status]

    # 处理 NaN 值，转为空字符串（否则前端JSON.parse会失败）
    def clean_nan(obj):
        if isinstance(obj, float) and pd.isna(obj):
            return ''
        return obj

    cleaned = []
    for q in questions:
        cleaned_q = {k: clean_nan(v) for k, v in q.items()}
        cleaned.append(cleaned_q)

    return jsonify({'code': 0, 'data': cleaned})


@admin_bp.route('/questions/stats', methods=['GET'])
def get_questions_stats():
    """获取题库统计信息"""
    data = load_data()
    questions = data.get('questions', [])

    total = len(questions)
    fill_count = len([q for q in questions if q.get('题型') == '填空题'])
    single_count = len([q for q in questions if q.get('题型') == '单选题'])
    multi_count = len([q for q in questions if q.get('题型') == '多选题'])
    judge_count = len([q for q in questions if q.get('题型') == '判断题'])

    return jsonify({
        'code': 0,
        'data': {
            'total': total,
            'fill': fill_count,
            'single': single_count,
            'multi': multi_count,
            'judge': judge_count
        }
    })


@admin_bp.route('/question/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """更新题目（编辑 / 启用禁用）"""
    new_data = request.get_json()
    data = load_data()
    questions = data.get('questions', [])

    for i, q in enumerate(questions):
        # 使用题目编号作为ID（你的CSV中"题目编号"字段是唯一标识）
        if q.get('题目编号') == f'Q{question_id:03d}' or q.get('id') == question_id:
            # 保留原有id字段，更新其他字段
            if 'id' in q:
                new_data['id'] = q['id']
            questions[i] = new_data
            data['questions'] = questions
            save_data(data)
            return jsonify({'code': 0, 'message': '更新成功'})

    return jsonify({'code': 1, 'message': '题目不存在'})


@admin_bp.route('/question/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """删除题目"""
    data = load_data()
    questions = data.get('questions', [])
    new_questions = [q for q in questions if q.get('id') != question_id and q.get('题目编号') != f'Q{question_id:03d}']

    if len(new_questions) == len(questions):
        return jsonify({'code': 1, 'message': '题目不存在'})

    data['questions'] = new_questions
    save_data(data)
    return jsonify({'code': 0, 'message': '删除成功'})

# ============================================================
# CSV 上传和导入
# ============================================================
@admin_bp.route('/questions/upload', methods=['POST'])
def upload_questions():
    """上传CSV文件，解析并返回预览数据"""
    import pandas as pd
    import io

    if 'file' not in request.files:
        return jsonify({'code': 1, 'message': '未选择文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 1, 'message': '文件名为空'})

    if not file.filename.endswith('.csv'):
        return jsonify({'code': 1, 'message': '仅支持CSV格式'})

    try:
        # 读取CSV
        content = file.read().decode('utf-8-sig')
        df = pd.read_csv(io.StringIO(content))

        # 检查必要列
        required_cols = ['题目编号', '题型', '题干', '正确答案', '默认分值']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({'code': 1, 'message': f'CSV缺少必要列: {", ".join(missing)}'})

        # 统计各题型数量
        type_counts = df['题型'].value_counts().to_dict()
        stats = {
            'total': len(df),
            'fill': type_counts.get('填空题', 0),
            'single': type_counts.get('单选题', 0),
            'multi': type_counts.get('多选题', 0),
            'judge': type_counts.get('判断题', 0)
        }

        # 转为字典列表（只取前20条预览）
        rows = df.head(20).fillna('').to_dict('records')

        # 全部数据暂存在内存中（用于确认导入）
        # 这里先用一个全局变量存储，正式环境建议用缓存或临时文件
        import hashlib
        import time
        import pickle
        import base64

        # 将整个df序列化后存储（简单处理）
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


# 全局缓存（仅用于演示，正式环境应使用Redis或文件缓存）
_upload_cache = []


@admin_bp.route('/questions/confirm', methods=['POST'])
def confirm_import():
    """确认导入预览的题目数据（从缓存读取完整数据）"""
    global _upload_cache

    questions_to_import = _upload_cache

    if not questions_to_import:
        return jsonify({'code': 1, 'message': '没有可导入的题目，请先上传CSV文件'})

    # 读取现有数据
    full_data = load_data()
    existing = full_data.get('questions', [])

    # 获取现有最大ID
    max_id = 0
    for q in existing:
        qid = q.get('id', 0)
        if qid > max_id:
            max_id = qid

    # 为每条题目分配新ID并补充默认字段
    imported_count = 0
    for q in questions_to_import:
        # 跳过空行
        if not q.get('题目编号'):
            continue

        # 检查是否已存在（按题目编号去重）
        exists = False
        for e in existing:
            if e.get('题目编号') == q.get('题目编号'):
                exists = True
                break

        if exists:
            continue

        max_id += 1
        q['id'] = max_id

        # 补充默认值
        if '默认分值' not in q or pd.isna(q.get('默认分值')):
            q['默认分值'] = 2
        if '是否用于考试' not in q or pd.isna(q.get('是否用于考试')):
            q['是否用于考试'] = '是'
        if '是否用于练习' not in q or pd.isna(q.get('是否用于练习')):
            q['是否用于练习'] = '是'
        if '题目状态' not in q or pd.isna(q.get('题目状态')):
            q['题目状态'] = '启用'
        if '知识点' not in q or pd.isna(q.get('知识点')):
            q['知识点'] = ''
        if '标签' not in q or pd.isna(q.get('标签')):
            q['标签'] = ''
        if '答案解析' not in q or pd.isna(q.get('答案解析')):
            q['答案解析'] = ''

        existing.append(q)
        imported_count += 1

    full_data['questions'] = existing
    save_data(full_data)

    # 清空缓存
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
    data = load_data()
    users = data.get('users', [])

    keyword = request.args.get('keyword', '').strip()
    unit = request.args.get('unit', '').strip()

    if keyword:
        users = [u for u in users if keyword in u.get('name', '') or keyword in u.get('unit', '') or keyword in u.get('phone', '')]

    if unit:
        users = [u for u in users if u.get('unit', '') == unit]

    return jsonify({'code': 0, 'data': users})


@admin_bp.route('/users/upload', methods=['POST'])
def upload_users():
    """上传人员CSV文件，解析并返回预览数据"""
    import pandas as pd
    import io

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
    """确认导入人员"""
    data = request.get_json()
    if data is None or 'users' not in data:
        return jsonify({'code': 1, 'message': '缺少人员数据'})

    users_to_import = data.get('users', [])
    if not users_to_import:
        return jsonify({'code': 1, 'message': '没有可导入的人员'})

    full_data = load_data()
    existing = full_data.get('users', [])

    max_id = 0
    for u in existing:
        uid = u.get('id', 0)
        if uid > max_id:
            max_id = uid

    imported_count = 0
    for u in users_to_import:
        if not u.get('姓名'):
            continue

        # 按身份证号去重
        exists = False
        for e in existing:
            if e.get('idNumber') == u.get('身份证号'):
                exists = True
                break

        if exists:
            continue

        max_id += 1
        u['id'] = max_id
        u['name'] = u.pop('姓名', '')
        u['unit'] = u.pop('单位', '')
        u['phone'] = u.pop('联系电话', '')
        u['idNumber'] = u.pop('身份证号', '')
        u['status'] = '正常'
        u['eligible'] = True

        existing.append(u)
        imported_count += 1

    full_data['users'] = existing
    save_data(full_data)

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
    data = load_data()
    scores = data.get('scores', [])

    exam_id = request.args.get('exam_id', '').strip()
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()

    if exam_id:
        scores = [s for s in scores if str(s.get('exam_id', '')) == exam_id]

    if keyword:
        scores = [s for s in scores if keyword in str(s.get('name', '')) or keyword in str(s.get('unit', ''))]

    if status:
        scores = [s for s in scores if s.get('status', '') == status]

    return jsonify({'code': 0, 'data': scores})


@admin_bp.route('/scores/stats', methods=['GET'])
def get_scores_stats():
    """获取成绩统计信息"""
    data = load_data()
    scores = data.get('scores', [])
    exam_id = request.args.get('exam_id', '').strip()

    if exam_id:
        scores = [s for s in scores if str(s.get('exam_id', '')) == exam_id]

    total = len(scores)
    submitted = len([s for s in scores if s.get('submitCount', 0) > 0])
    unsubmitted = total - submitted

    # 平均分
    if submitted > 0:
        avg_total = sum(s.get('total', 0) for s in scores if s.get('submitCount', 0) > 0) / submitted
        avg_total = round(avg_total, 1)
    else:
        avg_total = 0

    locked = len([s for s in scores if s.get('status') == '锁定'])
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
    """锁定全部成绩（锁定后考生无法再次提交）"""
    req_data = request.get_json() or {}
    exam_id = req_data.get('exam_id')

    data = load_data()
    scores = data.get('scores', [])

    count = 0
    for s in scores:
        if exam_id is not None:
            if str(s.get('exam_id', '')) == str(exam_id):
                s['status'] = '锁定'
                count += 1
        else:
            if s.get('submitCount', 0) > 0:
                s['status'] = '锁定'
                count += 1

    data['scores'] = scores
    save_data(data)

    return jsonify({
        'code': 0,
        'message': f'已锁定 {count} 份成绩',
        'data': {'count': count}
    })


@admin_bp.route('/score/<int:score_id>', methods=['PUT'])
def update_score(score_id):
    """更新单条成绩（人工调整分数等）"""
    new_data = request.get_json()
    data = load_data()
    scores = data.get('scores', [])

    for i, s in enumerate(scores):
        if s.get('id') == score_id:
            new_data['id'] = score_id
            scores[i] = {**s, **new_data}
            data['scores'] = scores
            save_data(data)
            return jsonify({'code': 0, 'message': '更新成功'})

    return jsonify({'code': 1, 'message': '成绩记录不存在'})