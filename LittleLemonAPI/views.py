from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from .models import MenuItem
from .serializers import MenuItemSerializer, StaffSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsDeliveryCrew, IsManager
from django.contrib.auth.models import User, Group
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            permission_classes = [IsAuthenticated, IsManager]
        elif self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        
        return [permission() for permission in permission_classes]

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated, IsManager]
        elif self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
class ManagersView(generics.ListAPIView, generics.CreateAPIView):
    group = Group.objects.get(name='Manager')
    queryset = User.objects.filter(groups=group)
    serializer_class = StaffSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'GET']:
            permission_classes = [IsAuthenticated, IsManager]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            try:
                user = get_object_or_404(User, username=username)
            except (Http404):
                super().create(request, *args, **kwargs)
                user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)
            return Response({'message':'Successfully added user to Manager group'}, status.HTTP_201_CREATED)
    
class DeliveryCrewView(generics.ListCreateAPIView):
    group = Group.objects.get(name='Delivery Crew')
    queryset = User.objects.filter(groups=group)
    serializer_class = StaffSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'GET']:
            permission_classes = [IsAuthenticated, IsManager]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            try:
                user = get_object_or_404(User, username=username)
            except (Http404):
                super().create(request, *args, **kwargs)
                user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.add(user)
            return Response({'message':'Successfully added user to Delivery Crew group'}, status.HTTP_201_CREATED)

class SingleManagerView(generics.DestroyAPIView):
    group = Group.objects.get(name='Manager')
    queryset = User.objects.filter(groups=group)
    serializer_class = StaffSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            permission_classes = [IsAuthenticated, IsManager]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]

        return [permission() for permission in permission_classes]
    
class SingleDeliveryCrewMemberView(generics.DestroyAPIView):
    group = Group.objects.get(name='Delivery Crew')
    queryset = User.objects.filter(groups=group)
    serializer_class = StaffSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            permission_classes = [IsAuthenticated, IsManager]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]

        return [permission() for permission in permission_classes]