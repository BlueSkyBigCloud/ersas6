from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Notification

class NotificationTests(APITestCase):
    def setUp(self):
        self.notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test notification.",
            status="unread"
        )

    def test_get_notifications(self):
        response = self.client.get(reverse('get_notifications'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_notification(self):
        response = self.client.post(reverse('create_notification'), {
            'title': 'New Notification',
            'message': 'This is a new notification.',
            'status': 'unread'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_notification(self):
        response = self.client.put(reverse('update_notification', args=[self.notification.id]), {
            'title': 'Updated Notification',
            'message': 'This notification has been updated.',
            'status': 'read'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_notification(self):
        response = self.client.delete(reverse('delete_notification', args=[self.notification.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_authenticate_user(self):
        response = self.client.post(reverse('authenticate_user'), {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
