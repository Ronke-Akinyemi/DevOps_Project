from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from django.conf import settings
from drf_yasg import openapi
from rest_framework import permissions
from django.conf.urls.static import static
from decouple import config

schema_view = get_schema_view(
   openapi.Info(
      title=settings.PROJECT_NAME_,
      default_version='v1',
      description= f"This is the backend APIs for {settings.PROJECT_NAME_}",
      contact=openapi.Contact(email="akinolasamson1234@gmail.com"),
      license=openapi.License(name=settings.PROJECT_NAME_),
   ),
   public=True,
   url = config("PROJECT_URL", "http://127.0.0.1:8000/"),
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   #  path('api/v1/admin/', include('administration.urls')),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/business/', include('business.urls')),
    path('api/v1/user/', include('user.urls')),
    path('api/v1/category/', include('category.urls')),
    path('api/v1/customer/', include('customer.urls')),
    path('api/v1/expenses/', include('expenses.urls')),
    path('api/v1/product/', include('product.urls')),
    path('api/v1/sale/', include('sale.urls')),
    path('api/v1/service/', include('service.urls')),
    path('api/v1/analytic/', include('analytic.urls')),
    path('api/v1/notification/', include('notification.urls')),
]
urlpatterns += static(settings.STATIC_URL,
                      document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ENVIROMENT != 'prod':
    urlpatterns += path('popsie/', admin.site.urls),