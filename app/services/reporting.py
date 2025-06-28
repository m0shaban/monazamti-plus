from datetime import datetime, timedelta
from app.models import Project, Task, User

class ReportingService:
    """
    Simple reporting service that provides project and task analytics
    without requiring pandas.
    """
    
    @staticmethod
    def get_project_completion_rate(department_id=None, start_date=None, end_date=None):
        """Get the percentage of completed projects"""
        query = Project.query
        
        if department_id:
            query = query.filter_by(department_id=department_id)
            
        if start_date:
            query = query.filter(Project.created_at >= start_date)
            
        if end_date:
            query = query.filter(Project.created_at <= end_date)
            
        total_projects = query.count()
        if total_projects == 0:
            return 0
            
        completed_projects = query.filter_by(status='Completed').count()
        return (completed_projects / total_projects) * 100
    
    @staticmethod
    def get_task_completion_stats(user_id=None, project_id=None, period_days=30):
        """Get task completion statistics"""
        query = Task.query
        
        if user_id:
            query = query.filter_by(assigned_to=user_id)
            
        if project_id:
            query = query.filter_by(project_id=project_id)
            
        if period_days:
            start_date = datetime.now() - timedelta(days=period_days)
            query = query.filter(Task.created_at >= start_date)
            
        total_tasks = query.count()
        if total_tasks == 0:
            return {
                'total': 0,
                'completed': 0,
                'completion_rate': 0,
                'on_time': 0,
                'delayed': 0
            }
            
        completed_tasks = query.filter_by(status='Completed').count()
        
        # Tasks completed after due date - use created_at since updated_at might not exist yet
        delayed_tasks = query.filter(
            Task.status == 'Completed',
            Task.due_date < Task.created_at
        ).count()
        
        # Tasks completed on time
        on_time_tasks = completed_tasks - delayed_tasks
        
        return {
            'total': total_tasks,
            'completed': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks) * 100,
            'on_time': on_time_tasks,
            'delayed': delayed_tasks
        }
    
    @staticmethod
    def get_team_workload(department_id):
        """Get workload statistics for team members"""
        team_members = User.query.filter_by(department_id=department_id).all()
        workload_stats = []
        
        for member in team_members:
            active_tasks = Task.query.filter_by(
                assigned_to=member.id,
                status='In Progress'
            ).count()
            
            # Use created_at instead of updated_at for backward compatibility
            completed_tasks = Task.query.filter(
                Task.assigned_to == member.id,
                Task.status == 'Completed',
                Task.created_at >= datetime.now() - timedelta(days=30)
            ).count()
            
            workload_stats.append({
                'user_id': member.id,
                'username': member.username,
                'active_tasks': active_tasks,
                'completed_tasks': completed_tasks,
                'workload_percentage': min((active_tasks / 10) * 100, 100) if active_tasks > 0 else 0
            })
            
        return workload_stats
