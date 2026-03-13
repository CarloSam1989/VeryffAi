def user_role_context(request):
    user = request.user

    if not user.is_authenticated:
        return {
            'is_artist_user': False,
            'is_fan_user': False,
            'current_artist_profile': None,
            'current_fan_profile': None,
        }

    artist_profile = getattr(user, 'artist_profile', None)
    fan_profile = getattr(user, 'fan_profile', None)

    return {
        'is_artist_user': artist_profile is not None,
        'is_fan_user': fan_profile is not None,
        'current_artist_profile': artist_profile,
        'current_fan_profile': fan_profile,
    }