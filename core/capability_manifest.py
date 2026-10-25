from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityManifest:
    read_only_research: bool = True
    sandbox_mutation: bool = True
    real_world_user_interaction: bool = False
    production_filesystem_write: bool = False
    financial_accounts: bool = False
    payments: bool = False
    external_apis: bool = False
    browser: bool = False

    def to_dict(self) -> dict:
        return {
            "read_only_research": self.read_only_research,
            "sandbox_mutation": self.sandbox_mutation,
            "real_world_user_interaction": self.real_world_user_interaction,
            "production_filesystem_write": self.production_filesystem_write,
            "financial_accounts": self.financial_accounts,
            "payments": self.payments,
            "external_apis": self.external_apis,
            "browser": self.browser,
        }

    def available(self, capability: str) -> bool:
        values = self.to_dict()
        return bool(values.get(capability, False))

    def unavailable(self) -> tuple[str, ...]:
        return tuple(
            name for name, enabled in self.to_dict().items() if not enabled
        )
