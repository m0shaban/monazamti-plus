# التعريف الكلّي للبرنامج

هذا البرنامج عبارة عن نظام لإدارة المشاريع وتتبع مهام الفريق وجوانب المخاطر والوقت والتكلفة، مع دعم صلاحيات مختلفة مثل المدير والمسؤول والمستخدم العادي.

## التصميم (Design)

- واجهة مستخدم بسيطة تعتمد على قوالب HTML وCSS لجعل التصفح سهلاً.
- تقسيم الصفحات لوحدات رئيسية (الصفحة الرئيسية، المهام، المشاريع، التقارير، إلخ).
- تنظيم الروابط والتوجيهات في النظام باستخدام Blueprint في Flask لتسهيل الصيانة.

## التقنيات المستخدمة

1. **Python (Flask)**: لتصميم واجهة الويب، والتحكم في المنطق الخلفي.
2. **SQLite** أو **PostgreSQL**: لإدارة قواعد البيانات والتخزين.
3. **SQLAlchemy**: للتعامل مع قاعدة البيانات.
4. **HTML/CSS/JavaScript**: لبناء الواجهة الأمامية.
5. **Werkzeug Security**: لتشفير كلمات المرور والتحقق من المستخدم.
6. **Flask-Login**: لإدارة جلسات تسجيل الدخول والتفويض.

## الهيكلة (Structure)

1. **المجلد الرئيسي**  
   - `app/` : يحتوي على ملفات الباك-إند كالموديلات والمسارات والقوالب.  
   - `venv/` : البيئة الافتراضية للمشروع.  
   - `run.py` : الملف الرئيسي لتشغيل التطبيق.  

2. **داخل مجلد app/**  
   - `models.py` : يشمل تعريفات الجداول (فئات SQLAlchemy).  
   - `main/` : يحتوي على المسارات المتعلقة بالصفحات العامة (لوحة التحكم، المهام...).  
   - `auth/` : يحتوي على المسارات المتعلقة بتسجيل الدخول والتسجيل وغيرها.  
   - `templates/` : القوالب الجاهزة للعرض.  

3. **المجلدات الأخرى**  
   - `instance/` : قد يتم تخزين قاعدة البيانات فيها (ملف SQLite).  
   - `requirements.txt` : يضم المكتبات المطلوبة للمشروع.  

## الوصف الكامل للبرنامج

- **إدارة المستخدمين**: إنشاء مستخدمين وتحديد أدوارهم كمسؤول أو مدير مشروع أو عضو فريق.  
- **إدارة المشاريع**: يستطيع المستخدم إنشاء مشاريع وتحديث معلوماتها كالاسم والوصف والميزانية.  
- **إدارة المهام**: إضافة مهام لكل مشروع، ربطها بمستخدمين، تحديد حالة المهمة وأولويتها.  
- **لوحة التحكم**: تُظهر إحصاءات سريعة عن المشاريع والمهام والمخاطر الحالية.  
- **إدارة الوقت**: تسجيل أوقات العمل على المهام، وحساب التكلفة لو كانت المهام مدفوعة الأجر.  
- **تحليلات وتقارير**: عرض تقارير عن سير العمل، ونسب الإنجاز، ومعدلات التكاليف.  
- **إدارة المخاطر**: تحديد المخاطر للمشاريع، مع وصف خطة التخفيف والمراقبة.

## الأقسام (Modules & Sections)

- قسم المستخدمين: يضم تسجيل الدخول والتفويض وإدارة الصلاحيات.
- قسم المشاريع: يحتوي على صفحات الإنشاء والتحرير والعرض التفصيلي للمشاريع.
- قسم المهام: يعرض المهام وإنشائها وتحديث حالتها وتعيين مسؤولها.
- قسم التقارير والتحليلات: يوفر تقارير عن الوقت والتكلفة ونسب الإنجاز.
- قسم إدارة المخاطر: يسمح بإضافة تقييمات المخاطر وإدارتها.

## السيناريوهات (Scenarios)

1. سيناريو إنشاء مشروع جديد وتعيين مهام لعضو فريق.
2. سيناريو إدارة مخاطر المشروع وتتبع خطط تخفيفها.
3. سيناريو متابعة وقت العمل لكل عضو وحساب التكاليف.
4. سيناريو تحرير بيانات مستخدم أو تعيينه في قسم جديد.
5. سيناريو توليد تقارير حول تقدم المهام والمشاريع.

## المميزات (Features)

- إنشاء وإدارة أقسام داخل المؤسسة (مثل التقنية، التسويق، المالية).
- دعم تعدد الأدوار: مسؤول، مدير مشروع، عضو فريق.
- نظام تسجيل دخول آمن باستخدام كلمات مرور مشفرة.
- واجهة سهلة للتعامل مع خطوط الزمن والمهام.
- لوحة تحكم تفاعلية لإدارة المخاطر ومراقبة حالة المشاريع.
- إمكانية عرض تقارير مفصلة عن الأداء والأوقات.
- تكامل مع النظام المالي لحساب التكلفة الفعلية (إذا تم توسيع المشروع).

## واجهة المستخدم (UI/UX)

- التصميم البصري: واجهة تحافظ على بساطة الألوان والخطوط وتُبرز المعلومات المهمة في صفحات مثل “المشاريع” و”المهام”.
- التوافق مع الأجهزة: استخدام تصميم متجاوب (Responsive) ليتوافق مع الشاشات الصغيرة والكبيرة.
- سهولة التنقل: قوائم واضحة وروابط مباشرة لكل قسم، مع تبويب يساعد المستخدم في الوصول لمطالباته بسرعة.
- التجربة التفاعلية: تنبيهات فورية (Flash Messages) وحالات تأكيد للتفاعلات مثل إنشاء مشروع جديد أو تسجيل مهمة.
- التركيز على قابلية الاستخدام: وضع أزرار إضافة أو تحرير أو حذف في أماكن ثابتة لضمان تجربة مستخدم متسقة.
- إجراءات الكواليس: عرض الرسائل التحذيرية عند نقص البيانات، وإظهار تحميل البيانات أثناء العمليات الطويلة.

## ملف يحتوي على جميع التفاصيل لبناء المشروع من جديد

لبناء المشروع من الصفر، تتبع الخطوات التالية:
1. **تثبيت Python 3.11 أو أحدث**.
2. **إنشاء بيئة افتراضية** وتشغيلها.
3. **تثبيت المتطلبات** عبر:
   ```
   pip install -r requirements.txt
   ```
4. **تهيئة ملف `.env`** وتعريف معلومات قاعدة البيانات وبيئة Flask.
5. **تشغيل الأوامر**:
   ```
   flask db migrate -m "Initial migration"
   flask db upgrade
   python run.py
   ```
6. **الوصول للتطبيق** على عنوان محلي مثل:  
   ```
   http://127.0.0.1:5000
   ```

## عملية الإعداد والتشغيل

### 1. إعداد قاعدة البيانات 
تم بنجاح إعداد قاعدة البيانات باستخدام الأمر `python setup_database.py` والذي قام بما يلي:
- إنشاء مجلد `instance` إذا لم يكن موجوداً
- إنشاء قاعدة بيانات SQLite في المسار `instance/site.db`
- إنشاء جداول النظام الأساسية
- إنشاء حساب المسؤول الافتراضي (admin/admin123)

### 2. تشغيل التطبيق
بعد إعداد قاعدة البيانات، يمكنك الآن تشغيل التطبيق باستخدام الأمر:
