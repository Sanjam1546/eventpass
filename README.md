# EventPass — Event Pass Scanner System (Django)

Ek complete Django-based system jisme:
- **Login/Signup** — professional glass-design UI, role-based accounts (Attendee / Scanner Staff / Organizer)
- **Event registration** — user kisi specific event ke liye date & time (session) choose karke pass register kar sakta hai
- **Member Management** — organizer manually attendees add kar sakta hai (name, father's name, address, phone number, company optional) — koi login account ki zaroorat nahi
- **VIP Pass System** — har member ke liye General ya VIP pass type choose kar sakte ho — VIP passes ka alag gold-themed ticket, gold QR code, aur scanner pe special VIP highlight
- **QR Pass generation** — har pass ke liye unique QR code auto-generate hota hai (Python `qrcode` library)
- **Entry Scanner** — browser camera se QR scan karke real-time entry allow/deny karta hai (html5-qrcode JS library), VIP guests ko badge ke saath highlight karta hai
- **Admin dashboard** — Django admin se events, sessions, members, passes manage kar sakte ho
- **Organizer panel** — event, date/time sessions, aur members create karne ke liye

---

## 1. Setup (local machine pe run karne ke liye)

```bash
# 1. Virtual environment banao (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Dependencies install karo
pip install -r requirements.txt

# 3. Database migrate karo
python manage.py makemigrations
python manage.py migrate

# 4. Admin/organizer account banao
python manage.py createsuperuser

# 5. Server run karo
python manage.py runserver
```

Browser mein kholo: **http://127.0.0.1:8000/**

---

## 2. User Roles kaise kaam karte hain

Har naya signup **Attendee** role se start hota hai. Roles Django Admin (`/admin/`) se `UserProfile` model mein change kar sakte ho:

| Role         | Kya kar sakta hai                                        |
|--------------|-----------------------------------------------------------|
| `attendee`   | Events browse karna, pass register karna, apna QR pass dekhna |
| `scanner`    | Entry Scanner page use kar sakta hai (`/scanner/`)         |
| `organizer`  | Events aur date/time sessions create kar sakta hai         |

Superuser (createsuperuser se banaya gaya) automatically har permission rakhta hai.

---

## 3. Flow — Attendee ke liye

1. Signup/Login karo
2. "Events" pe jao, event choose karo
3. "Register for a Pass" click karo → date/time (session) select karo
4. Pass generate hoga with unique **QR code**
5. "My Passes" mein apna pass dekh sakte ho, QR ko screenshot/download kar sakte ho

## 4. Flow — Scanner Staff ke liye

1. Scanner role wale account se login karo
2. "Scanner" menu pe jao (`/scanner/`) — browser camera permission allow karo
3. Attendee ka QR code camera ke saamne laao
4. System automatically check karega:
   - ✅ **Valid** → "Entry approved" + pass ko "used" mark kar dega
   - ⚠️ **Already Used** → dobara scan hone pe warning dega (time bhi dikhayega ki pehle kab use hua)
   - ⛔ **Invalid/Cancelled** → entry deny

## 5. Flow — Organizer ke liye

1. Organizer role wale account se login karo
2. "+ New Event" pe click karo → event details fill karo
3. Uske baad ek ya multiple date/time **sessions** add karo (capacity bhi set kar sakte ho, 0 = unlimited)
4. Har session ke liye **"+ Add Member"** button se ek saath **multiple attendees** add karo (5 rows by default dikhte hain, "+ Add Another Row" se aur bhi):
   - Har row mein: Full Name, Father's Name, Address, Phone Number (required)
   - Company Name (optional)
   - Pass Type: **General** ya **VIP** — har row alag-alag choose kar sakte ho
   - Khaali rows automatically skip ho jayengi
   - "Save All & Generate Passes" click karte hi sabke QR passes ek saath ban jayenge
5. "Manage Members" page se sabhi members ki list, unka pass status, aur "View Pass" (print/download ke liye) dekh sakte ho
6. Attendees bhi khud signup karke events "Register for a Pass" se apna pass generate kar sakte hain (self-registration flow General passes deta hai)

---

## 6. Project Structure

```
eventpass_project/
├── eventpass/          # Django project settings, urls
├── accounts/           # Login, signup, user roles (UserProfile)
├── passes/             # Event, EventSession, EventPass models + scanner logic
├── templates/           # HTML templates (glass-design theme)
├── static/css/style.css # Professional dark-navy glass UI
├── static/js/scanner.js # Camera QR scanner logic
└── media/qrcodes/       # Auto-generated QR images (created at runtime)
```

## 7. Tech Stack

- **Backend:** Django 5 (Python)
- **Database:** SQLite (default — production mein PostgreSQL/MySQL switch kar sakte ho)
- **QR Generation:** `qrcode` + `Pillow` (Python)
- **QR Scanning:** `html5-qrcode` (JS, browser camera access — no app install needed)
- **Frontend:** Plain HTML + CSS (glass-morphism, dark navy theme, Inter + Playfair Display fonts) — no build step needed

## 8. Production Notes (deploy karne se pehle)

- `eventpass/settings.py` mein `SECRET_KEY` change karo aur `DEBUG = False` set karo
- `ALLOWED_HOSTS` mein apna domain daalo
- HTTPS use karo — camera access (scanner) sirf HTTPS ya localhost pe kaam karta hai browsers mein
- Production database (PostgreSQL recommended) use karo
- Static/media files ko proper storage (S3, etc.) ya Nginx se serve karo

---

Koi bhi feature add/change karna ho (jaise email pass delivery, PDF ticket, multiple ticket types, payment integration) — bata dena, extend kar denge.
