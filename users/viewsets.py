from rest_framework import serializers, viewsets, status
from rest_framework.response import Response

from sa_helper import Session
from sa_helper.viewsets import SerializerModelMixin, ViewSetModelMixin

from .auth import create_session_key, SessionIdAuthentication
from .mappings import User


class PasswordField(serializers.CharField):
    def to_representation(self, value):
        return super().to_representation(value.hash)


class UserSerializer(SerializerModelMixin, serializers.Serializer):

    model = User

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    father_name = serializers.CharField(max_length=200)
    password = PasswordField(max_length=50)
    email = serializers.EmailField()
    country_id = serializers.UUIDField(required=False, allow_null=True)
    eyes_id = serializers.UUIDField(required=False, allow_null=True)

    url = serializers.HyperlinkedIdentityField(view_name='user-detail',
                                               lookup_field='id',
                                               lookup_url_kwarg='pk')

class UserViewSet(ViewSetModelMixin, viewsets.ViewSet):
    """
    User profiles CRUD operations
    """

    serializer_class = UserSerializer


class AuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = PasswordField(max_length=50)

    def create(self, validated_data):
        return validated_data

class AuthViewSet(viewsets.ViewSet):
    """
    Users auth via email and password
    POST: Returns the session_key for the valid email & password pair
    GET: For the valid session_key in URL returns the authorised users's id, null otherwise
    """
    authentication_classes = (SessionIdAuthentication,)
    serializer_class = AuthSerializer

    def get_view_name(self):
        return 'Auth endpoint'

    def list(self, request):
        return Response({'user_id': request.user.id})

    def create(self, request):
        sa_session = Session()
        serializer = AuthSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            user = sa_session.query(User).filter(User.email == data['email']).one_or_none()
            if user and user.password == data['password']:
                return Response({'status': 'OK',
                                 'session_key': create_session_key(str(user.id))},
                                status=status.HTTP_200_OK)
        return Response({'status': 'AUTH_ERROR'}, status=status.HTTP_403_FORBIDDEN)

