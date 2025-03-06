import database as db

class Cliente:
    def __init__(self, nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo):
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

    def salva(self):
        return db.add_cliente(self.nome, self.cognome, self.email, self.telefono, self.data_nascita, 
                              self.indirizzo, self.citta, self.cap, self.note, self.tipo)

    @staticmethod
    def get_cliente(cliente_id):
        return db.get_cliente(cliente_id)

    @staticmethod
    def get_all_clienti():
        return db.get_all_clienti()

# ... altre funzioni relative ai clienti se necessario ...
