# core/home/models.py
from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
import uuid
from datetime import datetime, timedelta



class User(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )

    # Common fields
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=255)  # plain for now, later hash

    # Customer-specific fields
    cnic_passport = models.CharField(max_length=20, unique=True, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    # Role field
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    # Standard audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_users')

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.name} ({self.role})"


class Route(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    duration = models.CharField(max_length=5, null=True, blank=True)  # e.g. "02:00"
    distance = models.FloatField(null=True, blank=True)

    # Standard audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_routes')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_routes')

    class Meta:
        db_table = "routes"
    
    def __str__(self):
        return f"{self.origin} → {self.destination}"


class Bus(models.Model):
    bus_number = models.CharField(max_length=20)
    capacity = models.IntegerField()
    route = models.ForeignKey("Route", on_delete=models.CASCADE)
    bus_type = models.CharField(
        max_length=50,
        choices=[("Express", "Express"), ("Cargo", "Cargo"), ("Metro", "Metro")]
    )
    departure_time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Standard audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_buses')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_buses')

    class Meta:
        db_table = "buses"

    def __str__(self):
        return f"{self.bus_type} ({self.route.origin} → {self.route.destination})"

    @property
    def arrival_time(self):
        """Calculate arrival time by adding route.duration to departure_time."""
        if not self.route.duration:
            return None

        duration_value = str(self.route.duration).strip()

        # If it's already a timedelta
        if isinstance(self.route.duration, timedelta):
            duration = self.route.duration

        # If it's like "HH:MM:SS"
        elif ":" in duration_value and "h" not in duration_value:
            hours, minutes, *_ = map(int, duration_value.split(":"))
            duration = timedelta(hours=hours, minutes=minutes)

        # If it's like "5h 30"
        elif "h" in duration_value:
            parts = duration_value.lower().replace("h", "").split()
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            duration = timedelta(hours=hours, minutes=minutes)

        else:
            # fallback: treat it as hours only (e.g. "5")
            duration = timedelta(hours=int(duration_value))

        departure_dt = datetime.combine(datetime.today(), self.departure_time)
        arrival_dt = departure_dt + duration
        return arrival_dt.time()


class ComplaintSuggestion(models.Model):
    SUGGESTION_TYPES = [
        ("complaint", "Complaint"),
        ("suggestion", "Suggestion"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    suggestion_type = models.CharField(max_length=20, choices=SUGGESTION_TYPES)
    title = models.CharField(max_length=200)
    first_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=15)
    message = models.TextField()

    # Standard audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_complaints')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_complaints')
    
    class Meta:
        db_table = "complaint_suggestion"
    
    def __str__(self):
        return f"{self.suggestion_type.title()} - {self.title}"



class Booking(models.Model):
    STATUS_CHOICES = [
        ("reserved", "Reserved"),
        ("confirmed", "Confirmed"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey("User", on_delete=models.CASCADE)
    route = models.ForeignKey("Route", on_delete=models.CASCADE)
    bus = models.ForeignKey("Bus", on_delete=models.CASCADE)
    booking_date = models.DateField()
    seat_number = models.CharField(max_length=200)
    booking_number = models.CharField(max_length=20, unique=True, blank=True)

    # ✅ Reservation system fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="reserved")
    reserved_until = models.DateTimeField(null=True, blank=True)

    # Standard audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_bookings")
    updated_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_bookings")

    class Meta:
        db_table = "booking"

    def save(self, *args, **kwargs):
        if not self.booking_number:
            self.booking_number = f"BK-{uuid.uuid4().hex[:8].upper()}"

        # If new booking is reserved, set expiry time (30 minutes)
        if self.status == "reserved" and not self.reserved_until:
            self.reserved_until = timezone.now() + timedelta(minutes=30)

        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if reservation has expired"""
        return self.status == "reserved" and self.reserved_until and timezone.now() > self.reserved_until

    def __str__(self):
        return f"{self.booking_number} - {self.user.name} on {self.booking_date}"



class RefundRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    refund_as = models.CharField(max_length=50)
    additional_notes = models.TextField(blank=True, null=True)
    
    # Extra fields for additional details
    passenger_cnic = models.CharField(max_length=20, blank=True, null=True)
    transaction_date = models.DateField(blank=True, null=True)
    transaction_time = models.TimeField(blank=True, null=True)
    transaction_attempts = models.CharField(max_length=255, blank=True, null=True)
    transaction_by = models.CharField(max_length=255, blank=True, null=True)
    card_type = models.CharField(max_length=100, blank=True, null=True)
    card_bank = models.CharField(max_length=255, blank=True, null=True)
    card_number = models.CharField(max_length=20, blank=True, null=True)
    booking_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    submitted_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default="Pending")  # Pending / Approved / Rejected

    # Standard audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_refunds')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_refunds')

    class Meta:
        db_table = "refund_request"

    def __str__(self):
        return f"Refund #{self.id} - {self.user.name} - {self.status}"



class Payment(models.Model):
    PAYMENT_METHODS = [
        ("card", "Credit/Debit Card"),
        ("cash", "Cash"),
        ("wallet", "Wallet"),
        ("bank_transfer", "Bank Transfer"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    paid_at = models.DateTimeField(blank=True, null=True)

    # Card info
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_expiry = models.CharField(max_length=7, blank=True, null=True)  # MM/YYYY

    # Bank transfer info
    account_number = models.CharField(max_length=30, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    

    # Standard audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_payments")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_payments")

    class Meta:
        db_table = "payments"

    def save(self, *args, **kwargs):
        if self.status == "completed" and not self.paid_at:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.id} - {self.booking.booking_number} - {self.status}"
