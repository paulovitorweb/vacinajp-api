from datetime import datetime


def get_fake_vaccination_sites():
    return [
        {
            "name": "Winford Henry",
            "address": {
                "street_name": "Rua Santa Luzia",
                "street_number": 701,
                "neighborhood": "Cristo Redentor",
            },
            "geo": {"type": "Point", "coordinates": [-168.45211, -42.683829]},
        },
        {
            "name": "Waldo Hawkins",
            "address": {
                "street_name": "Rua Sao Francisco",
                "street_number": 67,
                "neighborhood": "Cristo Redentor",
            },
            "geo": {"type": "Point", "coordinates": [-117.15525, 75.224872]},
        },
        {
            "name": "Marvin Ford",
            "address": {
                "street_name": "Rua Virgílio do Nascimento",
                "street_number": 811,
                "neighborhood": "Cristo Redentor",
            },
            "geo": {"type": "Point", "coordinates": [-174.083812, 5.388554]},
        },
    ]


def get_fake_calendar(vaccination_sites_ids):
    return [
        {
            "date": datetime(2022, 8, 1),
            "vaccination_site": vaccination_sites_ids[0],
            "total_schedules": 100,
            "remaining_schedules": 100,
            "is_available": True,
            "applied_vaccines": 0,
        },
        {
            "date": datetime(2022, 8, 1),
            "vaccination_site": vaccination_sites_ids[1],
            "total_schedules": 100,
            "remaining_schedules": 100,
            "is_available": True,
            "applied_vaccines": 0,
        },
        {
            "date": datetime(2022, 8, 1),
            "vaccination_site": vaccination_sites_ids[2],
            "total_schedules": 100,
            "remaining_schedules": 100,
            "is_available": True,
            "applied_vaccines": 0,
        },
    ]
