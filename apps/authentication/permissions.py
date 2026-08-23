from rest_framework import permissions

class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsOwnerOrShared(permissions.BasePermission):
     
    def has_object_permission(self, request, view, obj):
         
        if hasattr(obj, 'owner_id') and str(obj.owner_id) == str(request.user.id):
            return True
         