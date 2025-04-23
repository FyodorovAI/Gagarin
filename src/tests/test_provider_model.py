from pydantic import ValidationError
from models.provider import ProviderModel

def get_default_provider(
        provider: str | None = "openai",
        api_url: str | None = "https://api.openai.com",
        api_key: str | None = "key",
        models: list[str] | None = ["text-davinci-003"]
    ) -> ProviderModel:

    try:
        provider_model_instance = ProviderModel(
            provider_name=provider,
            api_url=api_url,
            api_key=api_key,
            models=models,
        )
    except ValidationError as e:
        print("Provider model validation error:", e)
        raise
    else:
        print("Provider update model:", provider_model_instance)
        return provider_model_instance

def test_default_provider_validation():
    try:
        get_default_provider()
    except Exception as e:
        assert False, f"An exception occurred: {e}"
    else:
        assert True, "No exception should be thrown"

def test_invalid_provider_validation():
    try:
        get_default_provider(provider_name="invalid-provider")
    except Exception as e:
        assert True, f"An exception should be thrown: {e}"
    else:
        assert False, "An exception should be thrown"

def test_invalid_api_url():
    invalid_urls = ['invalid-url', 'ftp://invalid-url', 'localhost:8000']
    for invalid_url in invalid_urls:
        try:
            print(f"Testing invalid URL: {invalid_url}")
            get_default_provider(api_url=invalid_url)
        except Exception as e:
            assert True, f"An exception should be thrown for {invalid_url}: {e}"
        else:
            assert False, "An exception should be thrown"