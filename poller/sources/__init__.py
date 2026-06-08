"""Adaptrar för källplattformar (all-in-one aggregator).

Varje svensk bostadsplattform — en separat adapter `SourceAdapter` som isolerar
hämtning och normalisering av data (BE-DE-005). Pollern går igenom alla aktiverade adaptrar
från registret och normaliserar annonser till en enhetlig modell `shared.models.Listing`.

⚠️ Innan en adapter aktiveras i prod — kontrollera plattformens ToS/robots.txt (COMPLIANCE.md).
"""

# Import av konkreta adaptrar registrerar dem i registret (@register körs vid import).
# När du lägger till en plattform — komplettera dess modul här så att poller.main ser adaptern.
from poller.sources import homeq, qasa, samtrygg  # noqa: E402,F401
from poller.sources.base import SourceAdapter
from poller.sources.registry import enabled_adapters, register

__all__ = ["SourceAdapter", "register", "enabled_adapters"]
