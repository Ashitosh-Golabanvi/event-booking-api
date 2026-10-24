
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
    request=RegisterSerializer,
    responses={201: dict, 400: dict},
)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
    request=LoginSerializer,
    responses={200: dict, 401: dict},
)

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(access),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_401_UNAUTHORIZED,
        )

class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class TokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
    request=TokenRefreshRequestSerializer,
    responses={200: dict, 400: dict, 401: dict},
)

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token

            return Response(
                {"access": str(access_token)},
                status=status.HTTP_200_OK,
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )