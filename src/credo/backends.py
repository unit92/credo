from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class CaseInsensitiveBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            d = {'%s__iexact' % UserModel.USERNAME_FIELD: username}
            user = UserModel.objects.get(**d)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            UserModel().set_password(password)

        return None
