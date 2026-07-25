import pymysql
from pymysql.cursors import DictCursor

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'yy050318',
    'database': 'online_exam',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}


def get_db():
    """获取数据库连接"""
    conn = pymysql.connect(**DB_CONFIG)
    return conn


def query(sql, args=None):
    """执行查询，返回结果列表"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchall()
    finally:
        conn.close()


def query_one(sql, args=None):
    """执行查询，返回单条结果"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchone()
    finally:
        conn.close()


def execute(sql, args=None):
    """执行增删改，返回受影响行数"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            result = cursor.execute(sql, args)
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_many(sql, args_list):
    """批量执行"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            result = cursor.executemany(sql, args_list)
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
