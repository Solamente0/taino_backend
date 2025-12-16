from django.contrib import auth
from django.contrib.auth.models import BaseUserManager


class TainoUserManager(BaseUserManager):
    use_in_migrations = True

    """
    Taino user model manager where vekalat_id is the unique identifiers
    for authentication instead of usernames.
    """

    def _create_user(self, phone_number, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """

        phone_number = self.normalize_phone_number(phone_number)
        user = self.model(phone_number=phone_number, **extra_fields)
        if not password:
            user.set_unusable_password()
            user.save(using=self._db)
            return user

        user.set_password(password)
        user.save(using=self._db)
        return user

    @staticmethod
    def normalize_phone_number(phone_number):
        return phone_number

    def create_user(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self._create_user(phone_number=phone_number, password=password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument"
                )
        elif not isinstance(backend, str):
            raise TypeError("backend must be a dotted import path string (got %r)" % backend)
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()

    def activate(self, username):
        # TODO: may use save() and send_mail()
        pass

    def activate_in_bulk(self, queryset):
        # TODO: may use queryset.update() instead of save()
        # TODO: may use send_mass_mail() instead of send_mail()
        pass
