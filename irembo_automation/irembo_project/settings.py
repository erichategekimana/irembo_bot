import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'irembo_auto_db',
        'USER': os.getenv('DB_USER', 'seric'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'seric123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
