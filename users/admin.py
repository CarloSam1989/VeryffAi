from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from songs.models import ArtistProfile, FanProfile, WalletProfile


class ArtistProfileInline(admin.StackedInline):
    model = ArtistProfile
    can_delete = False
    extra = 0


class FanProfileInline(admin.StackedInline):
    model = FanProfile
    can_delete = False
    extra = 0
    filter_horizontal = ("favoritos",)


class WalletProfileInline(admin.StackedInline):
    model = WalletProfile
    can_delete = False
    extra = 0


class CustomUserAdmin(UserAdmin):
    inlines = [ArtistProfileInline, FanProfileInline, WalletProfileInline]

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "has_artist_profile",
        "has_fan_profile",
        "has_wallet_profile",
    )

    search_fields = ("username", "first_name", "last_name", "email")

    @admin.display(boolean=True, description="Artista")
    def has_artist_profile(self, obj):
        return hasattr(obj, "artist_profile")

    @admin.display(boolean=True, description="Fan")
    def has_fan_profile(self, obj):
        return hasattr(obj, "fan_profile")

    @admin.display(boolean=True, description="Wallet")
    def has_wallet_profile(self, obj):
        return hasattr(obj, "wallet_profile")


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)