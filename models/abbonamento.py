from datetime import datetime, timedelta
import database as db

class Abbonamento:
    def __init__(self, cliente_id, pacchetto_id, data_inizio, prezzo_totale, numero_rate):
        self.cliente_id = cliente_id
        self.pacchetto_id = pacchetto_id
        self.data_inizio = data_inizio
        self.prezzo_totale = prezzo_totale
        self.numero_rate = numero_rate
        self.data_fine = self.calcola_data_fine()

    def calcola_data_fine(self):
        pacchetto = db.get_pacchetto(self.pacchetto_id)
        data_inizio_obj = datetime.strptime(self.data_inizio, "%Y-%m-%d")
        data_fine_obj = data_inizio_obj + timedelta(days=pacchetto['durata_giorni'])
        return data_fine_obj.strftime("%Y-%m-%d")

    def salva(self):
        return db.create_abbonamento(self.cliente_id, self.pacchetto_id, self.data_inizio, self.prezzo_totale, self.numero_rate)

# ... altre funzioni relative agli abbonamenti se necessario ...
