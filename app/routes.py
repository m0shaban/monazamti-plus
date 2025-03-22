from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import (Project, Task, EisenhowerTask, Comment, Rating, ProjectFollower,
                       Department, Team, TeamMember, ProjectMilestone, PerformanceReview, User, UserRole, DepartmentInvitation, AdminNotification)
from app import db  # Add this import for the database
from app.services.reporting import ReportingService
from sqlalchemy import func
from datetime import datetime, timedelta
from app.utils import admin_required, manager_required
from werkzeug.security import generate_password_hash

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    # للمدراء: عرض المشاريع التي أنشأوها
    if current_user.is_project_manager:
        created_projects = Project.query.filter_by(created_by=current_user.id).all()
    else:
        created_projects = []

    # للجميع: عرض المشاريع المشتركة معهم
    department_projects = Project.query.filter(
        (Project.department_id == current_user.department_id) & 
        (Project.visible_to_all_department == True)
    ).all()
    
    shared_projects = Project.query.filter(
        Project.shared_with.contains([current_user.id])
    ).all()

    projects = list(set(created_projects + department_projects + shared_projects))
    tasks = Task.query.filter_by(assigned_to=current_user.id).all()
    
    # إحصائيات إضافية للمدراء
    if current_user.is_project_manager:
        team_stats = {
            'total_members': User.query.filter_by(department_id=current_user.department_id).count(),
            'active_projects': len([p for p in projects if p.status == 'Active']),
            'total_tasks': Task.query.join(Project).filter(
                Project.department_id == current_user.department_id
            ).count()
        }
    else:
        team_stats = None

    # Calculate dashboard statistics
    stats = {
        'total_projects': Project.query.filter(
            (Project.created_by == current_user.id) |
            (Project.department_id == current_user.department_id)
        ).count(),
        'completed_projects': Project.query.filter(
            ((Project.created_by == current_user.id) |
             (Project.department_id == current_user.department_id)) &
            (Project.status == 'Completed')
        ).count(),
        'total_tasks': Task.query.filter_by(assigned_to=current_user.id).count(),
        'overdue_tasks': Task.query.filter(
            Task.assigned_to == current_user.id,
            Task.due_date < datetime.now(),
            Task.status != 'Completed'
        ).count()
    }

    return render_template('dashboard.html',
                         projects=projects,
                         tasks=tasks,
                         team_stats=team_stats,
                         stats=stats)

@bp.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    # Calculate task statistics
    task_stats = {
        'total': len(tasks),
        'completed': sum(1 for task in tasks if task.status == 'Completed'),
        'in_progress': sum(1 for task in tasks if task.status == 'In Progress'),
        'not_started': sum(1 for task in tasks if task.status == 'Not Started'),
        'blocked': sum(1 for task in tasks if task.status == 'Blocked')
    }
    
    return render_template('project_detail.html', 
                         project=project, 
                         tasks=tasks, 
                         task_stats=task_stats,
                         Rating=Rating,
                         Comment=Comment)

@bp.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task_detail.html', task=task, 
                          Rating=Rating, Comment=Comment)

@bp.route('/project/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create_project():
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            visible_to_all = request.form.get('visible_to_all') == 'yes'
            shared_with = request.form.getlist('shared_with')
            
            project = Project(
                name=name,
                description=description,
                created_by=current_user.id,
                department_id=current_user.department_id,
                visible_to_all_department=visible_to_all,
                shared_with=[int(uid) for uid in shared_with] if shared_with else []
            )
            db.session.add(project)
            db.session.commit()
            flash('Project created successfully', 'success')
            return redirect(url_for('main.dashboard'))
            
        team_members = User.query.filter_by(department_id=current_user.department_id).all()
        return render_template('create_project.html', team_members=team_members)
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating project: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

@bp.route('/task/<int:task_id>/update_status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assigned_to != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    new_status = request.json.get('status')
    if new_status not in ['Not Started', 'In Progress', 'Completed']:
        return jsonify({'error': 'Invalid status'}), 400
    
    task.status = new_status
    task.project.update_progress()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_progress': task.project.progress
    })

@bp.route('/project/<int:project_id>/task/create', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        task = Task(
            title=request.form.get('title'),
            description=request.form.get('description'),
            due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d') if request.form.get('due_date') else None,
            assigned_to=current_user.id,
            project_id=project.id,
            priority=request.form.get('priority', 'Medium')
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully', 'success')
        return redirect(url_for('main.project_detail', project_id=project.id))
    return render_template('create_task.html', project=project)

@bp.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.created_by != current_user.id:
        flash('You can only edit your own projects', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.priority = request.form.get('priority')
        project.deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d') if request.form.get('deadline') else None
        db.session.commit()
        flash('Project updated successfully', 'success')
        return redirect(url_for('main.project_detail', project_id=project.id))
    return render_template('edit_project.html', project=project)

@bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assigned_to != current_user.id:
        flash('You can only edit tasks assigned to you', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.priority = request.form.get('priority')
        task.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d') if request.form.get('due_date') else None
        db.session.commit()
        flash('Task updated successfully', 'success')
        return redirect(url_for('main.task_detail', task_id=task.id))
    return render_template('edit_task.html', task=task)

@bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assigned_to != current_user.id:
        flash('You can only delete tasks assigned to you', 'danger')
        return redirect(url_for('main.dashboard'))
    
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully', 'success')
    return redirect(url_for('main.project_detail', project_id=project_id))

@bp.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
@manager_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.created_by != current_user.id:
        flash('You can only delete your own projects', 'danger')
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/projects')
@login_required
def projects():
    sort_by = request.args.get('sort', 'created_at')
    direction = request.args.get('direction', 'desc')
    
    query = Project.query.filter_by(created_by=current_user.id)
    
    if sort_by == 'priority':
        query = query.order_by(Project.priority.desc() if direction == 'desc' else Project.priority)
    elif sort_by == 'deadline':
        query = query.order_by(Project.deadline.desc() if direction == 'desc' else Project.deadline)
    else:
        query = query.order_by(Project.created_at.desc() if direction == 'desc' else Project.created_at)
    
    projects = query.all()
    return render_template('projects.html', projects=projects, sort_by=sort_by, direction=direction)

@bp.route('/eisenhower-matrix')
@login_required
def eisenhower_matrix():
    tasks = Task.query.filter_by(assigned_to=current_user.id).all()
    matrix = {
        'urgent_important': [],
        'not_urgent_important': [],
        'urgent_not_important': [],
        'not_urgent_not_important': []
    }
    
    for task in tasks:
        classification = task.eisenhower_classification
        if classification:
            matrix[classification.quadrant].append(task)
        else:
            # Create default classification
            new_classification = EisenhowerTask(
                task_id=task.id,
                user_id=current_user.id,
                quadrant='not_urgent_not_important'
            )
            db.session.add(new_classification)
            matrix['not_urgent_not_important'].append(task)
    
    db.session.commit()
    return render_template('eisenhower_matrix.html', matrix=matrix)

@bp.route('/task/<int:task_id>/classify', methods=['POST'])
@login_required
def classify_task(task_id):
    task = Task.query.get_or_404(task_id)
    quadrant = request.json.get('quadrant')
    
    # Get existing classification or create new one
    classification = EisenhowerTask.query.filter_by(task_id=task.id).first()
    if not classification:
        classification = EisenhowerTask(task_id=task.id, user_id=current_user.id)
    
    classification.quadrant = quadrant
    db.session.add(classification)
    db.session.commit()
    
    return jsonify({'success': True})

# Comments routes
@bp.route('/project/<int:project_id>/comment', methods=['POST'])
@login_required
def add_project_comment(project_id):
    project = Project.query.get_or_404(project_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('main.project_detail', project_id=project_id))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        project_id=project_id
    )
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully', 'success')
    return redirect(url_for('main.project_detail', project_id=project_id))

@bp.route('/task/<int:task_id>/comment', methods=['POST'])
@login_required
def add_task_comment(task_id):
    task = Task.query.get_or_404(task_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        task_id=task_id
    )
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully', 'success')
    return redirect(url_for('main.task_detail', task_id=task_id))

@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Only allow comment creators or admins to delete comments
    if comment.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this comment', 'danger')
        if comment.project_id:
            return redirect(url_for('main.project_detail', project_id=comment.project_id))
        else:
            return redirect(url_for('main.task_detail', task_id=comment.task_id))
    
    project_id = comment.project_id
    task_id = comment.task_id
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted successfully', 'success')
    if project_id:
        return redirect(url_for('main.project_detail', project_id=project_id))
    else:
        return redirect(url_for('main.task_detail', task_id=task_id))

# Rating routes
@bp.route('/project/<int:project_id>/rate', methods=['POST'])
@login_required
def rate_project(project_id):
    project = Project.query.get_or_404(project_id)
    score = int(request.form.get('score', 0))
    feedback = request.form.get('feedback', '')
    
    if score < 1 or score > 5:
        flash('Rating must be between 1 and 5', 'danger')
        return redirect(url_for('main.project_detail', project_id=project_id))
    
    # Check if user already rated this project
    existing_rating = Rating.query.filter_by(
        user_id=current_user.id, 
        project_id=project_id
    ).first()
    
    if existing_rating:
        existing_rating.score = score
        existing_rating.feedback = feedback
    else:
        rating = Rating(
            score=score,
            feedback=feedback,
            user_id=current_user.id,
            project_id=project_id
        )
        db.session.add(rating)
    
    db.session.commit()
    flash('Rating submitted successfully', 'success')
    return redirect(url_for('main.project_detail', project_id=project_id))

@bp.route('/task/<int:task_id>/rate', methods=['POST'])
@login_required
def rate_task(task_id):
    task = Task.query.get_or_404(task_id)
    score = int(request.form.get('score', 0))
    feedback = request.form.get('feedback', '')
    
    if score < 1 or score > 5:
        flash('Rating must be between 1 and 5', 'danger')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    # Check if user already rated this task
    existing_rating = Rating.query.filter_by(
        user_id=current_user.id, 
        task_id=task_id
    ).first()
    
    if existing_rating:
        existing_rating.score = score
        existing_rating.feedback = feedback
    else:
        rating = Rating(
            score=score,
            feedback=feedback,
            user_id=current_user.id,
            task_id=task_id
        )
        db.session.add(rating)
    
    db.session.commit()
    flash('Rating submitted successfully', 'success')
    return redirect(url_for('main.task_detail', task_id=task_id))

# Follow/Unfollow Projects
@bp.route('/project/<int:project_id>/follow', methods=['POST'])
@login_required
def follow_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if already following
    follower = ProjectFollower.query.filter_by(
        user_id=current_user.id,
        project_id=project_id
    ).first()
    
    if follower:
        flash('You are already following this project', 'info')
    else:
        notification_level = request.form.get('notification_level', 'all')
        follower = ProjectFollower(
            user_id=current_user.id,
            project_id=project_id,
            notification_level=notification_level
        )
        db.session.add(follower)
        db.session.commit()
        flash('You are now following this project', 'success')
    
    return redirect(url_for('main.project_detail', project_id=project_id))

@bp.route('/project/<int:project_id>/unfollow', methods=['POST'])
@login_required
def unfollow_project(project_id):
    follower = ProjectFollower.query.filter_by(
        user_id=current_user.id,
        project_id=project_id
    ).first()
    
    if follower:
        db.session.delete(follower)
        db.session.commit()
        flash('You are no longer following this project', 'success')
    else:
        flash('You were not following this project', 'info')
    
    return redirect(url_for('main.project_detail', project_id=project_id))

@bp.route('/my-followed-projects')
@login_required
def followed_projects():
    followed = ProjectFollower.query.filter_by(user_id=current_user.id).all()
    projects = [f.followed_project for f in followed]
    
    return render_template('followed_projects.html', projects=projects)

@bp.route('/manager-dashboard')
@login_required
@manager_required
def manager_dashboard():
    try:
        # Get team performance data
        team_members = User.query.filter_by(department_id=current_user.department_id).all()
        team_stats = []
        team_labels = []
        team_performance_data = []

        for member in team_members:
            # Calculate workload and performance metrics
            active_tasks = Task.query.filter_by(
                assigned_to=member.id,
                status='In Progress'
            ).count()
            
            member_stats = {
                'username': member.username,
                'active_tasks_count': active_tasks,
                'workload_percentage': min((active_tasks / 10) * 100, 100),
                'performance_rating': 3  # Default rating if no review exists
            }
            team_stats.append(member_stats)
            team_labels.append(member.username)
            team_performance_data.append(member_stats['performance_rating'] * 20)

        # Get active projects
        projects = Project.query.filter_by(
            department_id=current_user.department_id,
            status='Active'
        ).all()

        # Get upcoming milestones (within next 30 days)
        upcoming_milestones = []

        return render_template('manager_dashboard.html',
                             team_members=team_stats,
                             upcoming_milestones=upcoming_milestones,
                             projects=projects,
                             team_labels=team_labels,
                             team_performance_data=team_performance_data)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

@bp.route('/assign-tasks')
@login_required
@manager_required
def assign_tasks():
    department = Department.query.get(current_user.department_id)
    employees = User.query.filter_by(department_id=current_user.department_id).all()
    unassigned_tasks = Task.query.filter_by(assigned_to=None).all()
    
    return render_template('assign_tasks.html',
                         department=department,
                         employees=employees,
                         unassigned_tasks=unassigned_tasks)

@bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    departments = Department.query.all()
    return render_template('admin/users.html', 
                         users=users, 
                         departments=departments,
                         UserRole=UserRole)

@bp.route('/admin/user/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        department_id = request.form.get('department_id')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('main.create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('main.create_user'))
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method='sha256'),
            role=role,
            department_id=department_id if department_id else None
        )
        
        db.session.add(user)
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('main.admin_users'))
    
    departments = Department.query.all()
    return render_template('admin/create_user.html', 
                         departments=departments,
                         UserRole=UserRole)

@bp.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        department_id = request.form.get('department_id')
        new_password = request.form.get('password')
        
        # Check if username exists for other users
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('Username already exists', 'danger')
            return redirect(url_for('main.edit_user', user_id=user_id))
        
        # Check if email exists for other users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('Email already registered', 'danger')
            return redirect(url_for('main.edit_user', user_id=user_id))
        
        user.username = username
        user.email = email
        user.role = role
        user.department_id = department_id if department_id else None
        
        if new_password:
            user.password = generate_password_hash(new_password, method='sha256')
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('main.admin_users'))
    
    departments = Department.query.all()
    return render_template('admin/edit_user.html', 
                         user=user,
                         departments=departments,
                         UserRole=UserRole)

@bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('main.admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('main.admin_users'))

@bp.route('/admin/departments')
@login_required
@admin_required
def admin_departments():
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)

@bp.route('/admin/department/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_department():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        manager_id = request.form.get('manager_id')
        
        department = Department(
            name=name,
            description=description,
            manager_id=manager_id if manager_id else None
        )
        db.session.add(department)
        
        # Create notification for admin
        notification = AdminNotification(
            title='New Department Created',
            content=f'Department "{name}" has been created',
            type='department_created',
            related_dept_id=department.id
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Department created successfully', 'success')
        return redirect(url_for('main.admin_departments'))
    
    managers = User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()
    return render_template('admin/create_department.html', managers=managers)

@bp.route('/department/<int:department_id>')
@login_required
def view_department(department_id):
    department = Department.query.get_or_404(department_id)
    
    # Get department statistics
    active_projects = Project.query.join(User).filter(
        User.department_id == department_id,
        Project.status == 'Active'
    ).all()
    
    pending_tasks = Task.query.join(User).filter(
        User.department_id == department_id,
        Task.status != 'Completed'
    ).all()
    
    # Calculate performance data
    performance_dates = []
    performance_data = []
    today = datetime.now()
    for i in range(7):
        date = today - timedelta(days=i)
        completed_tasks = Task.query.join(User).filter(
            User.department_id == department_id,
            Task.status == 'Completed',
            Task.updated_at >= date.replace(hour=0, minute=0),
            Task.updated_at < (date + timedelta(days=1)).replace(hour=0, minute=0)
        ).count()
        total_tasks = Task.query.join(User).filter(
            User.department_id == department_id,
            Task.updated_at >= date.replace(hour=0, minute=0),
            Task.updated_at < (date + timedelta(days=1)).replace(hour=0, minute=0)
        ).count()
        
        performance_dates.insert(0, date.strftime('%Y-%m-%d'))
        performance_data.insert(0, (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
    
    # Get available users for invitations
    available_users = User.query.filter(
        User.department_id == None,
        User.role != UserRole.ADMIN
    ).all()
    
    return render_template('department/view.html',
                         department=department,
                         active_projects=active_projects,
                         pending_tasks=pending_tasks,
                         performance_dates=performance_dates,
                         performance_data=performance_data,
                         available_users=available_users)

@bp.route('/department/<int:department_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    
    # Check if user has permission to edit
    if not current_user.is_admin and department.manager_id != current_user.id:
        flash('You do not have permission to edit this department', 'danger')
        return redirect(url_for('main.view_department', department_id=department_id))
    
    if request.method == 'POST':
        department.name = request.form.get('name')
        department.description = request.form.get('description')
        
        # Only admin can change manager
        if current_user.is_admin:
            manager_id = request.form.get('manager_id')
            department.manager_id = manager_id if manager_id else None
        
        db.session.commit()
        flash('Department updated successfully', 'success')
        return redirect(url_for('main.view_department', department_id=department_id))
    
    managers = User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()
    return render_template('department/edit.html',
                         department=department,
                         managers=managers)

@bp.route('/department/<int:department_id>/invite', methods=['POST'])
@login_required
def invite_department_member(department_id):
    department = Department.query.get_or_404(department_id)
    
    # Check if user has permission to invite
    if not current_user.is_admin and department.manager_id != current_user.id:
        flash('You do not have permission to invite members', 'danger')
        return redirect(url_for('main.view_department', department_id=department_id))
    
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        flash('Invalid user selected', 'danger')
        return redirect(url_for('main.view_department', department_id=department_id))
    
    invitation = DepartmentInvitation(
        department_id=department_id,
        user_id=user_id,
        manager_id=current_user.id
    )
    db.session.add(invitation)
    db.session.commit()
    
    flash('Invitation sent successfully', 'success')
    return redirect(url_for('main.view_department', department_id=department_id))

@bp.route('/manager/team')
@login_required
@manager_required
def manage_team():
    department = Department.query.filter_by(manager_id=current_user.id).first()
    if not department:
        flash('You are not assigned to manage any department', 'warning')
        return redirect(url_for('main.dashboard'))
    
    invitations = DepartmentInvitation.query.filter_by(department_id=department.id).all()
    team_members = User.query.filter_by(department_id=department.id).all()
    
    return render_template('manager/team.html', 
                         department=department,
                         invitations=invitations,
                         team_members=team_members)

@bp.route('/manager/invite', methods=['POST'])
@login_required
@manager_required
def invite_team_member():
    user_id = request.form.get('user_id')
    department = Department.query.filter_by(manager_id=current_user.id).first()
    
    if not department:
        flash('You are not assigned to manage any department', 'danger')
        return redirect(url_for('main.dashboard'))
    
    invitation = DepartmentInvitation(
        department_id=department.id,
        user_id=user_id,
        manager_id=current_user.id
    )
    db.session.add(invitation)
    
    notification = AdminNotification(
        title='New Team Invitation',
        content=f'Manager {current_user.username} invited a new member to {department.name}',
        type='invitation_sent',
        related_user_id=user_id,
        related_dept_id=department.id
    )
    db.session.add(notification)
    db.session.commit()
    
    flash('Invitation sent successfully', 'success')
    return redirect(url_for('main.manage_team'))

@bp.route('/invitations')
@login_required
def my_invitations():
    invitations = DepartmentInvitation.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).all()
    return render_template('invitations.html', invitations=invitations)

@bp.route('/invitation/<int:invite_id>/respond', methods=['POST'])
@login_required
def respond_invitation(invite_id):
    invitation = DepartmentInvitation.query.get_or_404(invite_id)
    response = request.form.get('response')
    
    if invitation.user_id != current_user.id:
        flash('Invalid invitation', 'danger')
        return redirect(url_for('main.dashboard'))
    
    invitation.status = response
    if response == 'accepted':
        current_user.department_id = invitation.department_id
        notification = AdminNotification(
            title='Invitation Accepted',
            content=f'{current_user.username} accepted invitation to join {invitation.department.name}',
            type='invitation_accepted',
            related_user_id=current_user.id,
            related_dept_id=invitation.department_id
        )
        db.session.add(notification)
    
    db.session.commit()
    flash(f'Invitation {response}', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/admin/notifications')
@login_required
@admin_required
def admin_notifications():
    # Get unread notifications first, then read ones, both ordered by creation date
    notifications = AdminNotification.query.order_by(
        AdminNotification.read.asc(),
        AdminNotification.created_at.desc()
    ).all()
    return render_template('admin/notifications.html', notifications=notifications)

@bp.route('/admin/notification/<int:notification_id>/read', methods=['POST'])
@login_required
@admin_required
def mark_notification_read(notification_id):
    notification = AdminNotification.query.get_or_404(notification_id)
    notification.read = True
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/admin/notifications/mark-all-read', methods=['POST'])
@login_required
@admin_required
def mark_all_notifications_read():
    AdminNotification.query.filter_by(read=False).update({'read': True})
    db.session.commit()
    return jsonify({'success': True})
