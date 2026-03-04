# نظام ماستر سيل - إدارة المبيعات والمخزون

## وصف المشروع
نظام إدارة متكامل للشركات يشمل إدارة المبيعات، المخزون، العملاء، الموردين، والخزينة.

## التقنيات المستخدمة
- **Backend:** FastAPI, Motor (MongoDB Async)
- **Frontend:** React, Axios
- **Database:** MongoDB

## ما تم إنجازه

### 2026-03-04: إصلاح مشاكل الآجل
- إصلاح مشكلة تعديل السعر: الآن يتم تحديث remaining_amount تلقائياً
- إخفاء الفواتير المسددة بالكامل من صفحة الآجل
- تغيير "عرض الدفعات" إلى "عرض الفاتورة" مع نافذة تفاصيل جديدة
- تتبع طريقة الدفع في الفواتير المسددة (payment_method_used)

### 2026-03-04: تحسين الأداء
- إضافة 35+ فهرس لقاعدة البيانات لتحسين سرعة الاستعلامات
- API جديد `/api/customers-balances` - جلب أرصدة العملاء دفعة واحدة
- API جديد `/api/customers/{id}/deferred-invoices` - جلب الفواتير الآجلة للعميل
- تحسين صفحة إدارة العملاء من 60+ ثانية إلى أقل من 4 ثواني

### الإصلاحات السابقة
- إصلاح استيراد المخزون والمواد الخام من Excel (إضافة company_id)
- إصلاح تعديل اسم العميل
- ميزة دمج العملاء
- جعل BUR الخيار الافتراضي لأنواع المواد
- إصلاح أخطاء ObjectId serialization

## المهام القادمة (P1)
1. [x] ترتيب كشف حساب العميل حسب التاريخ - مكتمل
2. [x] تتبع طريقة الدفع للفواتير الآجلة المسددة - مكتمل

## المهام المستقبلية (P2)
1. [ ] سجل تدقيق للفواتير المعدلة قبل حذفها

## الملفات الرئيسية
- `/app/backend/server.py` - API endpoints
- `/app/frontend/src/App.js` - React components
- `/app/backend/.env` - Backend configuration
- `/app/frontend/.env` - Frontend configuration

## بيانات الاختبار
- **Users:** Elsawy/100100 (Admin), master/146200 (Super Admin)
- **Feature Passwords:** 1462 (Invoice Edit), 200200 (Deleted Invoices), 100100 (Main Treasury)

## APIs الرئيسية
- `GET /api/customers-balances` - جلب أرصدة جميع العملاء
- `GET /api/customers/{id}/deferred-invoices` - جلب الفواتير الآجلة للعميل
- `GET /api/invoices-summary` - جلب ملخص الفواتير (محسّن للأداء)
- `GET /api/treasury/balances` - أرصدة الخزينة (محسّن بـ aggregation)
- `PUT /api/invoices/{id}` - تعديل الفاتورة (يحدث remaining_amount تلقائياً)
- `POST /api/customers/{id}/settle-account` - تصفية حساب العميل

## ملاحظات تقنية
- جميع الاستعلامات يجب أن تستبعد `_id` من النتائج لتجنب أخطاء JSON serialization
- جميع البيانات يجب أن تحتوي على `company_id: "elsawy"`
- الفهارس تُنشأ تلقائياً عند بدء الخادم
- عند تعديل items في الفاتورة، يتم تحديث subtotal و total_amount و remaining_amount
