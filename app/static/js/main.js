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

    // Language switching functionality
    // Set initial language based on HTML lang attribute or default to Arabic
    const currentLang = document.documentElement.lang || 'ar';
    if (currentLang === 'ar') {
        document.body.classList.add('rtl');
    }

    // Add event listeners to language switcher links
    const langLinks = document.querySelectorAll('[data-lang]');
    langLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            
            // Set language preference in localStorage
            localStorage.setItem('preferredLanguage', lang);
            
            // Toggle RTL class based on selected language
            if (lang === 'ar') {
                document.body.classList.add('rtl');
                document.documentElement.lang = 'ar';
                document.documentElement.dir = 'rtl';
            } else {
                document.body.classList.remove('rtl');
                document.documentElement.lang = 'en';
                document.documentElement.dir = 'ltr';
            }
            
            // Reload the page to apply language changes
            location.reload();
        });
    });

    // Setup CSRF token for AJAX requests
    const token = document.querySelector('meta[name="csrf-token"]');
    if (token) {
        const headers = new Headers({
            'Content-Type': 'application/json',
            'X-CSRFToken': token.getAttribute('content')
        });
        
        // Set default headers for fetch requests
        window.fetchWithCsrf = function(url, options = {}) {
            options.headers = {...headers, ...options.headers};
            return fetch(url, options);
        };
    }
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    if (popoverTriggerList.length > 0) {
        [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    }
    
    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sidebar-toggled');
            document.querySelector('.sidebar').classList.toggle('toggled');
        });
    }

    // أضف CSRF token إلى جميع نماذج HTML
    document.querySelectorAll('form').forEach(form => {
        // تخطي النماذج التي تستخدم طريقة GET
        if (form.method.toLowerCase() !== 'get' && !form.querySelector('input[name="csrf_token"]')) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            form.appendChild(csrfInput);
        }
    });
    
    // أضف CSRF token إلى جميع نماذج HTML التي تستخدم POST
    document.querySelectorAll('form').forEach(form => {
        // تخطي النماذج التي تستخدم طريقة GET أو التي تحتوي بالفعل على CSRF token
        if (form.method.toLowerCase() !== 'get' && !form.querySelector('input[name="csrf_token"]')) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            if (csrfMeta) {
                csrfInput.value = csrfMeta.getAttribute('content');
                form.appendChild(csrfInput);
            }
        }
    });
    
    // إضافة CSRF token لجميع طلبات AJAX
    const setUpAjaxCSRF = () => {
        const token = document.querySelector('meta[name="csrf-token"]');
        if (token) {
            // لـ fetch API
            window.fetchWithCsrf = (url, options = {}) => {
                if (!options.headers) options.headers = {};
                options.headers['X-CSRFToken'] = token.getAttribute('content');
                return fetch(url, options);
            };
            
            // لـ jQuery (إذا كان متاحًا)
            if (typeof $ !== 'undefined') {
                $.ajaxSetup({
                    beforeSend: function(xhr, settings) {
                        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", token.getAttribute('content'));
                        }
                    }
                });
            }
        }
    };
    
    setUpAjaxCSRF();
});

// إضافة CSRF token لجميع طلبات AJAX
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", document.querySelector('meta[name="csrf-token"]').getAttribute('content'));
        }
    }
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

// تصحيح استخدام "أو" العربية في أي تعليقات بالعربية

// تهيئة العناصر بعد تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // تهيئة زر القائمة للأجهزة المحمولة
    setupMobileMenu();
    
    // منع التحقق من البريد الالكتروني والرسائل بمجرد الكتابة
    setupFormValidation();
    
    // تهيئة القوائم المنسدلة
    setupDropdowns();
});

/**
 * تهيئة قائمة الأجهزة المحمولة وتفعيل الأزرار
 */
function setupMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const closeMenu = document.getElementById('closeMenu');
    const sidebar = document.getElementById('sidebar');
    const contentWrapper = document.getElementById('contentWrapper');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (mobileMenuToggle) {
        // تفعيل وإخفاء القائمة عند النقر على زر القائمة
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.add('show');
            if (overlay) overlay.classList.add('show');
            document.body.style.overflow = 'hidden'; // منع التمرير عند فتح القائمة
        });
    }
    
    if (closeMenu) {
        // إخفاء القائمة عند النقر على زر الإغلاق
        closeMenu.addEventListener('click', function() {
            sidebar.classList.remove('show');
            if (overlay) overlay.classList.remove('show');
            document.body.style.overflow = ''; // السماح بالتمرير مرة أخرى
        });
    }
    
    // إخفاء القائمة عند النقر خارجها (على الطبقة الشفافة)
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
            document.body.style.overflow = '';
        });
    }
    
    // إخفاء القائمة عند النقر على الروابط في الأجهزة المحمولة
    const mobileLinks = sidebar ? sidebar.querySelectorAll('.nav-link') : [];
    mobileLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 768) {
                sidebar.classList.remove('show');
                if (overlay) overlay.classList.remove('show');
                document.body.style.overflow = '';
            }
        });
    });
    
    // التعامل مع تغيير حجم النافذة
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            if (sidebar) sidebar.classList.remove('show');
            if (overlay) overlay.classList.remove('show');
            document.body.style.overflow = '';
        }
    });
}

/**
 * تهيئة القوائم المنسدلة لتعمل بشكل أفضل على الأجهزة المحمولة
 */
function setupDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                const menu = this.nextElementSibling;
                const isOpen = menu.classList.contains('show');
                
                // إغلاق جميع القوائم المنسدلة المفتوحة
                const openMenus = document.querySelectorAll('.dropdown-menu.show');
                openMenus.forEach(openMenu => {
                    if (openMenu !== menu) {
                        openMenu.classList.remove('show');
                        openMenu.previousElementSibling.setAttribute('aria-expanded', 'false');
                    }
                });
                
                // فتح/إغلاق القائمة المنسدلة الحالية
                if (isOpen) {
                    menu.classList.remove('show');
                    this.setAttribute('aria-expanded', 'false');
                } else {
                    menu.classList.add('show');
                    this.setAttribute('aria-expanded', 'true');
                }
            }
        });
    });
    
    // إغلاق القوائم المنسدلة عند النقر خارجها
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            const openMenus = document.querySelectorAll('.dropdown-menu.show');
            openMenus.forEach(menu => {
                menu.classList.remove('show');
                menu.previousElementSibling.setAttribute('aria-expanded', 'false');
            });
        }
    });
}

/**
 * تحسين التحقق من النماذج لتجربة أفضل على الأجهزة المحمولة
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            // التحقق فقط عند إرسال النموذج أو مغادرة الحقل
            input.addEventListener('blur', function() {
                validateInput(this);
            });
        });
        
        form.addEventListener('submit', function(e) {
            inputs.forEach(input => {
                validateInput(input);
            });
            
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

/**
 * التحقق من صحة حقل الإدخال
 */
function validateInput(input) {
    if (input.checkValidity()) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    } else {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
    }
}

/**
 * تحميل المزيد من المحتوى بشكل نوعي (لتحسين الأداء)
 * @param {string} url - عنوان URL لجلب البيانات
 * @param {string} containerId - معرف الحاوية لتعبئة البيانات
 * @param {Function} callback - دالة الاستدعاء بعد التحميل
 */
function loadMoreContent(url, containerId, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // إظهار مؤشر التحميل
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'text-center py-3';
    loadingIndicator.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">جاري التحميل...</span></div>';
    container.appendChild(loadingIndicator);
    
    // جلب البيانات
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // إزالة مؤشر التحميل
            container.removeChild(loadingIndicator);
            
            // استدعاء الدالة بعد التحميل
            if (typeof callback === 'function') {
                callback(data, container);
            }
        })
        .catch(error => {
            console.error('Error loading content:', error);
            
            // إزالة مؤشر التحميل وإظهار رسالة الخطأ
            container.removeChild(loadingIndicator);
            
            const errorMessage = document.createElement('div');
            errorMessage.className = 'alert alert-danger';
            errorMessage.textContent = 'حدث خطأ أثناء تحميل المحتوى. يرجى المحاولة مرة أخرى.';
            container.appendChild(errorMessage);
        });
}
