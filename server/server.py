import asyncio
from typing import List

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyHttpUrl
from pydantic.dataclasses import dataclass as pydantic_dataclass
from starlette.requests import Request
from starlette.responses import StreamingResponse

from server.proxies import PycoloreStationProxy
from server.utils import get_channel_or_404
from sunflower import settings
from sunflower.core.custom_types import NotifyChangeStatus, Step
from sunflower.settings import RADIO_NAME

app = FastAPI(title=RADIO_NAME, docs_url="/", redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# models

# This dataclass represents a real Channel object in the API
@pydantic_dataclass
class Channel:
    endpoint: str
    name: str
    audio_stream: AnyHttpUrl
    current_step: AnyHttpUrl
    next_step: AnyHttpUrl
    schedule: AnyHttpUrl

#
# @app.get("/", summary="API root", response_description="Redirect to channels lists.", tags=["general"])
# def api_root(request: Request):
#     """Redirect to channels lists."""
#     return RedirectResponse(request.url_for("channels_list"))


@app.get("/channels/", tags=["Channels-related endpoints"], summary="Channels list", response_description="List of channels URLs.")
def channels_list(request: Request):
    """Get the list of the channels: their endpoints and a link to their resource."""
    return {endpoint: request.url_for("get_channel", channel=endpoint)
            for endpoint in settings.CHANNELS}


# @app.get("/stations/", tags=["stations"], summary="Stations list", response_description="List of stations URLs.")
# def stations_list(request: Request):
#     return {endpoint: request.url_for("get_station", station=endpoint)
#             for endpoint in settings.STATIONS}


@app.get(
    "/channels/{channel}/",
    summary="Channel information",
    response_description="Channel information and related links",
    response_model=Channel,
    tags=["Channels-related endpoints"]
)
@get_channel_or_404
def get_channel(channel, request: Request):
    """Display information about one channel :

    - its endpoint
    - its name
    - the url to the current broadcast
    - the url to the next broadcast to be on air
    - the url to the schedule of this channel

    One path parameter is needed: the endpoint of the channel. URLs to all channels are given at /channels/ endpoint.
    """
    return {
        "endpoint": channel.endpoint,
        "name": channel.endpoint.capitalize(),
        "audio_stream": settings.ICECAST_SERVER_URL + channel.endpoint,
        "current_step": request.url_for("get_current_broadcast_of", channel=channel.endpoint),
        "next_step": request.url_for("get_next_broadcast_of", channel=channel.endpoint),
        "schedule": request.url_for("get_schedule_of", channel=channel.endpoint),
    }


# @app.get("/stations/{station}/", response_model=Station, tags=["stations"])
# @get_station_or_404
# def get_station(station):
#     return {
#         "endpoint": station.endpoint,
#         "name": station.name,
#     }


async def updates_generator(endpoint):
    pubsub = redis.Redis().pubsub()
    pubsub.subscribe("sunflower:channel:" + endpoint)
    while True:
        await asyncio.sleep(4)
        message = pubsub.get_message()
        if message is None:
            continue
        redis_data = message.get("data")
        data_to_send = {
            str(NotifyChangeStatus.UNCHANGED.value).encode(): "unchanged",
            str(NotifyChangeStatus.UPDATED.value).encode(): "updated"
        }.get(redis_data)
        if data_to_send is None:
            continue
        yield f"data: {data_to_send}\n\n"


@app.get("/channels/{channel}/events/", include_in_schema=False)
async def update_broadcast_info_stream(channel):
    return StreamingResponse(updates_generator(channel.endpoint), media_type="text/event-stream")


@app.get(
    "/channels/{channel}/current/",
    summary="Get current broadcast",
    tags=["Channels-related endpoints"],
    response_model=Step,
    response_description="Information about current broadcast"
)
# @get_channel_or_404
def get_current_broadcast_of(channel):
    """Get information about current broadcast on given channel"""
    return {"start":1595243714,"end":1595243940,"broadcast":{"title":"Le journal de 13h du lundi 20 juillet 2020","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is2-ssl.mzstatic.com/image/thumb/Podcasts124/v4/5c/02/ba/5c02ba72-c182-fd14-d644-cf574e7a7a7e/mza_16729882287712886319.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-journal-de-13h/le-journal-de-13h-20-juillet-2020","show_title":"Le journal de 13h","show_link":"https://www.franceinter.fr/emissions/le-journal-de-13h","summary":"","parent_show_title":"","parent_show_link":""}}


@app.get(
    "/channels/{channel}/next/",
    summary="Get next broadcast",
    tags=["Channels-related endpoints"],
    response_model=Step,
    response_description="Information about next broadcast"
)
# @get_channel_or_404
def get_next_broadcast_of(channel):
    """Get information about next broadcast on given channel"""
    return {"start":1595243940,"end":1595246310,"broadcast":{"title":"Jardiner en ville pour célébrer le vivant avec Thibaut Schepman","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/c8/1b/b3/c81bb38b-4059-6df3-1ca9-8b630004b188/mza_9352372465917026676.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/chacun-sa-route/chacun-sa-route-20-juillet-2020-0","show_title":"Chacun sa route","show_link":"https://www.franceinter.fr/emissions/chacun-sa-route","summary":"Il plante, il sème, il bêche et il récolte les bonnes idées de jardinage avec son récent ouvrage \"Jardinier urbain. 50 leçons de jardinage facile et ludique pour les citadins\" paru aux éditions Marabout. Le journaliste Thibaut Schepman nous offre tous ses conseils les plus pratiques au micro de \"Chacun sa route\".","parent_show_title":"","parent_show_link":""}}


@app.get(
    "/channels/{channel}/schedule/",
    summary="Get schedule of given channel",
    tags=["Channels-related endpoints"],
    response_model=List[Step],
    response_description="List of steps containing start and end timestamps, and broadcasts"
)
# @get_channel_or_404
def get_schedule_of(channel):
    """Get information about next broadcast on given channel"""
    return [{"start":1595196000,"end":1595214000,"broadcast":{"title":"Clap sur Eric Rohmer (1ère diffusion : 24/01/1973)","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://is2-ssl.mzstatic.com/image/thumb/Podcasts113/v4/07/df/fe/07dffe74-92db-448e-927a-878c94469dc7/mza_7690330889498434663.jpg/626x0w.jpg","link":"https://www.franceculture.fr/emissions/les-nuits-de-france-culture/clap-sur-eric-rohmer-1ere-diffusion-24011973","show_title":"Les Nuits de France Culture","show_link":"https://www.franceculture.fr/emissions/les-nuits-de-france-culture","summary":"","parent_show_title":"","parent_show_link":""}},{"start":1595217600,"end":1595228400,"broadcast":{"title":"Nathan Law - Amélie de Montchalin","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is4-ssl.mzstatic.com/image/thumb/Podcasts114/v4/2b/0a/1a/2b0a1aac-2844-0b22-d159-a1e67b475218/mza_1238233570775343260.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-6-9/le-6-9-20-juillet-2020","show_title":"Le 6/9","show_link":"https://www.franceinter.fr/emissions/le-6-9","summary":"","parent_show_title":"","parent_show_link":""}},{"start":1595228400,"end":1595228820,"broadcast":{"title":"JOURNAL DE 9H du lundi 20 juillet 2020","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://is5-ssl.mzstatic.com/image/thumb/Podcasts123/v4/0b/5a/06/0b5a062e-e093-b84b-6bba-67629871b17f/mza_7334404193089595851.jpg/626x0w.jpg","link":"https://www.franceculture.fr/emissions/journal-de-9h/journal-de-9h-du-lundi-20-juillet-2020","show_title":"Journal de 9h","show_link":"https://www.franceculture.fr/emissions/journal-de-9h","summary":"","parent_show_title":"","parent_show_link":""}},{"start":1595228820,"end":1595235473,"broadcast":{"title":"Sous les drapeaux rouges","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg","link":"https://www.franceculture.fr/emissions/grandes-traversees-karl-marx-linconnu/sous-les-drapeaux-rouges","show_title":"Grandes traversées : Karl Marx, l'inconnu","show_link":"https://www.franceculture.fr/emissions/karl-marx-linconnu-grandes-traversees","summary":"Pour les uns, il était le grand prophète. Pour les autres, il incarnait le mal absolu. Durant tout le XXe siècle, Marx et sa pensée sont déformés, caricaturés, puis oubliés pour devenir totalement méconnaissables.Traversée d'un siècle de marxismes sans Marx.","parent_show_title":"","parent_show_link":""}},{"start":1595235473,"end":1595239125,"broadcast":{"title":"Lettres de Russie (1/5) : Nicolas Gogol, le rire au bord de l’abîme (1809-1852)","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://is5-ssl.mzstatic.com/image/thumb/Podcasts123/v4/de/0c/1a/de0c1adf-8082-872c-02de-e8ae5640d0b9/mza_5489966496141001214.jpg/626x0w.jpg","link":"https://www.franceculture.fr/emissions/une-vie-une-oeuvre/lettres-de-russie-15-nicolas-gogol-le-rire-au-bord-de-labime-1809-1852","show_title":"Une vie, une oeuvre","show_link":"https://www.franceculture.fr/emissions/une-vie-une-oeuvre","summary":"Nicolas Gogol devient l’une des figures principales de l’Âge d’or de la littérature russe. Son plus grand succès est sa pièce le Révizor, où le spectacle de la corruption de tous provoque un rire ravageur.","parent_show_title":"","parent_show_link":""}},{"start":1595239200,"end":1595242680,"broadcast":{"title":"Faut-il arrêter de consommer ?","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is5-ssl.mzstatic.com/image/thumb/Podcasts123/v4/57/07/16/5707162c-d233-07a8-400c-e2fa4c9c8b0e/mza_491619198573183598.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-debat-de-midi/le-debat-de-midi-20-juillet-2020","show_title":"Le débat de midi","show_link":"https://www.franceinter.fr/emissions/le-debat-de-midi","summary":"Les soldes ont commencé, mais certains prônent la sobriété pour préserver la planète, pendant que d’autres appellent à relancer l’économie après le confinement. Alors faut-il arrêter de consommer ?","parent_show_title":"","parent_show_link":""}},{"start":1595242680,"end":1595243940,"broadcast":{"title":"Le journal de 13h du lundi 20 juillet 2020","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is2-ssl.mzstatic.com/image/thumb/Podcasts124/v4/5c/02/ba/5c02ba72-c182-fd14-d644-cf574e7a7a7e/mza_16729882287712886319.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-journal-de-13h/le-journal-de-13h-20-juillet-2020","show_title":"Le journal de 13h","show_link":"https://www.franceinter.fr/emissions/le-journal-de-13h","summary":"","parent_show_title":"","parent_show_link":""}},{"start":1595243940,"end":1595246310,"broadcast":{"title":"Jardiner en ville pour célébrer le vivant avec Thibaut Schepman","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/c8/1b/b3/c81bb38b-4059-6df3-1ca9-8b630004b188/mza_9352372465917026676.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/chacun-sa-route/chacun-sa-route-20-juillet-2020-0","show_title":"Chacun sa route","show_link":"https://www.franceinter.fr/emissions/chacun-sa-route","summary":"Il plante, il sème, il bêche et il récolte les bonnes idées de jardinage avec son récent ouvrage \"Jardinier urbain. 50 leçons de jardinage facile et ludique pour les citadins\" paru aux éditions Marabout. Le journaliste Thibaut Schepman nous offre tous ses conseils les plus pratiques au micro de \"Chacun sa route\".","parent_show_title":"","parent_show_link":""}},{"start":1595246400,"end":1595248105,"broadcast":{"title":"Le journal de Mohammed et Yi — Episode 1","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://is4-ssl.mzstatic.com/image/thumb/Podcasts123/v4/f2/91/ae/f291ae99-d8b9-cfc6-0dda-dcbce57a6576/mza_8620950480202799483.jpg/626x0w.jpg","link":"https://www.franceculture.fr/emissions/les-pieds-sur-terre/le-journal-de-mohammed-et-yi-episode-1","show_title":"Les Pieds sur terre","show_link":"https://www.franceculture.fr/emissions/les-pieds-sur-terre","summary":"Retour en forme de résumé des aventures de Mohammed et Yi, collégiens parisiens, diffusées entre décembre 2007 et mars 2008.","parent_show_title":"","parent_show_link":""}},{"start":1595248105,"end":1595249970,"broadcast":{"title":"Episode 16 : Un professeur survient à jeun qui cherchait aventure","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://is1-ssl.mzstatic.com/image/thumb/Podcasts123/v4/fa/d6/4a/fad64a70-dfd3-1f47-b650-56e07c7008e5/mza_703137802690338954.jpg/626x0w.jpg","link":"https://www.franceculture.fr/emissions/le-mystere-de-la-chambre-jaune/episode-16-un-professeur-survient-a-jeun-qui-cherchait-aventure","show_title":"Le Mystère de la chambre jaune","show_link":"https://www.franceculture.fr/emissions/le-mystere-de-la-chambre-jaune","summary":"Joseph Rouletabille et son ami Sainclair déjeunent à l'auberge du Donjon. Le professeur Arthur Rance, un savant américain en visite au château, se joint à eux.","parent_show_title":"","parent_show_link":""}},{"start":1595249970,"end":1595253525,"broadcast":{"title":"LA SERIE MUSICALE D'ETE du lundi 20 juillet 2020","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg","link":None,"show_title":"","show_link":"","summary":"","parent_show_title":"","parent_show_link":""}},{"start":1595253525,"end":1595257140,"broadcast":{"title":"Ahmadou Kourouma (1/4) : Kourouma crie sa colère","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://is5-ssl.mzstatic.com/image/thumb/Podcasts123/v4/f5/12/ac/f512acb5-3b36-0371-dffb-f8d63f6a8b24/mza_1389006842978961138.jpg/626x0w.jpg","link":"https://www.franceculture.fr/emissions/la-compagnie-des-oeuvres/ahmadou-kourouma-14-kourouma-crie-sa-colere","show_title":"La Compagnie des oeuvres","show_link":"https://www.franceculture.fr/emissions/la-compagnie-des-auteurs","summary":"Un écrivain engagé, un griot qui passe à l'écrit, Ahmadou Kourouma né en 1927 et mort en 2003, créa un rythme mêlant le malinké et le français, en même temps qu'il fit la critique de la situation politique de nombreux pays d'Afrique. Retour sur sa vie, entre la Côte d'Ivoire et la France.","parent_show_title":"","parent_show_link":""}},{"start":1595257140,"end":1595260440,"broadcast":{"title":"Faites du sport (1/4) : Des guerriers aux sportifs","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://is3-ssl.mzstatic.com/image/thumb/Podcasts123/v4/79/e0/3f/79e03f73-fe1e-2b88-25d6-a058010ba3ad/mza_6686782322002684811.jpg/626x0w.jpg","link":"https://www.franceculture.fr/emissions/lsd-la-serie-documentaire/faites-du-sport-14-des-guerriers-aux-sportifs-0","show_title":"LSD, La série documentaire","show_link":"https://www.franceculture.fr/emissions/lsd-la-serie-documentaire","summary":"\"Sport civil, d’élite, de masse, scolaire, militaire, amateur, professionnel, sport extrême ou de loisir, de bien être ou de santé… je crois que chacun met dans le vocable \"sport\", ce qu’il veut bien entendre\" Juliette Boutillier","parent_show_title":"","parent_show_link":""}},{"start":1595260440,"end":1595260655,"broadcast":{"title":"Le manchot empereur","type":"Programme","station":{"name":"France Culture","website":"https://www.franceculture.fr"},"thumbnail_src":"https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg","link":"https://www.franceculture.fr/emissions/pas-si-betes-la-chronique-du-monde-sonore-animal/manchot-australien","show_title":"Pas si bêtes, la chronique du monde sonore animal","show_link":"https://www.franceculture.fr/emissions/pas-si-betes-la-chronique-du-monde-sonore-animal","summary":"Au milieu d’une colonie de manchots, l’ambiance est assourdissante, 75 décibels, soit l’équivalent du périphérique aux heures de pointe. Les manchots sont bruyants.","parent_show_title":"","parent_show_link":""}},{"start":1595260800,"end":1595261340,"broadcast":{"title":"Le journal de 18h du lundi 20 juillet 2020","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is1-ssl.mzstatic.com/image/thumb/Podcasts123/v4/f7/66/02/f766029e-e46b-ce2a-a427-801897f768c0/mza_8159779510442728554.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-journal-de-18h/le-journal-de-18h-20-juillet-2020","show_title":"Le journal de 18h","show_link":"https://www.franceinter.fr/emissions/le-journal-de-18h","summary":"","parent_show_title":"","parent_show_link":""}},{"start":1595261340,"end":1595264310,"broadcast":{"title":"Faire fleurir les arts avec William Christie et Paul Agnew","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is5-ssl.mzstatic.com/image/thumb/Podcasts113/v4/6d/fe/69/6dfe693e-7e2e-4a34-8e33-a4291f6aee62/mza_3980971896014801858.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-mag-de-l-ete/le-mag-de-l-ete-20-juillet-2020","show_title":"Le Mag de l'été","show_link":"https://www.franceinter.fr/emissions/le-mag-de-l-ete","summary":"Après Nantes, Le Mag de l'été descend dans le village de Thiré, en Vendée. C'est là que se trouve la demeure du chef d'orchestre franco-américain William Christie, et où l'ensemble de musique baroque Les Arts Florissants qu'il co-dirige avec Paul Agnew se produit chaque année au mois d'août au milieu de ses jardins.","parent_show_title":"","parent_show_link":""}},{"start":1595264310,"end":1595265300,"broadcast":{"title":"Le journal de  19h du lundi 20 juillet 2020","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is2-ssl.mzstatic.com/image/thumb/Podcasts123/v4/b9/67/3d/b9673d6a-f03c-90a6-3c7f-a55b138003fb/mza_8096723723778573630.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-journal-de-19h/le-journal-de-19h-20-juillet-2020","show_title":"Le Journal de 19h","show_link":"https://www.franceinter.fr/emissions/le-journal-de-19h","summary":"","parent_show_title":"","parent_show_link":""}},{"start":1595265300,"end":1595267910,"broadcast":{"title":"Covid-19 : sommes-nous prêt à affronter une seconde vague ?","type":"Programme","station":{"name":"France Inter","website":"https://www.franceinter.fr"},"thumbnail_src":"https://is5-ssl.mzstatic.com/image/thumb/Podcasts113/v4/27/9b/06/279b061e-bb5e-0e20-29a1-d4e92f0e1dbf/mza_930049438934282639.jpg/626x0w.jpg","link":"https://www.franceinter.fr/emissions/le-telephone-sonne/le-telephone-sonne-20-juillet-2020","show_title":"Le Téléphone sonne","show_link":"https://www.franceinter.fr/emissions/le-telephone-sonne","summary":"","parent_show_title":"","parent_show_link":""}}]


# custom endpoints

@app.get(
    "/stations/pycolore/playlist/",
    summary="Get the playlist of Pycolore station",
    tags=["Endpoints specific to Radio Pycolore"],
    response_description="List of songs of the playlist"
)
def get_pycolore_playlist():
    """Get information about next broadcast on given channel"""
    return PycoloreStationProxy().public_playlist

