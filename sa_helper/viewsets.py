from uuid import UUID, uuid4
from rest_framework.response import Response
from rest_framework import status
from sqlalchemy.orm import exc

from . import Session

class SerializerModelMixin:
    """
    Provides model entities instantiation and modification facility for serializer
    """
    model = None
    
    def create(self, validated_data):
        return self.model(id=uuid4(), **validated_data)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        return instance
    
    
class ViewSetModelMixin:
    """
    Provides CRUD operations implementation via SA backend to DRF's Viewsets
    """
    serializer_class = None

    def get_object_or_404(self, pk):
        sa_session = Session()
        try:
            query = (sa_session.query(self.serializer_class.model)
                     .filter(self.serializer_class.model.id == UUID(pk)))
            obj = self.apply_qs_filters(query.one())
            return obj
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except exc.NoResultFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def apply_qs_filters(self, qs):
        return qs

    def list(self, request):
        sa_session = Session()
        queryset = sa_session.query(self.serializer_class.model)
        serializer = self.serializer_class(
            self.apply_qs_filters(queryset),
            many=True,
            context={'request': request})
        return Response(serializer.data)
    
    def create(self, request):
        sa_session = Session()
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            obj = serializer.save()
            sa_session.add(obj)
            sa_session.commit()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        obj = self.get_object_or_404(pk)
        return Response(self.serializer_class(obj,  context={'request': request}).data)
    
    def _update(self, request, pk, partial=False):
        obj = self.get_object_or_404(pk)
        serializer = self.serializer_class(
            context={'request': request},
            data=request.data,
            instance=obj,
            partial=partial)
        if serializer.is_valid():
            serializer.save()
            Session().commit()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        return self._update(request, pk, partial=False)
    
    def partial_update(self, request, pk=None):
        return self._update(request, pk, partial=True)
