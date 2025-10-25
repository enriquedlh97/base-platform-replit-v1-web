from supabase import Client, create_client

from app.core.config import settings

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_SERVICE_ROLE_KEY

supabase_admin_client: Client = create_client(url, key)


def get_public_storage_url(bucket_name: str, file_path: str) -> str:
    """
    Get a public URL for a file in Supabase Storage.

    This function handles the environment-specific URL correction to ensure
    external clients can access the files.
    """
    # Get the URL from Supabase client
    public_url: str = supabase_admin_client.storage.from_(bucket_name).get_public_url(
        file_path
    )

    # If in local environment, replace internal hostname with public one
    if settings.ENVIRONMENT == "local":
        public_url = public_url.replace(
            settings.SUPABASE_URL, settings.SUPABASE_PUBLIC_URL
        )

    return public_url
