from django.contrib import admin
from .models import (
    Genre,
    Song,
    IOTARegistration,
    Album,
    ArtistProfile,
    FanProfile,
    Playlist,
    FavoriteSong,
    LaunchProject,
    WalletProfile,
    ProjectToken,
    TokenBenefit,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name")
    ordering = ("name",)


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "artist",
        "iota_status",
        "iota_block_id",
        "upload_date",
    )
    list_filter = ("iota_status", "genre", "upload_date")
    search_fields = ("title", "artist__username", "artist__first_name", "artist__last_name", "fingerprint")
    filter_horizontal = ("genre",)
    readonly_fields = ("upload_date",)
    autocomplete_fields = ("artist",)


@admin.register(IOTARegistration)
class IOTARegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "song",
        "album",
        "fingerprint",
        "block_id",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("fingerprint", "block_id", "song__title", "album__title")
    readonly_fields = ("created_at",)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "artist",
        "iota_status",
        "iota_block_id",
        "release_date",
    )
    list_filter = ("iota_status", "genre", "release_date")
    search_fields = ("title", "artist__username", "artist__first_name", "artist__last_name")
    filter_horizontal = ("songs", "genre")
    readonly_fields = ("release_date",)
    autocomplete_fields = ("artist",)


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "email_contact",
        "phone",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "email_contact",
        "phone",
    )
    autocomplete_fields = ("user",)


@admin.register(FanProfile)
class FanProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "bio_short", "total_favoritos")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "bio",
    )
    filter_horizontal = ("favoritos",)
    autocomplete_fields = ("user",)

    @admin.display(description="Bio")
    def bio_short(self, obj):
        return (obj.bio[:60] + "...") if obj.bio and len(obj.bio) > 60 else obj.bio

    @admin.display(description="Favoritos")
    def total_favoritos(self, obj):
        return obj.favoritos.count()


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "created")
    list_filter = ("created",)
    search_fields = ("name", "user__username", "user__first_name", "user__last_name")
    filter_horizontal = ("songs",)
    readonly_fields = ("created",)
    autocomplete_fields = ("user",)


@admin.register(FavoriteSong)
class FavoriteSongAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "song", "added_at")
    list_filter = ("added_at",)
    search_fields = ("user__username", "song__title")
    readonly_fields = ("added_at",)
    autocomplete_fields = ("user", "song")


@admin.register(LaunchProject)
class LaunchProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "song", "status", "launch_date", "created_at")
    list_filter = ("status", "launch_date", "created_at")
    search_fields = ("name", "song__title", "description")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("song",)


@admin.register(WalletProfile)
class WalletProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "address", "network", "is_verified", "created_at")
    list_filter = ("network", "is_verified", "created_at")
    search_fields = ("user__username", "address")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(ProjectToken)
class ProjectTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "symbol",
        "project",
        "total_supply",
        "utility_type",
        "status",
        "created_at",
    )
    list_filter = ("utility_type", "status", "created_at")
    search_fields = ("name", "symbol", "token_id", "project__name")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("project",)


@admin.register(TokenBenefit)
class TokenBenefitAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "token", "min_balance", "active")
    list_filter = ("active",)
    search_fields = ("title", "token__name", "token__symbol")
    autocomplete_fields = ("token",)