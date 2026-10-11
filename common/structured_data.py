"""Shared JSON-LD normalization for raw and immutable acquisition artifacts."""
from collections.abc import Mapping

# schema.org LocalBusiness and its common subtypes: a business with a physical
# place or service area, for which Google requires an address.
LOCAL_BUSINESS_TYPES = frozenset({
    "LocalBusiness", "Restaurant", "Store", "Hotel", "LodgingBusiness", "FoodEstablishment", "MedicalBusiness",
    "Dentist", "AutoDealer", "AutoRepair", "HealthAndBeautyBusiness", "HomeAndConstructionBusiness",
    "ProfessionalService", "LegalService", "Attorney", "RealEstateAgent", "SportsActivityLocation", "TravelAgency",
    "FinancialService", "EntertainmentBusiness", "CafeOrCoffeeShop", "Bakery", "BarOrPub", "ChildCare",
    "DryCleaningOrLaundry", "EmergencyService", "EmploymentAgency", "GovernmentOffice", "InsuranceAgency",
    "Library", "Physician", "Pharmacy", "Optician", "Plumber", "Electrician", "HairSalon", "BeautySalon",
    "DaySpa", "ExerciseGym", "HealthClub", "ClothingStore", "GroceryStore", "HardwareStore", "FurnitureStore",
    "ElectronicsStore", "BookStore", "AutomotiveBusiness", "VeterinaryCare", "Hospital", "MedicalClinic",
})
# Properties that state where an organization is or which area it serves.
LOCATION_PROPERTIES = ("address", "geo", "areaServed", "serviceArea", "location", "hasMap")
LOCATION_TYPES = frozenset({"PostalAddress", "GeoCoordinates", "GeoShape", "Place", "City", "State", "Country",
                            "AdministrativeArea"})


def normalize_type(value):
    return value.strip().rsplit('/', 1)[-1].rsplit('#', 1)[-1].rsplit(':', 1)[-1] if isinstance(value, str) else ''

def types_of(node):
    value = node.get('@type', ())
    return {normalize_type(v) for v in (value if isinstance(value, (list, tuple)) else [value]) if isinstance(v, str)}

def iter_nodes(value, depth=0):
    # JSON is bounded at acquisition; cap nesting too, including synthetic inputs.
    if depth > 40:
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from iter_nodes(item, depth + 1)
    elif isinstance(value, Mapping):
        if '@type' in value:
            yield value
        for key, child in value.items():
            if key != '@context' and isinstance(child, (Mapping, list, tuple)):
                yield from iter_nodes(child, depth + 1)
