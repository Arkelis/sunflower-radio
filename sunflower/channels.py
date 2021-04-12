# This file is part of sunflower package. Radio app.

"""Module containing radio metadata fetching related functions."""

from sunflower.core.channel import Channel
from sunflower.core.persistence import RedisRepository
from sunflower.handlers import AdsHandler
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique
from sunflower.stations import PycolorePlaylistStation
from sunflower.stations import RTL2


# instantiate repository
redis_repository = RedisRepository()

# instantiate stations
france_culture = FranceCulture()
france_info = FranceInfo()
france_inter = FranceInter()
france_musique = FranceMusique()
fip = FranceInterParis()
rtl2 = RTL2()

radio_pycolore = PycolorePlaylistStation(redis_repository)

# define channels
tournesol = Channel(
    id="tournesol",
    repository=redis_repository,
    timetable_dict={
        # (weekday1, weekday2, ...)
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "05:00", france_culture), # Les nuits de France Culture
            ("05:00", "10:00", france_inter), # Matinale, Boomerang, l'instant M
            ("10:00", "12:00", france_culture), # Les chemins de la philosophie, Culture monde
            ("12:00", "12:30", france_info), # Info
            ("12:30", "13:30", france_inter), # Carnets de campagne, Jeu des mille, Journal
            ("13:30", "18:00", france_culture), # Les pieds sur terre, Entendez vous l'éco, compagnie des oeuvres, la méthode scientifique, LSD (La série documentaire)
            ("18:00", "20:00", france_inter), # Le 18/20 de France Inter
            ("20:00", "00:00", france_info), # Les informés, info
        ],
        (5,): [
            ("00:00", "06:00", france_culture), # Les nuits de France Culture
            ("06:00", "09:00", france_inter), # Matinale
            ("09:00", "11:00", france_info), # Info
            ("11:00", "12:00", france_culture), # Affaires étrangères
            ("12:00", "14:00", france_inter), # Le grand face à face
            ("14:00", "17:00", france_culture), # Plan large, Toute une vie, La Conversation scientifique
            ("17:00", "18:00", france_inter), # La preuve par Z
            ("18:00", "19:00", france_culture), # Débat
            ("19:00", "21:00", france_info), # Les informés
            ("21:00", "00:00", france_culture), # Soirée Culture (Fiction, Mauvais Genre, rediff Toute une vie)
        ],
        (6,): [
            ("00:00", "07:00", france_culture), # Les nuits de France Culture
            ("07:00", "09:00", france_musique), # Bach
            ("09:00", "10:00", france_inter), # Interception
            ("10:00", "11:00", france_info),
            ("11:00", "14:00", france_inter), # On va déguster, politique, journal
            ("14:00", "18:00", france_musique), # Aprem Musique
            ("18:00", "19:00", france_info), # Le masque et la plume
            ("19:00", "22:00", france_inter), # Le masque et la plume, Autant en emporte l'histoire
            ("22:00", "00:00", fip),
        ]
    },
)

music = Channel(
    "musique",
    redis_repository,
    handlers=(AdsHandler,),
    timetable_dict={
        (0, 1, 2, 3,): [
            ("00:00", "06:00", fip),
            ("06:00", "09:00", rtl2),
            ("09:00", "12:00", radio_pycolore),
            ("12:00", "13:30", rtl2),
            ("13:30", "18:00", fip),
            ("18:00", "22:00", rtl2),
            ("22:00", "00:00", radio_pycolore)],
        (4,): [
            ("00:00", "06:00", fip),
            ("06:00", "09:00", rtl2),
            ("09:00", "12:00", radio_pycolore),
            ("12:00", "13:30", rtl2),
            ("13:30", "18:00", fip),
            ("18:00", "22:00", rtl2),
            ("22:00", "01:00", radio_pycolore)],
        (5,): [
            ("00:00", "01:00", radio_pycolore),
            ("01:00", "06:00", fip),
            ("06:00", "09:00", rtl2),
            ("09:00", "12:00", radio_pycolore),
            ("12:00", "13:30", rtl2),
            ("13:30", "18:00", fip),
            ("18:00", "22:00", rtl2),
            ("22:00", "01:00", radio_pycolore)],
        (6,): [
            ("00:00", "01:00", radio_pycolore),
            ("01:00", "06:00", fip),
            ("06:00", "09:00", rtl2),
            ("09:00", "12:00", radio_pycolore),
            ("12:00", "13:30", rtl2),
            ("13:30", "22:00", fip),
            ("22:00", "00:00", radio_pycolore)]})

