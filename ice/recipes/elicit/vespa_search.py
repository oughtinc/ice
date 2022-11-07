from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from structlog import get_logger
from vespa.application import Vespa
from vespa.application import VespaAsync

from ice.agents.ought_inference import embed
from ice.recipe import recipe
from ice.settings import settings

VESPA_HITS_PER_HNSW_NODE = 400
VESPA_SEARCH_HITS = 400
VESPA_SERVER_SIDE_TIMEOUT_SECONDS = 1

VESPA_DIR = Path("/elicit")
VESPA_CERT_PATH = VESPA_DIR / "vespa_cert.pem"
VESPA_KEY_PATH = VESPA_DIR / "vespa_key.pem"

_VESPA_APP: Optional[Vespa] = None

log = get_logger()


def mount_vespa_cert_and_key():
    VESPA_DIR.mkdir(exist_ok=True)
    VESPA_CERT_PATH.write_text(settings.VESPA_CERT)
    VESPA_KEY_PATH.write_text(settings.VESPA_KEY)


def init_vespa():
    mount_vespa_cert_and_key()

    global _VESPA_APP
    _VESPA_APP = Vespa(
        url=settings.VESPA_ENDPOINT, cert=str(VESPA_CERT_PATH), key=str(VESPA_KEY_PATH)
    )


@asynccontextmanager
async def async_vespa(total_timeout: int = 15) -> AsyncIterator[VespaAsync]:
    if _VESPA_APP is None:
        # defensive: this should be done on app startup
        init_vespa()
        log.warning("Vespa app used before initialization; initialize on app startup")
    assert _VESPA_APP is not None
    async with _VESPA_APP.asyncio(total_timeout=total_timeout) as async_vespa:
        yield async_vespa


async def vespa_search(
    query: str = "What are the effects of creatine on cognition?",
    *,
    num_hits: int = VESPA_SEARCH_HITS,
):

    vector = await embed(query)

    filters = f"{{targetHits: {VESPA_HITS_PER_HNSW_NODE}}}nearestNeighbor(titleAbstractEmbedding, query_embedding)"  # noqa: E501

    yql = f"select * from work where ({filters})"

    body = {
        "hits": num_hits,
        "yql": yql,
        "presentation.timing": False,  # this causes Vespa to return a "timing" field in the response
        "ranking.matching.numThreadsPerSearch": 4,  # num threads used by Vespa content nodes per search (default 1, max 4 -- higher max requires Vespa config change)  # noqa: E501
        "ranking.matching.approximateThreshold": 0.1,  # fraction of estimated hits to fall back to brute force on (default 0.05)  # noqa: E501
        "timeout": VESPA_SERVER_SIDE_TIMEOUT_SECONDS,
        "ranking.features.query(query_embedding)": vector,
        "ranking.profile": "dense",
    }

    async with async_vespa() as vespa:
        response = await vespa.query(body=body)

    return response.json


init_vespa()

recipe.main(vespa_search)

# Example result:
#
# {
#     'root': {
#         'id': 'toplevel',
#         'relevance': 1.0,
#         'fields': {'totalCount': 6400},
#         'coverage': {
#             'coverage': 100,
#             'documents': 122780619,
#             'full': True,
#             'nodes': 16,
#             'results': 1,
#             'resultsFull': 1
#         },
#         'children': [
#             {
#                 'id': 'id:work:work::0e0eef6f40106d5e05ab3241aae87db4784d50d1',
#                 'relevance': 0.8139227057576519,
#                 'source': 'works',
#                 'fields': {
#                     'sddocname': 'work',
#                     'documentid': 'id:work:work::0e0eef6f40106d5e05ab3241aae87db4784d50d1',
#                     'title': 'Creatine in the brain',
#                     'abstract': 'Since the 1990’s, creatine has become one of the most popular supplements in the world for the purpose of increasing skeletal muscle creatine, increasing skeletal muscle mass, and improving the amount of exercise training. The first patient with brain creatine deficiency was reported around the year 2000, and this patient’s severe clinical symptoms such as impairment of brain function drove researchers to start focusing more on the brain and related studies. Both in vitro and in vivo studies have shown creatine in the body to cover a wide range of roles including bioenergetic, anabolic, bone remodeling, anti-oxidant, anti-apoptotic, antiexcitotoxic and neuroprotective. In this short review, we introduce recent findings on the effects of creatine supplementation on brain function closely related to mental health, which directly influences the quality of life of elderly people.',
#                     'publicationYear': 2017,
#                     'doi': '10.7600/JPFSM.6.215',
#                     'magId': 2735962642,
#                     'ssId': '0e0eef6f40106d5e05ab3241aae87db4784d50d1',
#                     'citedByCount': 1,
#                     'authors': [
#                         {'ssId': '6643621', 'name': 'Y. Kurosawa'},
#                         {'ssId': '35657815', 'name': 'T. Hamaoka'}
#                     ],
#                     'id': '0e0eef6f40106d5e05ab3241aae87db4784d50d1'
#                 }
#             },
#             {
#                 'id': 'id:work:work::9c4b06020d14e2644db3c186dbd92656b8704373',
#                 'relevance': 0.7983470652812391,
#                 'source': 'works',
#                 'fields': {
#                     'sddocname': 'work',
#                     'documentid': 'id:work:work::9c4b06020d14e2644db3c186dbd92656b8704373',
#                     'title': 'Creatine as a booster for human brain function. How might it work?',
#                     'abstract': 'Creatine, a naturally occurring nitrogenous organic acid found in animal tissues, has been found to play key roles in the brain including buffering energy supply, improving mitochondrial efficiency, directly acting as an anti-oxidant and acting as a neuroprotectant. Much of the evidence for these roles has been established in\xa0vitro or in pre-clinical studies. Here, we examine the roles of creatine and explore the current status of translation of this research into use in humans and the clinic. Some further possibilities for use of creatine in humans are also discussed.',
#                     'publicationYear': 2015,
#                     'doi': '10.1016/j.neuint.2015.08.010',
#                     'magId': 1504925078,
#                     'pmId': '26297632',
#                     'ssId': '9c4b06020d14e2644db3c186dbd92656b8704373',
#                     'venue': 'Neurochemistry International',
#                     'journalName': 'Neurochemistry International',
#                     'citedByCount': 60,
#                     'urls': [
#                         'http://wikigimn-cp528.wordpresstemporal.com/wp-content/uploads/CREATINA-BOOSTER-BRAIN-FUNCTION.pdf',
#                         'https://api.elsevier.com/content/article/pii/S0197018615300383',
#                         'https://www.sciencedirect.com/science/article/pii/S0197018615300383?dgcid=api_sd_search-api-endpoint'
#                     ],
#                     'outCitations': [
#                         '0b286947c5e7fdcf4ab163fc89fc777950d6e6de',
#                         '33bf8aafe801b8a92696d81b5c3f48cbb0ac127a',
#                         '5d57cee964874ce346370a5b906d00d60647ab8e',
#                         '42c4c501fee1e908efa208aec3a7b098f6b0c082',
#                         '3deb6e09e0d576c38856f5364ae6e991e0a1ebca',
#                         '8cbd17d691772def3cd2fa4e80c09b77fa28668a',
#                         '69cb754ba6333c2e7cd4de86ebbaeddf7f2ac78b',
#                         'fec4464dae64a4745e50825e152b81fff6cd24aa',
#                         'ef3e46f899c06bf5221993b5c3a94d23213f5cd6',
#                         '31a7718ce1497419330163411461942a4c227b00',
#                         'afcae6316114b6a0104a70fa45aa1d4c67d9d28b',
#                         '9d2e9ecedf152780b32c03f28ae934b1ca63d640',
#                         'a29cde8ab1711da403fec3c6e572d6e1e3108e99',
#                         '6a99f08f3687393cf75cb817a8e7328869d66f77',
#                         '0b468bc62c3bf8f3715116d3181b279f92d914d6',
#                         'e0fc11fb8c80cf5078068f154c6c74e3f93eda31',
#                         'f39e7bb972d636daae9be8ffd69ad106d59c2d6c',
#                         'a0810b780461a1b654c46f58ef1c82034c4937b4',
#                         '2b684cdebcb7dfc9270fb78bfc60de6736312aec',
#                         'd14913927c98d5c249e1bc28ac0535f4b08d48ed',
#                         'e979235faa93816cb52228dcececef8a893c6b23',
#                         '0efce6b795793d645b1a8fcf8d5970f0fa79f44e',
#                         '29d1aa321ea89c162f0180b2f83c0ad4860713f9',
#                         '8f59f94c9e1f93663c866f384713d3af52c51594',
#                         '57d34463409189f18837a07ef857ba8918162403',
#                         '4d8b147c8c8d39d4f2c61361fad700e1f65f177a',
#                         '7c5a35b64bf0956d99eeedb49f3cfaf7eb40c04c',
#                         '0cb90021541c7ccf8e6215e07dac5cdc6584445d',
#                         '9809486b416f4561f877d4808506b77580c008bd',
#                         '6f83dcf0af6fbcd5d3a79b6983a57103be1f49e1',
#                         'feae4dd51272b4f4031379172c5bb88cbae010e2',
#                         '0c9643076fe8d8103e6bb2b4fe678c4d3571a904',
#                         'c08529dd2defa61f7586bf6fa57c48207517f077',
#                         '03f62225b2b550dc70a0ae87888945390a7a347e',
#                         'cedaf6952b36e5b48168830f69ad57fb400b392f',
#                         'd0abeb3d68205d4cfa6dd299409edd3c90f70188',
#                         '0c48bdc575921a54b07930009cad81a3aa6570d4',
#                         '99fb95423281a36b81f4ae859086c7cf246a1ad4',
#                         '9ba66c85cd76c727eb9cbe73408923b2532c37d4',
#                         '8fcd70cf7263478b0f105f621ca204f64468b4e0',
#                         'b5cfa1717e70f281549b5e62d019200bcbfb6d64',
#                         'bed6103f0a15814c9b1338a90117969d42ef9a03',
#                         '512dde3e4317cc8b63656fbb6b73c53cca1f202f',
#                         '3423e849e306ce91bca86e9bd49a5353ee3e08fb',
#                         '24a04a13d10fd72fac3fd5de8edd6fc72977d695',
#                         '465c33d1ebefa7b91e9b65d49a95fddb74078bd2',
#                         '54586f092c15a7cbbad029ee4559ab1c6661c3f6',
#                         '3f87ebf181f78dbe4dbf184bbb1763b0c7f8b229',
#                         'eb6e7d7b6cb51c8eeb46d130875a4e18c7a1f942',
#                         'c036a5b0403df35181169d451aef0f44794f442e',
#                         '8f0b7b451ed526d92bac32223217e56cd3fae246',
#                         '8b9cc362c8ec02083f66138fd5d0ea678d149e7f',
#                         '6c74223c0aed1b428a04b41ad0633211a3cc77f1',
#                         'd167d2ae9c13410d5c88b9ddd53874b4512e2c49',
#                         '4c84cba30fc738d0acb38f74f97f4770d2e5ef56',
#                         'c8a80fc04851dec00b8d5d675fd83f0a8bfb319f',
#                         '91ee52f58febd04d16a14481c5dfdf372dcc8cce',
#                         '11e9f5ef289124740f06871a3ab7dcdbfa68e6d9',
#                         '9b94bf83f2c5400ca0cf96ccd987298afbf6db50',
#                         '5c680ee5585810d32db962ee78e1ee1e197bae67',
#                         '4a29a84f581962524ddf2b0acea0d965fac21758',
#                         '4f72131e36eca6f72805a3b2ed749fc7368309d7',
#                         '1f4111a08aa78f7b1ed0eaf8f29f7c89591bd5de',
#                         '20980c5fd02734111a2d903030345173a0565a03',
#                         '8c6127ded3b511678a4f1b3b6a5092189e6a1d55',
#                         'f1c18364d411c463efbb8a04b4705f22d25e3c5a',
#                         'f0e21e9484ce0879640998a5eeb91bb314b2adaa',
#                         'd916c72a9ad820bb517e1003a4eab7fedccb4387',
#                         '3c21cf7e9e3d28e65eb40a49af747f84990ce0ba',
#                         '96224f78668f04c75bf8b966b43bbfcfc12aa808',
#                         '6ff23a1ca7c05bf7492ba1a4e5f09601fd4d1bcc',
#                         '17b63fd1e587581950d4371d390c1b8462d48a00',
#                         'bd7cc437f8e3ea9279061b7937b3b29dc5978452',
#                         'a0936ebd9d4ae6020455ce5d91c26d569999910c',
#                         'b4621ec36483ed944d4a9bd9dff4ac997de7c268',
#                         '823af7401375d612b1c1cf3ec988752bc2714240',
#                         '3272b27452bfdb52b51569ed09f5cf8e3179f105',
#                         '44e23278d12cf2e304a38ee955148604abac5da5',
#                         '887cb6946505e5bd200ca9be994d6744d3a9f32b',
#                         '6207bc5758919464c2a8ee8ebda8d48c223ce7f6',
#                         '5eaeaf89e05775765869748e8f82daa1b12d5a30',
#                         'c481dcde71a1aa6cf8fcbfb1092e1c2ad92cf84c',
#                         'fc490919bf475d456343b59f6e90269b26f0ad75',
#                         '03d1f287ea43bd06a114bd9181e136d6653e094e',
#                         '88760eaedaa0c5bcc9f82f19f747d0e9dc63c5a3',
#                         '4083105da05083f2fdba7b5b30fb3d1c1607bac1',
#                         '7adc12cf21aad45f756d3140d94647adcbb25568',
#                         'dee1638bd33ec937dfcf7252ba679e044d7c7c76',
#                         'a54a9dd66ec50c2e01d97fc7dd5dff58508e09e8',
#                         '4af35188c36033bc84c78d10843596ec751f4332',
#                         '7c8f0f83ae74a0ad8c19fa99f2ffa7931c460455',
#                         '66f1d765505ff810de18563de630c22d644dc238',
#                         'c4b0f564de09446514ec8305abefbd6d121fb17e',
#                         '99949cc33003aa0b65aa70d1ffc26e7bde68e31f',
#                         '74f9ea5f095afdd56811fa53aff049be45a859e9',
#                         '1c6ae95ab5fac95d05ccce5a17e03f8a2bfcd836',
#                         'c8bf9935da80c9bba8ca7239681d3fe2cb5b8865',
#                         'b52d14ac3fd6d9510041cc32814f1ba722bb7dba',
#                         '1c20cafd63931f9954f36ebe67f52ebb4c41942a',
#                         '5c42ea5d310d2f46487fe533bb7dee8d1200b748',
#                         'c93dbb52ad0bd09eba3f53b72e52be2636f26824',
#                         '08a1bf234b86bb7f951e9e41682954a8f5589598',
#                         '482ae26e561d9c7c528812e5eecf10c582a017ca',
#                         '5eb7ad4f270363903fd825a6722b65d58ab59e0a',
#                         'a766a21a560833a0c54fa694ab966db10362d10e',
#                         '588328c1abe1c3bd848361085e9d5f07221e1226',
#                         '09c74956c971b0ab7f3299b431a20ac5ab656f06',
#                         '14018a3dcf983e1fa49e5b1bbb75f8f13b5ef626',
#                         '2e1829a6af923c6693a42a0f5e4bc3ac82b9653d',
#                         '685f7596a817847a57e4ce13a29c01514e28d091',
#                         'd85d2bdb4b6249a994f52933316ebdf280951b3b',
#                         '9b7c3c97d08da8ccb512f2f10a4f473e218532d0',
#                         '266b92fecf5ba5fd7b51e52a1e599e35e46aefc2',
#                         '095b8dc9c0663a13240b6bf01dc3050d5a8726ea',
#                         '6683069b804701f876d6eec15281b7a5fe10e7ee',
#                         '2e1b4d9e3e05115c7160d4bd73ef03e727938252',
#                         'eae96d3ca1d7beec382670dc6ce00b0d0e9d4345',
#                         'ef8637fae2973cfa4d132b6913500b6cbd7ffa5b',
#                         'c95ebbf17edab9fdcf1bcd9defd29617291001b5',
#                         '07b584c14b91a7d40932b004a9d370749fbff6ad',
#                         '047db70c4d4ad96c2d4b93fa28dcbfda3abbf92e',
#                         '96e32a11b23b29720eb3e2157df4991d5408c2eb'
#                     ],
#                     'inCitations': [
#                         'd6ac0dafae2d913d2b0f1c42a7e5216fd5ec5fe6',
#                         '14fff75f24f7078330b511445a25dfd855ccdf6e',
#                         '1c48012de2291b4b16074405db6dd829e4d90fff',
#                         'cdb96097d8defa4e923ed1ba61868f6ec653a530',
#                         '8e8c609bb6ec0644a6355188a5e65c8702ee2529',
#                         '1cf4e7a252c3cae7b9f86ed9c098b474c4544640',
#                         'a61b87b7a879e3be6f64f1c33eb43c093cbe2862',
#                         'effd7dcaf38e15fa43c67af1aa839992e8cf76b4',
#                         'f78f466d0c04daa58140c2506b4c0650a856804d',
#                         'e5fde4599a63f0e3c7b69b7ee0b4b379af66ab20',
#                         'ceb0b419b1e87093d91bbd31a60eb885bb8dc6fa',
#                         'c11389e28f2248a4f43974deeda93de40011cf9c',
#                         'd53f3bfc17bac867bd31cb7c0690a454affc88cb',
#                         '78b299d0dde731043e6fec95d750ab76b978316a',
#                         '2f63716f6308f7e82dcdfc3d1a0d9cfdf9c4b611',
#                         '3fc0d38e48b6b0dc97eb0cd93b82c0d81704e6d4',
#                         'cd726b63c78fd50dbb4bcddc0ea68468714d9ee0',
#                         'e1674d25ed80180c2cdd8206267dc40c7ad05be5',
#                         '82238456c90326248c9c2dbb506edaf2845bb055',
#                         'e5ae2352bb9fc27ea2b646c3484d3c08a286c8c2',
#                         '2edb018392f0820c23432ec75a8f48f83ffc0f98',
#                         'be490d51ab886591d99a08a319ff3338df220116',
#                         'aad022e4752db47cdac2ce3adcdc928bdc41f131',
#                         'bc0a39a575419bc3f704839bbdd27473c596a0c9',
#                         '450b742fefc1ef2cfbebdfb37c8eda8f04ec4c32',
#                         '0664cb8f8a8fc74755d13fc4cf117e468ba2a93e',
#                         'd206f63d2e724771093776ed1e95ecef13c193a4',
#                         'eaec1cbf7e68c1ac362fa2865935b24c2e99c777',
#                         'f363624c4f739e617a18d872c6f884d7cef994be',
#                         '16b53da1cd3827d3f9148acf7348bcd9c93fe03a',
#                         '17fb7282d51dee79bbf9ccc2a9e9639d44f60e94',
#                         'acc5678de2a768c21c61e4aba27415935cb869cd',
#                         '448ce4ec6c834d12bd35ced877d629cfad9ec4ed',
#                         '4599713e2da92b75d1e70b0e09db48bc9ac071ca',
#                         'c496e0c34f06348c42d5a1626a62889d6877f977',
#                         '0bfca4c73653cfbed314cc753cf7147dda1d8ca7',
#                         '646fa90103e28a4cd45c61a603b693c5c593327d',
#                         '717afa9b9c0488ba5f2e3e822414e105f9199a69',
#                         '36fcbb7894c84a42dc5f3028c241a76b7385db5f',
#                         '43ac81792cd97a5e7214d60ec381646bffcc4b51',
#                         '58ce83ef5e1d830802b67ca29edaeb62e5e79eb9',
#                         '35a4bbd57f83d9555c36a989a2a7f54639ec93d9',
#                         '64faf5f8bc1687a7cf51b06c4e8301b48bc96465',
#                         '5865bf34dff009cf989b9836ad9d1f65829dc995',
#                         'b92d1002e27f5e06f5759dd0085db85745a6a172',
#                         '78fb00506016b9502c2f8e1b91bd6920b4a32fc6',
#                         '4fd215d49daac2cc10005fe07dc20a2cee49774d',
#                         '2db63e3a5788bd0bff10a2a1d7bae090a6a74df9',
#                         'fd3aee0971ae2be8d88a8c49311307583ea859ea',
#                         'c08934aaf213b0ac777a775bde4c499104805ec4',
#                         'a64101d1e40a4f3c8081716fe34676e4b5283c71',
#                         'd7b6fca9aee656c98ecb138bf092308686c36613',
#                         'c6714fc83f412a3c15935b6a7bb1af0d369979a0',
#                         'a2715f646b49900154463cf4285b815972ebbb74',
#                         'cc54c9add9368dc3c64662b108edbe861a2c1f75',
#                         'f6df129dea9f94674779e38c3a0c5fb7e911aa21',
#                         '049c874b18210df406478ce94f23db8ca16e3df5',
#                         '2d8dc0f6f9f0ca5e5d173e53364c1b6a0fe8be90',
#                         'ca5344f4c9d5f671e793a4b7ded8da8194cad0bd',
#                         'ae088b15c91ce3980d0080ca397a453f869bde84'
#                     ],
#                     'authors': [
#                         {'ssId': '2254853', 'name': 'Caroline D. Rae'},
#                         {'ssId': '5865145', 'name': 'Stefan  Bröer'}
#                     ],
#                     'id': '9c4b06020d14e2644db3c186dbd92656b8704373'
#                 }
#             }
#         ]
#     }
# }
