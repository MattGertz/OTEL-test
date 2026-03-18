import "@typespec/http";
import "@typespec/rest";

using TypeSpec.Http;
using TypeSpec.Rest;

@service({
  title: "Nearest City Service",
})
@server("https://api.example.com", "Nearest City API")
namespace NearestCityService;

model GpsCoordinate {
  /** Latitude in decimal degrees (-90 to 90). */
  latitude: float64;

  /** Longitude in decimal degrees (-180 to 180). */
  longitude: float64;
}

model City {
  /** City name. */
  name: string;

  /** Country the city belongs to. */
  country: string;

  /** City population. */
  population: int64;

  /** Distance from the queried coordinate in kilometers. */
  distanceKm: float64;

  /** City center latitude. */
  latitude: float64;

  /** City center longitude. */
  longitude: float64;
}

model NearestCityRequest {
  /** Latitude of the query point. */
  latitude: float64;

  /** Longitude of the query point. */
  longitude: float64;

  /** Minimum population threshold. Only cities with this population or greater are considered. */
  @query minPopulation: int64;
}

@error
model ErrorResponse {
  code: int32;
  message: string;
}

@route("/nearest-city")
@tag("NearestCity")
interface NearestCity {
  /** Find the nearest city to the given GPS coordinate with at least the specified population. */
  @get find(
    @query latitude: float64,
    @query longitude: float64,
    @query minPopulation: int64,
  ): City | ErrorResponse;
}
