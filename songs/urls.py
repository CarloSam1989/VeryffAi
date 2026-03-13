from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_song, name='upload_song'),
    path('retry-iota/<int:song_id>/', views.retry_iota, name='retry_iota'),
    path('albums/create/', views.create_album, name='create_album'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('favorites/', views.fan_favorites, name='fan_favorites'),
    path('fan/profile/', views.fan_profile, name='fan_profile'),
    path('artist/profile/', views.artist_profile, name='artist_profile'),
    path('become-artist/', views.become_artist, name='become_artist'),
    path('song/<int:song_id>/', views.song_detail, name='song_detail'),
    path('favorite/toggle/<int:song_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('artist/<int:artist_id>/', views.artist_detail, name='artist_detail'),
    path("create-genre/", views.create_genre, name="create_genre"),

    # Fan Funding Demo
    path('funding/marketplace/', views.funding_marketplace, name='funding_marketplace'),
    path('funding/create/song/<int:song_id>/', views.funding_create_project, name='funding_create_project'),
    path('funding/project/<int:project_id>/', views.funding_project_detail, name='funding_project_detail'),
    path('funding/project/<int:project_id>/buy/', views.funding_buy, name='funding_buy'),
    path('funding/my-holdings/', views.funding_my_holdings, name='funding_my_holdings'),
    path('funding/my-projects/', views.funding_artist_projects, name='funding_artist_projects'),
    path('funding/marketplace/', views.funding_marketplace, name='funding_marketplace'),
    path('funding/wallet-kyc/', views.wallet_kyc_profile, name='wallet_kyc_profile'),
]