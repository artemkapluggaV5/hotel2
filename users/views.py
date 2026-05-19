from rest_framework import viewsets, mixins, permissions
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