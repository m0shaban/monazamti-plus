from app import create_app, db
from app.models import User, UserRole, Department, Project, Task
from werkzeug.security import generate_password_hash
import os
from datetime import datetime, timedelta

app = create_app()

def init_db():
    with app.app_context():
        try:
            # إنشاء قاعدة البيانات والجداول
            db.create_all()
            
            # إنشاء مستخدم أدمن إذا لم يكن موجوداً
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='eng.mohamed0shaban@gmail.com',
                    password=generate_password_hash('Mm123456789', method='sha256'),
                    role=UserRole.ADMIN
                )
                db.session.add(admin)
                db.session.commit()
                print("تم إنشاء مستخدم أدمن بنجاح")
                
                # إنشاء بيانات تجريبية للعرض
                create_demo_data()
            return True
        except Exception as e:
            print(f"خطأ في إعداد قاعدة البيانات: {e}")
            return False

def create_demo_data():
    """إنشاء بيانات تجريبية للعرض"""
    try:
        # إنشاء أقسام
        dept1 = Department(name="قسم تطوير البرمجيات", description="تطوير وصيانة تطبيقات الشركة", manager_id=1)
        dept2 = Department(name="قسم التسويق", description="تسويق منتجات الشركة وخدماتها", manager_id=1)
        db.session.add_all([dept1, dept2])
        db.session.commit()
        
        # إنشاء موظفين
        users = [
            User(username="محمد علي", email="mohamed@example.com", password=generate_password_hash("password123"), role=UserRole.PROJECT_MANAGER, department_id=1),
            User(username="أحمد سمير", email="ahmed@example.com", password=generate_password_hash("password123"), role=UserRole.TEAM_MEMBER, department_id=1),
            User(username="عمر مصطفى", email="omar@example.com", password=generate_password_hash("password123"), role=UserRole.TEAM_MEMBER, department_id=1),
            User(username="سارة أحمد", email="sara@example.com", password=generate_password_hash("password123"), role=UserRole.PROJECT_MANAGER, department_id=2),
            User(username="لينا محمود", email="leena@example.com", password=generate_password_hash("password123"), role=UserRole.TEAM_MEMBER, department_id=2)
        ]
        db.session.add_all(users)
        db.session.commit()
        
        # إنشاء مشاريع
        projects = [
            Project(name="تطوير موقع الشركة", description="إعادة تصميم وتطوير موقع الشركة الرئيسي", created_by=2, department_id=1, status="Active", priority="High", progress=75),
            Project(name="تطبيق الجوال", description="تطوير تطبيق الهاتف المحمول للعملاء", created_by=2, department_id=1, status="Active", priority="Medium", progress=30),
            Project(name="حملة تسويقية", description="إطلاق حملة تسويقية للمنتج الجديد", created_by=4, department_id=2, status="Active", priority="High", progress=50)
        ]
        db.session.add_all(projects)
        db.session.commit()
        
        # إنشاء مهام
        tasks = [
            Task(title="تصميم واجهة المستخدم", description="تصميم واجهة مستخدم جديدة للموقع", assigned_to=2, project_id=1, status="Completed", priority="High", due_date=datetime.now() + timedelta(days=5)),
            Task(title="تطوير الواجهة الخلفية", description="برمجة وتطوير API", assigned_to=3, project_id=1, status="In Progress", priority="Medium", due_date=datetime.now() + timedelta(days=10)),
            Task(title="اختبار الموقع", description="اختبار شامل للموقع الجديد", assigned_to=2, project_id=1, status="Not Started", priority="Medium", due_date=datetime.now() + timedelta(days=15)),
            Task(title="تصميم واجهة التطبيق", description="تصميم واجهة مستخدم للتطبيق", assigned_to=2, project_id=2, status="In Progress", priority="Medium", due_date=datetime.now() + timedelta(days=7)),
            Task(title="تطوير تطبيق iOS", description="تطوير نسخة iOS من التطبيق", assigned_to=3, project_id=2, status="Not Started", priority="High", due_date=datetime.now() + timedelta(days=20)),
            Task(title="إنشاء محتوى تسويقي", description="إنشاء محتوى لمنصات التواصل الاجتماعي", assigned_to=5, project_id=3, status="In Progress", priority="Medium", due_date=datetime.now() + timedelta(days=3)),
            Task(title="تحليل نتائج الحملة", description="تحليل أداء الحملة التسويقية", assigned_to=5, project_id=3, status="Not Started", priority="Medium", due_date=datetime.now() + timedelta(days=30))
        ]
        db.session.add_all(tasks)
        db.session.commit()
        
        print("تم إنشاء البيانات التجريبية بنجاح")
    except Exception as e:
        print(f"خطأ في إنشاء البيانات التجريبية: {e}")
        db.session.rollback()

@app.cli.command("init-db")
def init_db_command():
    """إعادة تهيئة قاعدة البيانات وإنشاء مستخدم أدمن"""
    init_db()
    print("تم تهيئة قاعدة البيانات")

if __name__ == '__main__':
    app.run(debug=False)
