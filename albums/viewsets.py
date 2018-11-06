from uuid import UUID
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated

from sa_helper.viewsets import ViewSetModelMixin, SerializerModelMixin
from users.auth import SessionIdAuthentication

from .mappings import Album


class AlbumSerializer(SerializerModelMixin, serializers.Serializer):
    model = Album

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=200, allow_blank=True)

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.user_id = UUID(self.context['request'].user.id)
        return instance

class AlbumViewSet(ViewSetModelMixin, viewsets.ViewSet):
    """
    Albums CRUD operations, shows only owned (via user_id field) albums.
    Requires auth via session_key url param
    """
    authentication_classes = (SessionIdAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = AlbumSerializer

    def apply_qs_filters(self, qs):
        return qs.filter(Album.user_id == self.request.user.id)
