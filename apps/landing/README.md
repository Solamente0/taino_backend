# Landing Page App - Taino AI Therapy Platform

این اپلیکیشن برای مدیریت و نمایش محتوای صفحه فرود پلتفرم درمان با هوش مصنوعی Taino طراحی شده است.

## نصب و راه‌اندازی

### 1. افزودن به INSTALLED_APPS

فایل `config/settings/base.py` را ویرایش کنید:

```python
INSTALLED_APPS = [
    # ... سایر اپلیکیشن‌ها
    "apps.landing.apps.LandingConfig",
]
```

### 2. افزودن URL به پروژه

فایل `config/urls.py` را ویرایش کنید:

```python
urlpatterns = [
    # ... سایر URLها
    path("api/landing/", include("apps.landing.api.urls"), name="landing"),
]
```

### 3. اجرای Migration

```bash
python manage.py makemigrations landing
python manage.py migrate landing
```

### 4. ایجاد Superuser (در صورت نیاز)

```bash
python manage.py createsuperuser
```

## ساختار مدل‌ها

### مدل‌های اصلی:

1. **HeroSection**: بخش هیرو/اصلی صفحه
2. **Feature**: ویژگی‌های پلتفرم
3. **Testimonial**: نظرات و بازخوردهای کاربران
4. **FAQ**: سوالات متداول
5. **Pricing**: پلن‌های قیمت‌گذاری
6. **Team**: اعضای تیم
7. **HowItWorks**: مراحل نحوه کار
8. **Statistic**: آمار و ارقام
9. **BlogPost**: پست‌های وبلاگ
10. **ContactMessage**: پیام‌های تماس کاربران
11. **Newsletter**: اشتراک خبرنامه
12. **AppScreenshot**: اسکرین‌شات‌های اپلیکیشن

## API Endpoints

### دریافت تمام داده‌های صفحه فرود

```
GET /api/landing/v1/all-data/
```

این endpoint تمام داده‌های مورد نیاز صفحه فرود را در یک درخواست برمی‌گرداند.

### Endpoints جداگانه

```
GET /api/landing/v1/hero-sections/          # بخش‌های هیرو
GET /api/landing/v1/features/                # ویژگی‌ها
GET /api/landing/v1/testimonials/            # نظرات کاربران
GET /api/landing/v1/faqs/                    # سوالات متداول
GET /api/landing/v1/faq-categories/          # دسته‌بندی‌های FAQ
GET /api/landing/v1/pricing/                 # پلن‌های قیمت‌گذاری
GET /api/landing/v1/team/                    # اعضای تیم
GET /api/landing/v1/how-it-works/            # مراحل نحوه کار
GET /api/landing/v1/statistics/              # آمارها
GET /api/landing/v1/screenshots/             # اسکرین‌شات‌ها
```

### ارسال پیام و اشتراک

```
POST /api/landing/v1/contact/               # ارسال پیام تماس
POST /api/landing/v1/newsletter/subscribe/  # اشتراک خبرنامه
```

### بلاگ

```
GET  /api/landing/v1/blog/                  # لیست پست‌ها
GET  /api/landing/v1/blog/{slug}/           # جزئیات پست
GET  /api/landing/v1/blog/popular/          # پست‌های پرطرفدار
GET  /api/landing/v1/blog/category/{name}/  # پست‌های یک دسته
```

## نمونه استفاده در Frontend

### دریافت تمام داده‌ها

```javascript
async function fetchLandingData() {
  const response = await fetch('/api/landing/v1/all-data/');
  const data = await response.json();
  
  // data شامل:
  // - hero_sections
  // - features
  // - testimonials
  // - faqs
  // - pricing
  // - team
  // - how_it_works
  // - statistics
  // - screenshots
  // - blog_posts
  
  return data;
}
```

### ارسال پیام تماس

```javascript
async function submitContact(formData) {
  const response = await fetch('/api/landing/v1/contact/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      subject: formData.subject,
      message: formData.message,
    }),
  });
  
  return await response.json();
}
```

### اشتراک در خبرنامه

```javascript
async function subscribeNewsletter(email) {
  const response = await fetch('/api/landing/v1/newsletter/subscribe/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });
  
  return await response.json();
}
```

## مدیریت محتوا در Django Admin

### دسترسی به پنل ادمین

```
https://your-domain.com/taino/admin/
```

### مدیریت محتوا:

1. **بخش‌های هیرو**: افزودن/ویرایش بخش‌های اصلی صفحه
2. **ویژگی‌ها**: تعریف ویژگی‌های پلتفرم
3. **نظرات**: مدیریت نظرات و بازخوردهای کاربران
4. **سوالات متداول**: ایجاد و دسته‌بندی سوالات
5. **قیمت‌گذاری**: تعریف پکیج‌ها و قیمت‌ها
6. **تیم**: معرفی اعضای تیم
7. **نحوه کار**: توضیح مراحل استفاده
8. **آمار**: نمایش آمار و ارقام مهم
9. **بلاگ**: انتشار مقالات و محتوا
10. **پیام‌ها**: مشاهده و پاسخ به پیام‌های کاربران
11. **خبرنامه**: مدیریت مشترکین
12. **اسکرین‌شات‌ها**: آپلود تصاویر اپلیکیشن

## ویژگی‌های مهم

### 1. Multi-language Ready
تمام متن‌ها با استفاده از `gettext_lazy` آماده ترجمه هستند.

### 2. SEO Friendly
- فیلد slug برای URL‌های سئو شده
- Meta descriptions
- Reading time برای بلاگ

### 3. Order Management
تمام مدل‌ها دارای فیلد `order` برای مرتب‌سازی دستی هستند.

### 4. Active/Inactive
کنترل نمایش محتوا با فیلد `is_active`

### 5. Rich Media Support
پشتیبانی از تصاویر، ویدیوها و آیکون‌ها

### 6. Analytics
- شمارش بازدید پست‌های بلاگ
- تاریخ انتشار و بروزرسانی

## Best Practices

### 1. تصاویر
- از تصاویر بهینه شده استفاده کنید
- نسبت تصویر مناسب برای موبایل و دسکتاپ
- استفاده از فرمت WebP برای کاهش حجم

### 2. محتوا
- عناوین کوتاه و گویا
- توضیحات واضح و مختصر
- استفاده از keywords مناسب

### 3. Performance
- Cache کردن داده‌های ثابت
- استفاده از pagination برای لیست‌ها
- بهینه‌سازی query‌ها با select_related

### 4. امنیت
- Validation ورودی‌های کاربر
- محدودیت rate limit برای contact و newsletter
- Sanitize کردن محتوای HTML در بلاگ

## نمونه داده برای تست

می‌توانید از Django shell برای ایجاد داده‌های نمونه استفاده کنید:

```python
python manage.py shell

from apps.landing.models import *

# ایجاد Hero Section
hero = HeroSection.objects.create(
    title="درمان هوشمند با Taino",
    subtitle="مشاوره روانشناسی با قدرت هوش مصنوعی",
    description="دسترسی به مشاوره حرفه‌ای 24/7 با استفاده از پیشرفته‌ترین تکنولوژی AI",
    cta_primary_text="شروع رایگان",
    cta_primary_link="/signup",
    is_active=True,
    order=1
)

# ایجاد Feature
feature = Feature.objects.create(
    title="مشاوره هوشمند",
    description="سیستم هوش مصنوعی ما به شما کمک می‌کند تا بهترین درمان را دریافت کنید",
    icon="brain",
    is_active=True,
    order=1
)

# و غیره...
```

## پشتیبانی

برای هرگونه سوال یا مشکل:
- ایمیل: support@taino.ir
- مستندات: https://docs.taino.ir
