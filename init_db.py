"""
数据库初始化脚本
执行：python init_db.py
功能：创建数据库、建表、导入现有题目数据
"""
import pymysql
import json
import os

# MySQL 连接配置（先不指定数据库）
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'yy050318',
    'charset': 'utf8mb4'
}

DB_NAME = 'online_exam'


def create_database():
    """创建数据库"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ 数据库 {DB_NAME} 创建成功")
    finally:
        conn.close()


def create_tables():
    """创建所有表"""
    conn = pymysql.connect(**MYSQL_CONFIG, database=DB_NAME)
    try:
        with conn.cursor() as cursor:
            # 题目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    question_code VARCHAR(50) COMMENT '题目编号',
                    question_type VARCHAR(20) COMMENT '题型',
                    category VARCHAR(100) COMMENT '题目分类',
                    knowledge_point VARCHAR(100) COMMENT '知识点',
                    difficulty INT DEFAULT 3 COMMENT '难度',
                    stem TEXT COMMENT '题干',
                    option_a TEXT COMMENT '选项A',
                    option_b TEXT COMMENT '选项B',
                    option_c TEXT COMMENT '选项C',
                    option_d TEXT COMMENT '选项D',
                    option_e TEXT COMMENT '选项E',
                    option_f TEXT COMMENT '选项F',
                    correct_answer TEXT COMMENT '正确答案',
                    alt_answer TEXT COMMENT '备选答案',
                    match_mode VARCHAR(100) COMMENT '答案匹配方式',
                    multi_score_mode VARCHAR(50) COMMENT '多选计分方式',
                    explanation TEXT COMMENT '答案解析',
                    default_score INT DEFAULT 2 COMMENT '默认分值',
                    for_exam VARCHAR(10) DEFAULT '是' COMMENT '是否用于考试',
                    for_practice VARCHAR(10) DEFAULT '是' COMMENT '是否用于练习',
                    tags VARCHAR(255) COMMENT '标签',
                    status VARCHAR(20) DEFAULT '启用' COMMENT '题目状态',
                    source VARCHAR(255) COMMENT '来源',
                    version DECIMAL(3,1) DEFAULT 1.0 COMMENT '版本',
                    remark TEXT COMMENT '备注',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_type (question_type),
                    INDEX idx_status (status),
                    INDEX idx_code (question_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目表'
            """)
            print("✅ questions 表创建成功")

            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE COMMENT '用户名',
                    password VARCHAR(100) DEFAULT '123456' COMMENT '密码',
                    name VARCHAR(50) COMMENT '姓名',
                    role VARCHAR(20) DEFAULT 'student' COMMENT '角色：admin/student',
                    unit VARCHAR(100) COMMENT '单位',
                    phone VARCHAR(20) COMMENT '电话',
                    id_number VARCHAR(20) COMMENT '身份证号',
                    status VARCHAR(20) DEFAULT '正常' COMMENT '状态',
                    eligible TINYINT DEFAULT 1 COMMENT '是否允许考试',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_role (role)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'
            """)
            print("✅ users 表创建成功")

            # 考试表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) COMMENT '考试名称',
                    description TEXT COMMENT '考试描述',
                    duration INT DEFAULT 60 COMMENT '考试时长（分钟）',
                    total_score INT DEFAULT 100 COMMENT '总分',
                    question_count INT DEFAULT 50 COMMENT '题目数量',
                    start_time DATETIME COMMENT '开始时间',
                    end_time DATETIME COMMENT '结束时间',
                    status VARCHAR(20) DEFAULT '未开始' COMMENT '状态',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考试表'
            """)
            print("✅ exams 表创建成功")

            # 成绩表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    exam_id INT COMMENT '考试ID',
                    exam_name VARCHAR(100) COMMENT '考试名称',
                    user_id INT COMMENT '用户ID',
                    user_name VARCHAR(50) COMMENT '考生姓名',
                    unit VARCHAR(100) COMMENT '单位',
                    score INT DEFAULT 0 COMMENT '得分',
                    total_score INT DEFAULT 100 COMMENT '总分',
                    correct_count INT DEFAULT 0 COMMENT '正确题数',
                    wrong_count INT DEFAULT 0 COMMENT '错误题数',
                    submit_time DATETIME COMMENT '提交时间',
                    is_locked TINYINT DEFAULT 0 COMMENT '是否锁定',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_exam (exam_id),
                    INDEX idx_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成绩表'
            """)
            print("✅ scores 表创建成功")

            # 练习记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS practice_records (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT COMMENT '用户ID',
                    user_name VARCHAR(50) COMMENT '用户名',
                    name VARCHAR(100) COMMENT '练习名称',
                    practice_type VARCHAR(20) COMMENT '练习类型',
                    category VARCHAR(50) COMMENT '分类',
                    time INT DEFAULT 0 COMMENT '用时（秒）',
                    total INT DEFAULT 0 COMMENT '总题数',
                    correct INT DEFAULT 0 COMMENT '正确数',
                    wrong INT DEFAULT 0 COMMENT '错误数',
                    score INT DEFAULT 0 COMMENT '得分',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='练习记录表'
            """)
            print("✅ practice_records 表创建成功")

            conn.commit()
    finally:
        conn.close()


def import_questions():
    """从 data.json 导入题目数据"""
    data_file = os.path.join(os.path.dirname(__file__), 'data.json')
    if not os.path.exists(data_file):
        print("⚠️  data.json 不存在，跳过题目导入")
        return

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = data.get('questions', [])
    if not questions:
        print("⚠️  data.json 中没有题目数据")
        return

    conn = pymysql.connect(**MYSQL_CONFIG, database=DB_NAME)
    try:
        with conn.cursor() as cursor:
            # 先清空
            cursor.execute("TRUNCATE TABLE questions")

            sql = """
                INSERT INTO questions (
                    question_code, question_type, category, knowledge_point, difficulty,
                    stem, option_a, option_b, option_c, option_d, option_e, option_f,
                    correct_answer, alt_answer, match_mode, multi_score_mode,
                    explanation, default_score, for_exam, for_practice, tags,
                    status, source, version, remark
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = []
            for q in questions:
                # 处理 NaN 值
                def clean(val):
                    if val is None or (isinstance(val, float) and val != val):
                        return ''
                    return str(val) if val is not None else ''

                values.append((
                    clean(q.get('题目编号')),
                    clean(q.get('题型')),
                    clean(q.get('题目分类')),
                    clean(q.get('知识点')),
                    int(q.get('难度', 3)),
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
                    int(q.get('默认分值', 2)),
                    clean(q.get('是否用于考试')),
                    clean(q.get('是否用于练习')),
                    clean(q.get('标签')),
                    clean(q.get('题目状态')),
                    clean(q.get('来源')),
                    float(q.get('版本', 1.0)),
                    clean(q.get('备注'))
                ))

            cursor.executemany(sql, values)
            conn.commit()
            print(f"✅ 成功导入 {len(questions)} 道题目")
    finally:
        conn.close()


def create_default_admin():
    """创建默认管理员和测试用户"""
    conn = pymysql.connect(**MYSQL_CONFIG, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            # 检查是否已有管理员
            cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'")
            result = cursor.fetchone()
            if result['cnt'] > 0:
                print("ℹ️  管理员已存在，跳过创建")
            else:
                cursor.execute("""
                    INSERT INTO users (username, password, name, role, unit, status, eligible)
                    VALUES ('admin', 'admin123', '系统管理员', 'admin', '系统', '正常', 1)
                """)
                print("✅ 默认管理员创建成功（账号：admin / 密码：admin123）")

            # 创建测试考生
            cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE username = 'student'")
            result = cursor.fetchone()
            if result['cnt'] == 0:
                cursor.execute("""
                    INSERT INTO users (username, password, name, role, unit, phone, id_number, status, eligible)
                    VALUES ('student', '123456', '测试考生', 'student', '某省广播电视技术中心', '13800138000', '110101199001011234', '正常', 1)
                """)
                print("✅ 测试考生创建成功（账号：student / 密码：123456）")

            conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)

    create_database()
    create_tables()
    import_questions()
    create_default_admin()

    print("=" * 50)
    print("🎉 数据库初始化完成！")
    print("=" * 50)
