"""
Microsoft Graph API authentication using MSAL device code flow.
No client secret needed - uses a public client app registration.
"""

import json
import os
import msal

# You can use the default Microsoft Graph Explorer app ID for personal use,
# or register your own at https://portal.azure.com
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Notes.ReadWrite", "Notes.Create", "Notes.ReadWrite.All"]

TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".token_cache.json")


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_access_token(client_id: str) -> str:
    """
    Authenticate via device code flow and return an access token.
    Token is cached locally so re-auth only happens when token expires.
    """
    cache = _load_cache()

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=AUTHORITY,
        token_cache=cache,
    )

    # Try silent auth first (cached token)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"]

    # Fall back to device code flow
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Failed to create device flow: {flow.get('error_description', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("AUTHENTICATION REQUIRED")
    print("=" * 60)
    print(f"\n{flow['message']}\n")
    print("=" * 60 + "\n")

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        error = result.get("error_description", result.get("error", "Unknown error"))
        raise RuntimeError(f"Authentication failed: {error}")

    _save_cache(cache)
    print("Authentication successful!\n")
    return result["access_token"]


def clear_token_cache() -> None:
    """Remove cached tokens to force re-authentication."""
    if os.path.exists(TOKEN_CACHE_FILE):
        os.remove(TOKEN_CACHE_FILE)
        print("Token cache cleared.")
