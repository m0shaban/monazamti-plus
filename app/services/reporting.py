from app.models import Project, Task, User, PerformanceReview
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

class ReportingService:
    @staticmethod
    def generate_project_report(project_id):
        project = Project.query.get(project_id)
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        stats = {
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for t in tasks if t.status == 'Completed'),
            'on_track_tasks': sum(1 for t in tasks if t.status != 'Completed' and t.due_date > datetime.now()),
            'overdue_tasks': sum(1 for t in tasks if t.status != 'Completed' and t.due_date < datetime.now()),
            'total_hours': sum(t.estimated_hours or 0 for t in tasks),
            'actual_hours': sum(t.actual_hours or 0 for t in tasks),
            'budget_performance': (project.actual_cost / project.budget * 100) if project.budget else 0
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
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer
