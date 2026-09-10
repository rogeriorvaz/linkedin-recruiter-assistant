"""Connection message generation."""


def create_connection_message(name: str) -> str:
    first_name = (name or "there").split()[0]

    return (
        f"Hi {first_name}, I’m currently exploring senior technology "
        f"delivery opportunities and noticed you specialise in technology "
        f"recruitment. I have 20+ years’ experience across software delivery, "
        f"Agile, Waterfall, Hybrid delivery and technical leadership. "
        f"I’d be glad to connect."
    )
