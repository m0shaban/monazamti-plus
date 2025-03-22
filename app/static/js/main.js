// Initialize tooltips
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

// Enhanced Form Validation
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Update task status and progress bar
    document.querySelectorAll('.task-status-select').forEach(select => {
        select.addEventListener('change', function() {
            const taskId = this.dataset.taskId;
            const newStatus = this.value;
            
            fetch(`/task/${taskId}/update_status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({ status: newStatus })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const progressBar = document.querySelector(`#progress-${taskId}`);
                    if (progressBar) {
                        progressBar.style.width = `${data.new_progress}%`;
                        progressBar.setAttribute('aria-valuenow', data.new_progress);
                        progressBar.textContent = `${data.new_progress}%`;
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});

// Task Status Updates
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('task-status')) {
        const taskId = e.target.dataset.taskId;
        const newStatus = e.target.value;
        
        fetch(`/tasks/${taskId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrf_token]').value
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to update task status');
            }
        });
    }
});

// Project Progress Chart
function initializeProgressChart(projectId, progressData) {
    const ctx = document.getElementById(`progressChart-${projectId}`);
    if (ctx) {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Not Started'],
                datasets: [{
                    data: progressData,
                    backgroundColor: [
                        '#198754',
                        '#0d6efd',
                        '#6c757d'
                    ],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += context.raw + '%';
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }
}

// Initialize all progress charts
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.progress-chart').forEach(chart => {
        const projectId = chart.dataset.projectId;
        const progressData = JSON.parse(chart.dataset.progress);
        initializeProgressChart(projectId, progressData);
    });

    // Animate progress bars when they come into view
    const progressBars = document.querySelectorAll('.progress-bar-custom');
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const progressBar = entry.target;
                const progress = progressBar.dataset.progress;
                progressBar.style.width = progress;
                progressBar.classList.add('active');
            }
        });
    }, { threshold: 0.5 });

    progressBars.forEach(bar => observer.observe(bar));
});

// Toast Notification System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 
                          type === 'error' ? 'exclamation-circle' : 
                          'info-circle'}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }, 100);
}

// Add loading indicators to forms
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('[type="submit"]');
        if (submitBtn && this.checkValidity()) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
            submitBtn.disabled = true;
            
            // Re-enable after 10s (failsafe)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 10000);
        }
    });
});

// Add confirmation dialogs
document.querySelectorAll('[data-confirm]').forEach(element => {
    element.addEventListener('click', function(e) {
        if (!confirm(this.dataset.confirm)) {
            e.preventDefault();
        }
    });
});
