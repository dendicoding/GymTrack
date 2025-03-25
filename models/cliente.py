import database as db

class Cliente:
    def __init__(self, nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente):
        self.nome = nome
        self.cognome = cognome
        self.email = email
        self.telefono = telefono
        self.data_nascita = data_nascita
        self.indirizzo = indirizzo
        self.citta = citta
        self.cap = cap
        self.note = note
        self.tipo = tipo
        self.codice_fiscale = codice_fiscale  # Nuovo campo
        self.tipologia = tipologia  # Nuovo campo
        self.taglia_giubotto = taglia_giubotto  # Nuovo campo
        self.taglia_cintura = taglia_cintura  # Nuovo campo
        self.taglia_braccia = taglia_braccia  # Nuovo campo
        self.taglia_gambe = taglia_gambe  # Nuovo campo
        self.obiettivo_cliente = obiettivo_cliente  # Nuovo campo

    def salva(self):
        return db.add_cliente(self.nome, self.cognome, self.email, self.telefono, self.data_nascita, 
                              self.indirizzo, self.citta, self.cap, self.note, self.tipo, self.codice_fiscale, self.tipologia, self.taglia_giubotto, self.taglia_cintura, self.taglia_braccia, self.taglia_gambe, self.obiettivo_cliente)

    @staticmethod
    def get_cliente(cliente_id):
        return db.get_cliente(cliente_id)

    @staticmethod
    def get_all_clienti():
        return db.get_all_clienti()

# ... altre funzioni relative ai clienti se necessario ...
