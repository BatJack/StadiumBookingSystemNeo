from django.apps import AppConfig
from django.db.backends.signals import connection_created


def set_sqlite_pragmas(sender, connection, **kwargs):
    """生产级 SQLite 调优 PRAGMA"""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA cache_size=-64000;')
        cursor.execute('PRAGMA busy_timeout=5000;')
        cursor.execute('PRAGMA temp_store=MEMORY;')


class BookingConfig(AppConfig):
    name = 'booking'

    def ready(self):
        connection_created.connect(set_sqlite_pragmas)
