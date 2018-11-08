from uuid import UUID

from django.conf import settings

from rest_framework import viewsets, serializers, parsers
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

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
        if 'status' in value:
            return value
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

    def _process_file(self, instance, validated_data):
        upfile = validated_data['orig_file']
        instance.orig_file = save_uploaded_photo(upfile)


    def create(self, validated_data, **kwargs):
        instance = super().create(validated_data, **kwargs)
        instance.thumbnails = {'status': 'processing'}
        self._process_file(instance, validated_data)
        return instance

    def update(self, instance, validated_data, **kwargs):
        instance = super().update(instance, validated_data, **kwargs)
        self._process_file(instance, validated_data)
        return instance

class PhotoAlbumPermission(IsAuthenticated):
    def has_permission(self, request, view):
        result = super().has_permission(request, view)
        if result and request.method not in SAFE_METHODS:
            return Session().query(Album).filter(Album.id == view.kwargs['parent_lookup_object_id'],
                                          Album.user_id == request.user.id).first() is not None
        else:
            return result


class PhotoViewSet(ViewSetModelMixin, viewsets.ViewSet):
    """
    Album's photos CRUD operations.
    Requires auth via session_key url param
    """
    authentication_classes = (SessionIdAuthentication,)
    permission_classes = (PhotoAlbumPermission,)
    serializer_class = PhotoSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser,)

    def apply_qs_filters(self, qs, **kwargs):
        return (qs.filter(Photo.album_id == UUID(kwargs['parent_lookup_object_id']))
                  .join(Album)
                  .filter(Album.user_id == self.request.user.id))

    def kwargs_to_validated_data(self, kwargs):
        return {'album_id': UUID(kwargs['parent_lookup_object_id'])}

    def post_save(self, request):
        process_upload(str(self.obj.id), str(request.user.id), self.obj.orig_file)
