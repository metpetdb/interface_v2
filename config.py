from getenv import env

CSRF_ENABLED = True
SECRET_KEY = env('SECRET_KEY')

MAIL_SERVER = env('MAIL_SERVER')
MAIL_PORT = env('MAIL_PORT')
MAIL_USE_TLS = env('MAIL_USE_TLS')
MAIL_USERNAME = env('MAIL_USERNAME')
MAIL_PASSWORD = env('MAIL_PASSWORD')
STATIC_URL = '/static/'
