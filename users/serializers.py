from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'full_name', 'phone']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_username(self, value):
        if not re.fullmatch(r'[A-Za-z0-9]+', value):
            raise serializers.ValidationError('Логин должен содержать только латинские буквы и цифры.')
        if len(value) < 6:
            raise serializers.ValidationError('Логин должен быть не короче 6 символов.')
        return value

    def validate_full_name(self, value):
        if value and not re.fullmatch(r'[А-Яа-яЁё\s]+', value):
            raise serializers.ValidationError('ФИО должно содержать только русские буквы.')
        return value

    def validate_phone(self, value):
        if value:
            if not re.fullmatch(r'^(\+7|8)\d{10}$', value):
                raise serializers.ValidationError('Введите номер в формате +79991234567 или 89991234567')

            if User.objects.filter(phone=value).exists():
                raise serializers.ValidationError('Этот номер телефона уже зарегистрирован.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Этот Email уже занят.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        token, _ = Token.objects.get_or_create(user=instance)
        ret['token'] = token.key
        return ret