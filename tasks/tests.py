from datetime import timedelta
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.exceptions import ValidationError

from projects.models import Project
from .models import Task, TaskStatus, TaskPriority
from .serializers import TaskSerializer
from .permissions import IsTaskProjectMemberOrCreator

# Get the User model
User = get_user_model()


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            created_by=self.user
        )
        self.project.members.add(self.user)
        
    def test_create_task(self):
        """Test creating a task with valid data"""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            project=self.project,
            created_by=self.user,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=timezone.now().date() + timedelta(days=7)
        )
        self.assertEqual(str(task), f"{task.title} ({task.get_status_display()})")
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.priority, TaskPriority.MEDIUM)
        self.assertFalse(task.is_overdue)
        
    def test_task_completion_percentage(self):
        """Test task completion percentage calculation"""
        # Create a task with no subtasks
        task = Task.objects.create(
            title='Parent Task',
            project=self.project,
            created_by=self.user,
            status=TaskStatus.IN_PROGRESS,
            completion_percentage=0
        )
        
        # Initially, completion should be 0
        self.assertEqual(task.completion_percentage, 0)
        
        # Create some subtasks
        subtask1 = Task.objects.create(
            title='Subtask 1',
            project=self.project,
            created_by=self.user,
            parent_task=task,
            status=TaskStatus.COMPLETED,
            completion_percentage=100
        )
        
        subtask2 = Task.objects.create(
            title='Subtask 2',
            project=self.project,
            created_by=self.user,
            parent_task=task,
            status=TaskStatus.IN_PROGRESS,
            completion_percentage=50
        )
        
        # Refresh the task to get updated subtasks
        task.refresh_from_db()
        
        # Calculate expected average (100 + 50) / 2 = 75
        expected_percentage = 75
        self.assertEqual(task.calculate_completion_percentage(), expected_percentage)
        
        # Test with no subtasks
        task_without_subtasks = Task.objects.create(
            title='Task Without Subtasks',
            project=self.project,
            created_by=self.user,
            status=TaskStatus.IN_PROGRESS,
            completion_percentage=30
        )
        self.assertEqual(task_without_subtasks.calculate_completion_percentage(), 30)



class TaskSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            created_by=self.user
        )
        self.project.members.add(self.user)
        
    def test_serializer_valid_data(self):
        """Test serializer with valid data"""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = self.user
        
        # Ensure the project exists and the user is a member
        self.project.members.add(self.user)
        
        data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'project': str(self.project.id),  # Ensure project ID is a string for UUID
            'status': TaskStatus.TODO,
            'priority': TaskPriority.MEDIUM,
            'start_date': timezone.now().date(),
            'due_date': (timezone.now() + timedelta(days=7)).date(),
            'assigned_to_ids': [str(self.user.id)]  # Ensure user ID is a string for UUID
        }
        
        # Create the task first to ensure project exists
        task = Task.objects.create(
            title='Test Task',
            project=self.project,
            created_by=self.user,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            start_date=timezone.now().date(),
            due_date=(timezone.now() + timedelta(days=7)).date()
        )
        task.assigned_to.add(self.user)
        
        # Now test the serializer
        serializer = TaskSerializer(instance=task, context={'request': request})
        serialized_data = serializer.data
        
        # Test that the serialized data contains our fields
        self.assertEqual(serialized_data['title'], 'Test Task')
        self.assertEqual(serialized_data['status'], TaskStatus.TODO)
        self.assertEqual(serialized_data['priority'], TaskPriority.MEDIUM)



class TaskPermissionsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            created_by=self.user
        )
        self.project.members.add(self.user)
        self.task = Task.objects.create(
            title='Test Task',
            project=self.project,
            created_by=self.user
        )
        self.permission = IsTaskProjectMemberOrCreator()
        
    def test_project_member_can_create_task(self):
        """Test that project members can create tasks"""
        request = self.factory.post('/tasks/', {
            'title': 'New Task',
            'project': self.project.id
        })
        request.user = self.user
        view = type('View', (), {'action': 'create'})
        self.assertTrue(self.permission.has_permission(request, view))

    def test_non_member_cannot_create_task(self):
        """Test that non-members cannot create tasks"""
        request = self.factory.post('/tasks/', {
            'title': 'New Task',
            'project': self.project.id
        })
        request.user = self.other_user
        view = type('View', (), {'action': 'create'})
        self.assertFalse(self.permission.has_permission(request, view))

    def test_creator_can_update_task(self):
        """Test that task creator can update the task"""
        request = self.factory.patch(f'/tasks/{self.task.id}/', {'title': 'Updated Title'})
        request.user = self.user
        view = type('View', (), {'action': 'partial_update'})
        self.assertTrue(self.permission.has_object_permission(request, view, self.task))

    def test_non_member_cannot_update_task(self):
        """Test that non-members cannot update tasks"""
        request = self.factory.patch(f'/tasks/{self.task.id}/', {'title': 'Updated Title'})
        request.user = self.other_user
        view = type('View', (), {'action': 'partial_update'})
        self.assertFalse(self.permission.has_object_permission(request, view, self.task))


class TaskAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            created_by=self.user
        )
        self.project.members.add(self.user)
        self.task = Task.objects.create(
            title='Test Task',
            project=self.project,
            created_by=self.user,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_create_task_authenticated(self):
        """Test creating a task as an authenticated user"""
        url = reverse('tasks:task-list')
        
        # Create a valid task data dictionary
        task_data = {
            'title': 'New Task',
            'description': 'New Task Description',
            'project': str(self.project.id),  # Convert UUID to string
            'status': TaskStatus.TODO,
            'priority': TaskPriority.MEDIUM,
            'start_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now() + timedelta(days=7)).date().isoformat(),
            'assigned_to_ids': [str(self.user.id)]  # Use assigned_to_ids as per serializer
        }
        
        # Print the data being sent for debugging
        print("Sending data:", task_data)
        
        # Make the request
        response = self.client.post(url, task_data, format='json')
        
        # Print the response for debugging
        print("Response status:", response.status_code)
        if hasattr(response, 'data'):
            print("Response data:", response.data)
        else:
            print("Response content:", response.content)
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the task was created in the database
        self.assertEqual(Task.objects.count(), 2)
        
        # Get the created task
        task = Task.objects.latest('created_at')
        self.assertEqual(task.title, 'New Task')
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.priority, TaskPriority.MEDIUM)
        self.assertEqual(task.created_by, self.user)
        self.assertEqual(list(task.assigned_to.all()), [self.user])

    def test_create_task_unauthenticated(self):
        """Test that unauthenticated users cannot create tasks"""
        self.client.force_authenticate(user=None)
        url = reverse('tasks:task-list')
        data = {'title': 'New Task', 'project': str(self.project.id)}
        response = self.client.post(url, data, format='json')
        # Expect 401 Unauthorized when authentication is required
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_task_unauthorized(self):
        """Test that non-members cannot update tasks"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('tasks:task-detail', args=[str(self.task.id)])  # Convert UUID to string
        data = {'title': 'Unauthorized Update'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_user_to_task(self):
        """Test assigning a user to a task"""
        self.client.force_authenticate(user=self.user)  # Ensure the user is authenticated
        url = reverse('tasks:task-assign-user', args=[str(self.task.id)])  # Convert UUID to string
        data = {'user_id': str(self.other_user.id)}  # Ensure user_id is a string
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()  # Refresh the task to get updated assigned_to
        self.assertTrue(self.other_user in self.task.assigned_to.all())

    def test_add_dependency_same_project(self):
        """Test adding a dependency within the same project"""
        self.client.force_authenticate(user=self.user)  # Ensure the user is authenticated
        dependent_task = Task.objects.create(
            title='Dependent Task',
            project=self.project,
            created_by=self.user,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM
        )
        url = reverse('tasks:task-add-dependency', args=[str(self.task.id)])  # Convert UUID to string
        data = {'task_id': str(dependent_task.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()  # Refresh the task to get updated dependencies
        self.assertTrue(dependent_task in self.task.dependencies.all())

    def test_add_dependency_different_project(self):
        """Test that dependencies must be in the same project"""
        self.client.force_authenticate(user=self.user)  # Ensure the user is authenticated
        
        # Create another project and task in that project
        other_project = Project.objects.create(
            name='Other Project',
            description='Other Description',
            created_by=self.other_user
        )
        other_project.members.add(self.other_user)
        
        other_task = Task.objects.create(
            title='Other Task',
            project=other_project,
            created_by=self.other_user,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM
        )
        
        # Try to add a dependency from a different project
        url = reverse('tasks:task-add-dependency', args=[str(self.task.id)])  # Convert UUID to string
        data = {'task_id': str(other_task.id)}
        response = self.client.post(url, data, format='json')
        
        # Should return 400 Bad Request with an error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Verify the dependency was not added
        self.task.refresh_from_db()
        self.assertFalse(other_task in self.task.dependencies.all())
