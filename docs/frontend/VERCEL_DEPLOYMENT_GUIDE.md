# دليل نشر واجهة AgriPulse على منصة Vercel
## Step-by-Step Vercel Deployment Guide for AgriPulse Frontend

> هذا الدليل يشرح كيفية رفع ونشر واجهة المستخدم (React 18 + Vite) على منصة **Vercel** مجاناً في دقيقتين للحصول على رابط مباشر (`https://agripulse-xyz.vercel.app`) ومشاركته مع فريق العمل ومشرفي المشروع.

---

### 🌟 الطريقة الأولى: النشر عبر لوحة تحكم موقع Vercel (مستحسن وأسهل)

1. **تسجيل الدخول في Vercel:**
   * افتح [vercel.com](https://vercel.com) وسجل الدخول بحساب GitHub الخاص بك (`AbdoLailah586`).

2. **استيراد المشروع (Import Project):**
   * اضغط على زر **"Add New..."** ثم اختر **"Project"**.
   * ابحث عن المستودع: `AgriPulse` ثم اضغط **Import**.

3. **تحديد مجلد الواجهة (Root Directory) — ⚠️ خطوة هامة جداً:**
   * في صفحة "Configure Project"، ستجد خيار **Root Directory**.
   * اضغط على **Edit** بجوارها، واختر مجلد:
     ```text
     frontend
     ```
   * اضغط **Continue**.

4. **إعدادات البناء (Build & Output Settings):**
   * ستتعرف Vercel تلقائياً على أن المشروع مبني بـ **Vite**.
   * **Framework Preset:** `Vite`
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
   * **Install Command:** `npm install`
   *(كل هذه الإعدادات افتراضية وصحيحة تلقائياً بفضل وجود `vercel.json`).*

5. **متغيرات البيئة (Environment Variables):**
   * افتح قسم **Environment Variables** وأضف:
     * `VITE_USE_MOCK_DATA` = `true` (لتشغيل الواجهة بمحاكاة كاملة لكافة الحساسات والمضخات دون الحاجة لسيرفر خلفي).
     * `VITE_API_BASE_URL` = `https://api.agripulse.ai/api` (أو اتركه افتراضياً).

6. **إطلاق الموقع (Deploy):**
   * اضغط على زر **Deploy**.
   * خلال أقل من 60 ثانية، سينتهي البناء وستحصل على رابط حي ومباشر مثل:
     ```text
     https://agri-pulse-frontend.vercel.app
     ```

---

### 💻 الطريقة الثانية: النشر عبر سطر الأوامر (Vercel CLI)

إذا كنت تفضل النشر مباشرة من جهازك عبر الـ Terminal:

```bash
# 1. الدخول إلى مجلد الواجهة
cd frontend

# 2. تثبيت أداة Vercel العالمية (مرة واحدة فقط)
npm i -g vercel

# 3. تسجيل الدخول والنشر
vercel
```

اتبع التعليمات في سطر الأوامر:
* `Set up and deploy?` -> اكتب `Y`
* `Which scope?` -> اختر حسابك
* `Link to existing project?` -> اكتب `N`
* `What's your project's name?` -> اكتب `agripulse-client`
* `In which directory is your code located?` -> اضغط Enter (`./`)
* `Auto-detected Project Settings (Vite)?` -> اضغط Enter للموافقة.

ولنشر الإصدار النهائي إلى الـ Production مباشرة:
```bash
vercel --prod
```

---

### 🛡️ ملاحظات تقنية هامة:
* **دعم التنقل داخل الصفحات (SPA Routing):** تم إنشاء ملف [`frontend/vercel.json`](file:///d:/doc/python/grad%20pro%203/frontend/vercel.json) لضمان عدم ظهور خطأ `404 Not Found` عند قيام المستخدم بتحديث الصفحة (Refresh) على مسارات مثل `/operations` أو `/predictive`.
* **الدخول التجريبي:** الرابط سيتيح لزملائك الدخول الفوري عبر زر **"1-Tap Demo: Lead Engineer"** أو حساب `tariq@agripulse.ai`.
