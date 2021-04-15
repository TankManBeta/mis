from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, send_from_directory
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import xlrd
from flask_sqlalchemy import SQLAlchemy
import settings
import decimal
from decimal import *
import os

app = Flask(__name__)
app.config.from_object(settings)
db = SQLAlchemy(app)
from models import *

login_manager = LoginManager()
# 绑定登录视图的路由
login_manager.login_view = 'login'
login_manager.login_message = '请先登陆!'
login_manager.session_protection = 'strong'
app.config['SECRET_KEY'] = '123456'
login_manager.init_app(app)

FILE_FOLDER = os.path.join(app.root_path, "upload_file")


@login_manager.user_loader
def user_loader(user_id):
    return User.query.filter_by(user_id=user_id).first()


@app.errorhandler(404)
def not_found(error):
    return render_template('error/404.html'), 404


@app.errorhandler(500)
def not_found(error):
    return render_template('error/500.html'), 500


# 完成
@app.route("/login", methods=["GET", "POST"])
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter(User.user_id == username).first()
        if user and user.check_hash_password(password):
            login_user(user)
            if user.user_type == "0":
                return redirect(url_for("student_index"))
            else:
                if user.user_type == "1":
                    return redirect(url_for("teacher_index"))
                if user.user_type == "2":
                    return redirect(url_for("course_coordinator_index"))
                if user.user_type == "3":
                    return redirect(url_for("discipline_leader_index"))
                if user.user_type == "4":
                    return redirect(url_for("instructor_index"))
        else:
            msg = "用户名或密码错误"
            return render_template("login.html", msg=msg)


# 完成
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# 完成
@app.route("/student/query", methods=["GET", "POST"])
@login_required
def student_index():
    if current_user.user_type == "0":
        if request.method == "GET":
            final_result = db.session.query(Result).filter(Result.stu_id == current_user.user_id).with_entities(Result.stu_result).first()
            final_list = []
            concat = db.session.query(Requirement, Support, Course, Point)
            concat = concat.join(Point, "毕业要求"+Point.requirement_id == Requirement.requirement_id)
            concat = concat.join(Support, Point.point_id == Support.point_id)
            concat = concat.join(Course, Course.course_id == Support.course_id).with_entities(Requirement.requirement_id, Point.point_id, Course.course_id, Course.course_name, Support.course_weight).all()
            for item in concat:
                final_list.append(list(item))
            each_grade = {}
            grades = db.session.query(Grade).filter(Grade.stu_id == current_user.user_id).with_entities(Grade.point_id, Grade.course_id, Grade.remark).all()
            # 把评价值添加进去
            if len(grades) != 0:
                for item in grades:
                    for foo in final_list:
                        if item[0] in foo and item[1] in foo:
                            foo.append(item[2])
            # 某个课程在某个指标点上的所占分数
            for i in final_list:
                if len(i) != 6:
                    i.append(None)
                    i.append(None)
                else:
                    i.append(i[-1]*i[-2])
                if i[1] not in each_grade.keys():
                    each_grade[i[1]] = decimal.Decimal('0.00')
                if i[-1] is not None:
                    each_grade[i[1]] += i[-1]
            # 某个指标点的最终评价值
            for item in final_list:
                for key in each_grade.keys():
                    if key in item:
                        item.append(each_grade[key])
            # 添加毕业要求的最小值
            requirement_dict = {}
            for doo in final_list:
                if doo[0] not in requirement_dict.keys():
                    requirement_dict[doo[0]] = decimal.Decimal('1.00')
                if doo[-1] != decimal.Decimal('0.00'):
                    if doo[-1] < requirement_dict[doo[0]]:
                        requirement_dict[doo[0]] = doo[-1]
            for my_i in requirement_dict.keys():
                for my_foo in final_list:
                    if my_i in my_foo:
                        my_foo.append(requirement_dict[my_i])
            # 最终评价结果添加进去
            if final_result is not None:
                final_result_grade = final_result[0]
                for i in final_list:
                    i.append(final_result_grade)
            user_data = db.session.query(Student).filter(Student.stu_id == current_user.user_id).with_entities(Student.need_amount, Student.already_amount).first()
            user_info = {
                "need": user_data[0],
                "already": user_data[1]
            }
            user_is_pass = db.session.query(Result).filter(Result.stu_id == current_user.user_id).with_entities(Result.stu_result).first()[0]
            user_info["grade"] = user_is_pass
            if user_info["need"] > user_info["already"]:
                msg = "您还未修完全部课程，目前毕业要求达成度为：" + str(Decimal(user_is_pass).quantize(Decimal('0.00')))
                user_info["notice"] = msg
            else:
                msg = "您已修完全部课程，最终毕业要求达成度为：" + str(Decimal(user_is_pass).quantize(Decimal('0.00')))
                user_info["notice"] = msg
            return render_template("student/student_query.html",send_data=final_list, user_info=user_info)


# 完成
@app.route("/teacher/info", methods=["GET", "POST"])
@login_required
def teacher_index():
    if current_user.user_type == "1":
        if request.method == "GET":
            info = db.session.query(Tutor, Course)
            info = info.join(Course, Tutor.course_id == Course.course_id)
            info = info.filter(Tutor.teacher_id == current_user.user_id, Tutor.course_state != "数据未提交",
                               Tutor.course_state != "未审核").with_entities(Tutor.teacher_id, Course.course_name,
                                                                          Tutor.course_state, Tutor.course_remark).all()
            check_info = []
            course_lists = db.session.query(Tutor, Course)
            course_lists = course_lists.join(Course, Tutor.course_id == Course.course_id)
            course_lists = course_lists.filter(Tutor.teacher_id == current_user.user_id).with_entities\
                (Course.course_id, Course.course_name).all()
            if info is not None:
                for item in info:
                    if item[2] == "审核通过":
                        msg = item[1] + "：" + item[2]
                        check_info.append(msg)
                    elif item[2] == "审核未通过":
                        msg = item[1] + "：" + item[2] + "，原因：" + item[3]
                        check_info.append(msg)
                return render_template("teacher/teacher_info.html", check_info=check_info, course_info=course_lists)
            else:
                return render_template("teacher/teacher_info.html", check_info=check_info, course_info=course_lists)


# 完成
@app.route("/teacher/import/<course_id>", methods=["GET", "POST"])
@login_required
def teacher_import(course_id):
    if current_user.user_type == "1":
        if request.method == "GET":
            course_lists = db.session.query(Tutor, Course)
            course_lists = course_lists.join(Course, Tutor.course_id == Course.course_id)
            course_lists = course_lists.filter(Tutor.teacher_id == current_user.user_id).with_entities \
                (Course.course_id, Course.course_name).all()
            class_options = db.session.query(Tutor)
            class_options = class_options.filter(Tutor.teacher_id == current_user.user_id, Tutor.course_id == course_id)
            class_options = class_options.with_entities(Tutor.class_name).all()
            point_options = db.session.query(Support)
            point_options = point_options.filter(Support.course_id == course_id).with_entities(Support.point_id).all()
            stu_info = db.session.query(Student, Tutor, Grade)
            stu_info = stu_info.join(Grade, Student.stu_id == Grade.stu_id)
            stu_info = stu_info.join(Tutor, Tutor.course_id == Grade.course_id)
            stu_info = stu_info.filter(Tutor.teacher_id == current_user.user_id, Grade.course_id == course_id).with_entities\
                (Student.stu_id, Student.stu_name, Student.stu_class, Grade.point_id, Grade.remark).all()
            return render_template("teacher/teacher_import.html", course_info=course_lists, classes=class_options,
                                   points=point_options, send_data=stu_info)
        elif request.method == "POST":
            data = request.get_json()
            grade_data = db.session.query(Grade, Tutor, Student)
            grade_data = grade_data.join(Grade, Grade.stu_id == Student.stu_id)
            grade_data = grade_data.join(Tutor, Tutor.course_id == Grade.course_id)
            if data["class_name"] == "全部":
                if data["point_id"] == "全部":
                    grade_data = grade_data.filter(Tutor.teacher_id == current_user.user_id, Tutor.course_id == course_id)
                    grade_data = grade_data.with_entities(Student.stu_id, Student.stu_name, Student.stu_class, Grade.point_id, Grade.remark).all()
                else:
                    grade_data = grade_data.filter(Tutor.teacher_id == current_user.user_id,
                                                   Tutor.course_id == course_id, Grade.point_id == data["point_id"])
                    grade_data = grade_data.with_entities(Student.stu_id, Student.stu_name, Student.stu_class,
                                                          Grade.point_id, Grade.remark).all()
            else:
                if data["point_id"] == "全部":
                    grade_data = grade_data.filter(Tutor.teacher_id == current_user.user_id,
                                                   Tutor.course_id == course_id, Student.stu_class == data["class_name"])
                    grade_data = grade_data.with_entities(Student.stu_id, Student.stu_name, Student.stu_class,
                                                          Grade.point_id, Grade.remark).all()
                else:
                    grade_data = grade_data.filter(Tutor.teacher_id == current_user.user_id,
                                                   Tutor.course_id == course_id, Student.stu_class == data["class_name"],
                                                   Grade.point_id == data["point_id"])
                    grade_data = grade_data.with_entities(Student.stu_id, Student.stu_name, Student.stu_class,
                                                          Grade.point_id, Grade.remark).all()
            msg = ""
            for item in grade_data:
                msg += "<tr><td>" + item[0] + "</td><td>" + item[1] + "</td><td>" + item[2] + "</td><td>" + item[3] + \
                       "</td><td>" + str(Decimal(item[4]).quantize(Decimal('0.00'))) + "</td></tr>"
            return msg


# 完成
@app.route("/teacher/download", methods=["GET", "POST"])
@login_required
def teacher_download():
    if current_user.user_type == "1":
        if request.method == "GET":
            try:
                response = make_response(send_from_directory("D:\\test", "学生评价值导入模板.xls", as_attachment=True))
                response.headers['Content-Type'] = 'text/plain;charset=UTF-8'
                return response
            except Exception as e:
                return redirect(url_for("teacher_download"))


# 完成
@app.route("/teacher/upload/<course_id>", methods=["GET", "POST"])
@login_required
def teacher_upload(course_id):
    if current_user.user_type == "1":
        if request.method == "POST":
            file = request.files.get('file')  # 获取文件
            if file:
                filename = file.filename
                if filename.split('.')[-1] in ["xls", "xlsx"]:
                    file_path = os.path.join(FILE_FOLDER, filename)
                    file.save(file_path)
                    workbook = xlrd.open_workbook(file_path)
                    data_sheet = workbook.sheets()[0]
                    row_num = data_sheet.nrows
                    col_num = data_sheet.ncols
                    my_list = []
                    # 获取excel中的所有数据
                    for i in range(row_num):
                        row_list = []
                        for j in range(col_num):
                            row_list.append(data_sheet.cell_value(i, j))
                        my_list.append(row_list)
                    # 看表格的指标点是否正确
                    header = []
                    points = db.session.query(Support).filter(Support.course_id == course_id).with_entities(Support.point_id).all()
                    for index in range(0, len(points)):
                        header.append(points[index][0])
                    for i in range(2, col_num):
                        if my_list[0][i] not in header:
                            msg = "表格指标点与该课程支撑的指标点不一致"
                            return jsonify(msg)
                    # 插入成绩数据
                    for i in range(1, row_num):
                        for j in range(2, col_num):
                            is_in = db.session.query(Grade).filter(Grade.stu_id == my_list[i][0], Grade.course_id == course_id, Grade.point_id == my_list[0][j]).all()
                            if len(is_in) == 0:
                                grade = Grade(my_list[i][0], course_id, my_list[0][j], decimal.Decimal(my_list[i][j]))
                                db.session.add(grade)
                                db.session.commit()
                            else:
                                continue
                    # 更新已经修完的课程数量
                    for i in range(1, row_num):
                        already = db.session.query(Grade).filter(Grade.stu_id == my_list[i][0]).with_entities(Grade.course_id)
                        already_amount = set(already)
                        stu = db.session.query(Student).filter(Student.stu_id == my_list[i][0]).first()
                        stu.already_amount = len(already_amount)
                        db.session.commit()
                    # 将tutor表中的改为未审核
                    tea = db.session.query(Tutor).filter(Tutor.teacher_id == current_user.user_id, Tutor.course_id == course_id).all()
                    for i in tea:
                        i.course_state = "未审核"
                        db.session.commit()
                    # 计算达成度
                    matrix = db.session.query(Grade, Support)
                    matrix = matrix.join(Support, Grade.course_id == Support.course_id).filter(Grade.point_id == Support.point_id)\
                        .with_entities(Grade.stu_id, Grade.point_id, Grade.remark, Support.course_weight).all()
                    result = {}
                    requirement_amount = len(db.session.query(Requirement).all())
                    for foo in matrix:
                        if foo[0] not in result.keys():
                            result[foo[0]] = {}
                        if foo[1] not in result[foo[0]].keys():
                            result[foo[0]][foo[1]] = decimal.Decimal('0.00')
                        result[foo[0]][foo[1]] += foo[2] * foo[3]
                    # print(result)
                    for key in result.keys():
                        for key_2 in result[key].keys():
                            value_info = db.session.query(Evaluation).filter(Evaluation.stu_id == key, Evaluation.point_id == key_2).first()
                            if value_info is None:
                                evalue = Evaluation(key, key_2, result[key][key_2])
                                db.session.add(evalue)
                                db.session.commit()
                            else:
                                value_info.evaluation_remark = result[key][key_2]
                                db.session.commit()
                        result_info = db.session.query(Result).filter(Result.stu_id == key).first()
                        if result_info is None:
                            final_answer = Result(key, min(result[key].values()), "未预警")
                            db.session.add(final_answer)
                            db.session.commit()
                        else:
                            result_info.result = min(result[key].values())
                            db.session.commit()
                    msg = "上传成功"
                else:
                    msg = "文件格式不正确，请重新上传！"
                return jsonify(msg)


# 完成
@app.route("/course_coordinator/reason", methods=["GET", "POST"])
@login_required
def course_coordinator_reason():
    if current_user.user_type == "2":
        if request.method == "POST":
            font_data = request.get_json()
            if "teacher_id" not in font_data.keys():
                return "请重试！"
            else:
                reason = db.session.query(Tutor)
                reason = reason.filter(Tutor.course_id == font_data["course_id"], Tutor.teacher_id == font_data["teacher_id"],
                                       Tutor.class_name == font_data["class_name"]).first()
                if reason is None:
                    return "请重试！"
                else:
                    reason.course_state = "审核未通过"
                    reason.course_remark = font_data["content"]
                    db.session.commit()
                    return "提交成功"


# 完成
@app.route("/course_coordinator/pass", methods=["GET", "POST"])
@login_required
def course_coordinator_pass():
    if current_user.user_type == "2":
        if request.method == "POST":
            data = request.get_json()
            if "teacher_id" not in data.keys():
                return "您还未选择课程！"
            else:
                search_data = db.session.query(Grade, Student)
                search_data = search_data.join(Student, Student.stu_id == Grade.stu_id)
                search_data = search_data.filter(Student.stu_class == data["class_name"])
                search_data = search_data.filter(Grade.course_id == data["course_id"]).with_entities(Grade.point_id, Grade.remark).all()
                if len(search_data) == 0:
                    return "该教师还未上传成绩！不能审核！"
                is_pass = db.session.query(Tutor)
                is_pass = is_pass.filter(Tutor.course_id == data["course_id"], Tutor.teacher_id == data["teacher_id"],
                                         Tutor.class_name == data["class_name"]).first()
                if is_pass is not None:
                    is_pass.course_state = "审核通过"
                    db.session.commit()
                    return "操作成功"
                else:
                    return "操作失败，请重试！"


# 完成
@app.route("/course_coordinator/refuse", methods=["GET", "POST"])
@login_required
def course_coordinator_refuse():
    if current_user.user_type == "2":
        if request.method == "POST":
            font_data = request.get_json()
            if "teacher_id" not in font_data.keys():
                return "您还未选择课程！"
            else:
                search_data = db.session.query(Grade, Student)
                search_data = search_data.join(Student, Student.stu_id == Grade.stu_id)
                search_data = search_data.filter(Student.stu_class == font_data["class_name"])
                search_data = search_data.filter(Grade.course_id == font_data["course_id"]).with_entities(Grade.point_id,
                                                                                                     Grade.remark).all()
                if len(search_data) == 0:
                    return "该教师还未上传成绩！不能审核！"
                else:
                    return "成功"


# 完成
@app.route("/course_coordinator/detail", methods=["GET", "POST"])
@login_required
def course_coordinator_detail():
    if current_user.user_type == "2":
        if request.method == "POST":
            data = request.get_json()
            if "teacher_id" not in data.keys():
                return "您还未选择需要查看的条目！"
            else:
                teacher_id = data["teacher_id"]
                class_name = data["class_name"]
                course_id = data["course_id"]
                search_data = db.session.query(Grade, Student)
                search_data = search_data.join(Student, Student.stu_id == Grade.stu_id)
                search_data = search_data.filter(Student.stu_class == class_name)
                search_data = search_data.filter(Grade.course_id == course_id).with_entities(Grade.point_id, Grade.remark).all()
                if len(search_data) == 0:
                    return "该课程暂无数据！"
                else:
                    amount = db.session.query(Support).filter(Support.course_id == course_id).all()
                    my_dict = {}
                    for item in search_data:
                        if item[0] not in my_dict.keys():
                            my_dict[item[0]] = [0, 0, 0, 0, Decimal('0.0')]
                        my_dict[item[0]][0] += 1
                        my_dict[item[0]][4] += item[1]
                        if item[1] < 0.65:
                            my_dict[item[0]][1] += 1
                        elif 0.65 <= item[1] < 0.9:
                            my_dict[item[0]][2] += 1
                        else:
                            my_dict[item[0]][3] += 1
                    data_list = []
                    for key in my_dict.keys():
                        html_content = "<thead><tr><th>指标点编号</th><th>达标人数</th><th>不达标人数</th><th>平均达成度</th></tr></thead>"\
                                       + "<tbody><tr><td>" + key + "</td><td>" + str(my_dict[key][0] - my_dict[key][1]) \
                                       + "</td><td>" + str(my_dict[key][1]) + "</td><td>" + str(Decimal(my_dict[key][4]/my_dict[key][0]).quantize(Decimal('0.00'))) \
                                       + "</td></tr></tbody>"
                        temp = ["指标点"+key, html_content, [my_dict[key][1], my_dict[key][2], my_dict[key][3]]]
                        data_list.append(temp)
                    my_data = {
                        "cal_data": data_list
                    }
                    return jsonify(my_data)


# 完成
@app.route("/course_coordinator/check", methods=["GET", "POST"])
@login_required
def course_coordinator_index():
    if current_user.user_type == "2":
        if request.method == "GET":
            result = db.session.query(Course, Tutor, Teacher)
            result = result.join(Tutor, Tutor.course_id == Course.course_id).join(Teacher, Teacher.teacher_id == Tutor.teacher_id)\
                .filter(Course.charge_teacher_id == current_user.user_id).with_entities\
                (Tutor.class_name, Course.course_id, Course.course_name, Teacher.teacher_name, Tutor.course_state, Tutor.teacher_id).all()
            return render_template("course_coordinator/course_coordinator_check.html", send_data=result)


# 完成
@app.route("/discipline_leader/format", methods=["GET", "POST"])
@login_required
def discipline_leader_index():
    if current_user.user_type == "3":
        if request.method == "GET":
            support = db.session.query(Support, Course)
            support = support.join(Course, Support.course_id == Course.course_id).with_entities(
                Support.point_id, Course.course_name, Support.course_weight, Course.course_credit, Course.course_time)
            data = support.all()
            return render_template("discipline_leader/discipline_leader_format.html", data=data)
        elif request.method == "POST":
            key = request.get_json()
            if "-" in key["search_key"]:
                specific_data = db.session.query(Support, Course)
                specific_data = specific_data.join(Course, Support.course_id == Course.course_id).filter(Support.point_id == key["search_key"])
                specific_data = specific_data.with_entities(Support.point_id, Course.course_name,
                                                            Support.course_weight, Course.course_credit,Course.course_time)
                data = specific_data.all()
                if data is not None:
                    msg = ""
                    for item in data:
                        msg += "<tr><td>" + item[0] + "</td><td>" + item[1] + "</td><td>" + str(Decimal(item[2]).quantize(Decimal('0.00'))) \
                          + "</td><td>" + str(Decimal(item[3]).quantize(Decimal('0.00'))) + "</td><td>" + str(item[4]) + "</td></tr>"
                else:
                    msg = ""
                return msg
            else:
                specific_data = db.session.query(Support, Course)
                specific_data = specific_data.join(Course, Support.course_id == Course.course_id).filter(Course.course_name == key["search_key"])
                specific_data = specific_data.with_entities(Support.point_id, Course.course_name, Support.course_weight,
                                                            Course.course_credit,Course.course_time)
                data = specific_data.all()
                if data is not None:
                    msg = ""
                    for item in data:
                        msg += "<tr><td>" + item[0] + "</td><td>" + item[1] + "</td><td>" + str(
                            Decimal(item[2]).quantize(Decimal('0.00'))) \
                               + "</td><td>" + str(Decimal(item[3]).quantize(Decimal('0.00'))) + "</td><td>" + str(
                            item[4]) + "</td></tr>"
                else:
                    msg = ""
                return msg


# 完成
@app.route("/discipline_leader/upload", methods=["GET", "POST"])
@login_required
def discipline_leader_upload():
    if request.method == "POST":
        file = request.files.get('file')  # 获取文件
        if file:
            filename = file.filename
            if filename.split('.')[-1] in ["xls", "xlsx"]:
                file_path = os.path.join(FILE_FOLDER, filename)
                file.save(file_path)
                workbook = xlrd.open_workbook(file_path)
                data_sheet = workbook.sheets()[0]
                row_num = data_sheet.nrows
                col_num = data_sheet.ncols
                my_list = []
                error_list = []
                msg = "上传成功"
                # 获取excel中的所有数据
                for i in range(row_num):
                    row_list = []
                    for j in range(col_num):
                        row_list.append(data_sheet.cell_value(i, j))
                    my_list.append(row_list)
                for i in range(0, row_num):
                    if my_list[i][0].startswith("毕业要求"):
                        requirement_in = db.session.query(Requirement)
                        requirement_in = requirement_in.filter(Requirement.requirement_id == my_list[i][0]).first()
                        if requirement_in is None:
                            requirement = Requirement(my_list[i][0], my_list[i][1])
                            db.session.add(requirement)
                            db.session.commit()
                        else:
                            requirement_in.requirement_content = my_list[i][1]
                            db.session.commit()
                    elif "-" in my_list[i][0]:
                        point_in = db.session.query(Point)
                        point_in = point_in.filter(Point.point_id == my_list[i][0]).first()
                        if point_in is None:
                            requirement_id = my_list[i][0].split("-")[0]
                            point = Point(my_list[i][0], my_list[i][1], requirement_id)
                            total = 0
                            for j in range(1, col_num):
                                if my_list[i + 2][j] != '':
                                    total += float(my_list[i + 2][j])
                            if round(total, 2) == 1:
                                db.session.add(point)
                                db.session.commit()
                                for j in range(1, col_num):
                                    if my_list[i + 2][j] != '':
                                        course_id = db.session.query(Course).filter(Course.course_name == my_list[i+1][j]).with_entities(Course.course_id).first()
                                        support = Support(my_list[i][0], course_id[0], decimal.Decimal(my_list[i+2][j]))
                                        db.session.add(support)
                                        db.session.commit()
                            else:
                                error_list.append(i+3)
                if len(error_list) != 0:
                    msg = ""
                    for i in error_list:
                        msg += str(i) + " "
                    msg = "第 " + msg + "行数据有误！"
                course_amount = db.session.query(Support).with_entities(Support.course_id).all()
                my_set = set(course_amount)
                length = len(my_set)
                students = db.session.query(Student).all()
                for item in students:
                    item.need_amount = length
                    db.session.commit()
            else:
                msg = "文件格式不正确，请重新上传！"
            return jsonify(msg)


# 完成
@app.route("/discipline_leader/download/template", methods=["GET", "POST"])
@login_required
def discipline_leader_download_template():
    if current_user.user_type == "3":
        if request.method == "GET":
            try:
                response = make_response(send_from_directory("D:\\test", "培养方案导入模板.xls", as_attachment=True))
                response.headers['Content-Type'] = 'text/plain;charset=UTF-8'
                return response
            except:
                return redirect(url_for("discipline_leader_download_template"))


# 完成
@app.route("/discipline_leader/detail", methods=["GET", "POST"])
@login_required
def discipline_teacher_detail():
    if current_user.user_type == "3":
        if request.method == "GET":
            dict = {}
            result = db.session.query(Point, Requirement)
            result = result.join(Requirement, ("毕业要求" + Point.requirement_id) == Requirement.requirement_id)
            result = result.with_entities(Requirement.requirement_id, Requirement.requirement_content, Point.point_id,
                                          Point.point_content)
            data = result.all()
            for data_num in data:
                dict[data_num[0]] = dict.get(data_num[0], 0) + 1
            return_list = []
            for key in dict:
                content = db.session.query(Requirement).filter(Requirement.requirement_id == key).with_entities\
                    (Requirement.requirement_content).first()[0]
                temp = [dict[key], key,content]
                return_list.append(temp)
            for item in data:
                for i in range(0,len(return_list)):
                    if item[0] in return_list[i]:
                        return_list[i].append(item[2])
                        return_list[i].append(item[3])
            return render_template("discipline_leader/discipline_leader_detail.html", data=return_list)


# 完成
@app.route("/discipline_leader/statistics", methods=["GET", "POST"])
@login_required
def discipline_leader_statistics():
    if current_user.user_type == "3":
        if request.method == "GET":
            teacher_profession = db.session.query(Teacher).filter(Teacher.teacher_id == current_user.user_id
                                                                  ).with_entities(Teacher.teacher_profession_id).first()[0]
            class_info = db.session.query(Student).with_entities(Student.stu_class).all()
            class_info = set(class_info)
            class_lists = []
            for item in class_info:
                class_lists.append(item[0])
            grade_lists = ['2017']
            course_info = db.session.query(Course).with_entities(Course.course_name).all()
            course_info = set(course_info)
            course_lists = []
            for item in course_info:
                course_lists.append(item[0])
            return render_template("discipline_leader/discipline_leader_statistics.html", class_lists=class_lists, grade_lists=grade_lists, course_lists=course_lists)


# 完成
@app.route("/discipline_leader/statistics/class", methods=["GET", "POST"])
@login_required
def discipline_leader_statistics_class():
    if current_user.user_type == "3":
        if request.method == "POST":
            data = request.get_json()
            send_data = {}
            if data["class"] != "请选择":
                stu_info = db.session.query(Student, Result)
                stu_info = stu_info.join(Result, Student.stu_id == Result.stu_id).filter\
                    (Student.stu_class == data["class"]).with_entities(Result.stu_result).all()
                if len(stu_info) != 0:
                    send_data["msg"] = "该班级有数据！"
                    send_data["header"] = data["class"]
                    people_list = [0]*3
                    for item in stu_info:
                        if item[0] < 0.65:
                            people_list[0] += 1
                        elif item[0] >= 0.9:
                            people_list[2] += 1
                        else:
                            people_list[1] += 1
                    send_data["series"] = people_list
                    send_data["form"] = "<table class='table table-bordered'><thead><tr><th>达成度情况</th><th>人数</th></tr></thead><tbody><tr><td><0.65</td><td>" + \
                                  str(people_list[0]) + "</td></tr><tr><td>0.65~0.9</td><td>" + str(people_list[1]) + \
                                  "</td></tr><tr><td>>=0.9</td><td>" + str(people_list[2]) + "</td></tr></tbody></table>"
                else:
                    send_data["msg"] = "该班级暂无数据！"
            else:
                send_data["msg"] = "您还未选择需要查看的班级！"
            return send_data


# 完成
@app.route("/discipline_leader/statistics/grade", methods=["GET", "POST"])
@login_required
def discipline_leader_statistics_grade():
    if current_user.user_type == "3":
        if request.method == "POST":
            data = request.get_json()
            send_data = {}
            if data["grade"] != "请选择":
                stu_grades = db.session.query(Result).with_entities(Result.stu_id, Result.stu_result).all()
                stu_info = []
                for foo in stu_grades:
                    if foo[0][0:4] == data["grade"]:
                        stu_info.append(foo[1])
                if len(stu_info) != 0:
                    send_data["msg"] = "该年级有数据！"
                    people_list = [0] * 2
                    for item in stu_info:
                        if item < 0.65:
                            people_list[0] += 1
                        else:
                            people_list[1] += 1
                    send_data["data"] = people_list
                    send_data["form"] = "<table class='table table-bordered'><thead><tr><th>达成度情况</th><th>人数</th></tr></thead><tbody><tr><td>不及格</td><td>" + \
                                  str(people_list[0]) + "</td></tr><tr><td>及格</td><td>" + str(people_list[1]) + "</td></tr></tbody></table>"
                else:
                    send_data["msg"] = "该年级暂无数据！"
            else:
                send_data["msg"] = "您还未选择需要查看的年级！"
            return send_data


# 完成
@app.route("/discipline_leader/statistics/course", methods=["GET", "POST"])
@login_required
def discipline_leader_statistics_course():
    if current_user.user_type == "3":
        if request.method == "POST":
            data = request.get_json()
            send_data = {}
            if data["course"] != "请选择":
                stu_grades = db.session.query(Grade, Course)
                stu_grades = stu_grades.join(Course, Grade.course_id == Course.course_id).filter\
                    (Course.course_name == data["course"]).with_entities(Grade.point_id, Grade.remark).all()
                if len(stu_grades) != 0:
                    send_data["msg"] = "该课程有数据！"
                    dict = {}
                    for item in stu_grades:
                        if item[0] not in dict.keys():
                            dict[item[0]] = 0
                        if item[1] >= 0.65:
                            dict[item[0]] += 1
                    header = []
                    amount = []
                    for key in dict.keys():
                        header.append(key)
                        amount.append(dict[key])
                    send_data["header"] = header
                    send_data["amount"] = amount
                    send_data["course"] = data["course"]
                    msg = ""
                    for i in range(0, len(send_data["header"])):
                        msg += "<tr><td>" + send_data["header"][i] + "</td><td>" + str(
                            send_data["amount"][i]) + "</td></td>"
                    msg = "<table class='table table-bordered'><thead><tr><th>指标点</th><th>达标人数</th></thead><tbody>" + msg + "</tbody></table>"
                    send_data["form"] = msg
                else:
                    send_data["msg"] = "该课程暂无数据！"
            else:
                send_data["msg"] = "您还未选择需要查看的课程！"
            return send_data


# 完成
@app.route("/instructor/statistics", methods=["GET", "POST"])
@login_required
def instructor_index():
    if current_user.user_type == "4":
        if request.method == "GET":
            class_info = db.session.query(Student).with_entities(Student.stu_class).all()
            class_info = set(class_info)
            class_lists = []
            for item in class_info:
                class_lists.append(item[0])
            grade_lists = ['2017']
            course_info = db.session.query(Course).with_entities(Course.course_name).all()
            course_info = set(course_info)
            course_lists = []
            for item in course_info:
                course_lists.append(item[0])
            return render_template("instructor/instructor_statistics.html", class_lists=class_lists, grade_lists=grade_lists, course_lists=course_lists)


# 完成
@app.route("/instructor/statistics/class", methods=["GET", "POST"])
@login_required
def instructor_statistics_class():
    if current_user.user_type == "4":
        if request.method == "POST":
            data = request.get_json()
            send_data = {}
            if data["class"] != "请选择":
                stu_info = db.session.query(Student, Result)
                stu_info = stu_info.join(Result, Student.stu_id == Result.stu_id).filter\
                    (Student.stu_class == data["class"]).with_entities(Result.stu_result).all()
                if len(stu_info) != 0:
                    send_data["msg"] = "该班级有数据！"
                    send_data["header"] = data["class"]
                    people_list = [0]*3
                    for item in stu_info:
                        if item[0] < 0.65:
                            people_list[0] += 1
                        elif item[0] >= 0.9:
                            people_list[2] += 1
                        else:
                            people_list[1] += 1
                    send_data["series"] = people_list
                    send_data["form"] = "<table class='table table-bordered'><thead><tr><th>达成度情况</th><th>人数</th></tr></thead><tbody><tr><td><0.65</td><td>" + \
                                        str(people_list[0]) + "</td></tr><tr><td>0.65~0.9</td><td>" + str(people_list[1]) + \
                                        "</td></tr><tr><td>>=0.9</td><td>" + str(people_list[2]) + "</td></tr></tbody></table>"
                else:
                    send_data["msg"] = "该班级暂无数据！"
            else:
                send_data["msg"] = "您还未选择需要查看的班级！"
            return send_data


# 完成
@app.route("/instructor/statistics/grade", methods=["GET", "POST"])
@login_required
def instructor_statistics_grade():
    if current_user.user_type == "4":
        if request.method == "POST":
            data = request.get_json()
            send_data = {}
            if data["grade"] != "请选择":
                stu_grades = db.session.query(Result).with_entities(Result.stu_id, Result.stu_result).all()
                stu_info = []
                for foo in stu_grades:
                    if foo[0][0:4] == data["grade"]:
                        stu_info.append(foo[1])
                if len(stu_info) != 0:
                    send_data["msg"] = "该年级有数据！"
                    people_list = [0] * 2
                    for item in stu_info:
                        if item < 0.65:
                            people_list[0] += 1
                        else:
                            people_list[1] += 1
                    send_data["data"] = people_list
                    send_data["form"] = "<table class='table table-bordered'><thead><tr><th>达成度情况</th><th>人数</th></tr></thead><tbody><tr><td>不及格</td><td>" + \
                                  str(people_list[0]) + "</td></tr><tr><td>及格</td><td>" + str(people_list[1]) + "</td></tr></tbody></table>"
                else:
                    send_data["msg"] = "该年级暂无数据！"
            else:
                send_data["msg"] = "您还未选择需要查看的年级！"
            return send_data


# 完成
@app.route("/instructor/statistics/course", methods=["GET", "POST"])
@login_required
def instructor_statistics_course():
    if current_user.user_type == "4":
        if request.method == "POST":
            data = request.get_json()
            send_data = {}
            if data["course"] != "请选择":
                stu_grades = db.session.query(Grade, Course)
                stu_grades = stu_grades.join(Course, Grade.course_id == Course.course_id).filter\
                    (Course.course_name == data["course"]).with_entities(Grade.point_id, Grade.remark).all()
                if len(stu_grades) != 0:
                    send_data["msg"] = "该课程有数据！"
                    dict = {}
                    for item in stu_grades:
                        if item[0] not in dict.keys():
                            dict[item[0]] = 0
                        if item[1] >= 0.65:
                            dict[item[0]] += 1
                    header = []
                    amount = []
                    for key in dict.keys():
                        header.append(key)
                        amount.append(dict[key])
                    send_data["header"] = header
                    send_data["amount"] = amount
                    send_data["course"] = data["course"]
                    msg = ""
                    for i in range(0, len(send_data["header"])):
                        msg += "<tr><td>" + send_data["header"][i] + "</td><td>" + str(send_data["amount"][i]) + "</td></td>"
                    msg = "<table class='table table-bordered'><thead><tr><th>指标点</th><th>达标人数</th></thead><tbody>" + msg +"</tbody></table>"
                    send_data["form"] = msg
                else:
                    send_data["msg"] = "该课程暂无数据！"
            else:
                send_data["msg"] = "您还未选择需要查看的课程！"
            return send_data


if __name__ == '__main__':
    app.run()
