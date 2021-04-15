from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(10), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.String(2), nullable=False)

    def __init__(self, user_id, password, user_type):
        self.user_id = user_id
        self.password = generate_password_hash(password)
        self.user_type = user_type

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.user_id

    def __repr__(self):
        return '<User %r>' % self.user_id

    def check_hash_password(self, raw_password):  # 这里的参数是hash过的参数以及原始传入hash
        is_valid = check_password_hash(self.password, raw_password)
        return is_valid  # 得到验证的密码　　


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stu_id = db.Column(db.String(10), nullable=False, unique=True)
    stu_name = db.Column(db.String(20), nullable=False)
    stu_class = db.Column(db.String(30), nullable=False)
    stu_profession_id = db.Column(db.String(4), nullable=False)
    # 方便预测使用
    need_amount = db.Column(db.Integer, nullable=True, server_default="0")
    already_amount = db.Column(db.Integer, nullable=True, server_default="0")
    fail_amount = db.Column(db.Integer, nullable=True, server_default="0")

    def __init__(self, stu_id, stu_name, stu_class, stu_profession_id):
        self.stu_id = stu_id
        self.stu_name = stu_name
        self.stu_class = stu_class
        self.stu_profession_id = stu_profession_id

    def __repr__(self):
        return '<Student %r>' % self.stu_id


class Profession(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profession_id = db.Column(db.String(10), nullable=False, unique=True)
    profession_name = db.Column(db.String(20), nullable=False)

    def __init__(self, profession_id, profession_name):
        self.profession_id = profession_id
        self.profession_name = profession_name

    def __repr__(self):
        return '<Profession %r>' % self.profession_id


# 最终达成度
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stu_id = db.Column(db.String(10), nullable=False, unique=True)
    stu_result = db.Column(db.DECIMAL(6, 2))
    stu_state = db.Column(db.String(10), server_default="未收到")

    def __init__(self, stu_id, stu_result, stu_state):
        self.stu_id = stu_id
        self.stu_result = stu_result
        self.stu_state = stu_state

    def __repr__(self):
        return '<Result %r>' % self.stu_id


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.String(10), nullable=False, unique=True)
    teacher_name = db.Column(db.String(20), nullable=False)
    teacher_profession_id = db.Column(db.String(4), nullable=False)

    def __init__(self, teacher_id, teacher_name, teacher_profession_id):
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.teacher_profession_id = teacher_profession_id

    def __repr__(self):
        return '<Teacher %r>' % self.teacher_id


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.String(10), nullable=False, unique=True)
    course_name = db.Column(db.String(20), nullable=False, unique=True)
    course_credit = db.Column(db.DECIMAL(6, 2), nullable=False)
    course_time = db.Column(db.Integer, nullable=False)
    charge_teacher_id = db.Column(db.String(10), nullable=False)

    def __init__(self, course_id, course_name, course_credit, course_time, charge_teacher_id):
        self.course_id = course_id
        self.course_name = course_name
        self.course_credit = course_credit
        self.course_time = course_time
        self.charge_teacher_id = charge_teacher_id

    def __repr__(self):
        return '<Course %r>' % self.course_id


class Support(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    point_id = db.Column(db.String(10), nullable=False)
    course_id = db.Column(db.String(10), nullable=False)
    course_weight = db.Column(db.DECIMAL(6, 2), nullable=False)

    def __init__(self, point_id, course_id, course_weight):
        self.point_id = point_id
        self.course_id = course_id
        self.course_weight = course_weight

    def __repr__(self):
        return '<Support %r>' % self.point_id


class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    point_id = db.Column(db.String(10), nullable=False)
    point_content = db.Column(db.Text, nullable=False)
    requirement_id = db.Column(db.String(10), nullable=False)

    def __init__(self, point_id, point_content, requirement_id):
        self.point_id = point_id
        self.point_content = point_content
        self.requirement_id = requirement_id

    def __repr__(self):
        return '<Point %r>' % self.point_id


class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    requirement_id = db.Column(db.String(10), nullable=False)
    requirement_content = db.Column(db.Text, nullable=False)

    def __init__(self, requirement_id, requirement_content):
        self.requirement_id = requirement_id
        self.requirement_content = requirement_content

    def __repr__(self):
        return '<Requirement %r>' % self.requirement_id


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stu_id = db.Column(db.String(10), nullable=False)
    course_id = db.Column(db.String(10), nullable=False)
    point_id = db.Column(db.String(10), nullable=False)
    remark = db.Column(db.DECIMAL(6, 2), nullable=False)

    def __init__(self, stu_id, course_id, point_id, remark):
        self.stu_id = stu_id
        self.course_id = course_id
        self.point_id = point_id
        self.remark = remark

    def __repr__(self):
        return '<Grade %r>' % self.stu_id


# 各指标点达成度
class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stu_id = db.Column(db.String(10), nullable=False)
    point_id = db.Column(db.String(10), nullable=False)
    evaluation_remark = db.Column(db.DECIMAL(6, 2))

    def __init__(self, stu_id, point_id, evaluation_remark):
        self.stu_id = stu_id
        self.point_id = point_id
        self.evaluation_remark = evaluation_remark

    def __repr__(self):
        return '<Evaluation %r>' % self.stu_id


class Tutor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.String(10), nullable=False)
    class_name = db.Column(db.String(30), nullable=False)
    course_id = db.Column(db.String(10), nullable=False)
    course_state = db.Column(db.String(10), server_default="数据未提交")
    course_remark = db.Column(db.Text, nullable=True)

    def __init__(self, teacher_id, class_name, course_id):
        self.teacher_id = teacher_id
        self.class_name = class_name
        self.course_id = course_id

    def __repr__(self):
        return '<Tutor %r>' % self.teacher_id
