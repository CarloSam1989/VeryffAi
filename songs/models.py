from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(User, on_delete=models.CASCADE)
    fingerprint = models.CharField(max_length=64, unique=True)
    iota_block_id = models.CharField(max_length=255, null=True, blank=True)

    IOTA_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]
    iota_status = models.CharField(max_length=20, choices=IOTA_STATUS_CHOICES, default='pending')
    iota_error = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='songs/', null=True, blank=True)
    genre = models.ManyToManyField(Genre, blank=True)

    def __str__(self):
        return f"{self.title} - {self.artist.username}"

class IOTARegistration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]

    song = models.ForeignKey('Song', on_delete=models.CASCADE, null=True, blank=True, related_name='iota_registrations')
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null=True, blank=True, related_name='iota_registrations')
    fingerprint = models.CharField(max_length=64)
    block_id = models.CharField(max_length=255, blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.song and not self.album:
            raise ValidationError("Debes asociar el registro IOTA a una canción o a un álbum.")

    def __str__(self):
        target = self.song.title if self.song else self.album.title if self.album else "Sin destino"
        return f"IOTARegistration - {target} - {self.status}"

class Album(models.Model):
    IOTA_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=255)
    artist = models.ForeignKey(User, on_delete=models.CASCADE)
    songs = models.ManyToManyField('Song', related_name='albums')
    iota_block_id = models.CharField(max_length=255, null=True, blank=True)
    release_date = models.DateTimeField(auto_now_add=True)
    genre = models.ManyToManyField(Genre, blank=True)
    iota_status = models.CharField(max_length=20, choices=IOTA_STATUS_CHOICES, default='pending')
    iota_error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.artist.username}"

class ArtistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='artist_profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    email_contact = models.EmailField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class FanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fan_profile')
    avatar = models.ImageField(upload_to='fan_avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)

    favoritos = models.ManyToManyField(Song, related_name='favorited_by', blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=100)
    songs = models.ManyToManyField(Song)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class FavoriteSong(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.song.title} favorited by {self.user.username}"

class LaunchProject(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PROJECT_TYPE_CHOICES = [
        ('fan_funding_demo', 'Fan Funding Demo'),
    ]

    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='launch_projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    project_type = models.CharField(max_length=40, choices=PROJECT_TYPE_CHOICES, default='fan_funding_demo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # MVP demo
    is_demo = models.BooleanField(default=True)
    total_participations = models.PositiveIntegerField(default=100000)
    participations_available = models.PositiveIntegerField(default=100000)

    # Reglas de concentración
    max_primary_buy_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    max_holding_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'))

    # En demo no tiene valor real, pero lo dejamos preparado
    price_per_participation = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    currency = models.CharField(max_length=20, default='DEMO')

    launch_date = models.DateTimeField(null=True, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    iota_asset_id = models.CharField(max_length=255, blank=True, null=True)
    metadata_block_id = models.CharField(max_length=255, blank=True, null=True)

    terms_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['song'], name='unique_launch_project_per_song'),
        ]

    def clean(self):
        if self.total_participations <= 0:
            raise ValidationError("El total de participaciones debe ser mayor que cero.")

        if self.participations_available > self.total_participations:
            raise ValidationError("Las participaciones disponibles no pueden superar el total.")

        if self.max_primary_buy_percent <= 0 or self.max_primary_buy_percent > 100:
            raise ValidationError("El límite de compra primaria debe estar entre 0 y 100.")

        if self.max_holding_percent <= 0 or self.max_holding_percent > 100:
            raise ValidationError("El límite de tenencia debe estar entre 0 y 100.")

        if self.max_primary_buy_percent > self.max_holding_percent:
            raise ValidationError("El límite de compra primaria no puede ser mayor al límite de tenencia.")

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"Fan Funding - {self.song.title}"

        if not self.pk and not self.participations_available:
            self.participations_available = self.total_participations

        super().save(*args, **kwargs)

    @property
    def sold_participations(self):
        return self.total_participations - self.participations_available

    @property
    def sold_percent(self):
        if self.total_participations == 0:
            return Decimal('0')
        return (Decimal(self.sold_participations) / Decimal(self.total_participations)) * Decimal('100')

    def max_primary_buy_units(self):
        return int((Decimal(self.total_participations) * self.max_primary_buy_percent) / Decimal('100'))

    def max_holding_units(self):
        return int((Decimal(self.total_participations) * self.max_holding_percent) / Decimal('100'))

    def user_total_holdings(self, user):
        holding = self.holdings.filter(user=user).first()
        return holding.balance if holding else 0

    def user_has_primary_purchase(self, user):
        return self.purchases.filter(user=user, purchase_phase='primary', status='completed').exists()

    def can_user_buy_primary(self, user, quantity):
        if self.status != 'open':
            return False, "El proyecto no está abierto para compras."

        if quantity <= 0:
            return False, "La cantidad debe ser mayor a cero."

        if quantity > self.participations_available:
            return False, "No hay suficientes participaciones disponibles."

        current_holding = self.user_total_holdings(user)
        future_holding = current_holding + quantity

        if future_holding > self.max_holding_units():
            return False, "Ya alcanzaste el límite máximo permitido para este proyecto. Este límite ayuda a mantener una distribución justa entre los fans."

        # Solo limitar la primera compra al 10%
        if not self.user_has_primary_purchase(user):
            if quantity > self.max_primary_buy_units():
                return False, "La primera compra no puede superar el 10% del proyecto."

        return True, "OK"

    def __str__(self):
        return f"{self.name} - {self.song.title}"

class WalletProfile(models.Model):
    NETWORK_CHOICES = [
        ('iota_mainnet', 'IOTA Mainnet'),
        ('iota_testnet', 'IOTA Testnet'),
    ]

    ADDRESS_STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet_profile')

    address = models.CharField(max_length=255, unique=True, null=True, blank=True)
    network = models.CharField(max_length=30, choices=NETWORK_CHOICES, default='iota_testnet')

    is_verified = models.BooleanField(default=False)
    address_status = models.CharField(
        max_length=20,
        choices=ADDRESS_STATUS_CHOICES,
        default='unverified'
    )
    address_verified_at = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=30, blank=True)
    did_identifier = models.CharField(max_length=255, blank=True)

    wallet_label = models.CharField(max_length=100, blank=True)
    last_challenge_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    demo_balance = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('100000'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def clean(self):
        if self.address:
            self.address = self.address.strip()

            if ' ' in self.address:
                raise ValidationError("La address no debe contener espacios.")

            if len(self.address) < 10:
                raise ValidationError("La address ingresada es demasiado corta.")

            if self.network not in dict(self.NETWORK_CHOICES):
                raise ValidationError("La red seleccionada no es válida.")

        if self.is_verified and self.address_status != 'verified':
            self.address_status = 'verified'

        if self.address_status == 'verified' and not self.address_verified_at:
            raise ValidationError("Debes registrar la fecha de verificación de la address.")

    @property
    def has_address(self):
        return bool(self.address)

    @property
    def can_transact_real(self):
        return self.address_status == 'verified'

    def __str__(self):
        return f"Wallet {self.user.username} - {self.network}"
    
class WalletVerificationChallenge(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
        ('used', 'Used'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_challenges')
    wallet = models.ForeignKey(WalletProfile, on_delete=models.CASCADE, related_name='verification_challenges')

    nonce = models.CharField(max_length=255, unique=True)
    message = models.TextField()
    signature = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.expires_at and self.verified_at and self.verified_at > self.expires_at:
            raise ValidationError("No puedes verificar un challenge después de su expiración.")

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() >= self.expires_at

    @property
    def is_active(self):
        return self.status == 'pending' and not self.is_used and not self.is_expired

    def mark_expired_if_needed(self):
        if self.is_expired and self.status == 'pending':
            self.status = 'expired'
            self.save(update_fields=['status'])

    def __str__(self):
        return f"Challenge {self.user.username} - {self.status}"
    
class KYCProfile(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('enhanced', 'Enhanced'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc_profile')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    verification_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True)

    provider = models.CharField(max_length=100, blank=True)
    provider_reference = models.CharField(max_length=255, blank=True)

    country_code = models.CharField(max_length=10, blank=True)
    risk_score = models.PositiveIntegerField(default=0)
    pep_sanctions_checked = models.BooleanField(default=False)

    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    did_identifier = models.CharField(max_length=255, blank=True)
    vc_credential_id = models.CharField(max_length=255, blank=True)

    full_name_verified = models.CharField(max_length=255, blank=True)
    date_of_birth_verified = models.DateField(null=True, blank=True)
    document_country = models.CharField(max_length=10, blank=True)
    document_type = models.CharField(max_length=50, blank=True)
    document_last4 = models.CharField(max_length=4, blank=True)

    consent_accepted = models.BooleanField(default=False)
    consent_accepted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def clean(self):
        if self.status == 'verified' and not self.verified_at:
            raise ValidationError("Debes establecer la fecha de verificación cuando el KYC esté verificado.")

        if self.risk_score > 100:
            raise ValidationError("El risk_score no puede ser mayor a 100.")

    @property
    def is_valid(self):
        from django.utils import timezone
        if self.status != 'verified':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return f"KYC {self.user.username} - {self.status}"
    
class KYCReviewLog(models.Model):
    ACTION_CHOICES = [
        ('submitted', 'Submitted'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('manual_review', 'Manual Review'),
    ]

    kyc_profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name='review_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kyc_actions_performed'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.kyc_profile.user.username} - {self.action}"

class ProjectToken(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('minted', 'Minted'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('retired', 'Retired'),
    ]

    UTILITY_CHOICES = [
        ('access', 'Access'),
        ('community', 'Community'),
        ('demo_participation', 'Demo Participation'),
    ]

    project = models.ForeignKey(LaunchProject, on_delete=models.CASCADE, related_name='tokens')
    name = models.CharField(max_length=120)
    symbol = models.CharField(max_length=20)
    total_supply = models.DecimalField(max_digits=30, decimal_places=8)
    token_id = models.CharField(max_length=255, blank=True, null=True)
    utility_type = models.CharField(max_length=50, choices=UTILITY_CHOICES, default='demo_participation')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('project', 'symbol')]

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class TokenBenefit(models.Model):
    token = models.ForeignKey(ProjectToken, on_delete=models.CASCADE, related_name='benefits')
    title = models.CharField(max_length=150)
    description = models.TextField()
    min_balance = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.token.symbol}"

class FanFundingHolding(models.Model):
    project = models.ForeignKey(LaunchProject, on_delete=models.CASCADE, related_name='holdings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fan_funding_holdings')

    balance = models.PositiveIntegerField(default=0)
    locked_balance = models.PositiveIntegerField(default=0)

    avg_cost = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    first_purchase_at = models.DateTimeField(null=True, blank=True)
    last_purchase_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('project', 'user')]
        ordering = ['-balance', 'user__username']

    def clean(self):
        if self.locked_balance > self.balance:
            raise ValidationError("El saldo bloqueado no puede superar el balance.")

    @property
    def available_balance(self):
        return self.balance - self.locked_balance

    @property
    def percentage(self):
        if self.project.total_participations == 0:
            return Decimal('0')
        return (Decimal(self.balance) / Decimal(self.project.total_participations)) * Decimal('100')

    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.balance}"

class FanFundingPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]

    PURCHASE_PHASE_CHOICES = [
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
    ]

    project = models.ForeignKey(LaunchProject, on_delete=models.CASCADE, related_name='purchases')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fan_funding_purchases')
    wallet = models.ForeignKey(
        WalletProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fan_funding_purchases'
    )

    purchase_phase = models.CharField(max_length=20, choices=PURCHASE_PHASE_CHOICES, default='primary')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))

    is_first_purchase = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    tx_hash = models.CharField(max_length=255, blank=True, null=True)
    block_id = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")

    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity) * Decimal(self.unit_price or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} compró {self.quantity} en {self.project.name}"

class FanFundingTransaction(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('lock', 'Lock'),
        ('unlock', 'Unlock'),
        ('adjustment', 'Adjustment'),
        ('refund', 'Refund'),
    ]

    project = models.ForeignKey(LaunchProject, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fan_funding_transactions')
    purchase = models.ForeignKey(
        FanFundingPurchase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.IntegerField()
    balance_after = models.PositiveIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.movement_type} - {self.user.username} - {self.quantity}"