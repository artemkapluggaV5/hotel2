from rest_framework import viewsets, mixins, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer

User = get_user_model()

class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "username": request.user.username,
            "email": request.user.email,
            "phone": request.user.phone,
            "role": request.user.role
        })

    def patch(self, request):
        user = request.user

        if 'email' in request.data:
            user.email = request.data['email']

        if 'phone' in request.data:
            user.phone = request.data['phone']

        user.save()
        return Response({"message": "Профиль успешно обновлен!"})


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email=email, verification_code=code)

            user.is_active = True
            user.verification_code = ''
            user.save()

            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "message": "Почта подтверждена!"})

        except User.DoesNotExist:
            return Response({"error": "Неверный код подтверждения"}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not user.check_password(current_password):
            return Response({"error": "Неверный текущий пароль"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Новые пароли не совпадают"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"error": "Пароль должен быть не менее 8 символов"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        Token.objects.filter(user=user).delete()
        new_token = Token.objects.create(user=user)

        return Response({
            "message": "Пароль успешно изменен",
            "new_token": new_token.key
        }, status=status.HTTP_200_OK)