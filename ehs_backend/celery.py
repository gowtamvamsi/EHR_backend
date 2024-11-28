import os
from celery import Celery
from .aws_config import AWSConfig

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ehs_backend.settings')

app = Celery('ehs_backend')

# Load AWS-specific Celery configuration
celery_config = AWSConfig.get_celery_config()
app.conf.update(celery_config)

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')