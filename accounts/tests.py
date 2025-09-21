from django.urls import reverse
from rest_framework import status
from rest_framework import serializers
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Profile, Role, AuditLog
from accounts.serializers import LoginSerializer

User = get_user_model()

class UserRegistrationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('accounts:register')
        self.valid_payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_register_user_success(self):
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_duplicate_email(self):
        # Create a user first
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='testpass123'
        )
        
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('email' in response.data)

class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_jwt_login_success(self):
        # Ensure the user exists and is active
        user = User.objects.get(email='test@example.com')
        user.is_active = True
        user.save()
        
        data = {
            'username_or_email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        # Debug output
        print("\n=== Login Response ===")
        print(f"Status: {response.status_code}")
        print(f"Data: {response.data}")
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK, 
                        f"Expected 200 OK, got {response.status_code}. Response: {response.data}")
        
        # Check response data structure
        self.assertIn('access', response.data, "Response should contain 'access' token")
        self.assertIn('refresh', response.data, "Response should contain 'refresh' token")
        self.assertIn('user', response.data, "Response should contain 'user' data")
        self.assertEqual(response.data['user']['email'], 'test@example.com', 
                        f"Expected user email to be 'test@example.com', got {response.data.get('user', {}).get('email')}")

    def test_jwt_login_invalid_credentials(self):
        data = {
            'username_or_email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_logout(self):
        print("\n=== Starting test_jwt_logout ===")
        
        # First, ensure the user is active
        user = User.objects.get(email='test@example.com')
        user.is_active = True
        user.save()
        print(f"User active status: {user.is_active}")
        
        # Login to get tokens
        login_data = {
            'username_or_email': 'test@example.com',
            'password': 'testpass123'
        }
        print(f"Login data: {login_data}")
        
        login_response = self.client.post(self.login_url, login_data, format='json')
        print(f"Login response status: {login_response.status_code}")
        print(f"Login response data: {login_response.data}")
        
        # Check if login was successful
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', login_response.data)
        self.assertIn('access', login_response.data)
        
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']
        print(f"Refresh token: {refresh_token[:15]}...")
        print(f"Access token: {access_token[:15]}...")
        
        # Now try to logout with the refresh token
        print("\n=== Attempting logout ===")
        import json
        
        # Print token details for debugging
        print(f"Refresh token length: {len(refresh_token)} characters")
        print(f"Refresh token (first 50 chars): {refresh_token[:50]}")
        print(f"Access token length: {len(access_token)} characters")
        print(f"Access token (first 50 chars): {access_token[:50]}")
        
        # Prepare logout data
        logout_data = {'refresh': refresh_token}
        json_data = json.dumps(logout_data)
        
        print(f"Logout data (dict): {logout_data}")
        print(f"Logout data (JSON): {json_data}")
        
        # Make the request with explicit JSON content
        response = self.client.post(
            self.logout_url,
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        print(f"Logout response status: {response.status_code}")
        print(f"Logout response data: {response.data}")
        print(f"Response headers: {dict(response.items())}")
        
        # Check logout response
        self.assertEqual(
            response.status_code, 
            status.HTTP_205_RESET_CONTENT,
            f"Expected 205 RESET_CONTENT, got {response.status_code}. Response: {response.data}"
        )
        
        # Verify the refresh token was blacklisted
        print("\n=== Verifying token blacklist ===")
        try:
            # Try to refresh the token (should fail if blacklisted)
            refresh = RefreshToken(refresh_token)
            # If we get here, the token wasn't blacklisted
            print("ERROR: Token was not blacklisted after logout!")
            self.fail("The refresh token should be blacklisted after logout")
        except Exception as e:
            # We expect an exception here
            error_message = str(e).lower()
            print(f"Expected error when using blacklisted token: {error_message}")
            self.assertTrue(
                any(x in error_message for x in ['blacklisted', 'invalid', 'expired']),
                f"Expected token to be blacklisted or invalid, got: {error_message}"
            )

class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create a profile for the user
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='',
            department=''
        )
        self.profile_url = reverse('accounts:profile')
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], self.user.email)

    def test_update_profile(self):
        data = {
            'phone_number': '+1234567890',
            'department': 'Engineering'
        }
        response = self.client.patch(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], data['phone_number'])
        self.assertEqual(response.data['department'], data['department'])
        # Refresh the profile from the database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone_number, data['phone_number'])
        self.assertEqual(self.profile.department, data['department'])

class RoleTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.role = Role.objects.create(
            name='developer',  # Using one of the valid role names
            description='A test role'
        )
        self.roles_url = reverse('accounts:role-list')

    def test_create_role_admin(self):
        # Setup test data - using one of the valid role names from Role.RoleName
        role_name = 'manager'  # Using 'manager' which is one of the valid choices
        data = {
            'name': role_name,
            'description': 'A new test role'
        }
        
        # Make the request
        self.client.force_authenticate(user=self.admin)
        initial_count = Role.objects.count()
        response = self.client.post(self.roles_url, data, format='json')
        
        # Check the response
        if response.status_code != status.HTTP_201_CREATED:
            print(f"\n=== Error Response ===")
            print(f"Status: {response.status_code}")
            print(f"Data: {response.data}")
        
        # Assert the response status code and basic data
        self.assertEqual(
            response.status_code, 
            status.HTTP_201_CREATED,
            f"Expected status code 201, but got {response.status_code}. Response: {response.data}"
        )
        self.assertEqual(Role.objects.count(), initial_count + 1)
        self.assertTrue(Role.objects.filter(name='manager').exists())
        
        # Verify the audit log was created (simplified check)
        self.assertTrue(AuditLog.objects.filter(
            user=self.admin,
            action='role_create'
        ).exists())

    def test_create_role_unauthorized(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {'name': 'Unauthorized Role'}
        response = self.client.post(self.roles_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Role.objects.filter(name='Unauthorized Role').exists())

class AuditLogTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.login_url = reverse('accounts:login')

    def test_audit_log_on_login(self):
        # Ensure the user is active
        self.user.is_active = True
        self.user.save()
        
        # First, verify no audit logs exist
        initial_audit_logs = AuditLog.objects.count()
        
        # Make login request
        data = {
            'username_or_email': 'test@example.com',
            'password': 'testpass123'
        }
        
        # Debug output
        print("\n=== Login Request ===")
        print(f"URL: {self.login_url}")
        print(f"Data: {data}")
        
        response = self.client.post(self.login_url, data, format='json')
        
        # Debug output
        print("\n=== Login Response ===")
        print(f"Status: {response.status_code}")
        print(f"Data: {response.data}")
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        f"Expected 200 OK, got {response.status_code}. Response: {response.data}")
        
        # Check the response structure
        self.assertIn('access', response.data, "Response should contain 'access' token")
        self.assertIn('refresh', response.data, "Response should contain 'refresh' token")
        self.assertIn('user', response.data, "Response should contain 'user' data")
        
        # Verify exactly one new audit log was created
        self.assertEqual(AuditLog.objects.count(), initial_audit_logs + 1,
                        f"Expected {initial_audit_logs + 1} audit logs, found {AuditLog.objects.count()}")
        
        # Get the created audit log
        audit_log = AuditLog.objects.filter(action='user_login').order_by('-timestamp').first()
        self.assertIsNotNone(audit_log, "No login audit log found")
        
        # Verify audit log details
        self.assertEqual(audit_log.user, self.user,
                        f"Audit log user {audit_log.user} does not match test user {self.user}")
        self.assertEqual(audit_log.action, 'user_login',
                        f"Expected action 'user_login', got '{audit_log.action}'")
        self.assertIsNotNone(audit_log.ip_address,
                            "Audit log IP address should not be None")
        self.assertIsNotNone(audit_log.timestamp,
                            "Audit log timestamp should not be None")
        
        # Verify the metadata contains the expected keys
        self.assertIsNotNone(audit_log.metadata,
                            "Audit log metadata should not be None")
        self.assertIn('user_agent', audit_log.metadata,
                     "Audit log metadata should contain 'user_agent'")

class ChangePasswordTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        self.change_password_url = reverse('accounts:change-password')
        self.client.force_authenticate(user=self.user)

    def test_change_password(self):
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(
            self.change_password_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
        
        # Verify audit log
        self.assertTrue(AuditLog.objects.filter(
            user=self.user,
            action='password_change'
        ).exists())

    def test_change_password_wrong_old_password(self):
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(
            self.change_password_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)