from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password"]

    def validate_email(self, value: str) -> str:
        normalized_email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("Користувач з таким email вже існує.")
        return normalized_email

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "date_joined"]