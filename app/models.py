from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin, current_user
from sqlalchemy import JSON  # Changed from ARRAY to JSON

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class UserRole:
    ADMIN = 'admin'
    PROJECT_MANAGER = 'project_manager'
    TEAM_MEMBER = 'team_member'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default=UserRole.TEAM_MEMBER)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id', name='fk_user_department'))
    reports_to = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_user_reports_to'))
    avatar = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    
    # Relationships
    projects = db.relationship('Project', backref='creator', lazy=True)
    tasks = db.relationship('Task', 
                          foreign_keys='Task.assigned_to',
                          back_populates='assignee', 
                          lazy=True)
    reviewed_tasks = db.relationship('Task',
                                   foreign_keys='Task.reviewer_id',
                                   back_populates='reviewer',
                                   lazy=True)
    reviews_given = db.relationship('PerformanceReview',
                                  foreign_keys='PerformanceReview.reviewer_id',
                                  backref='reviewer',
                                  lazy=True)
    reviews_received = db.relationship('PerformanceReview',
                                     foreign_keys='PerformanceReview.employee_id',
                                     backref='employee',
                                     lazy=True)
    following_projects = db.relationship('ProjectFollower', 
                                      back_populates='follower', 
                                      lazy='dynamic')
    team_memberships = db.relationship('TeamMember', backref='member', lazy=True)
    subordinates = db.relationship('User', backref=db.backref('manager', remote_side=[id]))
    
    def has_role(self, role):
        if self.role == UserRole.ADMIN:
            return True
        return self.role == role

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    @property
    def is_project_manager(self):
        return self.role == UserRole.PROJECT_MANAGER or self.is_admin

    @property
    def unread_notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, read=False).count()
    
    @property
    def recent_notifications(self):
        return Notification.query.filter_by(user_id=self.id)\
                               .order_by(Notification.created_at.desc())\
                               .limit(5).all()

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    employees = db.relationship('User', backref='department', lazy=True, 
                              foreign_keys='User.department_id')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_departments')

class DepartmentInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    department = db.relationship('Department', backref='invitations')
    user = db.relationship('User', foreign_keys=[user_id], backref='department_invitations')
    manager = db.relationship('User', foreign_keys=[manager_id], backref='sent_invitations')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    tasks = db.relationship('Task', backref='project', lazy=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    priority = db.Column(db.String(20), default='Medium')
    deadline = db.Column(db.DateTime)
    shared_with = db.Column(JSON, default=list)  # Changed from ARRAY to JSON
    visible_to_all_department = db.Column(db.Boolean, default=True)
    comments = db.relationship('Comment', backref='project', lazy='dynamic', 
                             foreign_keys='Comment.project_id', 
                             cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='rated_project', lazy='dynamic', 
                            foreign_keys='Rating.project_id', 
                            cascade='all, delete-orphan')
    followers = db.relationship('ProjectFollower', backref='followed_project', 
                              lazy='dynamic', cascade='all, delete-orphan')
    teams = db.relationship('Team', backref='project', lazy=True)
    department = db.relationship('Department', backref='projects')

    def update_progress(self):
        if not self.tasks:
            return 0
        completed_tasks = sum(1 for task in self.tasks if task.status == 'Completed')
        self.progress = int((completed_tasks / len(self.tasks)) * 100)
        db.session.commit()
    
    def is_visible_to(self, user):
        return (user.is_admin or 
                user.id == self.created_by or
                user.id == self.department.manager_id or
                user.id in self.shared_with or
                (self.visible_to_all_department and user.department_id == self.department_id))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    members = db.relationship('TeamMember', backref='team', lazy=True)

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', name='fk_member_team'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_member_user'))
    role = db.Column(db.String(50))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class PerformanceReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_performance_review_employee'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_performance_review_reviewer'))
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    rating = db.Column(db.Integer)  # 1-5 scale
    comments = db.Column(db.Text)
    goals_achieved = db.Column(db.Text)
    areas_improvement = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Not Started')
    due_date = db.Column(db.DateTime)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_task_assignee'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.String(20), default='Medium')
    eisenhower_tasks = db.relationship('EisenhowerTask', backref='task', 
                                     lazy='dynamic',
                                     cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='task', lazy='dynamic', 
                             foreign_keys='Comment.task_id', cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='rated_task', lazy='dynamic', 
                            foreign_keys='Rating.task_id', cascade='all, delete-orphan')
    dependencies = db.relationship('TaskDependency', 
                                 foreign_keys='TaskDependency.task_id',
                                 backref='dependent_task', 
                                 lazy=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('project_milestone.id', name='fk_task_milestone'))
    review_status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_task_reviewer'))
    review_comment = db.Column(db.Text)
    assignee = db.relationship('User', foreign_keys=[assigned_to], back_populates='tasks')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviewed_tasks')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def eisenhower_classification(self):
        """Get the current classification"""
        return self.eisenhower_tasks.first()

    def update_status(self, new_status):
        self.status = new_status
        self.project.update_progress()
        
        history = TaskHistory(
            task_id=self.id,
            old_status=self.status,
            new_status=new_status,
            changed_by=current_user.id
        )
        db.session.add(history)
        db.session.commit()

    @property
    def average_rating(self):
        ratings = [r.score for r in self.ratings]
        return sum(ratings) / len(ratings) if ratings else 0

class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_task_history_user'))
    task = db.relationship('Task', backref='history', lazy=True)
    user = db.relationship('User', backref='task_changes', lazy=True, foreign_keys=[changed_by])

class EisenhowerTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    quadrant = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='eisenhower_tasks')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_comment_user'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', name='fk_comment_task'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', name='fk_comment_project'), nullable=True)
    user = db.relationship('User', backref='comments', foreign_keys=[user_id])

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_rating_user'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', name='fk_rating_task'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', name='fk_rating_project'), nullable=True)
    user = db.relationship('User', backref='ratings', foreign_keys=[user_id])

class ProjectFollower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_follower_user'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_level = db.Column(db.String(20), default='all')  # all, major, none
    __table_args__ = (db.UniqueConstraint('user_id', 'project_id', name='uq_project_follower'),)
    follower = db.relationship('User', back_populates='following_projects', foreign_keys=[user_id])

class ProjectStakeholder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', name='fk_stakeholder_project'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_stakeholder_user'))
    role = db.Column(db.String(50))
    influence_level = db.Column(db.String(20))

class ProjectMilestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Integer, default=1)  # Importance weight for progress calculation

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    type = db.Column(db.String(20))  # task, project, review, etc.
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(200))  # URL to related resource
    user = db.relationship('User', backref='notifications')

class AdminNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    type = db.Column(db.String(50))  # department_created, invitation_sent, invitation_accepted, etc.
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    related_dept_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    related_user = db.relationship('User', backref='admin_notifications')
    related_department = db.relationship('Department')

class TaskDependency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', name='fk_dependency_task'))
    dependency_id = db.Column(db.Integer, db.ForeignKey('task.id', name='fk_dependency_depends_on'))
    dependency_type = db.Column(db.String(20))  # Start-to-Start, Finish-to-Start, etc.
    __table_args__ = (
        db.UniqueConstraint('task_id', 'dependency_id', name='uq_task_dependency'),
    )