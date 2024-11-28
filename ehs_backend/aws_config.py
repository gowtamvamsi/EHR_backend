from typing import Dict, Any
import os

class AWSConfig:
    @staticmethod
    def get_elasticache_config() -> Dict[str, Any]:
        """ElastiCache configuration for Redis"""
        return {
            'CACHES': {
                'default': {
                    'BACKEND': 'django_redis.cache.RedisCache',
                    'LOCATION': os.getenv('ELASTICACHE_URL'),
                    'OPTIONS': {
                        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                        'CONNECTION_POOL_CLASS': 'redis.connection.ConnectionPool',
                        'CONNECTION_POOL_CLASS_KWARGS': {
                            'max_connections': 50,
                            'timeout': 20,
                            'retry_on_timeout': True,
                            'socket_keepalive': True,
                            'socket_connect_timeout': 30,
                        },
                        'SERIALIZER_CLASS': 'django_redis.serializers.JSONSerializer',
                        'COMPRESSOR_CLASS': 'django_redis.compressors.zlib.ZlibCompressor',
                        'MASTER_CACHE': os.getenv('ELASTICACHE_URL'),
                    },
                    'KEY_PREFIX': 'ehs',
                    'TIMEOUT': 300,  # 5 minutes default
                }
            },
            'SESSION_ENGINE': 'django.contrib.sessions.backends.cache',
            'SESSION_CACHE_ALIAS': 'default',
        }

    @staticmethod
    def get_celery_config() -> Dict[str, Any]:
        """Celery configuration for AWS"""
        return {
            'CELERY_BROKER_URL': os.getenv('SQS_URL'),
            'CELERY_BROKER_TRANSPORT': 'sqs',
            'CELERY_BROKER_TRANSPORT_OPTIONS': {
                'region': os.getenv('AWS_REGION', 'ap-south-1'),
                'visibility_timeout': 3600,
                'polling_interval': 1,
                'queue_name_prefix': 'ehs-',
                'wait_time_seconds': 20,
            },
            'CELERY_RESULT_BACKEND': os.getenv('ELASTICACHE_URL'),
            'CELERY_TASK_DEFAULT_QUEUE': 'ehs-default',
            'CELERY_TASK_QUEUES': {
                'ehs-high-priority': {
                    'exchange': 'ehs-high-priority',
                    'routing_key': 'high',
                },
                'ehs-default': {
                    'exchange': 'ehs-default',
                    'routing_key': 'default',
                },
                'ehs-low-priority': {
                    'exchange': 'ehs-low-priority',
                    'routing_key': 'low',
                },
            },
            'CELERY_TASK_ROUTES': {
                'patients.tasks.process_medical_image': {'queue': 'ehs-high-priority'},
                'appointments.tasks.send_appointment_reminders': {'queue': 'ehs-default'},
                'analytics.tasks.*': {'queue': 'ehs-low-priority'},
            },
        }