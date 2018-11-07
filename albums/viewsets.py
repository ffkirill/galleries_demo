from uuid import UUID
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated

from sa_helper.viewsets import ViewSetModelMixin, SerializerModelMixin
from users.auth import SessionIdAuthentication

from .mappings import Album, Photo


class AlbumSerializer(SerializerModelMixin, serializers.Serializer):
    model = Album

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=200, allow_blank=True)
    url = serializers.HyperlinkedIdentityField(view_name='album-detail',
                                               lookup_field='id',
                                               lookup_url_kwarg='pk')

    def create(self, validated_data, **kwargs):
        instance = super().create(validated_data)
        instance.user_id = UUID(self.context['request'].user.id)
        return instance

    def update(self, instance, validated_data, **kwargs):
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

    def apply_qs_filters(self, qs, **kwargs):
        return qs.filter(Album.user_id == self.request.user.id)


class PhotoSerializer(SerializerModelMixin, serializers.Serializer):
    model = Photo

    id = serializers.UUIDField(read_only=True)
    orig_file = serializers.URLField()
    thumbnails = serializers.JSONField()


class PhotoViewSet(ViewSetModelMixin, viewsets.ViewSet):
    """
    Album's photos CRUD operations.
    Requires auth via session_key url param
    """
    authentication_classes = (SessionIdAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PhotoSerializer

    def apply_qs_filters(self, qs, **kwargs):
        return qs.filter(Photo.album_id == UUID(kwargs['parent_lookup_object_id']),
                         Album.user_id == self.request.user.id)

    def kwargs_to_validated_data(self, kwargs):
        return {'album_id': UUID(kwargs['parent_lookup_object_id'])}
