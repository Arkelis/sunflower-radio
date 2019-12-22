TIMETABLE = {
    # (weekday1, weekday2, ...)
    (0, 1, 2, 3, 4): [
        # (start, end, station_name),
        ("00:00", "06:00", "RTL 2"),
        ("06:00", "07:00", "France Info"),
        ("07:00", "09:00", "France Inter"),
        ("09:00", "12:30", "RTL 2"),
        ("12:30", "14:30", "France Inter"),
        ("14:30", "18:00", "RTL 2"),
        ("18:00", "20:00", "France Inter"),
        ("20:00", "21:00", "France Info"),
        ("21:00", "00:00", "RTL 2"),
    ],
    (5,): [
        ("00:00", "06:00", "RTL 2"),
        ("06:00", "07:00", "France Info"),
        ("07:00", "09:00", "France Inter"),
        ("09:00", "13:00", "RTL 2"),
        ("13:00", "14:00", "France Inter"),
        ("14:00", "16:00", "RTL 2"),
        ("16:00", "17:00", "France Culture"),
        ("17:00", "20:00", "RTL 2"),
        ("20:00", "21:00", "France Info"),
        ("21:00", "00:00", "RTL 2"),
    ],
    (6,): [
        ("00:00", "06:00", "RTL 2"),
        ("06:00", "07:00", "France Info"),
        ("07:00", "09:00", "France Inter"),
        ("09:00", "13:00", "RTL 2"),
        ("13:00", "14:00", "France Inter"),
        ("14:00", "16:00", "RTL 2"),
        ("16:00", "17:00", "France Culture"),
        ("17:00", "20:00", "RTL 2"),
        ("20:00", "21:00", "France Info"),
        ("21:00", "00:00", "RTL 2"),    
    ]
}

FLUX_URL = "https://icecast.pycolore.fr/tournesol"

BACKUP_SONGS_GLOB_PATTERN = "/home/guillaume/radio/songs/*.ogg"
