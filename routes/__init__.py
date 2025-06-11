#from .auth import auth_bp
from .clienti import clienti_bp
from .pacchetti import pacchetti_bp
from .abbonamenti import abbonamenti_bp
from .lezioni import lezioni_bp
from .appuntamenti import appuntamenti_bp
from .rate import rate_bp
from .trainers import trainers_bp
from .gerarchie import gerarchie_bp
from .statistiche import stats_bp
from .utils import utils_bp
from .auth import auth_bp
#from .calendario import calendario_bp
#from .statistiche import statistiche_bp
# ... altri blueprint

blueprints = [
    clienti_bp,
    pacchetti_bp,
    abbonamenti_bp,
    lezioni_bp,
    appuntamenti_bp,
    rate_bp,
    trainers_bp,
    gerarchie_bp,
    stats_bp,
    utils_bp,
    auth_bp
]