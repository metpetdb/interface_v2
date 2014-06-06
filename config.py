from getenv import env

CSRF_ENABLED = True
SECRET_KEY = env('SECRET_KEY')
