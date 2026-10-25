from core.identity import NovaIdentity


def test_nova_starts_with_zero_money():
    nova = NovaIdentity()

    assert nova.name == "NOVA"
    assert nova.balance == 0.0
    assert nova.owner_funding == 0.0
    assert nova.life_day == 1