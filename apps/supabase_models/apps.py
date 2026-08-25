from django.apps import AppConfig


class SupabaseModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.supabase_models'
    verbose_name = 'Supabase Models'