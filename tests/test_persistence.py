from core.identity import NovaIdentity
from database.identity_repository import load_identity, save_identity
from database.schema import initialize_database

def test_identity_can_be_saved_and_loaded():
    initialize_database()
    original = NovaIdentity()
    save_identity(original)
    loaded = load_identity()
    assert loaded is not None
    assert loaded.name == "NOVA"
    assert loaded.version == "0.1.0"
    assert loaded.life_day == 1
    assert loaded.balance == 0.0
    assert loaded.owner_funding == 0.0