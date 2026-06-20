from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "CashTrail Admin"
admin.site.site_title  = "CashTrail"
admin.site.index_title = "Administration Panel"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('expenses/', include('expenses.urls')),
    path('analytics/', include('analytics.urls')),
    path('admin-panel/', include('adminpanel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
