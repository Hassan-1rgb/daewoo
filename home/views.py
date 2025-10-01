from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.db.models import Sum
from .models import User, Route, Bus, ComplaintSuggestion, Booking, RefundRequest
from .forms import CustomerRegisterForm, UserLoginForm, AdminForm, RouteForm, BusForm, ComplaintSuggestionForm, BookingForm
from django.contrib import admin
from django.utils import timezone
from decimal import Decimal


 
# ----------------------------
# Home / Index Page
# ----------------------------
def index(request):
    return render(request, "home/index.html") 

def terminal_view(request):
    return render(request, 'home/terminal.html')

def lahore_feeder(request):
    return render(request, 'home/lahore_feeder.html')

def multan_metro(request):
    return render(request, 'home/multan_metro.html')

def workshop(request):
    return render(request, 'home/workshop.html')

def in_journey_attractions(request):
    return render(request, "home/in_journey_attractions.html")

def safety_security(request):
    return render(request, "home/safety_security.html")

def trained_crew(request):
    return render(request, "home/trained_crew.html")

def terms_conditions(request):
    return render(request, "home/terms_conditions.html")

def news(request):
    return render(request, "home/news.html")

def about_us(request):
    return render(request, "home/about_us.html")

def blog(request):
    return render(request, "home/blog.html")

def health_policy(request):
    return render(request, "home/health_policy.html")

def gender_policy(request):
    return render(request, "home/gender_policy.html")

# ----------------------------
# Customer Registration
# ----------------------------
def customer_register_view(request):
    if request.method == "POST":
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "customer"
            user.save()
            return redirect("login")
    else:
        form = CustomerRegisterForm()
    return render(request, "home/register.html", {"form": form})


# ----------------------------
# Login View (Role-based)
# ----------------------------
def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            try:
                user = User.objects.get(email=email, password=password)

                # ✅ Save user details in session
                request.session["user_id"] = user.id
                request.session["role"] = user.role.lower().strip()  # normalize role
                request.session["user_name"] = getattr(user, "name", "")
                request.session["user_phone"] = getattr(user, "phone", "")
                request.session["user_email"] = user.email
                request.session["user_address"] = getattr(user, "address", "")
                request.session["user_cnic"] = getattr(user, "cnic_passport", "")

                # ✅ Force save session
                request.session.modified = True

                # ✅ Redirect based on role
                if request.session["role"] == "admin":
                    return redirect("admin_management")
                else:
                    return redirect("customer_dashboard")

            except User.DoesNotExist:
                form.add_error(None, "Invalid email or password")
    else:
        form = UserLoginForm()

    return render(request, "home/login.html", {"form": form})



def edit_profile(request):
    if request.method == "POST" and "user_id" in request.session:
        try:
            user = User.objects.get(id=request.session["user_id"])
            user.name = request.POST.get("name")
            user.phone = request.POST.get("phone")
            user.email = request.POST.get("email")
            user.cnic_passport = request.POST.get("cnic_passport")
            user.address = request.POST.get("address")
            user.save()

            # update session so modal shows fresh values
            request.session["user_name"] = user.name
            request.session["user_phone"] = user.phone
            request.session["user_email"] = user.email
            request.session["user_cnic"] = user.cnic_passport
            request.session["user_address"] = user.address

            messages.success(request, "Profile updated successfully!")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
        return redirect("customer_dashboard")
    else:
        return redirect("login")


def complaint_suggestion_view(request):
    # ✅ Ensure only logged-in users can submit complaints/suggestions
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please login first to submit a complaint or suggestion.")
        return redirect("login")

    if request.method == "POST":
        form = ComplaintSuggestionForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user_id = user_id  # assign logged-in user
            complaint.save()
            messages.success(request, "Thank you! Your complaint/suggestion has been submitted.")
            return redirect("customer_dashboard")  # redirect to dashboard after submit
    else:
        form = ComplaintSuggestionForm()

    return render(request, "home/complaint_suggestion.html", {"form": form})



def complaint_list_view(request):
    # Only admins can view
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or role != "admin":
        return redirect("login")

    complaints = ComplaintSuggestion.objects.all().order_by("-created_at")
    return render(request, "home/complaint_list.html", {"complaints": complaints})





def admin_management(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    # ✅ Only allow admins
    if not user_id or role != "admin":
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("login")

    # ✅ Handle Add Admin form
    form = AdminForm()
    active_section = "dashboard"

    if request.method == "POST":
        form = AdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Admin added successfully!")
            active_section = "add-admin"
            form = AdminForm()
        else:
            messages.error(request, "Please correct the errors in the form.")
            active_section = "add-admin"

    # ✅ Fetch data with proper error handling
    try:
        customers = User.objects.filter(role="customer").order_by("-created_at")
        routes = Route.objects.all().order_by("id")
        buses = Bus.objects.select_related("route").all().order_by("id")
        complaints = ComplaintSuggestion.objects.select_related("user").all().order_by("-created_at")
        bookings = Booking.objects.select_related("user", "bus", "route").all().order_by("-created_at")
        refunds = RefundRequest.objects.select_related(
            "user", "booking", "booking__bus", "booking__route"
        ).all().order_by("-submitted_at")

        # ✅ Attach latest payment to each booking
        for booking in bookings:
            booking.payment = Payment.objects.filter(
                booking=booking
            ).order_by("-created_at").first()

        # ✅ Enhanced Debug information
        print("=== ADMIN MANAGEMENT DEBUG ===")
        print(f"Total Users in DB: {User.objects.count()}")
        print(f"Total Routes in DB: {Route.objects.count()}")

        if Route.objects.exists():
            first_route = Route.objects.first()
            print(f"First route: {first_route}")
            print(f"Route fields: {[field.name for field in Route._meta.fields]}")
            print(f"Route values: {first_route.__dict__}")
        else:
            print("No routes exist in database")

        print(f"Route model: {Route}")
        print(f"Routes queryset: {routes}")
        print(f"Routes count: {routes.count()}")

        for route in routes:
            print(f"Route {route.id}: {route}")

    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        import traceback
        traceback.print_exc()

        # Initialize empty querysets on error
        customers = User.objects.none()
        routes = Route.objects.none()
        buses = Bus.objects.none()
        complaints = ComplaintSuggestion.objects.none()
        bookings = Booking.objects.none()
        refunds = RefundRequest.objects.none()

        messages.error(request, f"Error loading data: {str(e)}")

    # ✅ Prepare context
    context = {
        "form": form,
        "customers": customers,
        "routes": routes,
        "buses": buses,
        "complaints": complaints,
        "bookings": bookings,
        "refunds": refunds,
        "active_section": active_section,
        "customers_count": customers.count(),
        "routes_count": routes.count(),
        "buses_count": buses.count(),
        "complaints_count": complaints.count(),
        "bookings_count": bookings.count(),
        "refunds_count": refunds.count(),
    }

    return render(request, "home/admin.html", context)




def update_admin_profile(request):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("login")  # if session expired

        user = get_object_or_404(User, id=user_id)

        # update fields
        user.name = request.POST.get("name", user.name)
        user.email = request.POST.get("email", user.email)
        user.phone = request.POST.get("phone", user.phone)
        user.address = request.POST.get("address", user.address)
        user.cnic_passport = request.POST.get("cnic", user.cnic_passport)
        user.save()

        # update session values
        request.session["user_name"] = user.name
        request.session["user_email"] = user.email
        request.session["user_phone"] = user.phone
        request.session["user_address"] = user.address
        request.session["user_cnic"] = user.cnic_passport

        return redirect("admin_management")  # or wherever you want after save

    return redirect("admin_management")



def add_customer(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or role != "admin":
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("login")

    if request.method == "POST":
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            password = form.cleaned_data.get("password")
            confirm_password = form.cleaned_data.get("confirm_password")

            if password != confirm_password:
                messages.error(request, "Passwords do not match ❌")
                return render(request, "home/add_customer.html", {"form": form})

            customer.password = password
            customer.role = "customer"
            customer.created_at = timezone.now()
            customer.updated_at = timezone.now()
            customer.created_by_id = user_id
            customer.updated_by_id = user_id
            customer.save()

            messages.success(request, "Customer added successfully ✅")
            return redirect("/booking?hide_navbar=1")
        else:
            messages.error(request, "Please fix the errors below ❌")
    else:
        form = CustomerRegisterForm()

    return render(request, "home/add_admin_customer.html", {"form": form})





def edit_customer(request, customer_id):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or role != "admin":
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("login")

    customer = get_object_or_404(User, id=customer_id, role="customer")

    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.email = request.POST.get("email")
        customer.phone = request.POST.get("phone")
        customer.cnic_passport = request.POST.get("cnic_passport")
        customer.dob = request.POST.get("dob")
        customer.city = request.POST.get("city")
        customer.address = request.POST.get("address")

        password = request.POST.get("password")
        if password:
            customer.password = password

        customer.updated_by_id = user_id
        customer.updated_at = timezone.now()
        customer.save()

        messages.success(request, f"✅ Customer '{customer.name}' updated successfully")
        return redirect("admin_management")

    return render(request, "home/edit_customer.html", {"customer": customer})


def delete_customer(request, customer_id):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or role != "admin":
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("login")

    customer = get_object_or_404(User, id=customer_id, role="customer")

    if request.method == "POST":
        customer.delete()
        messages.success(request, "❌ Customer deleted successfully")
        return redirect("admin_management")

    return render(request, "home/delete_customer_confirm.html", {"customer": customer})


# ------------------- BOOKING VIEWS -------------------

def add_booking(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or role != "admin":
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("login")

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.created_by_id = user_id
            booking.updated_by_id = user_id
            booking.created_at = timezone.now()
            booking.updated_at = timezone.now()
            booking.save()
            messages.success(request, "Booking added successfully ✅")
            return redirect("admin_management")
        else:
            messages.error(request, "Please fix the errors below ❌")
    else:
        form = BookingForm()

    return render(request, "home/admin_booking.html", {"form": form})



def booking_success_admin_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    seat_count = len(booking.seat_number.split(','))
    total_price = seat_count * booking.bus.price

    return render(request, "home/booking_success_admin.html", {
        "booking": booking,
        "total_price": total_price,
    })


def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    users = User.objects.filter(role='customer')
    routes = Route.objects.all()
    buses = Bus.objects.all()

    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or role != "admin":
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("login")

    if request.method == "POST":
        booking.user_id = request.POST.get("user")
        booking.route_id = request.POST.get("route")
        booking.bus_id = request.POST.get("bus")
        booking.booking_date = request.POST.get("booking_date")
        booking.seat_number = request.POST.get("seat_number")
        booking.updated_by_id = user_id
        booking.updated_at = timezone.now()
        booking.save()

        messages.success(request, "Booking updated successfully ✅")
        return redirect("admin_management")

    return render(request, "home/edit_booking.html", {
        "booking": booking,
        "users": users,
        "routes": routes,
        "buses": buses,
    })


def delete_booking(request, booking_id):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or role != "admin":
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("login")

    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        booking_number = booking.booking_number
        booking.delete()
        messages.success(request, f"Booking {booking_number} deleted successfully ❌")
        return redirect("admin_management")

    return render(request, "home/delete_booking_confirm.html", {"booking": booking})


# home/views.py


def create_payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Calculate total price
    seat_count = len(booking.seat_number.split(",")) if booking.seat_number else 1
    total_price = Decimal(seat_count) * booking.bus.price

    if request.method == "POST":
        method = request.POST.get("method", "cash")
        payment = Payment(
            booking=booking,
            user=booking.user,
            amount=total_price,
            method=method,
            status="completed",
            created_by=booking.user,  # or admin if needed
            paid_at=timezone.now(),
        )

        # Card details
        if method == "card":
            card_number = request.POST.get("card_number")
            expiry_date = request.POST.get("expiry_date")
            if card_number:
                payment.card_last4 = card_number[-4:]
            if expiry_date:
                payment.card_expiry = expiry_date

        # Bank transfer
        elif method == "bank_transfer":
            payment.account_number = request.POST.get("account_number")
            payment.bank_name = request.POST.get("bank_name")
            payment.transaction_ref = request.POST.get("transaction_ref")

        payment.save()

        # Update booking
        booking.status = "confirmed"
        booking.reserved_until = None
        booking.save()

        # Send email
        try:
            yag = yagmail.SMTP("your-email@gmail.com", "your-email-password")
            yag.send(
                to=booking.user.email,
                subject="Booking Confirmation ✅",
                contents=f"""
<html>
  <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {booking.user.name},</p>
    <p>Your booking has been <strong>confirmed</strong> & payment received! 🎉</p>
    <p>
      <b>Booking No:</b> {booking.booking_number}<br>
      <b>Seats:</b> {booking.seat_number}<br>
      <b>Date:</b> {booking.booking_date}<br>
      <b>Total:</b> Rs {total_price}
    </p>
    <p>Thank you for choosing us!</p>
  </body>
</html>
"""
            )
        except Exception as e:
            messages.warning(request, f"Booking confirmed but email could not be sent: {e}")

        messages.success(request, "✅ Payment created and booking confirmed.")
        return redirect("admin_management")

    return render(request, "home/create_payment.html", {
        "booking": booking,
        "seat_count": seat_count,
        "total_price": total_price,
    })





# Logout
# ----------------------------
def logout_view(request):
    request.session.flush()
    return redirect("home")





# views.py - Update customer_dashboard function
def customer_dashboard(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or role != "customer":
        messages.warning(request, "You must login first to access the dashboard.")
        return redirect("login")

    customer = User.objects.get(id=user_id)
    latest_booking = Booking.objects.filter(user=customer).order_by('-id').first()
    
    # Calculate booking statistics
    total_bookings = Booking.objects.filter(user=customer).count()
    upcoming_bookings = Booking.objects.filter(
        user=customer, 
        booking_date__gte=timezone.now().date()
    ).count()
    completed_bookings = total_bookings - upcoming_bookings
    
    # Get favorite routes
    from django.db.models import Count
    favorite_routes = Booking.objects.filter(user=customer).values(
        'bus__route__origin', 'bus__route__destination'
    ).annotate(count=Count('id')).order_by('-count')[:3]
    
    # Get preferred bus types
    preferred_bus_types = Booking.objects.filter(user=customer).values(
        'bus__bus_type'
    ).annotate(count=Count('id')).order_by('-count')[:3]

    return render(request, "home/customer.html", {
        "customer": customer,
        "latest_booking": latest_booking,
        "total_bookings": total_bookings,
        "upcoming_bookings": upcoming_bookings,
        "completed_bookings": completed_bookings,
        "favorite_routes": favorite_routes,
        "preferred_bus_types": preferred_bus_types
    })





def refund_home(request, booking_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "You must login first to submit a refund request.")
        return redirect('login')

    # Get the actual user instance
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Invalid user. Please login again.")
        return redirect('login')

    # Get the booking instance for this user
    booking = get_object_or_404(Booking, id=booking_id, user=user)

    if request.method == "POST":
        refund_as = request.POST.get("refund_as")
        additional_notes = request.POST.get("additional_notes")

        # Create RefundRequest with proper User and Booking instances
        RefundRequest.objects.create(
            user=user,        # must be User instance
            booking=booking,  # must be Booking instance
            refund_as=refund_as,
            additional_notes=additional_notes
        )
        messages.success(request, "Refund request submitted successfully.")
        return redirect('online_refund', booking_id=booking.id)

    return render(request, "home/online_refund.html", {
        "user": user,
        "booking": booking
    })






from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
import uuid
import json


import json
import pytz
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from .models import Route, Bus, Booking, User
import yagmail  # for sending emails

# -----------------------------
# Booking Search Page
# -----------------------------
def booking_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please login first to access booking.")
        return redirect("login")

    hide_navbar = request.GET.get("hide_navbar", "0") == "1"    
    from_admin = request.GET.get("from_admin", "0") == "1"

    origins = Route.objects.values_list("origin", flat=True).distinct()
    destinations = Route.objects.values_list("destination", flat=True).distinct()

    buses = None
    booking_date = request.GET.get("booking_date")

    # ✅ Default to today if no date is selected
    pakistan_tz = pytz.timezone('Asia/Karachi')
    current_datetime = datetime.now(pakistan_tz)
    current_date = current_datetime.date()

    if not booking_date:
        booking_date = current_date.strftime("%Y-%m-%d")

    booked_seats = {}

    if request.GET.get("origin") and request.GET.get("destination") and booking_date:
        origin = request.GET["origin"]
        destination = request.GET["destination"]
        routes = Route.objects.filter(origin=origin, destination=destination)
        all_buses = Bus.objects.filter(route__in=routes).order_by('departure_time')

        current_time = current_datetime.time()
        booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()

        filtered_buses = []

        if booking_date_obj == current_date:
            buses_to_process = [bus for bus in all_buses if bus.departure_time > current_time]
        elif booking_date_obj > current_date:
            buses_to_process = list(all_buses)
        else:
            buses_to_process = []

        for bus in buses_to_process:
            bookings = Booking.objects.filter(bus=bus, booking_date=booking_date).select_related('user')
            booked_seats[bus.id] = {}
            total_booked_count = 0
            for booking_item in bookings:
                seats = booking_item.seat_number.split(',')
                for seat in seats:
                    seat = seat.strip()
                    booked_seats[bus.id][seat] = {'user_name': booking_item.user.name}
                    total_booked_count += 1
            bus.available_seats_count = bus.capacity - total_booked_count
            filtered_buses.append(bus)

        buses = filtered_buses
    else:
        buses = []

    rows = range(1, 13)

    return render(request, "home/booking.html", {
        "origins": origins,
        "destinations": destinations,
        "buses": buses,
        "booking_date": booking_date,  # ✅ always has today’s date if none given
        "rows": rows,
        "booked_seats": json.dumps(booked_seats),
        "current_time_pk": current_datetime.strftime("%I:%M %p"),
        "current_date": current_date,
        "booking_date_obj": datetime.strptime(booking_date, '%Y-%m-%d').date() if booking_date else None,
        "hide_navbar": hide_navbar,
        "from_admin": from_admin,
    })


# -----------------------------
# Confirm Booking (POST)
# -----------------------------

from .models import Bus, Booking, User, Payment  # Make sure Payment model exists


def confirm_booking(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    booking_date = request.GET.get("booking_date") or request.POST.get("booking_date")
    from_admin = request.GET.get("from_admin", "0") == "1"

    if not booking_date:
        messages.error(request, "Please select a journey date first.")
        return redirect("booking")

    pakistan_tz = pytz.timezone('Asia/Karachi')
    current_datetime = datetime.now(pakistan_tz)
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()

    # Prevent booking for past or departed buses
    if booking_date_obj == current_date and bus.departure_time <= current_time:
        messages.error(
            request,
            f"⚠️ This bus has already departed at {bus.departure_time.strftime('%I:%M %p')}."
        )
        url = f"{reverse('booking')}?booking_date={booking_date}&origin={bus.route.origin}&destination={bus.route.destination}"
        return redirect(url)
    elif booking_date_obj < current_date:
        messages.error(request, "⚠️ Cannot book for past dates.")
        return redirect("booking")

    # Check login
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "You must be logged in to book a seat.")
        return redirect("login")

    if request.method == "POST":
        seats = request.POST.get("selected_seats")
        if not seats:
            messages.error(request, "⚠️ Please select at least one seat.")
            return redirect("booking")

        selected_seat_list = [seat.strip() for seat in seats.split(',')]
        existing_bookings = Booking.objects.filter(bus=bus, booking_date=booking_date)

        # Check already booked seats
        already_booked_seats = []
        for booking_item in existing_bookings:
            booked_seats = [seat.strip() for seat in booking_item.seat_number.split(',')]
            for seat in selected_seat_list:
                if seat in booked_seats:
                    already_booked_seats.append(seat)

        if already_booked_seats:
            messages.error(
                request,
                f"⚠️ The following seats are already booked: {', '.join(already_booked_seats)}."
            )
            url = f"{reverse('booking')}?booking_date={booking_date}&origin={bus.route.origin}&destination={bus.route.destination}"
            return redirect(url)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found. Please login again.")
            return redirect("login")

        # Create the booking with status 'reserved'
        booking = Booking.objects.create(
            user=user,
            route=bus.route,
            bus=bus,
            booking_date=booking_date,
            seat_number=seats,
            status='reserved',  # Set status to reserved
            created_by=user,
            updated_by=user,
        )

        # Calculate price
        seat_count = len(selected_seat_list)
        total_price = seat_count * bus.price

        # Instead of sending email & going to success directly → go to payment
        request.session['pending_booking_id'] = booking.id  # store booking in session
        return redirect('payment', booking_id=booking.id)

    return render(request, "home/confirm_booking.html", {
        "bus": bus,
        "booking_date": booking_date,
        "from_admin": from_admin,
    })


from decimal import Decimal
from datetime import timedelta
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone
import yagmail



from decimal import Decimal
from datetime import timedelta
import pytz
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
import yagmail
from .models import Booking, Payment

def payment_view(request, booking_id):
    booking = get_object_or_404(
        Booking, id=booking_id, user_id=request.session.get("user_id")
    )

    # calculate seat count & total
    seat_count = len(booking.seat_number.split(",")) if booking.seat_number else 1
    total_price = Decimal(seat_count) * booking.bus.price

    # Pakistan timezone
    local_tz = pytz.timezone("Asia/Karachi")

    if request.method == "POST":
        action_type = request.POST.get("action_type")

        # -----------------
        # RESERVATION
        # -----------------
        if action_type == "reserve":
            booking.status = "reserved"
            booking.reserved_until = timezone.now() + timedelta(minutes=30)
            booking.save()

            # Convert reserved_until to Pakistan timezone
            reserved_local = booking.reserved_until.astimezone(local_tz)

            try:
                yag = yagmail.SMTP("hassanali.jutt576@gmail.com", "qgok oilz xyzy lhhq")
                yag.send(
                    to=booking.user.email,
                    subject="Seat Reserved ✅",
                    contents=f"""
<html>
  <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {booking.user.name},</p>
    <p>Your seat has been <strong>reserved</strong> for 30 minutes! ⏰</p>
    <p>
      <b>Booking No:</b> {booking.booking_number}<br>
      <b>Seats:</b> {booking.seat_number}<br>
      <b>Date:</b> {booking.booking_date}<br>
      <b>Departure:</b> {booking.bus.departure_time.strftime('%I:%M %p')}<br>
      <b>Reserved Until:</b> {reserved_local.strftime('%Y-%m-%d %I:%M %p')}<br>
      <b>Total:</b> Rs {total_price}
    </p>
    <p>Please complete the payment within 30 minutes to confirm your booking.</p>
  </body>
</html>
"""
                )
            except Exception as e:
                messages.warning(
                    request, f"Seat reserved but email could not be sent: {e}"
                )

            messages.success(
                request,
                "✅ Your seat has been reserved for 30 minutes. Please complete the payment to confirm.",
            )
            return redirect("booking_success", booking_id=booking.id)

        # -----------------
        # PAYMENT
        # -----------------
        elif action_type == "pay":
            method = request.POST.get("method", "cash")
            payment = Payment(
                booking=booking,
                user=booking.user,
                amount=total_price,
                method=method,
                status="completed",
                created_by=booking.user,
                paid_at=timezone.now(),
            )

            # Card payment
            if method == "card":
                card_number = request.POST.get("card_number")
                expiry_date = request.POST.get("expiry_date")
                if card_number:
                    payment.card_last4 = card_number[-4:]
                if expiry_date:
                    payment.card_expiry = expiry_date

            # Bank transfer
            elif method == "bank_transfer":
                payment.account_number = request.POST.get("account_number")
                payment.bank_name = request.POST.get("bank_name")
                payment.transaction_ref = request.POST.get("transaction_ref")

            payment.save()

            # Mark booking as confirmed
            booking.status = "confirmed"
            booking.reserved_until = None  # clear reservation
            booking.save()

            # Send confirmation email
            try:
                yag = yagmail.SMTP("hassanali.jutt576@gmail.com", "qgok oilz xyzy lhhq")
                yag.send(
                    to=booking.user.email,
                    subject="Booking Confirmation ✅",
                    contents=f"""
<html>
  <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {booking.user.name},</p>
    <p>Your booking has been <strong>confirmed</strong> & payment received! 🎉</p>
    <p>
      <b>Booking No:</b> {booking.booking_number}<br>
      <b>Seats:</b> {booking.seat_number}<br>
      <b>Date:</b> {booking.booking_date}<br>
      <b>Departure:</b> {booking.bus.departure_time.strftime('%I:%M %p')}<br>
      <b>Total:</b> Rs {total_price}
    </p>
    <p>Thank you for choosing us!</p>
  </body>
</html>
"""
                )
            except Exception as e:
                messages.warning(
                    request, f"Booking confirmed but email could not be sent: {e}"
                )

            messages.success(request, "✅ Payment successful and booking confirmed.")
            return redirect("booking_success", booking_id=booking.id)

    return render(
        request,
        "home/add_payment.html",
        {
            "booking": booking,
            "seat_count": seat_count,
            "total_price": total_price,
        },
    )


def booking_success_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user_id=request.session.get("user_id"))
    
    # Calculate total price
    seat_count = len(booking.seat_number.split(','))
    total_price = seat_count * booking.bus.price
    
    # Get payment status
    payment = Payment.objects.filter(booking=booking).first()
    status = "confirmed"
    reserved_until = None
    
    if booking.status == "reserved":
        status = "reserved"
        reserved_until = booking.reserved_until
    
    return render(request, "home/booking_success.html", {
        "booking": booking,
        "total_price": total_price,
        "status": status,
        "reserved_until": reserved_until
    })




def payment_list(request):
    payments = Payment.objects.select_related("booking").all()
    return render(request, "home/payment_list.html", {"payments": payments})








# views.py - Update upcoming_tickets_view and past_tickets_view
def upcoming_tickets_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Please login first to view your tickets.")
        return redirect('login')

    today = timezone.now().date()
    tickets = Booking.objects.filter(
        user_id=user_id,
        booking_date__gte=today
    ).select_related("bus", "route").order_by('booking_date')

    # Add total price calculation
    for ticket in tickets:
        seats = ticket.seat_number.split(",") if ticket.seat_number else []
        ticket.total_price = len(seats) * ticket.bus.price
        ticket.seat_count = len(seats)

    context = {"tickets": tickets}
    return render(request, "home/upcoming_tickets.html", context)

def past_tickets_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    today = timezone.now().date()
    tickets = Booking.objects.filter(
        user_id=user_id,
        booking_date__lt=today
    ).select_related("bus", "route").order_by('-booking_date')

    # Add total price calculation
    for ticket in tickets:
        seats = ticket.seat_number.split(",") if ticket.seat_number else []
        ticket.total_price = len(seats) * ticket.bus.price
        ticket.seat_count = len(seats)

    context = {"tickets": tickets}
    return render(request, "home/past_tickets.html", context)


# views.py - Add ticket_detail_view
def ticket_detail_view(request, ticket_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Please login first to view ticket details.")
        return redirect('login')
    
    ticket = get_object_or_404(Booking, id=ticket_id, user_id=user_id)
    
    # Calculate total price
    seats = ticket.seat_number.split(",") if ticket.seat_number else []
    total_price = len(seats) * ticket.bus.price
    
    return render(request, "home/ticket_detail.html", {
        "ticket": ticket,
        "total_price": total_price
    })


def cancel_ticket_view(request, ticket_id):
    
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    ticket = get_object_or_404(Booking, id=ticket_id, user_id=user_id)

    if request.method == "POST":
        ticket.delete()
        messages.success(request, "Your ticket has been cancelled successfully.")
        return redirect('upcoming_tickets') 

    return redirect('upcoming_tickets')







def route_list_view(request):
    routes = Route.objects.all()
    return render(request, "home/admin.html", {"routes": routes})

def add_route_view(request):
    if request.method == "POST":
        form = RouteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("route_list")
    else:
        form = RouteForm()
    return render(request, "home/add_route.html", {"form": form})


def bus_list_view(request):
    buses = Bus.objects.all()
    return render(request, "home/admin.html", {"buses": buses})

def add_bus_view(request):
    form = BusForm()
    if request.method == "POST":
        form = BusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('bus_list')
    return render(request, "home/add_bus.html", {"form": form})



from datetime import datetime, timedelta

def available_buses(request):
    booking_date = request.GET.get("booking_date")
    route_id = request.GET.get("route_id")

    buses = Bus.objects.filter(route_id=route_id)

    for bus in buses:
        # only calculate if arrival_time is empty AND duration is available
        if not bus.arrival_time and bus.route.duration:
            try:
                # convert duration "HH:MM:SS" to hours/minutes
                duration_parts = str(bus.route.duration).split(":")
                hours = int(duration_parts[0])
                minutes = int(duration_parts[1])

                # calculate arrival time
                departure_dt = datetime.combine(datetime.today(), bus.departure_time)
                arrival_dt = departure_dt + timedelta(hours=hours, minutes=minutes)

                # assign to bus object (not saved in DB, just for template use)
                bus.arrival_time = arrival_dt.time()
            except Exception as e:
                bus.arrival_time = None

    return render(request, "available_buses.html", {
        "buses": buses,
        "booking_date": booking_date,
    })
