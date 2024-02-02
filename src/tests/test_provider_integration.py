import pytest
from fyodorov_utils.config.config import Settings
from models.provider import ProviderModel
from services.provider import Provider
from tests.test_provider_model import get_default_provider

@pytest.fixture
async def provider_fixture() -> Provider:
    default_provider: ProviderModel = get_default_provider()
    return default_provider

@pytest.mark.asyncio
async def test_get_providers(provider_fixture):
    provider = await provider_fixture
    providers = Provider.get_all_in_db()
    assert len(providers) > 0
    providerService = Provider(provider)
    providerService.delete_in_db()

@pytest.mark.asyncio
async def test_update_provider(provider_fixture):
    provider = await provider_fixture
    provider.api_url = "https://azure.com"
    providerService = Provider(provider)
    updated_tool = await providerService.update_provider_in_db()
    assert updated_tool['api_url'] == "https://azure.com"
    providerService.delete_in_db()

@pytest.mark.asyncio
async def test_get_provider(provider_fixture):
    provider = await provider_fixture
    providerService = Provider(provider)
    provider_copy = await providerService.get_provider_by_id(provider.id)
    assert provider_copy['id'] == provider.id
    providerService.delete_in_db()
