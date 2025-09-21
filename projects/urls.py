from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'projects'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    
    # Nested routes for project labels
    path('', include([
        path(
            'projects/<uuid:project_pk>/labels/', 
            views.ProjectLabelViewSet.as_view({
                'get': 'list',
                'post': 'create'
            }), 
            name='project-labels-list'
        ),
        path(
            'projects/<uuid:project_pk>/labels/<uuid:pk>/', 
            views.ProjectLabelViewSet.as_view({
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            }), 
            name='project-labels-detail'
        ),
    ])),
]
