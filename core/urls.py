"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from home import views as home_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_views.index, name='home'),

   
    path('login/', home_views.login_view, name='login'),
    path('register/', home_views.customer_register_view, name='register'),
    path('logout/', home_views.logout_view, name='logout'),
  
    # Admin management (list and add admins)
    path('admins/', home_views.admin_management, name='admin_management'),
    path('customer/', home_views.customer_dashboard, name='customer_dashboard'),
    
    path('routes/', home_views.route_list_view, name='route_list'),
    path('routes/add/', home_views.add_route_view, name='add_route'),
    path('buses/', home_views.bus_list_view, name='bus_list'),
    path('buses/add/', home_views.add_bus_view, name='add_bus'),

    path('terminal/', home_views.terminal_view, name='terminal'),
    path('lahore-feeder/', home_views.lahore_feeder, name='lahore_feeder'),
    path('multan-metro/', home_views.multan_metro, name='multan_metro'),
    path('workshop/', home_views.workshop, name='workshop'),
    path("in-journey-attractions/", home_views.in_journey_attractions, name="in_journey_attractions"),
    path("in_journey_attractions/", home_views.in_journey_attractions),
    path("safety_security/", home_views.safety_security, name="safety_security"),
    path("trained_crew/", home_views.trained_crew, name= "trained_crew"),
    path("terms_conditions/", home_views.terms_conditions, name="terms_conditions"),
    path("news/", home_views.news, name="news"),
    path("about/", home_views.about_us, name="about_us"),
    path("blog/", home_views.blog, name= "blog"),
    path("health_policy/", home_views.health_policy, name= "health_policy"),
    path("gender_policy/", home_views.gender_policy, name= "gender_policy"),

    path("complaints/", home_views.complaint_suggestion_view, name="complaint_suggestion"),
    path("complaints/success/", 
         lambda request: render(request, "home/complaint_success.html"), 
         name="complaint_success"),

    path("admin/complaints/", home_views.complaint_list_view, name="complaint_list"),
    path("booking/", home_views.booking_view, name="booking"),
    path("booking/confirm/<int:bus_id>/", home_views.confirm_booking, name="confirm_booking"),
    # urls.py
    # urls.py
    path('refund/<int:booking_id>/', home_views.refund_home, name='online_refund'),

    path('tickets/upcoming/', home_views.upcoming_tickets_view, name='upcoming_tickets'),
    path('tickets/past/', home_views.past_tickets_view, name='past_tickets'),

    path("tickets/cancel/<int:ticket_id>/", home_views.cancel_ticket_view, name="cancel_ticket"),
    
    path('booking/success/<int:booking_id>/', home_views.booking_success_view, name='booking_success'),
    path('ticket/<int:ticket_id>/', home_views.ticket_detail_view, name='ticket_detail'),
    path("admin_dashboard/", home_views.admin_management, name="admin_dashboard"),
    path("add_customer/", home_views.add_customer, name="add_customer"),


    path("admin_management/", home_views.admin_management, name="admin_management"),
    path("add_customer/", home_views.add_customer, name="add_customer"),
    path("edit_customer/<int:customer_id>/", home_views.edit_customer, name="edit_customer"),
    path("delete_customer/<int:customer_id>/", home_views.delete_customer, name="delete_customer"),

    path("bookings/add/", home_views.add_booking, name="add_booking"),
    path("bookings/edit/<int:booking_id>/", home_views.edit_booking, name="edit_booking"),
    path("bookings/delete/<int:booking_id>/", home_views.delete_booking, name="delete_booking"),
    path('bookings/add/', home_views.add_booking, name='admin_booking'),
    path('admin/booking-success/<int:booking_id>/', home_views.booking_success_admin_view, name='booking_success_admin'),
    path("edit-profile/", home_views.edit_profile, name="edit_profile"),
    path("update-admin-profile/", home_views.update_admin_profile, name="update_admin_profile"),
    path("payments/", home_views.payment_list, name="payment_list"),
    path("payments/<int:booking_id>/", home_views.payment_view, name="payment"),
    path("payment/<int:booking_id>/", home_views.payment_view, name="add_payment"),
    path("create-payment/<int:booking_id>/", home_views.create_payment_view, name="create_payment"),


]


# Admin booking steps
