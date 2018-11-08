from uuid import UUID

from django.conf import settings

from rest_framework import viewsets, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from sa_helper import Session
from sa_helper.viewsets import ViewSetModelMixin, SerializerModelMixin
from users.auth import SessionIdAuthentication

from .mappings import Album, Photo
from .file_storage import save_uploaded_photo
from .tasks import process_upload


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

    def destroy(self, request, pk=None, **kwargs):
        album = self.get_object_or_404(pk)
        sa_session = Session()
        sa_session.delete(album)
        try:
            sa_session.commit()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            sa_session.rollback()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImageField(serializers.ImageField):
    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(settings.MEDIA_URL + value)
        return value


class ThumbnailsJSONField(serializers.JSONField):
    def to_representation(self, value):
        value = super().to_representation(value)
        if not value:
            return None
        request = self.context.get('request', None)
        if request is not None:
            return {key:request.build_absolute_uri(settings.MEDIA_URL + filename)
                    for key, filename in value.items()}
        return value


class PhotoSerializer(SerializerModelMixin, serializers.Serializer):
    model = Photo

    id = serializers.UUIDField(read_only=True)
    orig_file = ImageField()
    thumbnails = ThumbnailsJSONField(read_only=True)

    def create(self, validated_data, **kwargs):
        instance = super().create(validated_data, **kwargs)
        upfile = validated_data['orig_file']
        instance.orig_file = save_uploaded_photo(upfile)
        return instance


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

    def create(self, request, **kwargs):
        result = super().create(request, **kwargs)
        process_upload(self.obj.id, str(request.user.id), self.obj.orig_file)
        return result
