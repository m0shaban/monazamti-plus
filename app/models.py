from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager
from enum import Enum
from dataclasses import dataclass
from app.utils.date_utils import utc_now
from sqlalchemy import MetaData
from werkzeug.security import check_password_hash, generate_password_hash

# Try to import Flask-Security; use fallbacks if not available
try:
    from flask_security import RoleMixin, SQLAlchemyUserDatastore, UserMixin as SecurityUserMixin
    has_flask_security = True
except ImportError:
    # Provide fallback classes if Flask-Security is not installed
    has_flask_security = False
    
    class RoleMixin:
        """Fallback implementation of RoleMixin when Flask-Security is not available."""
        pass
    
    class SQLAlchemyUserDatastore:
        """Fallback implementation of SQLAlchemyUserDatastore when Flask-Security is not available."""
        def __init__(self, *args, **kwargs):
            pass

# العلاقات بين الجداول
project_followers = db.Table('project_followers',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
)

# تعريف أدوار المستخدمين
class UserRole(str, Enum):
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    TEAM_MEMBER = "team_member"
    CLIENT = "client"

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='settings')
    
    timezone = db.Column(db.String(50), default='UTC')
    primary_color = db.Column(db.String(20), default='#4e73df')  # Add primary color field with default
    language = db.Column(db.String(10), default='ar')
    theme = db.Column(db.String(20), default='light')
    compact_mode = db.Column(db.Boolean, default=False)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    
    # العلاقات
    user = db.relationship('User', back_populates='settings')

# نموذج المستخدم
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default=UserRole.TEAM_MEMBER.value)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(200))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id', name='fk_user_department'))
    phone = db.Column(db.String(20))
    position = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=utc_now)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    fs_uniquifier = db.Column(db.String(255), unique=True)
    
    # العلاقات
    department = db.relationship('Department', foreign_keys=[department_id], backref=db.backref('members', lazy='dynamic'))
    settings = db.relationship('UserSettings', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    # العلاقة مع المشاريع التي يتابعها المستخدم
    following_projects = db.relationship(
        'Project',
        secondary=project_followers,
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # خصائص مشتقة لتسهيل التحقق من الأدوار
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN.value
    
    @property
    def is_project_manager(self):
        return self.role == UserRole.PROJECT_MANAGER.value
    
    @property
    def is_team_member(self):
        return self.role == UserRole.TEAM_MEMBER.value
    
    # إعادة تعريف دالة get_id لتوافق flask-security
    def get_id(self):
        return self.fs_uniquifier or str(self.id)
    
    # دالة للحصول على إعدادات المستخدم or إنشاءها
    def get_or_create_settings(self):
        if not self.settings:
            self.settings = UserSettings(user_id=self.id)
            db.session.add(self.settings)
            db.session.commit()
        return self.settings

    def check_password(self, password):
        """Verify the password against its hash."""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Generate password hash."""
        self.password_hash = generate_password_hash(password)

# جدول العلاقة بين الأدوار والمستخدمين
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

# نموذج القسم
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_department_manager'))
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # العلاقات
    manager = db.relationship('User', foreign_keys=[manager_id], backref=db.backref('managed_departments', lazy='dynamic'))
    projects = db.relationship('Project', back_populates='department')

# نموذج المشروع
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Active')
    priority = db.Column(db.String(20), default='Medium')
    progress = db.Column(db.Integer, default=0)  # نسبة مئوية للتقدم
    start_date = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    budget = db.Column(db.Float, default=0)
    estimated_hours = db.Column(db.Float, default=0)
    tags = db.Column(db.String(255))
    visible_to_all_department = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # العلاقات
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_projects')
    client = db.relationship('User', foreign_keys=[client_id], backref='client_projects')
    department = db.relationship('Department', back_populates='projects')
    tasks = db.relationship('Task', back_populates='project', cascade='all, delete-orphan')
    risks = db.relationship('RiskAssessment', back_populates='project', cascade='all, delete-orphan')
    time_entries = db.relationship('TimeEntry', back_populates='project', cascade='all, delete-orphan')
    
    # حساب نسبة استخدام الميزانية المتبقية
    @property
    def budget_status(self):
        """حساب وإرجاع نسبة الميزانية المستهلكة or المتبقية"""
        if not hasattr(self, 'budget') or not self.budget or self.budget <= 0:
            return 100  # إذا لم يكن هناك ميزانية، نفترض أن كل شيء على ما يرام
        
        # حساب إجمالي التكاليف من سجلات الوقت
        total_costs = sum(entry.calculate_cost() for entry in self.time_entries)
        
        # حساب النسبة المئوية للميزانية المتبقية
        budget_used_percentage = (total_costs / self.budget) * 100
        remaining_percentage = max(0, 100 - budget_used_percentage)
        
        return round(remaining_percentage)
    
    # حساب نسبة الوقت المتبقي
    @property
    def time_status(self):
        if not hasattr(self, 'estimated_hours') or not self.estimated_hours or self.estimated_hours <= 0:
            return 100
        
        actual_hours = sum(entry.duration or 0 for entry in self.time_entries)
        time_used_percentage = (actual_hours / self.estimated_hours) * 100
        remaining_percentage = max(0, 100 - time_used_percentage)
        
        return round(remaining_percentage)
    
    # حساب التكلفة الفعلية
    @property
    def actual_cost(self):
        return sum(entry.calculate_cost() for entry in self.time_entries)
    
    # حساب ساعات العمل الفعلية
    @property
    def actual_hours(self):
        return sum(entry.duration or 0 for entry in self.time_entries)
    
    def calculate_budget_status(self):
        """Calculate budget status as percentage"""
        if not hasattr(self, 'budget') or not self.budget or self.budget <= 0:
            return 100

        # ...existing code...

    def get_budget_warnings(self):
        """Get budget-related warnings"""
        warnings = []
        if not self.budget or self.budget <= 0:
            warnings.append("No budget set")
        elif self.calculate_cost() > self.budget:
            warnings.append("Over budget")
        return warnings

    @property
    def is_over_budget(self):
        """Check if project is over budget"""
        if not self.budget or self.budget <= 0:
            return False
        return self.calculate_cost() > self.budget

    def validate_task(self):
        if not self.title or not self.project_id:
            return False
        # ...existing code...

    def check_status(self):
        if self.active or self.verified or self.balance > 0:
            return True
        # ...existing code...

    def validate_budget(self):
        """Validate project budget"""
        if not hasattr(self, 'budget') or not self.budget or self.budget <= 0:
            return False
        return True

    def validate_dates(self):
        """Validate project dates"""
        if not self.start_date or not self.deadline or self.start_date >= self.deadline:
            return False
        return True

    def validate_estimated_hours(self):
        """Validate estimated hours"""
        if not hasattr(self, 'estimated_hours') or not self.estimated_hours or self.estimated_hours <= 0:
            return False
        return True

    def calculate_actual_hours(self):
        """Calculate actual hours"""
        actual_hours = sum(entry.duration or 0 for entry in self.time_entries)
        return actual_hours

    def get_unique_identifier(self):
        """Return a unique identifier for the user."""
        return self.fs_uniquifier or str(self.id)

    def is_active_and_verified(self):
        """Check if the user is active and verified"""
        if self.active and self.verified and self.balance > 0:
            return True
        return False

    def calculate_total_duration(self):
        """Calculate total duration"""
        return sum(entry.duration or 0 for entry in self.time_entries)

    def calculate_average_rating(self, ratings):
        """Calculate average rating"""
        if not ratings or len(ratings) == 0:
            return 0
        return sum(ratings) / len(ratings)

    def validate_task(self):
        """Validate task"""
        if not self.title or not self.project_id:
            return False
        return True

# نموذج المهام
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    status = db.Column(db.String(50), default='Not Started')
    priority = db.Column(db.String(20), default='Medium')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    due_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float, default=0)
    importance = db.Column(db.Integer, default=2)  # لمصفوفة آيزنهاور: 1=مهم جدًا، 4=أقل أهمية
    require_evidence = db.Column(db.Boolean, default=False)
    is_recurring = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # العلاقات
    project = db.relationship('Project', back_populates='tasks')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    time_entries = db.relationship('TimeEntry', back_populates='task', cascade='all, delete-orphan')
    
    # حساب ساعات العمل الفعلية
    @property
    def actual_hours(self):
        return sum(entry.duration or 0 for entry in self.time_entries)
    
    # حساب متوسط التقييم
    @property
    def average_rating(self):
        ratings = TaskRating.query.filter_by(task_id=self.id).all()
        if not ratings or len(ratings) == 0:
            return 0
        return sum(r.score for r in ratings) / len(ratings)

# نموذج تقييم المهام
class TaskRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # تقييم من 1-5
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # العلاقات
    task = db.relationship('Task', backref=db.backref('ratings', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('task_ratings', lazy='dynamic'))

# نموذج تسجيل الوقت
class TimeEntry(db.Model):
    __tablename__ = 'time_entry'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, default=utc_now)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # بالساعات
    billable = db.Column(db.Boolean, default=True)
    hourly_rate = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # العلاقات
    user = db.relationship('User', backref=db.backref('time_entries', lazy='dynamic'))
    project = db.relationship('Project', back_populates='time_entries')
    task = db.relationship('Task', back_populates='time_entries')
    
    # حساب التكلفة
    def calculate_cost(self):
        """Calculate the cost of the time entry."""
        return self.duration * self.hourly_rate if self.billable else 0  # Fixed Arabic 'إذا'

# نموذج تقييم المخاطر
class RiskAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    impact = db.Column(db.Integer, default=3)  # من 1 إلى 5
    probability = db.Column(db.Integer, default=3)  # من 1 إلى 5
    status = db.Column(db.String(50), default='Open')
    mitigation_plan = db.Column(db.Text)
    contingency_plan = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # العلاقات
    project = db.relationship('Project', back_populates='risks')
    creator = db.relationship('User', backref='risk_assessments')
    
    # حساب شدة الخطر
    @property
    def severity(self):
        return self.impact * self.probability

# دالة تحميل المستخدم لـ flask-login
@login_manager.user_loader
def load_user(user_id):
    # Fix missing parenthesis in query
    return User.query.filter_by(fs_uniquifier=user_id).first()
