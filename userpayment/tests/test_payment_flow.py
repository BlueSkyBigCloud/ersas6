import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from userpayment.models import UserPayment
from company.models import Company

User = get_user_model()


@pytest.mark.django_db
class TestPaymentFlow:

    @pytest.fixture
    def user(self, client):
        """Create a test user and log them in."""
        user = User.objects.create_user(email="test@example.com", password="pass1234")
        client.force_login(user)
        return user

    def test_user_payment_created_on_first_payment(self, client, user):
        """Ensure UserPayment is created when first visiting make_payment."""
        url = reverse("make_payment")
        response = client.get(url)
        assert response.status_code == 200
        assert UserPayment.objects.filter(app_user=user).exists()

    @patch("stripe.Customer.create")
    @patch("stripe.checkout.Session.create")
    def test_checkout_session_created(
        self, mock_session_create, mock_customer_create, client, user
    ):
        """Test that Stripe checkout session is created properly."""
        mock_customer_create.return_value = {"id": "cus_test123"}
        mock_session_create.return_value = type(
            "obj", (object,), {"url": "https://checkout.stripe.test/session"}
        )

        url = reverse("make_payment")
        response = client.post(url)

        # Check redirect to mocked Stripe URL
        assert response.status_code == 302
        assert "stripe.test" in response.url

        # Verify Stripe calls were made
        mock_customer_create.assert_called_once()
        mock_session_create.assert_called_once()

        # Ensure UserPayment was updated
        payment = UserPayment.objects.get(app_user=user)
        assert payment.stripe_checkout_id == "cus_test123"

    def test_company_subscription_activated_on_payment_signal(self, user):
        """Ensure company subscription is activated when payment_bool=True."""
        company = Company.objects.create(
            name="Test Company",
            address="123 Test St",
            city="Testville",
            zip=12345,
            state="TS",
            country="USA",
            created_by_user=user,
        )
        user.company = company
        user.save()

        # Create payment and mark as successful
        payment = UserPayment.objects.create(app_user=user, payment_bool=False)
        payment.payment_bool = True
        payment.save()  # should trigger post_save signal

        company.refresh_from_db()
        assert company.is_company_subscription_active is True