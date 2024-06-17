from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, StaffSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsDeliveryCrew, IsManager
from django.contrib.auth.models import User, Group
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from datetime import date


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
        
class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            return Order.objects.all()
        elif self.request.user.groups.filter(name="Delivery Crew").exists():
            return Order.objects.filter(delivery_crew = self.request.user)
        else:
            return Order.objects.filter(user = self.request.user)
        
    def create(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user = request.user)
        cart_items = cart.values()

        if not cart_items:
            return Response({'message': 'Cart is empty'}, status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(user = request.user, status = False, total = sum(cart_item['price'] for cart_item in cart_items), date = str(date.today()))

        for item in cart_items:
            order_item = OrderItem.objects.create(order = order, menuitem = get_object_or_404(MenuItem, id=item['menuitem_id']), quantity = item.get('quantity'), unit_price = item.get('unit_price'), price = item.get('price'))
            order_item.save()

        cart.delete()
        return Response({'message': 'Successfully placed order'}, status.HTTP_201_CREATED)

class OrderItemView(generics.ListAPIView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemSerializer

    def get_permissions(self):
        order = Order.objects.get(pk=self.kwargs['pk'])
        if self.request.user == order.user and self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PUT' or self.request.method == 'DELETE':
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        elif self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsManager | IsDeliveryCrew]
        else:
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        return[permission() for permission in permission_classes] 

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return OrderItem.objects.all()
        selected_order = Order.objects.get(id=self.kwargs.get('pk'))
        return OrderItem.objects.filter(order=selected_order)
    
    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()
        return Response({'message':'Status of order #'+ str(order.id)+' changed to '+str(order.status)}, status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        OrderItemSerializer(data=request.data).is_valid()
        new_crew_id = request.data['delivery_crew']
        new_crew = get_object_or_404(User, pk=new_crew_id)
        order.delivery_crew = new_crew
        order.save()
        return Response({'message': 'Updated Delivery Crew to ' + str(new_crew) + ' for order ' + str(order.id)})
    
    def destroy(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs.get('pk'))
        order_id = order.id
        order.delete()
        return Response({'message': "Deleted order " + str(order_id)})
