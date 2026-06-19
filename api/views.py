from urllib import request
from django.dispatch import receiver
from django.http import JsonResponse
from app.serializers import *
from app.models import APIObject, Employee
from app.models import ServiceRequest, Directmessage
import stripe
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from app.models import Invitation
from app.serializers import InvitationSerializer
import logging
logger = logging.getLogger(__name__)
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from app.permissions import CustomIsAuthenticated
from app.views import create_invite
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render
from video.models import Video

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [CustomIsAuthenticated]  # Ensure user is logged in

    def create(self, request, *args, **kwargs):
        email = request.data.get("email")  # Getting email from JSON payload

        if not email:
            return Response({"error": "Email address is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure `request` is passed properly to `create_invite`
        response = create_invite(request)  # Call the function

        # If the function returns a response (HTML-based), convert to API format
        if isinstance(response, Response):
            return response  # Return as is
        return Response({"message": "Invite sent successfully!"}, status=status.HTTP_201_CREATED)


class APIObjectViewSet(viewsets.ModelViewSet):
    queryset = APIObject.objects.all()
    serializer_class = APIObjectSerializer
    permission_classes = [CustomIsAuthenticated]

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [CustomIsAuthenticated]


class ServiceRequestView(APIView):
    def get(self, request):
        service_requests = ServiceRequest.objects.all()  # Ensure it's called
        serializer = ServiceRequestSerializer(service_requests, many=True)
        return Response(serializer.data)


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [CustomIsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        try:
            return ServiceRequest.objects.filter(
                created_by_user=user
            ) | ServiceRequest.objects.filter(
                assigned_employees__assigned_user=user
            )
        except Employee.DoesNotExist:
            return ServiceRequest.objects.filter(created_by_user=user)  # Default to user-created requests
        


from users.models import CustomUser

class DirectMessageViewSet(viewsets.ModelViewSet):
    queryset = Directmessage.objects.all()
    serializer_class = DirectmessageSerializer
    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            created_by_user = request.user
            to_emails = data.get("to_users", [])
            if not to_emails:
                return Response({"error": "At least one recipient is required."}, status=status.HTTP_400_BAD_REQUEST)
            # Fetch recipient users based on their email addresses
            recipient_users = CustomUser.objects.filter(email__in=to_emails)
            if not recipient_users.exists():
                return Response({"error": "No valid recipients found."}, status=status.HTTP_400_BAD_REQUEST)
            # Check that the created_by_user is not in the recipients
            if created_by_user.email in to_emails:
                return Response({"error": "You cannot send a message to yourself."}, status=status.HTTP_400_BAD_REQUEST)
            directmessage = Directmessage.objects.create(
                body=data['body'],
                created_by_user=created_by_user,
            )
            directmessage.to_users.set(recipient_users)
            return Response({"message": "Direct messages created!", "id": directmessage.id}, status=status.HTTP_201_CREATED)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def get_queryset(self):
        user = self.request.user
        return Directmessage.objects.filter(created_by_user=user) | Directmessage.objects.filter(to_users=user)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            if instance.created_by_user == request.user and instance.marked_for_deletion.count() == instance.to_users.count() + 1:
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "You do not have permission to delete this message."}, status=status.HTTP_403_FORBIDDEN)

        except Http404:
            return Response({"error": "Message not found."}, status=status.HTTP_404_NOT_FOUND)
        
class DirectmessageListView(APIView):
    def get(self, request):
        
        direct_messages = Directmessage.objects.filter(to_users=request.user)
        serializer = DirectmessageSerializer(direct_messages, many=True, context={'user': request.user})

        return Response(serializer.data)



from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'servicerequest', ServiceRequestViewSet)
urlpatterns = router.urls

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from rest_framework.exceptions import AuthenticationFailed
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

@api_view(['POST'])
def verify_token(request):
    token = request.headers.get('Authorization')
    if not token:
        raise AuthenticationFailed('Authorization token missing')
    if token.startswith('Bearer '):
        token = token[7:]
    try:
        user = User.objects.get(auth_token=token)
        email_from_request = request.data.get('email')
        if user.email != email_from_request:
            raise AuthenticationFailed('Token does not match email')
        return Response({'message': 'Token verified successfully'})
    except User.DoesNotExist:
        raise AuthenticationFailed('Invalid token')


@receiver(post_save, sender=Token)
def create_api_key_on_token_creation(sender, instance, created, **kwargs):
    if created:  # Ensure this only runs when a token is newly created
        api_key, key = APIKey.objects.create_key(name=f"{instance.user.email}_api_key")
        print(f"API Key for {instance.user.email}: {key}")  # Log the API key


User = get_user_model()

from rest_framework.decorators import api_view, authentication_classes, permission_classes



@api_view(['GET'])
@authentication_classes([TokenAuthentication])  # Supports JWT and Token Auth
@permission_classes([CustomIsAuthenticated])
def check_auth_token(request):
    # Retrieve the token from the request
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return Response({"error": "Authorization token is required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        # Extract token from header
        token_key = auth_header.split(" ")[1]  # Extract token part after "Bearer" or "Token"

        # Check if token exists in the database
        token = Token.objects.get(key=token_key)

        # Ensure the token belongs to the authenticated user
        if token.user != request.user:
            return Response({"error": "Invalid token for user"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"message": "User authenticated successfully", "user": request.user.email})

    except Token.DoesNotExist:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny]) 
def create_user(request):
    data = request.data
    if 'email' not in data or 'password' not in data:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=data['email']).exists():
        return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        email=data['email'],
        username=data.get('username', ''),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        password=data['password']
    )

    return Response({"message": "User created successfully", "user_id": user.id}, status=status.HTTP_201_CREATED)

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow non-authenticated users to request password reset
def forgot_password(request):
    email = request.data.get('email')

    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'No user with this email'}, status=status.HTTP_404_NOT_FOUND)
    reset_url = "www.proforops.com/accounts/password/reset"

    send_mail(
        subject="Password Reset Request",
        message=f"Click the link to reset your password: {reset_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get('email')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not email or not token or not new_password:
        return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

from userpayment.views import *
from rest_framework.exceptions import ValidationError

import urllib.request

@api_view(['POST'])
def create_payment_session(request):
    try:
        logger.info(f"Request received: {request.body}")
        data = request.data
        price_id = data.get("price_id")
        if not price_id:
            raise ValidationError("Price ID is missing from the request")
        
        if not isinstance(price_id, str):
            raise ValidationError("Invalid Price ID")
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode='subscription',
            success_url="https://www.proforops.com/success",
            cancel_url="https://www.proforops.com/cancel",
        )
        return JsonResponse({'id': session.id, 'checkout_url': session.url})

    except Exception as e:
        # Handle other exceptions
        return JsonResponse({'error': str(e)})
    

@api_view(['GET'])
@authentication_classes([TokenAuthentication])  # Supports JWT and Token Auth
@permission_classes([CustomIsAuthenticated])
def get_stripe_secret_key(request):
    return Response({"stripe_secret_key": settings.STRIPE_PUBLISHABLE_KEY})



