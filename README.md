# 🛒 SwiftKart E-Commerce Website

## 📌 Project Overview

SwiftKart is a simple e-commerce web application built using Django. Users can browse products, add items to cart, place orders, and receive order confirmation via email.

---

## 🚀 Features

* 👤 User Registration & Login
* 🛍️ Product Listing & Details
* 🛒 Add to Cart Functionality
* 💳 Order Placement
* 📧 Email Notification (Order Confirmation via Gmail)
* 📦 Order History
* 🔐 Secure Authentication

---

## 📧 Email Notification Feature

When a user places an order:

* A confirmation email is automatically sent to the user's Gmail
* The email includes order details like product name and order status

---

## 🛠️ Technologies Used

* Backend: Django (Python)
* Frontend: HTML, CSS, Bootstrap
* Database: SQLite
* Email Service: Gmail SMTP

---

## ⚙️ Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/Vaykulnikhil/swiftkart-ecommerce.git
   cd swiftkart-ecommerce
   ```

2. Create virtual environment:

   ```bash
   python -m venv env
   env\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:

   ```bash
   python manage.py migrate
   ```

5. Create superuser:

   ```bash
   python manage.py createsuperuser
   ```

6. Run server:

   ```bash
   python manage.py runserver
   ```

---

## 📧 Gmail Configuration

Add this in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

⚠️ Use **App Password**, not your real Gmail password.

---

## 📂 Project Structure

* `accounts/` – User authentication
* `store/` – Product management
* `orders/` – Order handling
* `templates/` – HTML files
* `static/` – CSS, JS, Images

---

## 🎯 Future Improvements

* Online Payment Integration
* Product Reviews & Ratings
* Admin Dashboard UI Improvements

---

## 👨‍💻 Author

Nikhil Vaykul

---

## 📌 Conclusion

SwiftKart is a beginner-friendly Django project that demonstrates core e-commerce functionality along with email integration using Gmail.
