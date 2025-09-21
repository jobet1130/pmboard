from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Define the app name for URL namespacing
app_name = 'tasks'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include the default router URLs
    path('', include(router.urls)),
    
    # Additional endpoints for task actions
    path('tasks/<uuid:pk>/assign_user/', 
         views.TaskViewSet.as_view({'post': 'assign_user'}), 
         name='task-assign-user'),
    path('tasks/<uuid:pk>/unassign_user/', 
         views.TaskViewSet.as_view({'post': 'unassign_user'}), 
         name='task-unassign-user'),
    path('tasks/<uuid:pk>/change_status/', 
         views.TaskViewSet.as_view({'post': 'change_status'}), 
         name='task-change-status'),
    path('tasks/<uuid:pk>/add_dependency/', 
         views.TaskViewSet.as_view({'post': 'add_dependency'}), 
         name='task-add-dependency'),
    path('tasks/<uuid:pk>/remove_dependency/', 
         views.TaskViewSet.as_view({'post': 'remove_dependency'}), 
         name='task-remove-dependency'),
    
    # User tasks overview endpoint
    path('tasks/overview/', 
         views.user_tasks_overview, 
         name='user-tasks-overview'),
]
