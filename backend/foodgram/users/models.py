from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'

    ROLES_CHOICES = [
        (ADMIN, 'Администратор'),
        (MODERATOR, 'Модератор'),
        (USER, 'Пользователь'),
    ]

    STAFF = [
        ADMIN, MODERATOR
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLES_CHOICES,
        default=USER,
    )

    first_name = models.CharField(max_length=150,)
    last_name = models.CharField(max_length=150,)
    email = models.EmailField(max_length=150, unique=True)

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_personnel(self):
        return self.role in self.STAFF

    def is_subscribed(self, author):
        return Follow.objects.filter(user=self, author=author).exists()


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followings',
        verbose_name='Подписки'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчики'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='following'
            ),
        )
