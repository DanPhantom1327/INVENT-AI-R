from rest_framework.permissions import BasePermission


class TienePermisoDeRol(BasePermission):

    def has_permission(
        self,
        request,
        view
    ):

        roles_permitidos = getattr(
            view,
            "roles_permitidos",
            None
        )

        if not roles_permitidos:
            return True

        usuario = request.user

        return bool(
            usuario
            and getattr(
                usuario,
                "rol",
                None
            ) in roles_permitidos
        )