from uuid import UUID, uuid4
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ParseError
from rest_framework import status
from sqlalchemy.orm import exc

from . import Session

class SerializerModelMixin:
    """
    Provides model entities instantiation and modification facility for serializer
    """
    model = None
    
    def create(self, validated_data, **kwargs):
        return self.model(id=uuid4(), **validated_data)

    def update(self, instance, validated_data, **kwargs):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        return instance
    
    
class ViewSetModelMixin:
    """
    Provides CRUD operations implementation via SA backend to DRF's Viewsets
    """
    serializer_class = None
    obj = None

    def get_object_or_404(self, pk, **kwargs):
        sa_session = Session()
        try:
            query = (sa_session.query(self.serializer_class.model)
                     .filter(self.serializer_class.model.id == UUID(pk)))
            obj = self.apply_qs_filters(query, **kwargs).one()
            return obj
        except ValueError:
            raise ParseError
        except exc.NoResultFound:
            raise NotFound

    def kwargs_to_validated_data(self, kwargs):
        return kwargs

    def apply_qs_filters(self, qs, **kwargs):
        return qs

    def _post_save(self, request):
        if self.obj is not None:
            self.post_save(request)

    def post_save(self, request):
        pass

    def list(self, request, **kwargs):
        sa_session = Session()
        queryset = sa_session.query(self.serializer_class.model)
        serializer = self.serializer_class(
            self.apply_qs_filters(queryset, **kwargs),
            many=True,
            context={'request': request})
        return Response(serializer.data)
    
    def create(self, request, **kwargs):
        sa_session = Session()
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            self.obj = serializer.save(**self.kwargs_to_validated_data(kwargs))
            sa_session.add(self.obj)
            try:
                sa_session.commit()
                self._post_save(request)
            except Exception as e:
                sa_session.rollback()
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None, **kwargs):
        self.obj = self.get_object_or_404(pk, **kwargs)
        return Response(self.serializer_class(self.obj,  context={'request': request}).data)
    
    def _update(self, request, pk, partial=False, **kwargs):
        self.obj = self.get_object_or_404(pk, **kwargs)
        serializer = self.serializer_class(
            context={'request': request},
            data=request.data,
            instance=self.obj,
            partial=partial)
        if serializer.is_valid():
            serializer.save(**self.kwargs_to_validated_data(kwargs))
            sa_session = Session()
            try:
                sa_session.commit()
                self._post_save(request)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                sa_session.rollback()
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None, **kwargs):
        return self._update(request, pk, partial=False, **kwargs)
    
    def partial_update(self, request, pk=None, **kwargs):
        return self._update(request, pk, partial=True, **kwargs)

    def destroy(self, request, pk=None, **kwargs):
        self.obj = self.get_object_or_404(pk, **kwargs)
        sa_session = Session()
        sa_session.delete(self.obj)
        try:
            sa_session.commit()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            sa_session.rollback()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
