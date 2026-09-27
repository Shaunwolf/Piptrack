"""Pluggable data sources. Each returns a SourceResult with an explicit status."""

from .prices import YahooPrices, PolygonPrices
from .filings import SecEdgarFilings
from .news import PolygonNews, GdeltNews
from .social import PullpushReddit


def default_price_sources(settings):
    """Polygon first when a key is set (it keeps delisted tickers), Yahoo as fallback"""
    sources = []
    if settings.polygon_api_key:
        sources.append(PolygonPrices(settings))
    sources.append(YahooPrices(settings))
    return sources


def default_context_sources(settings):
    """Sources describing what happened around the stock in the pre-pump window"""
    return [
        SecEdgarFilings(settings),
        PolygonNews(settings),
        GdeltNews(settings),
        PullpushReddit(settings),
    ]
