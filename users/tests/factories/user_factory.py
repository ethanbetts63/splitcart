import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

# Long enough for MinimumLengthValidator and unremarkable enough for
# CommonPasswordValidator.
TEST_PASSWORD = 'correct-horse-battery-7'


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ('email',)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    full_name = factory.Sequence(lambda n: f'Test User {n}')

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or TEST_PASSWORD)
        if create:
            obj.save()
