from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Creates DB tables'

    def handle(self, *args, **options):
        from sa_helper import get_engine, BaseMapping
        engine = get_engine()

        # UsersBase.metadata.create_all(engine)
        BaseMapping.metadata.create_all(engine)
