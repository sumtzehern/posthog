from typing import Dict, Optional

from django.test import TestCase
from rest_framework.test import APITestCase

from posthog.models import Organization, Team, User


class ErrorResponsesMixin:
    ERROR_RESPONSE_UNAUTHENTICATED: Dict[str, Optional[str]] = {
        "type": "authentication_error",
        "code": "not_authenticated",
        "detail": "Authentication credentials were not provided.",
        "attr": None,
    }

    ERROR_RESPONSE_NOT_FOUND: Dict[str, Optional[str]] = {
        "type": "invalid_request",
        "code": "not_found",
        "detail": "Not found.",
        "attr": None,
    }

    def permission_denied_response(
        self, message: str = "You do not have permission to perform this action.",
    ) -> Dict[str, Optional[str]]:
        return {
            "type": "authentication_error",
            "code": "permission_denied",
            "detail": message,
            "attr": None,
        }


class TestMixin:
    TESTS_ORGANIZATION_NAME: str = "Test"
    TESTS_EMAIL: Optional[str] = "user1@posthog.com"
    TESTS_PASSWORD: Optional[str] = "testpassword12345"
    TESTS_API_TOKEN: str = "token123"
    TESTS_AUTO_LOGIN: bool = True
    team: Team = None
    user: User = None

    def _create_user(self, email: str, password: Optional[str] = None, first_name: str = "", **kwargs) -> User:
        return User.objects.create_and_join(self.organization, email, password, first_name, **kwargs)

    def setUp(self):
        super().setUp()
        if self.TESTS_AUTO_LOGIN and self.user:
            self.client.force_login(self.user)

    @classmethod
    def setUpTestData(cls):
        cls.organization: Organization = Organization.objects.create(name=cls.TESTS_ORGANIZATION_NAME)
        cls.team: Team = Team.objects.create(
            organization=cls.organization,
            api_token=cls.TESTS_API_TOKEN,
            test_account_filters=[
                {"key": "email", "value": "@posthog.com", "operator": "not_icontains", "type": "person"},
            ],
        )
        if cls.TESTS_EMAIL:
            cls.user = User.objects.create_and_join(cls.organization, cls.TESTS_EMAIL, cls.TESTS_PASSWORD)
            cls.organization_membership = cls.user.organization_memberships.get()


class BaseTest(TestMixin, ErrorResponsesMixin, TestCase):
    """
    Base class for performing Postgres-based backend unit tests on.
    Each class and each test is wrapped inside an atomic block to rollback DB commits after each test.
    Read more: https://docs.djangoproject.com/en/3.1/topics/testing/tools/#testcase 
    """

    pass


class APIBaseTest(TestMixin, ErrorResponsesMixin, APITestCase):
    """
    Functional API tests using Django REST Framework test suite.
    """

    pass
