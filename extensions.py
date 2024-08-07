from maltego_trx.decorator_registry import TransformRegistry
from settings import api_key_setting

registry = TransformRegistry(
    owner="Spur Intelligence Corp",
    author="Jack <jack@spur.us>",
    host_url="https://spurintelligence.github.io",
    seed_ids=["context"]
)

registry.global_settings = [api_key_setting]

registry.version = "0.3"

registry.display_name_suffix = " [Spur Intelligence]"