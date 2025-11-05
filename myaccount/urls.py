from django.urls import path
from . import views

from django.contrib.auth import views as auth_views


urlpatterns = [

    path('register/', views.register, name='register'),
    # My login / logout urls
    path('my-login/', views.my_login, name='my-login'),
    path('user-logout/', views.user_logout, name='user-logout'),

    path('google/login/', views.google_login, name='google-login'),
    path('google/callback/', views.google_callback, name='google-callback'),
   

    # Email verification URL's
    path('email-verification/<str:uidb64>/<str:token>/', views.email_verification, name='email-verification'),
    path('email-verification-sent/', views.email_verification_sent, name='email-verification-sent'),
    path('email-verification-success/', views.email_verification_success, name='email-verification-success'),
    path('email-verification-failed/', views.email_verification_failed, name='email-verification-failed'),

    # Dashboard / profile urls
    path('dashboard/', views.dashboard, name='dashboard'),
    # Track orders url
    path('track-orders/' , views.track_orders, name='track-orders'),
    # Manage shipping url
    path('manage-shipping/' , views.manage_shipping, name='manage-shipping'),

    path('profile-management/', views.profile_management, name='profile-management'),
    path('profile-update/', views.profile_update, name='profile-update'),
    path('delete-account/', views.delete_account, name='delete-account'),



    # Password management urls / Class-Based View in Django
    # reset
    # 1 )   Submit our email form
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name= 'account/password/password-reset.html'), name='reset_password' ),
    # 2 )   Success message  stating that apassword reset email was sent
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name= 'account/password/password-reset-sent.html'), name= 'password_reset_done'),
    # 3 )   Password reset link
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name= 'account/password/password-reset-form.html'), name= 'password_reset_confirm'),
    # 4 )   Success message stating that our password was reset
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name= 'account/password/password-reset-complete.html'), name= 'password_reset_complete'),

    #change
    path('change_password/', auth_views.PasswordChangeView.as_view(template_name='account/password/password-change.html',success_url='/account/change_password_done/'), name='password_change'),
    
    path('change_password_done/', auth_views.PasswordChangeDoneView.as_view(template_name='account/password/password-change-done.html'), name='password_change_done'),
]