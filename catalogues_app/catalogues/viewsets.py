from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import serializers, viewsets

from sa_helper.viewsets import SerializerModelMixin, ViewSetModelMixin
from .mappings import Country, EyeColor


class BaseSerializer(SerializerModelMixin, serializers.Serializer):

    model = None

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=400, allow_blank=True)


class CountrySerializer(BaseSerializer):
    model = Country
    url = serializers.HyperlinkedIdentityField(view_name='country-detail',
                                               lookup_field='id',
                                               lookup_url_kwarg='pk')


class EyeColorSerializer(BaseSerializer):
    model = EyeColor
    url = serializers.HyperlinkedIdentityField(view_name='eye-color-detail',
                                               lookup_field='id',
                                               lookup_url_kwarg='pk')


class CountryViewSet(ViewSetModelMixin, viewsets.ViewSet):
    serializer_class = CountrySerializer

    @method_decorator(cache_page(60 * 60 * 24, key_prefix='countries'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EyeColorViewSet(ViewSetModelMixin, viewsets.ViewSet):
    serializer_class = EyeColorSerializer

    @method_decorator(cache_page(60 * 60 * 24, key_prefix='eye_colors'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


