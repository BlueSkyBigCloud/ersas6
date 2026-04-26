from rest_framework import serializers
from .models import ServiceRequest, APIObject
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from app.models import *
from business.models import *
from video.models import *

class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ['id', 'email', 'token', 'company', 'created_at', 'accepted']
        read_only_fields = ['id', 'token', 'created_at']

class APIObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIObject
        fields = ('id', 'name', 'description', 'created_by_user', 'updated_at', 'created_at')

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('name')


class DecryptFieldsMixin:

    def to_representation(self, instance):
         representation = super().to_representation(instance)
         fields_to_decrypt = self.get_fields_to_decrypt()
         for field in fields_to_decrypt:
             if field in representation:
                 representation[field] = self.decrypt_field(representation[field])
 
         return representation
 

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location.decrypt_fields

    def get_fields_to_decrypt(self):
        return ['address', 'city', 'state', 'country', 'description']
    
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'  # Include all fields

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = 'name'

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment.decrypt_fields
        fields = '__all__'  # Include all fields

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee.decrypt_fields
        fields = '__all__'  # Include all fields

class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType.decrypt_fields
        fields = '__all__'  # Include all fields

class ServiceRequestSerializer(serializers.ModelSerializer):
    start_location = serializers.StringRelatedField()
    end_location = serializers.StringRelatedField()
    equipment = serializers.StringRelatedField()
    employee = serializers.StringRelatedField()
    service_type = serializers.StringRelatedField()
    created_by_user = serializers.StringRelatedField()
    created_timestamp = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    class Meta:
        model = ServiceRequest
        fields = '__all__'  # Serialize all fields

class CustomUserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)  # Correct field from the Company model
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'company_name')  # Add any additional fields you need

from rest_framework import serializers
from .models import Directmessage

class DirectmessageSerializer(serializers.ModelSerializer, DecryptFieldsMixin):

    body = serializers.CharField()
    created_by_user = CustomUserSerializer(many=False, read_only=True)  # Read-only field
    to_users = CustomUserSerializer(many=True, read_only=True)
    created_timestamp = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Directmessage
        fields = '__all__'

    def to_representation(self, instance):
        # Get the current user
        user = self.context['request'].user

        # Decrypt the message body if the user is the creator or in the recipient list
        representation = super().to_representation(instance)
        if user == instance.created_by_user or user in instance.to_users.all():
            representation['body'] = decrypt(representation['body'])
        return representation


class CustomRegisterSerializer(RegisterSerializer):
    company_name = serializers.CharField(required=False, allow_blank=True)

    def save(self, request):
        user = super().save(request)
        user.company.name = self.data.get('company_name')
        user.save()
        return user


# Custom login serializer
class CustomLoginSerializer(LoginSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


    # We can override methods to add any custom logic for the login process if needed
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Username and password are required")
        
        # Additional validation logic can be added here if needed
        return attrs

from userpayment.models import UserPayment

class UserPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPayment
        fields = '__all__'

