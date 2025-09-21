from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework.test import force_authenticate
from datetime import date, timedelta

from .models import Project, ProjectLabel, ProjectStatus, ProjectPriority
from .permissions import IsProjectMemberOrCreator

User = get_user_model()


class ProjectModelTest(TestCase):
    """Test the Project model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            created_by=self.user,
            status=ProjectStatus.PLANNED,
            priority=ProjectPriority.MEDIUM,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
    
    def test_project_creation(self):
        """Test project creation with required fields."""
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.created_by, self.user)
        self.assertEqual(self.project.status, ProjectStatus.PLANNED)
        self.assertEqual(self.project.priority, ProjectPriority.MEDIUM)
        self.assertIsNotNone(self.project.id)
        # Check that the creator is automatically added as a member
        self.assertIn(self.user, self.project.members.all())
    
    def test_project_str_representation(self):
        """Test the string representation of the project."""
        # The actual implementation includes the status in parentheses
        expected = f'Test Project ({ProjectStatus.PLANNED.label})'
        self.assertEqual(str(self.project), expected)
    
    def test_project_dates_validation(self):
        """Test that end date cannot be before start date."""
        invalid_project = Project(
            name='Invalid Project',
            created_by=self.user,
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1)  # End date before start date
        )
        with self.assertRaises(Exception):
            invalid_project.full_clean()


class ProjectLabelModelTest(TestCase):
    """Test the ProjectLabel model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            created_by=self.user
        )
        self.label = ProjectLabel.objects.create(
            name='Test Label',
            color='#FF0000',
            project=self.project
        )
    
    def test_label_creation(self):
        """Test label creation with required fields."""
        self.assertEqual(self.label.name, 'Test Label')
        self.assertEqual(self.label.project, self.project)
        self.assertEqual(self.label.color, '#FF0000')
    
    def test_label_str_representation(self):
        """Test the string representation of the label."""
        # The actual implementation includes the project name in parentheses
        expected = f'Test Label ({self.project.name})'
        self.assertEqual(str(self.label), expected)


class ProjectAPITest(APITestCase):
    """Test the Project API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            created_by=self.user,
            status=ProjectStatus.PLANNED,
            priority=ProjectPriority.MEDIUM
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_project(self):
        """Test creating a new project."""
        url = reverse('projects:project-list')
        data = {
            'name': 'New Project',
            'description': 'New Description',
            'status': ProjectStatus.PLANNED,
            'priority': ProjectPriority.HIGH,
            'member_ids': [self.other_user.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(Project.objects.get(name='New Project').created_by, self.user)
        self.assertTrue(self.other_user in Project.objects.get(name='New Project').members.all())
    
    def test_list_projects(self):
        """Test listing all projects."""
        url = reverse('projects:project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Project')
    
    def test_retrieve_project(self):
        """Test retrieving a project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')
    
    def test_update_project(self):
        """Test updating a project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.id})
        data = {'name': 'Updated Project'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project')
    
    def test_delete_project(self):
        """Test deleting a project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)
    
    def test_add_member(self):
        """Test adding a member to a project."""
        url = reverse('projects:project-add-member', kwargs={'pk': self.project.id})
        data = {'user_ids': [self.other_user.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.other_user in self.project.members.all())
    
    def test_remove_member(self):
        """Test removing a member from a project."""
        self.project.members.add(self.other_user)
        url = reverse('projects:project-remove-member', kwargs={'pk': self.project.id})
        data = {'user_ids': [self.other_user.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.other_user in self.project.members.all())


class ProjectPermissionTest(APITestCase):
    """Test project permissions."""
    
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            created_by=self.creator
        )
        self.project.members.add(self.member)
        
        # Create API clients for each user
        self.creator_client = APIClient()
        self.creator_client.force_authenticate(user=self.creator)
        
        self.member_client = APIClient()
        self.member_client.force_authenticate(user=self.member)
        
        self.other_client = APIClient()
        self.other_client.force_authenticate(user=self.other_user)
    
    def test_creator_can_edit_project(self):
        """Test that the creator can edit the project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.id})
        data = {'name': 'Updated by Creator'}
        response = self.creator_client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated by Creator')
    
    def test_member_can_edit_project(self):
        """Test that a member can edit the project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.id})
        data = {'name': 'Updated by Member'}
        response = self.member_client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated by Member')
    
    def test_non_member_cannot_edit_project(self):
        """Test that a non-member cannot edit the project."""
        print("\n=== Starting test_non_member_cannot_edit_project ===")
        print(f"Project ID: {self.project.id}")
        print(f"Project creator: {self.project.created_by}")
        print(f"Project members: {list(self.project.members.all())}")
        print(f"Other user: {self.other_user}")
        
        url = reverse('projects:project-detail', kwargs={'pk': self.project.id})
        print(f"URL: {url}")
        
        data = {'name': 'Should Not Update'}
        print("Sending PATCH request...")
        response = self.other_client.patch(url, data, format='json')
        
        print(f"Response status code: {response.status_code}")
        print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("=== test_non_member_cannot_edit_project completed ===\n")
    
    def test_anyone_can_view_project(self):
        """Test that any authenticated user can view the project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.id})
        response = self.other_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')


class ProjectValidationTest(APITestCase):
    """Test project validation rules."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_end_date_before_start_date_validation(self):
        """Test that end date cannot be before start date."""
        url = reverse('projects:project-list')
        data = {
            'name': 'Invalid Date Project',
            'description': 'Test invalid dates',
            'start_date': '2023-01-01',
            'end_date': '2022-12-31',  # Before start date
            'status': ProjectStatus.PLANNED,
            'priority': ProjectPriority.MEDIUM,
            'member_ids': []  # Include required field
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data)
        self.assertIn('End date must be after start date', str(response.data['end_date']))
