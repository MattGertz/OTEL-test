"""Client for the Nearest City Service."""

from __future__ import annotations

import urllib.parse
import urllib.request
import json
from typing import Optional

from .models import City, ErrorResponse
from .exceptions import NearestCityServiceError


class NearestCityClient:
    """Client for the Nearest City Service.

    Args:
        base_url: Base URL of the service. Defaults to ``https://api.example.com``.
    """

    def __init__(self, base_url: str = "https://api.example.com") -> None:
        self._base_url = base_url.rstrip("/")

    def find_nearest_city(
        self,
        latitude: float,
        longitude: float,
        min_population: int,
    ) -> City:
        """Find the nearest city to a GPS coordinate with at least the given population.

        Args:
            latitude: Latitude in decimal degrees (-90 to 90).
            longitude: Longitude in decimal degrees (-180 to 180).
            min_population: Minimum population threshold.

        Returns:
            The nearest ``City`` meeting the population criteria.

        Raises:
            NearestCityServiceError: If the service returns an error response.
        """
        params = urllib.parse.urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "minPopulation": min_population,
        })
        url = f"{self._base_url}/nearest-city?{params}"

        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")

        with urllib.request.urlopen(req) as resp:  # noqa: S310
            body = json.loads(resp.read().decode())

        # If the response contains an error shape, raise
        if "code" in body and "message" in body and "name" not in body:
            error = ErrorResponse(code=body["code"], message=body["message"])
            raise NearestCityServiceError(error)

        return City(
            name=body["name"],
            country=body["country"],
            population=body["population"],
            distance_km=body["distanceKm"],
            latitude=body["latitude"],
            longitude=body["longitude"],
        )
