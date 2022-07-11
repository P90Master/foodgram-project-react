from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

EMPTY = '-пусто-'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
    )

    list_editable = (
        'username', 'email', 'first_name', 'last_name', 'role'
    )
    search_fields = ('username',)
    list_filter = ('role',)
    empty_value_display = EMPTY
