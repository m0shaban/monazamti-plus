from flask import render_template, redirect, url_for, flash, request, jsonify, session, Response, abort, current_app
from flask_login import login_required, current_user, logout_user
from app.main import bp
from app.models import Project, Task, User, Department, UserRole, TimeEntry, RiskAssessment, TaskRating
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import json
import pytz
import csv
import io
import os
from app.utils.date_utils import utc_now
from app.utils.decorators import admin_required, manager_required

@bp.route('/', endpoint='index')
@login_required
def dashboard():
    try:
        user_projects = Project.query.filter_by(created_by=current_user.id).all()
        assigned_tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        completed_tasks = Task.query.filter_by(assigned_to=current_user.id, status='Completed').count()
        pending_tasks = Task.query.filter_by(assigned_to=current_user.id).filter(Task.status != 'Completed').count()

        return render_template('dashboard.html',
                               title='Dashboard',
                               user_projects=user_projects,
                               assigned_tasks=assigned_tasks,
                               completed_tasks=completed_tasks,
                               pending_tasks=pending_tasks)
    except Exception as e:
        flash(f"Error loading dashboard: {e}", 'danger')
        return render_template('dashboard.html', title='Dashboard', user_projects=[], assigned_tasks=[], completed_tasks=0, pending_tasks=0)

@bp.route('/dashboard', endpoint='dashboard')
@login_required
def show_dashboard():
    return dashboard()

@bp.route('/projects')
@login_required
def projects():
    try:
        projects = Project.query.all()
        return render_template('projects.html', title='Projects', projects=projects)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('projects.html', title='Projects', projects=[])

@bp.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # حساب إحصائيات المهام
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == 'Completed')
        in_progress_tasks = sum(1 for task in tasks if task.status == 'In Progress')
        not_started_tasks = sum(1 for task in tasks if task.status == 'Not Started')
        blocked_tasks = sum(1 for task in tasks if task.status == 'Blocked')
        
        # إنشاء قاموس لإحصائيات المهام
        task_stats = {
            'total': total_tasks,
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'not_started': not_started_tasks,
            'blocked': blocked_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
        
        return render_template('project_detail.html',
                              title=project.name,
                              project=project,
                              tasks=tasks,
                              task_stats=task_stats)
    except OperationalError:
        flash('حدث خطأ في الاتصال بقاعدة البيانات. الرجاء المحاولة مرة أخرى لاحقًا.', 'danger')
        return redirect(url_for('main.projects'))
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@bp.route('/project/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        department_id = request.form.get('department_id')
        priority = request.form.get('priority')
        deadline_str = request.form.get('deadline')
        
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d') if deadline_str else None
            
            project = Project(
                name=name,
                description=description,
                status='Active',
                created_by=current_user.id,
                department_id=department_id if department_id else None,
                priority=priority,
                deadline=deadline,
                created_at=utc_now(),
                progress=0
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Project created successfully', 'success')
            return redirect(url_for('main.project_detail', project_id=project.id))
        except Exception as e:
            flash(f'Error creating project: {str(e)}', 'danger')
    
    departments = Department.query.all()
    return render_template('create_project.html', 
                          title='Create Project',
                          departments=departments)

@bp.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to edit this project
    if project.created_by != current_user.id and not current_user.is_admin and not current_user.is_project_manager:
        flash('You do not have permission to edit this project.', 'danger')
        return redirect(url_for('main.project_detail', project_id=project.id))
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.status = request.form.get('status')
        project.priority = request.form.get('priority')
        deadline_str = request.form.get('deadline')
        project.deadline = datetime.strptime(deadline_str, '%Y-%m-%d') if deadline_str else None
        project.progress = int(request.form.get('progress', 0))
        project.department_id = request.form.get('department_id') or None
        
        try:
            db.session.commit()
            flash('Project updated successfully', 'success')
            return redirect(url_for('main.project_detail', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating project: {str(e)}', 'danger')
    
    departments = Department.query.all()
    return render_template('edit_project.html',
                          title=f'Edit {project.name}',
                          project=project,
                          departments=departments)

@bp.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # التحقق من صلاحيات الحذف
        if project.created_by != current_user.id and not current_user.is_admin and not current_user.is_project_manager:
            flash('ليس لديك صلاحية لحذف هذا المشروع.', 'danger')
            return redirect(url_for('main.project_detail', project_id=project.id))
        
        # حذف المهام المرتبطة بالمشروع أولاً
        Task.query.filter_by(project_id=project.id).delete()
        
        # حذف المشروع نفسه
        project_name = project.name  # نحفظ الاسم قبل الحذف
        db.session.delete(project)
        db.session.commit()
        
        flash(f'تم حذف المشروع "{project_name}" بنجاح.', 'success')
        return redirect(url_for('main.projects'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المشروع: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@bp.route('/task/create', methods=['GET', 'POST'])
@login_required
def create_task():
    # Get data for the form
    try:
        projects = Project.query.all()
        team_members = User.query.all()
        
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            project_id = request.form.get('project_id')
            assigned_to = request.form.get('assigned_to')
            status = request.form.get('status', 'Not Started')
            priority = request.form.get('priority')
            due_date_str = request.form.get('due_date')
            estimated_hours = request.form.get('estimated_hours')
            
            # Validation
            if not title or not project_id:
                flash('Title and Project are required fields', 'danger')
                return render_template('create_task.html', 
                                      title='Create Task',
                                      projects=projects,
                                      team_members=team_members)
            
            # Create the task
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
                estimated_hours = float(estimated_hours) if estimated_hours else 0
                
                task = Task(
                    title=title,
                    description=description,
                    project_id=project_id,
                    assigned_to=assigned_to if assigned_to else None,
                    created_by=current_user.id,
                    status=status,
                    priority=priority,
                    due_date=due_date,
                    created_at=utc_now(),
                    estimated_hours=estimated_hours
                )
                
                db.session.add(task)
                db.session.commit()
                
                flash('Task created successfully', 'success')
                return redirect(url_for('main.tasks'))
            except Exception as e:
                flash(f'Error creating task: {str(e)}', 'danger')
                
        return render_template('create_task.html', 
                            title='Create Task',
                            projects=projects,
                            team_members=team_members)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return redirect(url_for('main.dashboard'))

@bp.route('/tasks')
@login_required
def tasks():
    try:
        # الحصول على مهام المستخدم
        assigned_tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        
        # حساب الإحصائيات
        total_tasks = len(assigned_tasks)
        completed_tasks = sum(1 for task in assigned_tasks if task.status == 'Completed')
        in_progress_tasks = sum(1 for task in assigned_tasks if task.status == 'In Progress')
        blocked_tasks = sum(1 for task in assigned_tasks if task.status == 'Blocked')
        not_started_tasks = total_tasks - completed_tasks - in_progress_tasks - blocked_tasks
        
        # المهام التي أنشأها المستخدم or المدير
        if current_user.is_admin or current_user.is_project_manager:
            managed_tasks = Task.query.filter_by(created_by=current_user.id).all()
        else:
            managed_tasks = []
        
        return render_template('tasks.html',
                               title='المهام',
                               assigned_tasks=assigned_tasks,
                               managed_tasks=managed_tasks,
                               total_tasks=total_tasks,
                               completed_tasks=completed_tasks,
                               in_progress_tasks=in_progress_tasks,
                               blocked_tasks=blocked_tasks,
                               not_started_tasks=not_started_tasks)
    except OperationalError:
        flash('حدث خطأ في الاتصال بقاعدة البيانات. الرجاء المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('main.dashboard'))

@bp.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        return render_template('task_detail.html', title=task.title, task=task)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return redirect(url_for('main.tasks'))

@bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    projects = Project.query.all()
    team_members = User.query.all()
    
    # Check if user has permission to edit this task
    if task.created_by != current_user.id and task.assigned_to != current_user.id and not current_user.is_admin and not current_user.is_project_manager:
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('main.task_detail', task_id=task.id))
    
    if request.method == 'POST':
        # Update the task with form data
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.project_id = request.form.get('project_id')
        task.assigned_to = request.form.get('assigned_to') or None
        task.status = request.form.get('status')
        task.priority = request.form.get('priority')
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        try:
            db.session.commit()
            flash('Task updated successfully', 'success')
            return redirect(url_for('main.task_detail', task_id=task.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating task: {str(e)}', 'danger')
        
    return render_template('edit_task.html', 
                         title=f"Edit {task.title}",
                         task=task,
                         projects=projects,
                         team_members=team_members)

@bp.route('/task/<int:task_id>/update_status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if user has permission
    if task.assigned_to != current_user.id and task.created_by != current_user.id and not current_user.is_admin and not current_user.is_project_manager:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.json
    new_status = data.get('status')
    
    if new_status in ['Not Started', 'In Progress', 'Completed', 'Blocked']:
        task.status = new_status
        
        # If task is completed, record the completion time
        if new_status == 'Completed':
            task.completed_at=utc_now()
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Invalid status'}), 400

@bp.route('/task/<int:task_id>/rate', methods=['POST'])
@login_required
def rate_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        
        if not current_user.is_admin and task.created_by != current_user.id and task.project.created_by != current_user.id:
            flash('ليس لديك صلاحية لتقييم هذه المهمة', 'danger')
            return redirect(url_for('main.task_detail', task_id=task_id))
        
        # الحصول على بيانات التقييم
        score = int(request.form.get('score', 0))
        feedback = request.form.get('feedback', '')
        
        if score < 1 or score > 5:
            flash('يجب أن يكون التقييم بين 1 and 5', 'danger')
            return redirect(url_for('main.task_detail', task_id=task_id))
        
        # التحقق من وجود تقييم سابق لهذا المستخدم لهذه المهمة
        existing_rating = TaskRating.query.filter_by(
            task_id=task_id,
            user_id=current_user.id
        ).first()
        
        if existing_rating:
            # تحديث التقييم الموجود
            existing_rating.score = score
            existing_rating.feedback = feedback
            existing_rating.updated_at = utc_now()
            db.session.commit()
            flash('تم تحديث تقييمك بنجاح', 'success')
        else:
            # إنشاء تقييم جديد
            new_rating = TaskRating(
                task_id=task_id,
                user_id=current_user.id,
                score=score,
                feedback=feedback
            )
            db.session.add(new_rating)
            db.session.commit()
            flash('تم إضافة تقييمك بنجاح', 'success')
        
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء التقييم: {str(e)}', 'danger')
        return redirect(url_for('main.task_detail', task_id=task_id))

@bp.route('/eisenhower_matrix')
@login_required
def eisenhower_matrix():
    try:
        # Get tasks for the current user
        tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        
        # Separate tasks into quadrants
        q1_tasks = [] # Important & Urgent
        q2_tasks = [] # Important & Not Urgent
        q3_tasks = [] # Not Important & Urgent
        q4_tasks = [] # Not Important & Not Urgent
        
        for task in tasks:
            # Determine importance and urgency
            importance = task.importance if hasattr(task, 'importance') else 0
            urgency = task.urgency if hasattr(task, 'urgency') else 0
            
            # If importance and urgency aren't set, determine based on priority and due date
            if importance == 0:
                importance = 3 if task.priority in ['High', 'Critical'] else 1
            
            if urgency == 0:
                # Tasks due within 2 days are urgent
                if task.due_date and (task.due_date - datetime.now()).days <= 2:
                    urgency = 3
                else:
                    urgency = 1
            
            # Assign to quadrants
            if importance > 2 and urgency > 2:
                q1_tasks.append(task)
            elif importance > 2 and urgency <= 2:
                q2_tasks.append(task)
            elif importance <= 2 and urgency > 2:
                q3_tasks.append(task)
            else:
                q4_tasks.append(task)
        
        return render_template('eisenhower_matrix.html', 
                              title='Eisenhower Matrix',
                              q1_tasks=q1_tasks,
                              q2_tasks=q2_tasks,
                              q3_tasks=q3_tasks,
                              q4_tasks=q4_tasks)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('eisenhower_matrix.html', title='Eisenhower Matrix')

@bp.route('/time_tracking')
@login_required
def time_tracking():
    try:
        # Get all projects for dropdown
        projects = Project.query.all()
        
        # Get time entries for the current user
        time_entries = TimeEntry.query.filter_by(user_id=current_user.id).order_by(TimeEntry.start_time.desc()).all()
        
        # Calculate total hours and cost
        total_hours = sum(entry.duration or 0 for entry in time_entries)
        total_cost = sum(entry.calculate_cost() for entry in time_entries)
        
        # Data for charts
        project_names = [project.name for project in projects[:5]] if projects else []
        project_hours = [10, 15, 8, 12, 5]  # Mock hours per project for now
        
        # Data for daily hours chart
        today = datetime.now()
        date_labels = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
        daily_hours = [4, 7, 6, 8, 5, 3, 6]  # Mock hours per day for now
        
        return render_template('time_tracking.html', 
                              title='Time Tracking',
                              time_entries=time_entries,
                              projects=projects,
                              total_hours=total_hours,
                              total_cost=total_cost,
                              project_names=project_names,
                              project_hours=project_hours,
                              date_labels=date_labels,
                              daily_hours=daily_hours)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('time_tracking.html', 
                              title='Time Tracking',
                              time_entries=[],
                              projects=[],
                              total_hours=0,
                              total_cost=0,
                              project_names=[],
                              project_hours=[],
                              date_labels=[],
                              daily_hours=[])

@bp.route('/add_time_entry', methods=['POST'])
@login_required
def add_time_entry():
    try:
        project_id = request.form.get('project_id')
        task_id = request.form.get('task_id')
        description = request.form.get('description')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        billable = 'billable' in request.form
        hourly_rate = float(request.form.get('hourly_rate', 0))
        
        # التحقق من البيانات المطلوبة
        if not project_id:
            flash('يرجى تحديد المشروع', 'danger')
            return redirect(url_for('main.time_tracking'))
        
        # تحويل التواريخ من النص إلى كائنات datetime
        start_time = datetime.fromisoformat(start_time_str) if start_time_str else utc_now()
        end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
        
        # حساب المدة إذا توفر وقت البداية والنهاية
        duration = None
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds() / 3600  # تحويل إلى ساعات
        
        # إنشاء سجل وقت جديد
        time_entry = TimeEntry(
            user_id=current_user.id,
            project_id=project_id,
            task_id=task_id if task_id else None,
            description=description,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            billable=billable,
            hourly_rate=hourly_rate
        )
        
        db.session.add(time_entry)
        db.session.commit()
        
        flash('تمت إضافة تسجيل الوقت بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إضافة تسجيل الوقت: {str(e)}', 'danger')
    
    return redirect(url_for('main.time_tracking'))

@bp.route('/api/project/<int:project_id>/tasks')
@login_required
def get_project_tasks(project_id):
    try:
        tasks = Task.query.filter_by(project_id=project_id).all()
        tasks_data = [{'id': task.id, 'title': task.title} for task in tasks]
        return jsonify({'success': True, 'tasks': tasks_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/projects_report')
@login_required
def projects_report():
    try:
        projects = Project.query.all()
        return render_template('projects_report.html', title='Project Reports', projects=projects)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('projects_report.html', title='Project Reports', projects=[])

@bp.route('/project/<int:project_id>/reports')
@login_required
def project_reports(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        # Data for report charts
        task_status_counts = {
            'Completed': Task.query.filter_by(project_id=project_id, status='Completed').count(),
            'In Progress': Task.query.filter_by(project_id=project_id, status='In Progress').count(),
            'Not Started': Task.query.filter_by(project_id=project_id, status='Not Started').count(),
            'Blocked': Task.query.filter_by(project_id=project_id, status='Blocked').count()
        }
        
        task_status_data = list(task_status_counts.values())
        
        # Mock time data for now
        time_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        time_data = [12, 19, 8, 15]
        
        # Mock expense data for now
        expense_categories = ['Labor', 'Materials', 'Software', 'Travel', 'Other']
        expense_values = [5000, 2000, 1500, 800, 700]
        
        # Mock progress data
        task_progress = {task.id: task.id * 10 % 100 for task in tasks}  # For demo
        
        return render_template('project_reports.html',
                            title=f'{project.name} Report',
                            project=project,
                            tasks=tasks,
                            task_status_data=task_status_data,
                            time_labels=time_labels,
                            time_data=time_data,
                            expense_categories=expense_categories,
                            expense_values=expense_values,
                            task_progress=task_progress,
                            now=datetime.now(),
                            total_expenses='$10,000',  # Mock data
                            labor_costs='$5,000',      # Mock data
                            other_expenses='$5,000')   # Mock data
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return redirect(url_for('main.projects_report'))

@bp.route('/team_performance')
@login_required
def team_performance():
    try:
        if not current_user.is_project_manager and not current_user.is_admin:
            flash('Access denied. Manager privileges required.', 'danger')
            return redirect(url_for('main.dashboard'))
            
        # Get team members
        if current_user.is_admin:
            team_members = User.query.all()
        else:
            # For project managers, get members of their department or projects
            department_id = current_user.department_id
            if department_id:
                team_members = User.query.filter_by(department_id=department_id).all()
            else:
                team_members = []
        
        # Get performance metrics for each member
        for member in team_members:
            member.task_count = Task.query.filter_by(assigned_to=member.id).count()
            member.completed_tasks = Task.query.filter_by(assigned_to=member.id, status='Completed').count()
            member.completion_rate = (member.completed_tasks / member.task_count * 100) if member.task_count > 0 else 0
        
        return render_template('team_performance.html', title='Team Performance', team_members=team_members)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('team_performance.html', title='Team Performance', team_members=[])

@bp.route('/risks_dashboard')
@login_required
def risks_dashboard():
    try:
        # Get all projects
        projects = Project.query.all()
        
        # Handle case when there are no projects
        if not projects:
            return render_template('risks_dashboard.html', 
                                  title='Risk Dashboard',
                                  risks=[],
                                  projects=[],
                                  risks_by_project={},
                                  extreme_risks=[],
                                  high_risks=[],
                                  medium_risks=[],
                                  low_risks=[])
        
        # Get risk data from the database
        risks = RiskAssessment.query.all()
        
        # If no risks in the database, create mock data for the demo
        if not risks:
            risks = []
            for i in range(1, 20):
                severity = i % 25  # Will create a range of severities
                project_id = (i % len(projects)) + 1 if projects else 1
                
                # Get a valid project from the list
                project = next((p for p in projects if p.id == project_id), projects[0])
                
                risks.append({
                    'id': i,
                    'title': f'Risk {i}',
                    'description': f'Description for risk {i}',
                    'impact': (i % 5) + 1,
                    'probability': ((i + 2) % 5) + 1,
                    'severity': severity,
                    'status': 'Open' if i % 3 == 0 else ('Mitigated' if i % 3 == 1 else 'Closed'),
                    'project_id': project_id,
                    'project': project
                })
        
        # Group risks by project
        risks_by_project = defaultdict(list)
        for risk in risks:
            project = getattr(risk, 'project', None)
            if project:
                risks_by_project[project].append(risk)
        
        # Calculate risk categories based on severity
        extreme_risks = [r for r in risks if getattr(r, 'severity', 0) > 16]
        high_risks = [r for r in risks if 9 < getattr(r, 'severity', 0) <= 16]
        medium_risks = [r for r in risks if 4 < getattr(r, 'severity', 0) <= 9]
        low_risks = [r for r in risks if getattr(r, 'severity', 0) <= 4]
        
        return render_template('risks_dashboard.html', 
                              title='Risk Dashboard',
                              risks=risks,
                              projects=projects,
                              risks_by_project=risks_by_project,
                              extreme_risks=extreme_risks,
                              high_risks=high_risks,
                              medium_risks=medium_risks,
                              low_risks=low_risks)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('risks_dashboard.html', 
                              title='Risk Dashboard',
                              risks=[],
                              projects=[],
                              risks_by_project={},
                              extreme_risks=[],
                              high_risks=[],
                              medium_risks=[],
                              low_risks=[])

@bp.route('/project/<int:project_id>/risks')
@login_required
def risk_management(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        risks = RiskAssessment.query.filter_by(project_id=project_id).all()
        
        return render_template('risk_management.html', 
                            title=f'Risk Management - {project.name}',
                            project=project,
                            risks=risks)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return redirect(url_for('main.risks_dashboard'))

@bp.route('/project/<int:project_id>/add_risk', methods=['POST'])
@login_required
def add_risk(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        impact = int(request.form.get('impact', 1))
        probability = int(request.form.get('probability', 1))
        status = request.form.get('status', 'Open')
        mitigation_plan = request.form.get('mitigation_plan', '')
        contingency_plan = request.form.get('contingency_plan', '')
        
        # Calculate severity
        severity = impact * probability
        
        # Create the risk
        risk = RiskAssessment(
            project_id=project_id,
            title=title,
            description=description,
            impact=impact,
            probability=probability,
            severity=severity,
            mitigation_plan=mitigation_plan,
            contingency_plan=contingency_plan,
            created_by=current_user.id,
            created_at=utc_now(),
            status=status
        )
        
        db.session.add(risk)
        db.session.commit()
        
        flash('Risk added successfully', 'success')
    except Exception as e:
        flash(f'Error adding risk: {str(e)}', 'danger')
    
    return redirect(url_for('main.risk_management', project_id=project_id))

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', title='Profile')

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bio = request.form.get('bio')
        avatar = request.form.get('avatar')
        
        # Update user
        user = current_user
        user.username = username
        user.email = email
        user.phone = phone
        user.bio = bio
        user.avatar = avatar
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')
    
    return redirect(url_for('main.profile'))

@bp.route('/settings')
@login_required
def settings():
    # Ensure user has settings
    current_user.get_or_create_settings()
    
    return render_template('settings.html', title='الإعدادات')

@bp.route('/settings/account', methods=['POST'])
@login_required
def update_account_settings():
    try:
        settings = current_user.get_or_create_settings()
        
        # Update settings
        settings.language = request.form.get('language', 'ar')
        settings.timezone = request.form.get('timezone', 'Africa/Cairo')
        settings.show_activity_status = 'activity_status' in request.form
        
        # Apply timezone to session
        session['timezone'] = settings.timezone
        
        db.session.commit()
        flash('تم تحديث إعدادات الحساب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث الإعدادات: {str(e)}', 'danger')
        
    return redirect(url_for('main.settings'))

@bp.route('/settings/notifications', methods=['POST'])
@login_required
def update_notification_settings():
    try:
        settings = current_user.get_or_create_settings()
        
        # Update email notifications
        email_notifications = {
            'task_assigned': 'email_task_assigned' in request.form,
            'task_updated': 'email_task_update' in request.form,
            'project_updated': 'email_project_update' in request.form
        }
        
        # Update system notifications
        system_notifications = {
            'task_reminder': 'sys_task_reminder' in request.form,
            'comments': 'sys_comments' in request.form,
            'mentions': 'sys_mentions' in request.form
        }
        
        settings.email_notifications = email_notifications
        settings.system_notifications = system_notifications
        
        db.session.commit()
        flash('تم تحديث إعدادات الإشعارات بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث الإعدادات: {str(e)}', 'danger')
        
    return redirect(url_for('main.settings'))

@bp.route('/settings/appearance', methods=['POST'])
@login_required
def update_appearance_settings():
    try:
        settings = current_user.get_or_create_settings()
        
        # Update appearance settings
        settings.theme = request.form.get('theme', 'light')
        settings.primary_color = request.form.get('primary_color', '4568dc')
        settings.compact_mode = 'compact_mode' in request.form
        
        db.session.commit()
        flash('تم تحديث إعدادات المظهر بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث الإعدادات: {str(e)}', 'danger')
        
    return redirect(url_for('main.settings'))

@bp.route('/settings/password', methods=['POST'])
@login_required
def update_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords
        if not check_password_hash(current_user.password, current_password):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            return redirect(url_for('main.settings'))
            
        if new_password != confirm_password:
            flash('كلمة المرور الجديدة وتأكيدها غير متطابقين', 'danger')
            return redirect(url_for('main.settings'))
            
        if len(new_password) < 8:
            flash('كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل', 'danger')
            return redirect(url_for('main.settings'))
        
        # Update password
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        
        flash('تم تغيير كلمة المرور بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تغيير كلمة المرور: {str(e)}', 'danger')
        
    return redirect(url_for('main.settings'))

@bp.route('/settings/logout-all', methods=['POST'])
@login_required
def logout_all_devices():
    try:
        # Generate new fs_uniquifier to invalidate all existing sessions
        current_user.fs_uniquifier = os.urandom(16).hex()
        db.session.commit()
        
        # Logout current session too
        logout_user()
        flash('تم تسجيل الخروج من جميع الأجهزة بنجاح', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تسجيل الخروج: {str(e)}', 'danger')
        
    return redirect(url_for('main.settings'))

@bp.route('/settings/download-data', methods=['POST'])
@login_required
def download_data():
    try:
        # Create a CSV with user data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write user info
        writer.writerow(['User Information'])
        writer.writerow(['ID', 'Username', 'Email', 'Role', 'Created At'])
        writer.writerow([
            current_user.id,
            current_user.username,
            current_user.email,
            current_user.role,
            current_user.created_at.strftime('%Y-%m-%d %H:%M:%S') if current_user.created_at else ''
        ])
        
        # Write projects
        writer.writerow([])
        writer.writerow(['Projects'])
        writer.writerow(['ID', 'Name', 'Status', 'Created At', 'Deadline'])
        for project in current_user.created_projects:
            writer.writerow([
                project.id,
                project.name,
                project.status,
                project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else '',
                project.deadline.strftime('%Y-%m-%d') if project.deadline else ''
            ])
        
        # Write tasks
        writer.writerow([])
        writer.writerow(['Tasks'])
        writer.writerow(['ID', 'Title', 'Status', 'Project', 'Due Date'])
        for task in current_user.assigned_tasks:
            writer.writerow([
                task.id,
                task.title,
                task.status,
                task.project.name if task.project else '',
                task.due_date.strftime('%Y-%m-%d') if task.due_date else ''
            ])
        
        # Prepare the response
        output.seek(0)
        
        # Create response
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=user_data_{now}.csv'
            }
        )
    except Exception as e:
        flash(f'حدث خطأ أثناء تنزيل البيانات: {str(e)}', 'danger')
        return redirect(url_for('main.settings'))

@bp.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    try:
        # Verify confirmation
        if request.form.get('delete_confirm') != 'حذف':
            flash('تأكيد غير صحيح. الحساب لم يتم حذفه.', 'danger')
            return redirect(url_for('main.settings'))
        
        # Don't allow deleting the admin account
        if current_user.is_admin and User.query.filter_by(role=UserRole.ADMIN.value).count() <= 1:
            flash('لا يمكن حذف حساب المسؤول الوحيد في النظام.', 'danger')
            return redirect(url_for('main.settings'))
        
        # Delete the user
        user_id = current_user.id
        logout_user()
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()
        
        flash('تم حذف حسابك بنجاح.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الحساب: {str(e)}', 'danger')
        
    return redirect(url_for('main.settings'))

@bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    users = User.query.all()
    return render_template('admin/users.html', 
                          title='User Management',
                          users=users,
                          UserRole=UserRole)

@bp.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    departments = Department.query.all()
    
    if request.method == 'POST':
        # Update user with form data
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        user.department_id = request.form.get('department_id') or None
        
        # Update password if provided
        password = request.form.get('password')
        if password:
            user.password = generate_password_hash(password)
        
        try:
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('main.admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('admin/edit_user.html',
                         title=f'Edit User - {user.username}',
                         user=user,
                         departments=departments,
                         roles=UserRole)

@bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Ensure admin can't delete themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('main.admin_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('main.admin_users'))

@bp.route('/admin/departments')
@login_required
def admin_departments():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    departments = Department.query.all()
    
    # For each department, ensure members is properly loaded
    for dept in departments:
        # Force evaluation of lazy relationship if needed
        _ = dept.members.count()
    
    return render_template('admin/departments.html', 
                          title='Department Management',
                          departments=departments)

@bp.route('/department/<int:department_id>')
@login_required
def department_detail(department_id):
    try:
        department = Department.query.get_or_404(department_id)
        
        # Get department employees
        employees = User.query.filter_by(department_id=department_id).all()
        
        # Get projects in this department
        projects = Project.query.filter_by(department_id=department_id).all()
        
        # Get active projects
        active_projects = [p for p in projects if p.status == 'Active']
        
        # Get pending tasks
        pending_tasks = Task.query.join(Project).filter(
            Project.department_id == department_id,
            Task.status != 'Completed'
        ).all()
        
        # Mock performance data
        performance_dates = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        performance_data = [65, 59, 80, 81, 85, 90]
        
        return render_template('department/view.html',
                             title=department.name,
                             department=department,
                             employees=employees,
                             projects=projects,
                             active_projects=active_projects,
                             pending_tasks=pending_tasks,
                             performance_dates=performance_dates,
                             performance_data=performance_data)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return redirect(url_for('main.admin_departments'))

@bp.route('/department/create', methods=['GET', 'POST'])
@login_required
def create_department():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    managers = User.query.filter_by(role='project_manager').all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        manager_id = request.form.get('manager_id') or None
        
        try:
            department = Department(
                name=name,
                description=description,
                manager_id=manager_id,
                created_at=utc_now()
            )
            
            db.session.add(department)
            db.session.commit()
            
            flash('Department created successfully', 'success')
            return redirect(url_for('main.admin_departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating department: {str(e)}', 'danger')
        
    return render_template('admin/create_department.html',
                          title='Create Department',
                          managers=managers)

@bp.route('/department/<int:department_id>/view', endpoint='department_view')
@login_required
def view_department_details(department_id):
    department = Department.query.get_or_404(department_id)
    
    # Count active projects in this department
    active_projects = Project.query.filter_by(
        department_id=department.id, 
        status='Active'
    ).count()
    
    # Get department members with their roles
    members = User.query.filter_by(department_id=department.id).all()
    
    return render_template('admin/view_department.html', 
                          department=department,
                          members=members,
                          active_projects=active_projects)

@bp.route('/department/<int:department_id>/invite', methods=['POST'])
@login_required
def invite_department_member(department_id):
    department = Department.query.get_or_404(department_id)
    
    # Check if current user is authorized
    if not current_user.is_admin and department.manager_id != current_user.id:
        flash('Permission denied', 'danger')
        return redirect(url_for('main.department_detail', department_id=department_id))
    
    # Get form data
    user_id = request.form.get('user_id')
    
    if not user_id:
        flash('Please select a user to invite', 'warning')
        return redirect(url_for('main.department_detail', department_id=department_id))
    
    # Update user's department
    try:
        user = User.query.get(user_id)
        if user:
            user.department_id = department_id
            db.session.commit()
            flash(f'{user.username} has been added to {department.name}', 'success')
        else:
            flash('User not found', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error inviting user: {str(e)}', 'danger')
    
    return redirect(url_for('main.department_detail', department_id=department_id))

@bp.route('/admin/user/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        department_id = request.form.get('department_id')
        
        # Basic validation
        if not username or not email or not password:
            flash('Username, email, and password are required', 'danger')
            departments = Department.query.all()
            return render_template('admin/create_user.html', 
                                title='Create User',
                                departments=departments,
                                roles=UserRole)
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            departments = Department.query.all()
            return render_template('admin/create_user.html', 
                                title='Create User',
                                departments=departments,
                                roles=UserRole)
                                
        if User.query.filter_by(email=email).first():
            flash('Email already in use', 'danger')
            departments = Department.query.all()
            return render_template('admin/create_user.html', 
                                title='Create User',
                                departments=departments,
                                roles=UserRole)
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                role=role,
                department_id=department_id if department_id else None,
                created_at=utc_now()
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('User created successfully', 'success')
            return redirect(url_for('main.admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
    
    departments = Department.query.all()
    return render_template('admin/create_user.html', 
                          title='Create User',
                          departments=departments,
                          roles=UserRole)

@bp.route('/manager/dashboard')
@login_required
def manager_dashboard():
    if not current_user.is_project_manager and not current_user.is_admin:
        flash('Access denied. Manager privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    try:
        # Get managed projects
        if current_user.is_admin:
            projects = Project.query.all()
        else:
            # Get projects in manager's department or created by manager
            projects = Project.query.filter(
                (Project.created_by == current_user.id) or 
                (Project.department_id == current_user.department_id)
            ).all()
        
        # Get team members
        if current_user.is_admin:
            team_members = User.query.all()
        else:
            # Get members of manager's department
            team_members = User.query.filter_by(department_id=current_user.department_id).all()
        
        # Add performance rating to team members
        for member in team_members:
            # Calculate performance rating based on task completion
            tasks_count = Task.query.filter_by(assigned_to=member.id).count()
            completed_tasks = Task.query.filter_by(assigned_to=member.id, status='Completed').count()
            
            # Default rating is 3 out of 5
            member.performance_rating = 3
            
            # Adjust rating based on task completion rate
            if tasks_count > 0:
                completion_rate = completed_tasks / tasks_count
                if completion_rate > 0.8:
                    member.performance_rating = 5
                elif completion_rate > 0.6:
                    member.performance_rating = 4
                elif completion_rate < 0.3:
                    member.performance_rating = 2
                elif completion_rate < 0.1:
                    member.performance_rating = 1
            
        # Data for charts
        team_labels = [member.username for member in team_members[:5]] if team_members else []
        team_performance_data = [75, 65, 80, 60, 90]  # Mock performance data
        
        # Get upcoming milestones (tasks with due dates)
        upcoming_milestones = Task.query.filter(
            Task.status != 'Completed',
            Task.due_date.isnot(None),
            Task.due_date > datetime.now()
        ).order_by(Task.due_date).limit(5).all()
        
        return render_template('manager_dashboard.html',
                              title='Manager Dashboard',
                              projects=projects,
                              team_members=team_members,
                              team_labels=team_labels,
                              team_performance_data=team_performance_data,
                              upcoming_milestones=upcoming_milestones)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('manager_dashboard.html',
                              title='Manager Dashboard',
                              projects=[],
                              team_members=[],
                              team_labels=[],
                              team_performance_data=[],
                              upcoming_milestones=[])

@bp.route('/manager/team')
@login_required
def team_management():
    if not current_user.is_project_manager and not current_user.is_admin:
        flash('Access denied. Manager privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Get team members based on user role
        if current_user.is_admin:
            team_members = User.query.all()
        else:
            # Get members of manager's department
            team_members = User.query.filter_by(department_id=current_user.department_id).all()
        
        # Get users that can be invited to the team
        if current_user.is_admin:
            available_users = User.query.all()
        else:
            # Users not in any department
            available_users = User.query.filter_by(department_id=None).all()
        
        # Get department
        if current_user.is_admin:
            department = Department.query.first()  # Default for admin
        else:
            department = Department.query.get(current_user.department_id)
        
        # Get departments for dropdown
        departments = Department.query.all()
        
        # Get projects for task assignment
        if current_user.is_admin:
            projects = Project.query.all()
        else:
            projects = Project.query.filter(
                (Project.created_by == current_user.id) or 
                (Project.department_id == current_user.department_id)
            ).all()
        
        return render_template('manager/team.html',
                              title='Team Management',
                              team_members=team_members,
                              available_users=available_users,
                              invitations=[],  # Placeholder for invitation system
                              department=department,
                              departments=departments,
                              projects=projects)
    except OperationalError:
        flash('Database schema error. Please run the database fix script.', 'danger')
        return render_template('manager/team.html',
                              title='Team Management',
                              team_members=[],
                              available_users=[],
                              invitations=[],
                              department=None,
                              departments=[])

@bp.route('/manager/team/invite', methods=['POST'])
@login_required
def invite_team_member():
    if not current_user.is_project_manager and not current_user.is_admin:
        flash('Access denied. Manager privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        email = request.form.get('email')
        role = request.form.get('role')
        department_id = request.form.get('department_id')
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Update existing user's department
            if department_id:
                user.department_id = department_id
                db.session.commit()
                flash(f'User {user.username} has been added to the department', 'success')
            else:
                flash('Please select a department', 'warning')
        else:
            # In a real implementation, would send an invitation email with registration link
            flash(f'Invitation sent to {email}', 'success')
    
    except Exception as e:
        flash(f'Error inviting team member: {str(e)}', 'danger')
    
    return redirect(url_for('main.team_management'))

@bp.route('/manager/assign_task', methods=['POST'])
@login_required
def assign_task():
    if not current_user.is_project_manager and not current_user.is_admin:
        flash('Access denied. Manager privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        member_id = request.form.get('member_id')
        project_id = request.form.get('project_id')
        task_title = request.form.get('task_title')
        task_description = request.form.get('task_description')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'Medium')
        
        # Validate required fields
        if not member_id or not project_id or not task_title:
            flash('Team member, project, and task title are required', 'warning')
            return redirect(url_for('main.team_management'))
        
        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format', 'warning')
                return redirect(url_for('main.team_management'))
        
        # Create task
        task = Task(
            title=task_title,
            description=task_description,
            project_id=project_id,
            created_by=current_user.id,
            assigned_to=member_id,
            status='Not Started',
            priority=priority,
            due_date=due_date,
            created_at=utc_now()
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task assigned successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning task: {str(e)}', 'danger')
    
    return redirect(url_for('main.team_management'))

@bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    try:
        # Logic to mark notification as read would go here
        flash('Notification marked as read', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('main.admin_notifications'))

@bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    try:
        # Logic to mark all notifications as read would go here
        return {'success': True}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@bp.route('/admin/notifications')
@login_required
def admin_notifications():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Mock notifications for now
    notifications = []
    
    return render_template('admin/notifications.html',
                         title='System Notifications',
                         notifications=notifications)

@bp.route('/documentation')
def documentation():
    """عرض صفحة توثيق النظام"""
    return render_template('documentation.html', title='توثيق النظام')

@bp.route('/technical-documentation')
@login_required
def technical_documentation():
    """عرض صفحة التوثيق التقني (مخفية من القائمة)"""
    # تتطلب هذه الصفحة تسجيل الدخول لكنها غير ظاهرة في القائمة الرئيسية
    if not current_user.is_admin:
        flash('أنت لا تملك الصلاحيات الكافية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('technical_docs.html', title='التوثيق التقني')

@bp.route('/add_task', methods=['POST'])
@login_required
def add_task():
    if not request.form.get('csrf_token') or not current_app.csrf.validate_token(request.form.get('csrf_token')):
        abort(403)

    title = request.form.get('title')
    project_id = request.form.get('project_id')
    
    if not title or not project_id:
        flash('Title and project are required', 'error')
        return redirect(url_for('main.index'))

@bp.route('/validate_project', methods=['POST'])
@login_required
def validate_project():
    if not request.json or not 'project_id' in request.json:
        return jsonify({'error': 'Invalid request'}), 400

@bp.route('/admin/departments/<int:department_id>')
@login_required
@admin_required
def view_department(department_id):
    """View department details"""
    department = Department.query.get_or_404(department_id)
    
    # Count active projects in this department
    active_projects = Project.query.filter_by(
        department_id=department.id, 
        status='Active'
    ).count()
    
    # Get department members with their roles - eager load instead of relying on lazy loading
    members = User.query.filter_by(department_id=department.id).all()
    
    # Force evaluation of members count if needed
    members_count = department.members.count()
    
    return render_template('admin/view_department.html', 
                          department=department,
                          members=members,
                          members_count=members_count,
                          active_projects=active_projects)

@bp.route('/admin/departments/<int:department_id>/edit', endpoint='edit_department')
@login_required
@admin_required
def edit_department(department_id):
    """Edit an existing department"""
    department = Department.query.get_or_404(department_id)
    
    # Get potential managers (users who can be managers)
    potential_managers = User.query.filter(
        User.role.in_([UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value])
    ).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        manager_id = request.form.get('manager_id')
        
        if not name:
            flash('Department name is required', 'danger')
        else:
            # Update department details
            department.name = name
            department.description = description
            
            # Update manager if changed
            if manager_id:
                department.manager_id = int(manager_id)
            else:
                department.manager_id = None
                
            db.session.commit()
            flash('Department updated successfully', 'success')
            return redirect(url_for('main.admin_departments'))
    
    return render_template('admin/edit_department.html', 
                          department=department, 
                          managers=potential_managers)

@bp.route('/admin/departments/<int:department_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(department_id):
    """Delete a department"""
    department = Department.query.get_or_404(department_id)
    
    # Check if department has members
    if department.members.count() > 0:
        # Don't allow deleting departments with members
        flash(f'Cannot delete department "{department.name}" because it has members. Please reassign or remove members first.', 'danger')
        return redirect(url_for('main.admin_departments'))
    
    try:
        # Keep a copy of the name for the flash message
        name = department.name
        
        # Delete the department
        db.session.delete(department)
        db.session.commit()
        
        flash(f'Department "{name}" has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting department: {str(e)}', 'danger')
    
    return redirect(url_for('main.admin_departments'))