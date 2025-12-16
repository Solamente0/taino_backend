# Jazzmin settings
JAZZMIN_SETTINGS = {
    # General settings
    "site_title": "مدیریت سایت",
    "site_header": "پنل مدیریت",
    "site_brand": "سیستم مدیریت",
    "site_logo": None,
    "welcome_sign": "به پنل مدیریت خوش آمدید",
    "copyright": "سامانه وکالت آنلاین © 2025",
    # RTL settings
    "show_ui_builder": True,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    # Critical for RTL
    "related_modal_active": False,
    "custom_css": "css/jazzmin-rtl.css",
    # Top Menu settings
    "topmenu_links": [
        {"name": "خانه", "url": "admin:index", "permissions": ["auth.view_user"]},
    ],
    # User Menu settings
    "usermenu_links": [
        {"name": "پشتیبانی", "url": "https://your-support-url.com", "new_window": True},
    ],
}
