from models import *


def insert_user():
    user = User("20171188", "123456", "3")
    db.session.add(user)
    db.session.commit()
    user = User("20171199", "123456", "4")
    db.session.add(user)
    db.session.commit()


def insert_stu_info():
    for i in range(2016113121, 2016113151):
        stu = Student(str(i), "李一", "16软工三班", "113")
        db.session.add(stu)
        db.session.commit()


def insert_tea_info():
    for i in range(20171151, 20171172):
        tea = Teacher(str(i), "王一", "113")
        db.session.add(tea)
        db.session.commit()


def insert_tutor():
    for i in range(20171151, 20171172):
        tutor = Tutor(str(i), "17软工四班", "113001")
        db.session.add(tutor)
        db.session.commit()
    for i in range(20171151, 20171172):
        tutor = Tutor(str(i), "17软工四班", "113001")
        db.session.add(tutor)
        db.session.commit()


def insert_grade_data():
    for i in range(2017113121, 2017113151):
        grade = Grade(str(i), "113023", "12-3", 0.75)
        db.session.add(grade)
        db.session.commit()

my_list = [None]*7
print(my_list)
my_list[5] = 2
print(my_list)
