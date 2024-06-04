from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, StaffSerializer, CartSerializer
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
        try:
            username = request.data['username']
        except:
            return HttpResponseBadRequest("No username given")
        if username:
            try:
                user = get_object_or_404(User, username=username)
            except (Http404):
                super().create(request, *args, **kwargs)
                user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)
            managers.save()
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
        try:
            username = request.data['username']
        except:
            return HttpResponseBadRequest("No username given")
        if username:
            try:
                user = get_object_or_404(User, username=username)
            except (Http404):
                super().create(request, *args, **kwargs)
                user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.add(user)
            delivery_crew.save()
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

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response({'message':'Successfully deleted specified Manager'}, status.HTTP_200_OK)
    
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
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response({'message':'Successfully deleted specified Delivery Crew member'}, status.HTTP_200_OK)
    
class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Cart.objects.filter(user=user)
    
    def create(self, request, *args, **kwargs):
        request_item = request.data['menuitem']
        menuitem = MenuItem.objects.get(pk=request_item['id'])
        quantity = (int) (request.data['quantity'])
        unit_price = menuitem.price
        price = quantity * unit_price

        if not menuitem:
            return Response({'message': 'Unable to retrieve valid item'}, status.HTTP_400_BAD_REQUEST)
        try:
            cart_item = Cart.objects.create(user = self.request.user, menuitem = menuitem, quantity = quantity, unit_price = unit_price, price = price)
            
        except:
            cart_item = Cart.objects.get(menuitem=request_item['id'])
            cart_item.quantity += quantity
            
        cart_item.save()
        return Response({'message':'Successfully added to cart'}, status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        user = self.request.user
        try: 
            Cart.objects.filter(user=user).delete()
            return Response({'message': 'Successfully deleted cart'}, status.HTTP_200_OK)
        except:
            return Response({'message': 'Unable to delete cart'}, status.HTTP_400_BAD_REQUEST)
        