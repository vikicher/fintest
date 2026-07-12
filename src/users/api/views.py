from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from users.api.serializers import RegisterSerializer, UserSerializer, RegisterResponseSerializer


class RegisterView(generics.CreateAPIView):
    """Реєстрація користувача за email+пароль. Одразу повертає JWT-пару,
    щоб не змушувати користувача логінитись окремим запитом одразу після реєстрації."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Реєстрація користувача",
        description="Реєстрація за email+паролем. Одразу повертає JWT-пару, "
                    "щоб не змушувати користувача логінитись окремим запитом одразу після реєстрації.",
        request=RegisterSerializer,
        responses={201: RegisterResponseSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class UserView(generics.RetrieveAPIView):
    """Дані поточного автентифікованого користувача"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Поточний користувач",
        description="Повертає дані користувача, автентифікованого за JWT-токеном.",
        responses=UserSerializer,
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        return self.request.user