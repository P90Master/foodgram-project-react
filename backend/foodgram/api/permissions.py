from rest_framework import permissions


def is_staff(user):
    if user.is_authenticated:
        return user.is_personnel or user.is_staff

    return False


def is_admin(user):
    if user.is_authenticated:
        return user.is_admin or user.is_staff

    return False


class OnlyForAdmin(permissions.BasePermission):
    """
    Действия с этим пермишенном разрешены только с наличием роли админа.
    """

    def has_permission(self, request, view):
        return is_admin(request.user)


class ReadOnly(permissions.BasePermission):
    """
    Обычным пользователям разрешено только чтение.
    """

    def has_permission(self, request, views):
        if request.method in permissions.SAFE_METHODS:
            return True

        return is_admin(request.user)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешено изменение только своего контента.
    """

    def has_object_permission(self, request, views, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_authenticated:
            return obj.author == request.user or is_staff(request.user)

        return False


class NoRoleChange(permissions.BasePermission):
    '''
    Запрещает изменять поле role в /me обычным пользователям
    '''

    def has_object_permission(self, request, views, obj):
        if request.context.get('role'):
            return is_admin(request.user)

        return True
