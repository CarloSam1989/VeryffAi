import hashlib
import json
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import *
from .models import *
from .services.iota_service import register_album_on_iota, register_song_on_iota

def build_user_role_context(user):
    is_artist_user = hasattr(user, 'artist_profile')
    is_fan_user = hasattr(user, 'fan_profile')

    return {
        'is_artist_user': is_artist_user,
        'is_fan_user': is_fan_user,
        'current_artist_profile': getattr(user, 'artist_profile', None),
        'current_fan_profile': getattr(user, 'fan_profile', None),
        'menu_dashboard_url': 'artist_profile' if is_artist_user else 'dashboard',
    }

@login_required
def upload_song(request):
    if not hasattr(request.user, 'artist_profile'):
        ArtistProfile.objects.create(user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        file = request.FILES.get('song')
        genre_ids = request.POST.getlist('genre')

        if not title:
            messages.error(request, 'El título es obligatorio.')
            return redirect('upload_song')

        if not file:
            messages.error(request, 'No seleccionaste ningún archivo.')
            return redirect('upload_song')

        h = hashlib.sha256()
        for chunk in file.chunks():
            h.update(chunk)
        fingerprint = h.hexdigest()

        if Song.objects.filter(fingerprint=fingerprint).exists():
            messages.error(request, 'Esta obra ya fue registrada.')
            return redirect('upload_song')

        song = Song.objects.create(
            title=title,
            artist=request.user,
            fingerprint=fingerprint,
            iota_status='pending',
            file=file,
        )

        if genre_ids:
            genres = Genre.objects.filter(id__in=genre_ids)
            song.genre.set(genres)

        result = register_song_on_iota(song)

        song.iota_block_id = result.get("block_id")
        song.iota_status = result.get("status", "failed")
        song.iota_error = result.get("error")
        song.save(update_fields=["iota_block_id", "iota_status", "iota_error"])

        IOTARegistration.objects.create(
            song=song,
            fingerprint=song.fingerprint,
            block_id=result.get("block_id"),
            payload=result.get("payload", {}),
            status=result.get("status", "failed"),
            error_message=result.get("error"),
        )

        if result.get("ok"):
            messages.success(request, f"¡Obra '{song.title}' registrada en IOTA correctamente!")
        else:
            messages.warning(
                request,
                f"La obra se guardó, pero falló el registro en IOTA: {result.get('error')}"
            )

        return redirect('artist_profile')

    genres = Genre.objects.all()
    context = {
        'genres': genres,
        **build_user_role_context(request.user),
    }
    return render(request, 'songs/upload_song.html', context)

@login_required
def retry_iota(request, song_id):
    song = get_object_or_404(Song, id=song_id, artist=request.user)

    result = register_song_on_iota(song)

    song.iota_block_id = result.get("block_id")
    song.iota_status = result.get("status", "failed")
    song.iota_error = result.get("error")
    song.save(update_fields=["iota_block_id", "iota_status", "iota_error"])

    IOTARegistration.objects.create(
        song=song,
        fingerprint=song.fingerprint,
        block_id=result.get("block_id"),
        payload=result.get("payload", {}),
        status=result.get("status", "failed"),
        error_message=result.get("error"),
    )

    if result.get("ok"):
        messages.success(request, 'Registro en IOTA completado.')
    else:
        messages.warning(request, f'La red IOTA aún no responde: {result.get("error")}')

    return redirect('artist_profile')

@login_required
def create_album(request):
    if not hasattr(request.user, 'artist_profile'):
        ArtistProfile.objects.create(user=request.user)

    user_songs = Song.objects.filter(artist=request.user).order_by('-upload_date')
    genres = Genre.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        song_ids = request.POST.getlist('songs')
        genre_ids = request.POST.getlist('genre')

        if not title:
            messages.error(request, 'El título del álbum es obligatorio.')
            return redirect('create_album')

        if not song_ids:
            messages.error(request, 'Debes seleccionar al menos una canción.')
            return redirect('create_album')

        selected_songs = Song.objects.filter(
            id__in=song_ids,
            artist=request.user
        ).order_by('id')

        if not selected_songs.exists():
            messages.error(request, 'Las canciones seleccionadas no son válidas.')
            return redirect('create_album')

        fingerprints_joined = ''.join(song.fingerprint for song in selected_songs)
        album_fingerprint = hashlib.sha256(
            fingerprints_joined.encode('utf-8')
        ).hexdigest()

        album = Album.objects.create(
            title=title,
            artist=request.user,
            iota_status='pending',
        )

        album.songs.set(selected_songs)

        if genre_ids:
            album.genre.set(Genre.objects.filter(id__in=genre_ids))

        result = register_album_on_iota(album, album_fingerprint)

        album.iota_block_id = result.get("block_id")
        album.iota_status = result.get("status", "failed")
        album.iota_error = result.get("error")
        album.save(update_fields=["iota_block_id", "iota_status", "iota_error"])

        IOTARegistration.objects.create(
            album=album,
            fingerprint=album_fingerprint,
            block_id=result.get("block_id"),
            payload=result.get("payload", {}),
            status=result.get("status", "failed"),
            error_message=result.get("error"),
        )

        if result.get("ok"):
            messages.success(request, f'Álbum "{album.title}" registrado en IOTA exitosamente.')
        else:
            messages.warning(
                request,
                f'Álbum guardado, pero falló el registro en IOTA: {result.get("error")}'
            )

        return redirect('artist_profile')

    context = {
        'user_songs': user_songs,
        'genres': genres,
    }
    return render(request, 'songs/create_album.html', context)

@login_required
def dashboard(request):
    profile, _ = FanProfile.objects.get_or_create(user=request.user)

    search_query = request.GET.get('query', '').strip()
    genre_id = request.GET.get('genre', '').strip()

    songs = Song.objects.all().select_related('artist').prefetch_related('genre')
    artists = ArtistProfile.objects.select_related('user').all()[:12]
    genres = Genre.objects.all()

    if search_query:
        songs = songs.filter(
            Q(title__icontains=search_query) |
            Q(artist__username__icontains=search_query) |
            Q(artist__first_name__icontains=search_query) |
            Q(artist__last_name__icontains=search_query)
        )

    if genre_id:
        songs = songs.filter(genre__id=genre_id)

    songs = songs.distinct().order_by('-upload_date')
    favorite_songs = profile.favoritos.all().select_related('artist').prefetch_related('genre')[:5]
    favorite_song_ids = list(profile.favoritos.values_list('id', flat=True))

    context = {
        'songs': songs[:12],
        'artists': artists,
        'favorite_songs': favorite_songs,
        'favorite_song_ids': favorite_song_ids,
        'search_query': search_query,
        'searching': bool(search_query or genre_id),
        'selected_genre_id': int(genre_id) if genre_id.isdigit() else None,
        'genero': genres,
        **build_user_role_context(request.user),
    }

    return render(request, 'fan/dashboard.html', context)

@login_required
def fan_favorites(request):
    profile, _ = FanProfile.objects.get_or_create(user=request.user)
    favorite_songs = profile.favoritos.all().select_related('artist').prefetch_related('genre').order_by('-id')

    context = {
        'favorite_songs': favorite_songs,
        **build_user_role_context(request.user),
    }
    return render(request, 'fan/favorites.html', context)

@login_required
def become_artist(request):
    if request.method == 'POST':
        ArtistProfile.objects.get_or_create(user=request.user)
        messages.success(request, 'Ahora tu cuenta también tiene perfil de artista.')
        return redirect('artist_profile')

    return redirect('dashboard')

@login_required
def artist_profile(request):
    artist_profile, _ = ArtistProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ArtistProfileForm(request.POST, request.FILES, instance=artist_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil de artista actualizado correctamente.')
            return redirect('artist_profile')
    else:
        form = ArtistProfileForm(instance=artist_profile)

    context = {
        'form': form,
        'artist_profile': artist_profile,
    }
    return render(request, 'artist/profile.html', context)

@login_required
def fan_profile(request):
    profile, _ = FanProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = FanUserForm(request.POST, instance=request.user)
        profile_form = FanProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('fan_profile')
    else:
        user_form = FanUserForm(instance=request.user)
        profile_form = FanProfileForm(instance=profile)

    context = {
        'profile': profile,
        'user_form': user_form,
        'profile_form': profile_form,
        'favorite_songs_count': profile.favoritos.count(),
        'playlists_count': 0,
        'favorite_songs': profile.favoritos.all().select_related('artist')[:5],
        **build_user_role_context(request.user),
    }

    return render(request, 'fan/profile.html', context)

@login_required
def song_detail(request, song_id):
    song = get_object_or_404(
        Song.objects.select_related('artist').prefetch_related('genre', 'launch_projects'),
        id=song_id
    )

    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FanProfile.objects.filter(
            user=request.user,
            favoritos=song
        ).exists()

    existing_funding_project = song.launch_projects.first()

    context = {
        'song': song,
        'is_favorite': is_favorite,
        'existing_funding_project': existing_funding_project,
        **build_user_role_context(request.user),
    }

    return render(request, 'songs/song_detail.html', context)

@login_required
@require_POST
def toggle_favorite(request, song_id):
    profile, _ = FanProfile.objects.get_or_create(user=request.user)

    try:
        song = Song.objects.select_related('artist').get(id=song_id)
    except Song.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'La canción no existe.'}, status=404)

    if profile.favoritos.filter(id=song.id).exists():
        profile.favoritos.remove(song)
        is_favorite = False
    else:
        profile.favoritos.add(song)
        is_favorite = True

    favorites_data = []
    for fav_song in profile.favoritos.all().select_related('artist')[:5]:
        artist_name = fav_song.artist.get_full_name() if fav_song.artist.get_full_name() else fav_song.artist.username
        favorites_data.append({
            'id': fav_song.id,
            'title': fav_song.title,
            'artist': artist_name,
            'url': reverse('song_detail', args=[fav_song.id]),
        })

    return JsonResponse({
        'ok': True,
        'is_favorite': is_favorite,
        'favorites_count': profile.favoritos.count(),
        'favorites': favorites_data,
    })

@login_required
def artist_detail(request, artist_id):
    artist = get_object_or_404(ArtistProfile, id=artist_id)
    songs = Song.objects.filter(artist=artist.user).prefetch_related('genre').order_by('-upload_date')

    context = {
        'artist': artist,
        'artist_songs': songs,
    }
    return render(request, 'artist/detail.html', context)

@login_required
def create_genre(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

    data = json.loads(request.body)
    name = data.get('name', '').strip()

    if not name:
        return JsonResponse({'success': False, 'error': 'Nombre vacío.'}, status=400)

    genre, created = Genre.objects.get_or_create(name=name)

    return JsonResponse({
        'success': True,
        'id': genre.id,
        'name': genre.name,
    })

@login_required
def funding_create_project(request, song_id):
    song = get_object_or_404(
        Song.objects.select_related('artist'),
        id=song_id,
        artist=request.user
    )

    if not hasattr(request.user, 'artist_profile'):
        ArtistProfile.objects.get_or_create(user=request.user)

    existing_project = LaunchProject.objects.filter(song=song).first()
    if existing_project:
        messages.info(request, 'Esta canción ya tiene un proyecto de fan funding.')
        return redirect('funding_project_detail', project_id=existing_project.id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip() or f"Fan Funding - {song.title}"
        description = request.POST.get('description', '').strip()
        total_participations = request.POST.get('total_participations', '100000').strip()

        try:
            total_participations = int(total_participations)
        except ValueError:
            messages.error(request, 'El total de participaciones debe ser numérico.')
            return redirect('funding_create_project', song_id=song.id)

        if total_participations <= 0:
            messages.error(request, 'El total de participaciones debe ser mayor a cero.')
            return redirect('funding_create_project', song_id=song.id)

        project = LaunchProject.objects.create(
            song=song,
            name=name,
            description=description,
            status='open',
            is_demo=True,
            total_participations=total_participations,
            participations_available=total_participations,
            max_primary_buy_percent=Decimal('10.00'),
            max_holding_percent=Decimal('15.00'),
            price_per_participation=Decimal('0'),
            currency='DEMO',
            launch_date=timezone.now(),
            starts_at=timezone.now(),
            terms_accepted=True,
        )

        symbol_base = ''.join(ch for ch in song.title.upper() if ch.isalnum())[:6] or 'FUND'
        token_symbol = f"{symbol_base}{project.id}"

        ProjectToken.objects.create(
            project=project,
            name=f"{song.title} Demo Participation",
            symbol=token_symbol,
            total_supply=Decimal(project.total_participations),
            utility_type='demo_participation',
            status='active',
        )

        messages.success(request, f'Se creó el proyecto demo para "{song.title}".')
        return redirect('funding_project_detail', project_id=project.id)

    context = {
        'song': song,
        **build_user_role_context(request.user),
    }
    return render(request, 'funding/create_project.html', context)

@login_required
def funding_project_detail(request, project_id):
    project = get_object_or_404(
        LaunchProject.objects.select_related('song', 'song__artist')
        .prefetch_related('tokens', 'holdings__user'),
        id=project_id
    )

    wallet, _ = WalletProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'network': 'iota-testnet',
            'demo_balance': Decimal('100000'),
        }
    )

    user_holding = project.holdings.filter(user=request.user).first()
    top_holders = project.holdings.select_related('user').order_by('-balance', 'user__username')[:10]
    purchases = project.purchases.select_related('user').order_by('-created_at')[:20]

    can_create = project.song.artist_id == request.user.id
    is_owner = can_create

    context = {
        'project': project,
        'wallet': wallet,
        'user_holding': user_holding,
        'top_holders': top_holders,
        'recent_purchases': purchases,
        'is_owner': is_owner,
        'can_create': can_create,
        'max_primary_buy_units': project.max_primary_buy_units(),
        'max_holding_units': project.max_holding_units(),
        **build_user_role_context(request.user),
    }
    return render(request, 'funding/project_detail.html', context)

@login_required
@require_POST
def funding_buy(request, project_id):
    project = get_object_or_404(
        LaunchProject.objects.select_related('song', 'song__artist'),
        id=project_id
    )

    if project.song.artist_id == request.user.id:
        messages.error(request, 'El artista no puede comprar participaciones de su propio proyecto demo.')
        return redirect('funding_project_detail', project_id=project.id)

    quantity_raw = request.POST.get('quantity', '').strip()

    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        messages.error(request, 'La cantidad ingresada no es válida.')
        return redirect('funding_project_detail', project_id=project.id)

    wallet, _ = WalletProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'network': 'iota-testnet',
            'demo_balance': Decimal('100000.0000'),
        }
    )

    allowed, reason = project.can_user_buy_primary(request.user, quantity)
    if not allowed:
        messages.error(request, reason)
        return redirect('funding_project_detail', project_id=project.id)

    with transaction.atomic():
        project = LaunchProject.objects.select_for_update().get(id=project.id)

        allowed, reason = project.can_user_buy_primary(request.user, quantity)
        if not allowed:
            messages.error(request, reason)
            return redirect('funding_project_detail', project_id=project.id)

        holding, _ = FanFundingHolding.objects.select_for_update().get_or_create(
            project=project,
            user=request.user,
            defaults={
                'balance': 0,
                'locked_balance': 0,
                'avg_cost': Decimal('0'),
            }
        )

        is_first_purchase = not project.user_has_primary_purchase(request.user)

        purchase = FanFundingPurchase.objects.create(
            project=project,
            user=request.user,
            wallet=wallet,
            purchase_phase='primary',
            quantity=quantity,
            unit_price=Decimal('0'),
            is_first_purchase=is_first_purchase,
            status='completed',
            completed_at=timezone.now(),
            notes='Compra demo de fan funding',
        )

        old_balance = holding.balance
        new_balance = old_balance + quantity

        if old_balance > 0:
            holding.avg_cost = Decimal('0')
        else:
            holding.avg_cost = Decimal('0')

        holding.balance = new_balance
        if is_first_purchase and not holding.first_purchase_at:
            holding.first_purchase_at = timezone.now()
        holding.last_purchase_at = timezone.now()
        holding.save()

        project.participations_available -= quantity
        project.save(update_fields=['participations_available', 'updated_at'])

        FanFundingTransaction.objects.create(
            project=project,
            user=request.user,
            purchase=purchase,
            movement_type='buy',
            quantity=quantity,
            balance_after=holding.balance,
            metadata={
                'phase': 'primary',
                'is_demo': True,
                'is_first_purchase': is_first_purchase,
            },
        )

    messages.success(
        request,
        f'Compraste {quantity} participaciones demo de "{project.song.title}" correctamente.'
    )
    return redirect('funding_project_detail', project_id=project.id)

@login_required
def funding_my_holdings(request):
    wallet, _ = WalletProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'network': 'iota-testnet',
            'demo_balance': Decimal('100000'),
        }
    )

    holdings = (
        FanFundingHolding.objects
        .filter(user=request.user, balance__gt=0)
        .select_related('project', 'project__song', 'project__song__artist')
        .order_by('-balance', 'project__created_at')
    )

    purchases = (
        FanFundingPurchase.objects
        .filter(user=request.user)
        .select_related('project', 'project__song')
        .order_by('-created_at')
    )

    context = {
        'wallet': wallet,
        'holdings': holdings,
        'purchases': purchases[:50],
        **build_user_role_context(request.user),
    }
    return render(request, 'funding/my_holdings.html', context)

@login_required
def funding_artist_projects(request):
    if not hasattr(request.user, 'artist_profile'):
        messages.error(request, 'Debes tener perfil de artista para ver tus proyectos.')
        return redirect('dashboard')

    projects = (
        LaunchProject.objects
        .filter(song__artist=request.user)
        .select_related('song')
        .prefetch_related('holdings', 'tokens')
        .order_by('-created_at')
    )

    context = {
        'projects': projects,
        **build_user_role_context(request.user),
    }
    return render(request, 'funding/artist_projects.html', context)

@login_required
def funding_marketplace(request):
    projects = (
        LaunchProject.objects
        .filter(status='open', is_demo=True)
        .select_related('song', 'song__artist')
        .prefetch_related('holdings')
        .order_by('-created_at')
    )

    query = request.GET.get('q', '').strip()
    if query:
        projects = projects.filter(
            Q(name__icontains=query) |
            Q(song__title__icontains=query) |
            Q(song__artist__username__icontains=query)
        )

    marketplace_projects = []
    for project in projects:
        holders_count = project.holdings.filter(balance__gt=0).count()
        marketplace_projects.append({
            'project': project,
            'holders_count': holders_count,
            'sold_percent': project.sold_percent,
            'max_primary_buy_units': project.max_primary_buy_units(),
        })

    context = {
        'marketplace_projects': marketplace_projects,
        'search_query': query,
        **build_user_role_context(request.user),
    }
    return render(request, 'funding/marketplace.html', context)

@login_required
def wallet_kyc_profile(request):
    wallet, _ = WalletProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'network': 'iota_testnet',
            'demo_balance': Decimal('100000'),
        }
    )

    kyc, _ = KYCProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'status': 'not_started',
        }
    )

    if request.method == 'POST':
        wallet_form = WalletProfileForm(request.POST, instance=wallet)
        kyc_form = KYCProfileForm(request.POST, instance=kyc)

        if wallet_form.is_valid() and kyc_form.is_valid():
            wallet_obj = wallet_form.save(commit=False)

            # Si cambia la address y todavía no está verificada,
            # mantenemos el estado coherente
            if wallet_obj.address and wallet_obj.address_status == 'verified' and not wallet_obj.address_verified_at:
                wallet_obj.address_status = 'pending'
                wallet_obj.is_verified = False

            wallet_obj.save()

            kyc_obj = kyc_form.save(commit=False)

            # En esta fase MVP no verificamos realmente KYC,
            # solo lo marcamos como pendiente cuando el usuario envía datos
            if (
                kyc_obj.verification_level or
                kyc_obj.country_code or
                kyc_obj.document_country or
                kyc_obj.document_type
            ):
                if kyc_obj.status == 'not_started':
                    kyc_obj.status = 'pending'

            kyc_obj.save()

            messages.success(request, 'Wallet y KYC actualizados correctamente.')
            return redirect('wallet_kyc_profile')
    else:
        wallet_form = WalletProfileForm(instance=wallet)
        kyc_form = KYCProfileForm(instance=kyc)

    context = {
        'wallet': wallet,
        'kyc': kyc,
        'wallet_form': wallet_form,
        'kyc_form': kyc_form,
        **build_user_role_context(request.user),
    }
    return render(request, 'funding/wallet_kyc_profile.html', context)


