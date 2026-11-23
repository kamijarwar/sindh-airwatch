from place_search import search_places_in_sindh

NAMES = [
    "Saddar", "DHA", "Clifton", "Gulshan-e-Iqbal", "Gulistan-e-Johar",
    "Korangi", "Malir", "Lyari", "Orangi Town", "Nazimabad",
    "North Nazimabad", "Landhi", "Keamari", "Scheme 33", "PECHS",
    "Tariq Road", "Baldia Town", "Surjani Town", "Hyderabad City", "Sanghar",
]

print(f"{'Naam':<22} | {'Mila?':<6} | Pehla result")
print("-" * 80)

for q in NAMES:
    places = search_places_in_sindh(q)
    if places:
        p = places[0]
        print(f"{q:<22} | {'Haan':<6} | {p['name']} ({p['district']}) {p['lat']}, {p['lon']}")
    else:
        print(f"{q:<22} | {'Nahi':<6} | ---")