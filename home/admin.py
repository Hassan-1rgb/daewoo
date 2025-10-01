from django.contrib import admin
from .models import ComplaintSuggestion   # <-- import your model here
from .models import Bus

@admin.register(ComplaintSuggestion)
class ComplaintSuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "suggestion_type", "title", "first_name", "email", "mobile_number", "created_at")
    search_fields = ("title", "first_name", "email", "mobile_number")
    list_filter = ("suggestion_type", "created_at")



@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ("id", "bus_number", "bus_type", "capacity", "route", "departure_time", "price")
