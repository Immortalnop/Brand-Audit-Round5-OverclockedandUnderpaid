"""Shared JSON-LD normalization for raw and immutable acquisition artifacts."""
from collections.abc import Mapping

# The Organization types that name the site's own organization wherever they
# appear (the set identity resolution has always used).
CORE_ORGANIZATION_TYPES = frozenset({"Organization", "Corporation", "LocalBusiness", "OnlineStore", "NGO",
                                     "EducationalOrganization", "GovernmentOrganization"})
# schema.org LocalBusiness and its common subtypes: a business with a physical
# place or service area.
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
# Organization and its common subtypes. A Plumber or a CollegeOrUniversity is an
# Organization; on the home page such a node names the site's own organization.
# Elsewhere a subtype may be a listing (a directory of restaurants), so identity
# resolution only trusts subtypes on the home page.
ORGANIZATION_TYPES = frozenset({
    "Organization", "Corporation", "OnlineStore", "OnlineBusiness", "NGO", "EducationalOrganization",
    "CollegeOrUniversity", "School", "HighSchool", "MiddleSchool", "ElementarySchool", "Preschool",
    "GovernmentOrganization", "NewsMediaOrganization", "MedicalOrganization", "SportsOrganization", "SportsTeam",
    "PerformingGroup", "Airline", "Consortium", "LibrarySystem", "ResearchOrganization", "WorkersUnion",
    "Cooperative",
}) | LOCAL_BUSINESS_TYPES

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
