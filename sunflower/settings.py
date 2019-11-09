TIMETABLE = [
    # (start, end, station_name),
    ("00:00", "06:00", "RTL 2"),
    ("06:00", "07:00", "France Info"),
    ("07:00", "09:00", "France Inter"),
    ("09:00", "13:00", "RTL 2"),
    ("13:00", "14:00", "France Inter"),
    ("14:00", "19:00", "RTL 2"),
    ("19:00", "20:00", "France Inter"),
    ("20:00", "21:00", "France Info"),
    ("21:00", "00:00", "RTL 2"),
]

FLUX_URL = "https://icecast.pycolore.fr/tournesol"

BACKUP_SONGS = [ # In case of ads.
    # (path/url, artist, title, length in sec)
    ("~/radio/songs/calogero-en-apesanteur.ogg", "Calogero", "En apesanteur", 203), 
    ("~/radio/songs/calogero-musique.ogg", "Calogero", "Je joue de la musique", 240), 
    ("~/radio/songs/calogero-fondamental.ogg", "Calogero", "Fondamental", 184), 
    ("~/radio/songs/fre-gol-jon-juste-apres.ogg", "Fredericks Goldman Jones", "Juste après", 277), 
    ("~/radio/songs/goldman-signe.ogg", "Jean-Jacques Goldman", "Il suffira d'un signe (live)", 265), 
    ("~/radio/songs/cdp-combustible.ogg", "Coeur de Pirate", "Combustible", 226), 
    ("~/radio/songs/muse-madness.ogg", "Muse", "Madness", 281), 
]
