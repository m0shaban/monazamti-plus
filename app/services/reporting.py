from app.models import Project, Task, User, PerformanceReview
from datetime import datetime, timedelta
import io

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    ADVANCED_REPORTING = True
except ImportError:
    ADVANCED_REPORTING = False

class ReportingService:
    @staticmethod
    def generate_project_report(project_id):
        project = Project.query.get(project_id)
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        stats = {
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for t in tasks if t.status == 'Completed'),
            'on_track_tasks': sum(1 for t in tasks if t.status != 'Completed' and t.due_date > datetime.now()),
            'overdue_tasks': sum(1 for t in tasks if t.status != 'Completed' and t.due_date < datetime.now())
        }
        
        return stats

    @staticmethod
    def generate_employee_performance_report(user_id, period_start, period_end):
        tasks = Task.query.filter_by(assigned_to=user_id)\
                    .filter(Task.due_date.between(period_start, period_end)).all()
        
        performance_data = {
            'completed_on_time': sum(1 for t in tasks if t.status == 'Completed' and t.completion_date <= t.due_date),
            'completed_late': sum(1 for t in tasks if t.status == 'Completed' and t.completion_date > t.due_date),
            'pending': sum(1 for t in tasks if t.status != 'Completed'),
            'average_completion_time': timedelta(days=0),  # Calculate average time to complete tasks
            'efficiency_score': 0  # Calculate based on estimated vs actual hours
        }
        
        return performance_data

    @staticmethod
    def export_to_excel(data, filename):
        # Simplified export without pandas
        return None
