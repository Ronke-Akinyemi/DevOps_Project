from django.contrib import admin
from authentication.models import User, EmailVerification, ForgetPasswordToken, Marketter
# Register your models here.

class CustomUser(admin.ModelAdmin):
  
    list_display = ('id','firstname', 'lastname', 'email', 'role')
    search_fields =  ('id','firstname', 'lastname', 'email', 'role')


admin.site.register(User, CustomUser)
admin.site.register(EmailVerification)
admin.site.register(ForgetPasswordToken)
admin.site.register(Marketter)