from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from analyzer.views import index
from django.contrib.auth import views as auth_views
from analyzer import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('track/<int:track_id>/', views.index, name='index_with_track'),
    path('delete/<int:track_id>/', views.delete_track, name='delete_track'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

# This allows the <audio> tag to actually load the file from /media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
