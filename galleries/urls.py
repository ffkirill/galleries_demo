"""galleries URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework_extensions.routers import ExtendedDefaultRouter

from users.viewsets import UserViewSet, AuthViewSet
from albums.viewsets import AlbumViewSet, PhotoViewSet

router = ExtendedDefaultRouter()
router.register(r'users', UserViewSet, basename='user')

(router.register(r'albums', AlbumViewSet, basename='album')
       .register(r'photos', PhotoViewSet, 'photo',
                 parents_query_lookups=['object_id']))

router.register(r'auth', AuthViewSet, basename='auth')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^api-v1/', include(router.urls)),
]
