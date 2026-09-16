"""Print whether hosted embed keys exist. Never print the key."""

from semantic_afterlife.config import get_settings


def main() -> None:
    settings = get_settings()
    print(f"routerai_key={settings.has_key('routerai')}")
    print(f"openrouter_key={settings.has_key('openrouter')}")
    print(f"budget_total={settings.afterlife_budget_usd_total}")
    print(f"budget_per_run={settings.afterlife_budget_usd_per_run}")


if __name__ == "__main__":
    main()
