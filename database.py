import sqlite3
import os
from datetime import datetime, timedelta
import pyodbc
import psycopg2
from flask import flash
import os
#DATABASE_PATH = "gym_manager.db"

#def get_db_connection():
 #   """Crea una connessione al database"""
  #  conn = sqlite3.connect(DATABASE_PATH)
   # conn.row_factory = sqlite3.Row
    #return conn 
def get_db_connection():
    """Crea una connessione a PostgreSQL"""
    dbname = os.environ.get('DATABASE_NAME', 'GYMTRACK')
    user = os.environ.get('DATABASE_USER', 'gymtrack')
    password = os.environ.get('DATABASE_PASSWORD', 'gymtrack')
    host = os.environ.get('DATABASE_SERVER', 'localhost')
    port = os.environ.get('DATABASE_PORT', '5432')
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    return conn
""" 
def init_db():
    #Inizializza il database con le tabelle necessarie
    if os.path.exists(DATABASE_PATH):
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Creazione tabella clienti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clienti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        email TEXT,
        telefono TEXT,
        data_nascita TEXT,
        indirizzo TEXT,
        citta TEXT,
        cap TEXT,
        note TEXT,
        tipo TEXT NOT NULL,  -- 'lead' o 'effettivo'
        codice_fiscale TEXT, -- Nuovo campo per il codice fiscale
        data_registrazione TEXT NOT NULL,
        taglia_giubotto TEXT,  -- Nuovo campo per la taglia giubotto
        taglia_cintura TEXT,   -- Nuovo campo per la taglia cintura
        taglia_braccia TEXT,   -- Nuovo campo per la taglia braccia
        taglia_gambe TEXT,     -- Nuovo campo per la taglia gambe
        obiettivo_cliente TEXT, -- Nuovo campo per l'obiettivo cliente
        sede_id INTEGER NOT NULL, -- Nuovo campo per la sede
        FOREIGN KEY (sede_id) REFERENCES sede (id)
    )
    ''')
    
    # Creazione tabella pacchetti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacchetti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descrizione TEXT,
        prezzo REAL NOT NULL,
        numero_lezioni INTEGER NOT NULL,
        durata_giorni INTEGER NOT NULL,
        attivo BOOLEAN NOT NULL DEFAULT 1,
        pagamento_unico BOOLEAN NOT NULL DEFAULT 0
    )
    ''')
    
    # Creazione tabella abbonamenti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS abbonamenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        pacchetto_id INTEGER NOT NULL,
        data_inizio DATE NOT NULL,
        data_fine DATE NOT NULL,
        numero_lezioni INTEGER NOT NULL,
        lezioni_utilizzate INTEGER DEFAULT 0,
        prezzo_totale DECIMAL(10,2) NOT NULL,
        numero_rate INTEGER DEFAULT 1,
        FOREIGN KEY (cliente_id) REFERENCES clienti (id),
        FOREIGN KEY (pacchetto_id) REFERENCES pacchetti (id)
    )
    ''')
    
    # Creazione tabella rate
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbonamento_id INTEGER NOT NULL,
        importo DECIMAL(10,2) NOT NULL,
        data_scadenza DATE NOT NULL,
        data_pagamento DATE,
        pagato BOOLEAN DEFAULT 0,
        numero_rata INTEGER NOT NULL,
        metodo_pagamento TEXT,  -- Nuovo campo per il metodo di pagamento
        FOREIGN KEY (abbonamento_id) REFERENCES abbonamenti (id)
    )
    ''')
    
    # Creazione tabella lezioni
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lezioni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbonamento_id INTEGER NOT NULL,
        data DATE NOT NULL,
        note TEXT,
        registrata_da INTEGER DEFAULT 1,
        FOREIGN KEY (abbonamento_id) REFERENCES abbonamenti (id),
        FOREIGN KEY (registrata_da) REFERENCES utenti (id)
    )
    ''')
    
    # Creazione tabella utenti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS utenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        ruolo TEXT NOT NULL DEFAULT 'staff',
        attivo BOOLEAN NOT NULL DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Inserimento di dati di esempio per i pacchetti
    cursor.execute('''
    INSERT INTO pacchetti (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo)
    VALUES 
        ('Base', 'Pacchetto base con 10 lezioni', 300.00, 10, 60, 1),
        ('Intermedio', 'Pacchetto intermedio con 20 lezioni', 500.00, 20, 90, 1),
        ('Avanzato', 'Pacchetto avanzato con 30 lezioni', 700.00, 30, 120, 1)
    ''')
    
    # Inserisci un utente admin di default se non esiste
    admin_exists = conn.execute(
        "SELECT 1 FROM utenti WHERE email = 'admin@gym.com'").fetchone()
    if not admin_exists:
        conn.execute('''
        INSERT INTO utenti (nome, cognome, email, password, ruolo)
        VALUES ('Admin', 'System', 'admin@gym.com', 'admin123', 'admin')
        ''')

    conn.commit()
    conn.close()
    
    print("Database inizializzato con successo!")
"""
def get_all_clienti(sede_ids=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if sede_ids:
        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f'SELECT * FROM clienti WHERE sede_id IN ({placeholders}) ORDER BY cognome, nome'
        cursor.execute(query, sede_ids)
    else:
        cursor.execute('SELECT * FROM clienti ORDER BY cognome, nome')
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    clienti = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return clienti

def get_all_utenti():
    """Retrieve all users from the utenti table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM utenti ORDER BY nome, cognome')
        utenti = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in utenti]
    finally:
        conn.close()

def delete_user(user_id):
    """Delete a user from the utenti table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM utenti WHERE id = %s', (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_cliente(cliente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clienti WHERE id = %s', (cliente_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

def get_leads(sede_ids=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if sede_ids:
        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f"SELECT * FROM clienti WHERE tipo = 'lead' AND sede_id IN ({placeholders}) ORDER BY cognome, nome"
        cursor.execute(query, sede_ids)
    else:
        cursor.execute("SELECT * FROM clienti WHERE tipo = 'lead' ORDER BY cognome, nome")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    leads = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return leads

def get_clienti_effettivi(sede_ids=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if sede_ids:
        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f"SELECT * FROM clienti WHERE tipo = 'effettivo' AND sede_id IN ({placeholders}) ORDER BY cognome, nome"
        cursor.execute(query, sede_ids)
    else:
        cursor.execute("SELECT * FROM clienti WHERE tipo = 'effettivo' ORDER BY cognome, nome")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    clienti = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return clienti

def add_cliente(nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, provenienza, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data_registrazione = datetime.now().strftime("%Y-%m-%d")

    # Correggi i campi data vuoti
    data_nascita = data_nascita if data_nascita not in ("", None) else None

    try:
        cursor.execute(''' 
            INSERT INTO clienti (
                nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, data_registrazione, tipologia, provenienza, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, data_registrazione, tipologia, provenienza, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id
        ))
        cliente_id = cursor.fetchone()[0]
        conn.commit()
        return cliente_id
    except Exception as e:
        print(f"Errore durante l'inserimento del cliente: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def update_cliente(cliente_id, nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(''' 
            UPDATE clienti 
            SET nome = %s, cognome = %s, email = %s, telefono = %s, data_nascita = %s, 
                indirizzo = %s, citta = %s, cap = %s, note = %s, tipo = %s, codice_fiscale = %s, 
                tipologia = %s, taglia_giubotto = %s, taglia_cintura = %s, taglia_braccia = %s, 
                taglia_gambe = %s, obiettivo_cliente = %s
            WHERE id = %s
        ''', (
            nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo,
            codice_fiscale, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe,
            obiettivo_cliente, cliente_id
        ))
        conn.commit()
    except Exception as e:
        print(f"Errore durante l'aggiornamento del cliente: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def delete_cliente(cliente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM clienti WHERE id = %s', (cliente_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'eliminazione del cliente: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
# Funzioni di utilità per i pacchetti
def get_all_pacchetti():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pacchetti ORDER BY nome')
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    pacchetti = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return pacchetti

def get_all_pacchetti_validi():
    conn = get_db_connection()
    oggi = datetime.now().strftime('%Y-%m-%d')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM pacchetti
        WHERE data_scadenza IS NULL OR data_scadenza >= %s
        ORDER BY nome
    ''', (oggi,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    pacchetti = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return pacchetti

def delete_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pacchetti WHERE id = %s', (pacchetto_id,))
        conn.commit()
    except Exception as e:
        print(f"Errore durante l'eliminazione del pacchetto: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_pacchetto(pacchetto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pacchetti WHERE id = %s', (pacchetto_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

def add_pacchetto(nome, descrizione, prezzo, numero_lezioni, attivo, pagamento_unico, data_scadenza=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Correggi il campo data_scadenza vuoto
    if data_scadenza in ("", None):
        data_scadenza = None
    cursor.execute('''
        INSERT INTO pacchetti (nome, descrizione, prezzo, numero_lezioni,attivo, pagamento_unico, data_scadenza)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (nome, descrizione, prezzo, numero_lezioni, attivo, pagamento_unico, data_scadenza))
    pacchetto_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return pacchetto_id

def update_pacchetto(pacchetto_id, nome, descrizione, prezzo, numero_lezioni, attivo, pagamento_unico, data_scadenza=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE pacchetti 
        SET nome = %s, descrizione = %s, prezzo = %s, numero_lezioni = %s, attivo = %s, pagamento_unico = %s, data_scadenza = %s
        WHERE id = %s
    ''', (nome, descrizione, prezzo, numero_lezioni, attivo, pagamento_unico, data_scadenza, pacchetto_id))
    conn.commit()
    conn.close()
    return pacchetto_id

# Funzioni per gli abbonamenti
from datetime import datetime, date
def create_abbonamento(cliente_id, pacchetto_id, data_inizio, prezzo_totale, numero_rate=1):
    conn = get_db_connection()
    try:
        pacchetto = get_pacchetto(pacchetto_id)
        if not pacchetto:
            return False

        cliente = get_cliente(cliente_id)
        sede_id = cliente['sede_id'] if cliente and 'sede_id' in cliente else None

        cursor = conn.cursor()

        # Assicurati che data_inizio sia un oggetto date
        if isinstance(data_inizio, str):
            data_inizio = datetime.strptime(data_inizio, '%Y-%m-%d').date()
        elif isinstance(data_inizio, datetime):
            data_inizio = data_inizio.date()

        #data_fine = data_inizio + timedelta(days=pacchetto['durata_giorni'])

        # Converti le date in stringhe 'YYYY-MM-DD'
        data_inizio_sql = data_inizio.strftime('%Y-%m-%d')
        #data_fine_sql = data_fine.strftime('%Y-%m-%d')

        print("DEBUG create_abbonamento params:", {
            "cliente_id": cliente_id,
            "pacchetto_id": pacchetto_id,
            "data_inizio": data_inizio_sql,
            "numero_lezioni": pacchetto['numero_lezioni'],
            "prezzo_totale": prezzo_totale,
            "numero_rate": numero_rate,
            "sede_id": sede_id
        })

        cursor.execute('''
            INSERT INTO abbonamenti (
                cliente_id, 
                pacchetto_id, 
                data_inizio, 
                numero_lezioni,
                lezioni_utilizzate,
                prezzo_totale,
                numero_rate,
                sede_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            cliente_id, 
            pacchetto_id, 
            data_inizio_sql, 
            pacchetto['numero_lezioni'],
            0,  # lezioni_utilizzate
            prezzo_totale,
            numero_rate,
            sede_id
        ))
        abbonamento_id = cursor.fetchone()[0]
        print("DEBUG abbonamento_id:", abbonamento_id)

        importo_rata = prezzo_totale / numero_rate
        for i in range(numero_rate):
            data_scadenza = data_inizio + timedelta(days=(i + 1) * 30)
            data_scadenza_sql = data_scadenza.strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO rate (
                    abbonamento_id,
                    importo,
                    data_scadenza,
                    pagato,
                    numero_rata
                ) VALUES (%s, %s, %s, %s, %s)
            ''', (abbonamento_id, importo_rata, data_scadenza_sql, False, i + 1))

        conn.commit()
        return True

    except Exception as e:
        import traceback
        print(f"Errore durante la creazione dell'abbonamento: {e}")
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

def get_rate_scadenza(sede_ids):
    conn = get_db_connection()
    if not sede_ids:
        return []

    placeholders = ','.join(['%s'] * len(sede_ids))
    query = f'''
        SELECT 
            r.*,
            c.nome || ' ' || c.cognome as nome_cliente,
            c.id as cliente_id,
            p.nome as tipo_pacchetto,
            a.id as abbonamento_id
        FROM rate r
        JOIN abbonamenti a ON r.abbonamento_id = a.id
        JOIN clienti c ON a.cliente_id = c.id
        JOIN pacchetti p ON a.pacchetto_id = p.id
        WHERE r.pagato = FALSE AND c.sede_id IN ({placeholders})
        ORDER BY r.data_scadenza ASC
    '''
    cursor = conn.cursor()
    cursor.execute(query, sede_ids)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    rate = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return rate

def get_rate_incassate_mese(sede_ids=None):
    mese_inizio = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    mese_fine = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    mese_fine = mese_fine.strftime("%Y-%m-%d")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if sede_ids:
            placeholders = ','.join(['%s'] * len(sede_ids))
            query = f'''
                SELECT 
                    r.*,
                    c.nome || ' ' || c.cognome AS nome_cliente,
                    c.id AS cliente_id,
                    p.nome AS tipo_pacchetto,
                    a.id AS abbonamento_id
                FROM rate r
                JOIN abbonamenti a ON r.abbonamento_id = a.id
                JOIN clienti c ON a.cliente_id = c.id
                JOIN pacchetti p ON a.pacchetto_id = p.id
                WHERE r.data_pagamento BETWEEN %s AND %s 
                AND r.pagato = TRUE
                AND c.sede_id IN ({placeholders})
                ORDER BY r.data_pagamento ASC;
            '''
            params = [mese_inizio, mese_fine] + sede_ids
            cursor.execute(query, params)
        else:
            query = '''
                SELECT 
                    r.*,
                    c.nome || ' ' || c.cognome AS nome_cliente,
                    c.id AS cliente_id,
                    p.nome AS tipo_pacchetto,
                    a.id AS abbonamento_id
                FROM rate r
                JOIN abbonamenti a ON r.abbonamento_id = a.id
                JOIN clienti c ON a.cliente_id = c.id
                JOIN pacchetti p ON a.pacchetto_id = p.id
                WHERE r.data_pagamento BETWEEN %s AND %s 
                AND r.pagato = TRUE
                ORDER BY r.data_pagamento ASC;
            '''
            cursor.execute(query, (mese_inizio, mese_fine))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        rate = [dict(zip(columns, row)) for row in rows]
        return rate
    finally:
        conn.close()

def get_rate_calendario(mese=None, anno=None, sede_ids=None):
    conn = get_db_connection()
    try:
        if not sede_ids:
            return []

        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f'''
            SELECT 
                r.data_scadenza,
                COUNT(r.id) as rate_da_pagare,
                STRING_AGG(c.nome || ' ' || c.cognome, ', ') as clienti,
                STRING_AGG(CAST(c.id AS TEXT), ',') as clienti_ids
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            WHERE r.pagato = FALSE AND c.sede_id IN ({placeholders})
        '''
        params = sede_ids.copy()

        if mese and anno:
            query += ''' 
                AND TO_CHAR(r.data_scadenza, 'YYYY-MM') = %s
            '''
            params.append(f"{anno:04d}-{mese:02d}")

        query += '''
            GROUP BY r.data_scadenza
            ORDER BY r.data_scadenza ASC
        '''

        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        scadenze = [dict(zip(columns, row)) for row in rows]
        return scadenze
    finally:
        conn.close()

def paga_rata(rata_id, metodo_pagamento, importo_pagato):
    conn = get_db_connection()
    data_pagamento = datetime.now().strftime("%Y-%m-%d")
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE rate SET pagato = TRUE, data_pagamento = %s, metodo_pagamento = %s, importo = %s WHERE id = %s
        ''', (data_pagamento, metodo_pagamento, importo_pagato, rata_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la registrazione del pagamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_abbonamenti_by_cliente(cliente_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                a.*,
                p.nome as nome_pacchetto,
                (SELECT COUNT(*) FROM rate r WHERE r.abbonamento_id = a.id AND r.pagato = TRUE) as rate_pagate
            FROM abbonamenti a
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE a.cliente_id = %s
            ORDER BY a.data_inizio ASC
        ''', (cliente_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        abbonamenti = [dict(zip(columns, row)) for row in rows]
        return abbonamenti
    finally:
        conn.close()

def get_rate_by_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                r.*,
                r.importo as importo_rata,
                r.data_scadenza,
                r.data_pagamento,
                r.pagato,
                r.numero_rata
            FROM rate r
            WHERE r.abbonamento_id = %s
            ORDER BY r.numero_rata ASC
        ''', (abbonamento_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        rate = [dict(zip(columns, row)) for row in rows]
        return rate
    finally:
        conn.close()

def get_lezioni_abbonamento(abbonamento_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM lezioni
        WHERE abbonamento_id = %s
        ORDER BY data
    ''', (abbonamento_id,))
    lezioni = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    lezioni_list = [dict(zip(columns, row)) for row in lezioni]
    conn.close()
    return lezioni_list

def add_lezione(abbonamento_id, data, note, registrata_da):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Inserisci la nuova lezione e ottieni l'id
        cursor.execute('''
            INSERT INTO lezioni (abbonamento_id, data, note, registrata_da)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (abbonamento_id, data, note, registrata_da))
        lezione_id = cursor.fetchone()[0]

        # Incrementa il numero di lezioni utilizzate per l'abbonamento
        cursor.execute('''
            UPDATE abbonamenti
            SET lezioni_utilizzate = lezioni_utilizzate + 1
            WHERE id = %s
        ''', (abbonamento_id,))

        conn.commit()
        return lezione_id
    except Exception as e:
        print(f"Errore durante l'aggiunta della lezione: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def modifica_rata_pagata(rata_id, data_pagamento, metodo_pagamento):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE rate
            SET data_pagamento = %s, metodo_pagamento = %s
            WHERE id = %s
        ''', (data_pagamento, metodo_pagamento, rata_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la modifica della rata pagata: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def modifica_rata_non_pagata(rata_id, importo, data_scadenza):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE rate
            SET importo = %s, data_scadenza = %s
            WHERE id = %s
        ''', (importo, data_scadenza, rata_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la modifica della rata non pagata: {e}")
        conn.rollback()
        return False
    finally:    
        conn.close()

def completa_lezione(lezione_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE lezioni SET completata TRUE WHERE id = %s
        ''', (lezione_id,))
        
        # Aggiorna il contatore delle lezioni utilizzate
        cursor.execute('SELECT abbonamento_id FROM lezioni WHERE id = %s', (lezione_id,))
        lezione = cursor.fetchone()
        if lezione:
            abbonamento_id = lezione[0]
            cursor.execute('''
                UPDATE abbonamenti 
                SET lezioni_utilizzate = lezioni_utilizzate + 1
                WHERE id = %s
            ''', (abbonamento_id,))
        conn.commit()
    finally:
        conn.close()

def get_pacchetti_venduti_mese(sede_ids=None):
    conn = get_db_connection()
    try:
        mese_inizio = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        mese_fine = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        mese_fine = mese_fine.strftime("%Y-%m-%d")
        cursor = conn.cursor()
        if sede_ids:
            placeholders = ','.join(['%s'] * len(sede_ids))
            query = f"""
                SELECT COUNT(*) FROM abbonamenti
                WHERE data_inizio BETWEEN %s AND %s
                AND cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))
            """
            params = [mese_inizio, mese_fine] + sede_ids
            cursor.execute(query, params)
        else:
            query = """
                SELECT COUNT(*) FROM abbonamenti
                WHERE data_inizio BETWEEN %s AND %s
            """
            cursor.execute(query, (mese_inizio, mese_fine))
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()

# Funzioni per la dashboard
def get_statistiche_dashboard(sede_ids=None):
    conn = get_db_connection()
    oggi = datetime.now().strftime("%Y-%m-%d")
    stats = {}
    try:
        cursor = conn.cursor()
        if sede_ids:
            placeholders = ','.join(['%s'] * len(sede_ids))
            stats['totale_clienti'] = len(get_clienti_effettivi(sede_ids))
            stats['totale_leads'] = len(get_leads(sede_ids))

            cursor.execute(
                f"SELECT COUNT(*) FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))",
                sede_ids
            )
            stats['abbonamenti_attivi'] = cursor.fetchone()[0]

            stats['pacchetti_venduti_mese'] = get_pacchetti_venduti_mese(sede_ids)

            cursor.execute(
                f"SELECT COUNT(*) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza = %s AND pagato = FALSE",
                sede_ids + [oggi]
            )
            stats['rate_oggi'] = cursor.fetchone()[0]

            cursor.execute(
                f"SELECT COUNT(*) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza < %s AND pagato = FALSE",
                sede_ids + [oggi]
            )
            stats['rate_scadute'] = cursor.fetchone()[0]

            cursor.execute(
                f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza < %s AND pagato = FALSE",
                sede_ids + [oggi]
            )
            stats['rate_scadute_importo'] = cursor.fetchone()[0] or 0

            # Previsione mese corrente
            mese_inizio = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            mese_fine = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            mese_fine = mese_fine.strftime("%Y-%m-%d")

            cursor.execute(
                f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_pagamento BETWEEN %s AND %s AND pagato = TRUE",
                sede_ids + [mese_inizio, mese_fine]
            )
            stats['incassi_mese'] = cursor.fetchone()[0] or 0

            cursor.execute(
                f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza BETWEEN %s AND %s AND pagato = TRUE",
                sede_ids + [mese_inizio, mese_fine]
            )
            stats['previsione_mese'] = cursor.fetchone()[0] or 0

            # Previsione mese prossimo
            current_date = datetime.now()
            prossimo_mese_inizio = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%Y-%m-%d")
            prossimo_mese_fine = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) + timedelta(days=31)
            prossimo_mese_fine = prossimo_mese_fine.replace(day=1) - timedelta(days=1)
            prossimo_mese_fine = prossimo_mese_fine.strftime("%Y-%m-%d")

            cursor.execute(
                f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza BETWEEN %s AND %s AND pagato = FALSE",
                sede_ids + [prossimo_mese_inizio, prossimo_mese_fine]
            )
            stats['previsione_mese_prossimo'] = cursor.fetchone()[0] or 0
        else:
            stats = {
                'totale_clienti': 0,
                'totale_leads': 0,
                'abbonamenti_attivi': 0,
                'rate_oggi': 0,
                'rate_scadute': 0,
                'rate_scadute_importo': 0,
                'incassi_mese': 0,
                'previsione_mese': 0,
                'previsione_mese_prossimo': 0
            }
    finally:
        conn.close()
    return stats

def get_rate_contanti(sede_ids=None, da=None, a=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = '''
            SELECT r.*, 
                   c.nome || ' ' || c.cognome as nome_cliente, 
                   p.nome as tipo_pacchetto, 
                   a.id as abbonamento_id,
                   c.id as cliente_id
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE r.pagato = TRUE AND r.metodo_pagamento = 'Contanti'
        '''
        params = []
        if sede_ids:
            placeholders = ','.join(['%s'] * len(sede_ids))
            query += f' AND c.sede_id IN ({placeholders})'
            params += sede_ids
        if da:
            query += ' AND r.data_pagamento >= %s'
            params.append(da)
        if a:
            query += ' AND r.data_pagamento <= %s'
            params.append(a)
        query += ' ORDER BY r.data_pagamento DESC'
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        rate = [dict(zip(columns, row)) for row in rows]
        return rate
    finally:
        conn.close()

def get_scadenze_calendario():
    conn = get_db_connection()
    oggi = datetime.now().strftime("%Y-%m-%d")
    # Calcola la data di un mese dopo oggi
    un_mese_dopo = (datetime.now() + timedelta(days=31)).strftime("%Y-%m-%d")
    
    query = '''
    SELECT r.id, r.data_scadenza, r.importo, c.nome, c.cognome
    FROM rate r
    JOIN abbonamenti a ON r.abbonamento_id = a.id
    JOIN clienti c ON a.cliente_id = c.id
    WHERE r.data_scadenza BETWEEN %s AND %s
    AND r.pagato = FALSE
    ORDER BY r.data_scadenza
    '''
    
    cursor = conn.cursor()
    cursor.execute(query, (oggi, un_mese_dopo))
    scadenze = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    
    # Organizza le scadenze per data
    calendario = {}
    for row in scadenze:
        scadenza = dict(zip(columns, row))
        data = scadenza['data_scadenza']
        if data not in calendario:
            calendario[data] = []
        calendario[data].append({
            'id': scadenza['id'],
            'cliente': f"{scadenza['nome']} {scadenza['cognome']}",
            'importo': scadenza['importo']
        })
    
    return calendario

def get_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                a.*,
                p.nome as tipo,
                p.descrizione as descrizione_pacchetto,
                p.numero_lezioni as numero_lezioni_pacchetto
            FROM abbonamenti a
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE a.id = %s
        ''', (abbonamento_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    finally:
        conn.close()

def get_lezioni_by_cliente(cliente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.*,
               p.nome as tipo,
               'Admin' as registrata_da_nome  -- Valore predefinito per ora
        FROM lezioni l
        JOIN abbonamenti a ON l.abbonamento_id = a.id
        JOIN pacchetti p ON a.pacchetto_id = p.id
        WHERE a.cliente_id = %s
        ORDER BY l.data DESC
    ''', (cliente_id,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    lezioni = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return lezioni

def get_lezioni_by_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                l.*,
                COALESCE(u.nome || ' ' || u.cognome, 'Sistema') as registrata_da_nome
            FROM lezioni l
            LEFT JOIN utenti u ON l.registrata_da = u.id
            WHERE l.abbonamento_id = %s
            ORDER BY l.data DESC
        ''', (abbonamento_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        lezioni = [dict(zip(columns, row)) for row in rows]
        return lezioni
    finally:
        conn.close()

def registra_lezione(abbonamento_id, data, note):
    conn = get_db_connection()
    try:
        # Verifica se l'abbonamento esiste e ha lezioni disponibili
        abbonamento = get_abbonamento(abbonamento_id)
        if not abbonamento:
            return False

        if (abbonamento['lezioni_utilizzate'] >= abbonamento['numero_lezioni']):
            return False

        cursor = conn.cursor()
        # Inserisci la nuova lezione con il campo registrata_da = 1
        cursor.execute('''
            INSERT INTO lezioni (abbonamento_id, data, note, registrata_da)
            VALUES (%s, %s, %s, 1)
        ''', (abbonamento_id, data, note))

        # Aggiorna il conteggio delle lezioni utilizzate
        cursor.execute('''
            UPDATE abbonamenti
            SET lezioni_utilizzate = lezioni_utilizzate + 1
            WHERE id = %s
        ''', (abbonamento_id,))

        conn.commit()
        return True

    except Exception as e:
        print(f"Errore durante la registrazione della lezione: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def incrementa_lezioni_utilizzate(abbonamento_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE abbonamenti 
            SET lezioni_utilizzate = lezioni_utilizzate + 1
            WHERE id = %s
        ''', (abbonamento_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento delle lezioni utilizzate: {e}")
        return False
    finally:
        conn.close()

def migrate_lezioni_table():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Prova ad aggiungere la colonna registrata_da se non esiste già
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='lezioni' AND column_name='registrata_da'
                ) THEN
                    ALTER TABLE lezioni ADD COLUMN registrata_da TEXT DEFAULT NULL;
                END IF;
            END
            $$;
        """)
        conn.commit()
        print("Migrazione completata con successo")
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_statistiche_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Ottieni il numero di abbonamenti attivi
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM abbonamenti
            WHERE pacchetto_id = %s 
        ''', (pacchetto_id,))
        abbonamenti_attivi = cursor.fetchone()[0]

        # Ottieni il numero totale di abbonamenti
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM abbonamenti
            WHERE pacchetto_id = %s
        ''', (pacchetto_id,))
        totale_abbonamenti = cursor.fetchone()[0]

        # Calcola l'incasso totale
        cursor.execute('''
            SELECT COALESCE(SUM(prezzo_totale), 0) as total
            FROM abbonamenti
            WHERE pacchetto_id = %s
        ''', (pacchetto_id,))
        incasso_totale = cursor.fetchone()[0]

        return {
            'abbonamenti_attivi': abbonamenti_attivi,
            'totale_abbonamenti': totale_abbonamenti,
            'incasso_totale': incasso_totale
        }

    finally:
        conn.close()

def get_vendite_mensili_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                TO_CHAR(data_inizio, 'YYYY-MM') as mese,
                COUNT(*) as vendite
            FROM abbonamenti
            WHERE pacchetto_id = %s
            AND data_inizio >= (CURRENT_DATE - INTERVAL '6 months')
            GROUP BY TO_CHAR(data_inizio, 'YYYY-MM')
            ORDER BY mese ASC
        ''', (pacchetto_id,))
        vendite = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        mesi = []
        vendite_mensili = []

        mesi_ita = {
            '01': 'Gennaio', '02': 'Febbraio', '03': 'Marzo',
            '04': 'Aprile', '05': 'Maggio', '06': 'Giugno',
            '07': 'Luglio', '08': 'Agosto', '09': 'Settembre',
            '10': 'Ottobre', '11': 'Novembre', '12': 'Dicembre'
        }

        for v in vendite:
            row = dict(zip(columns, v))
            anno, mese = row['mese'].split('-')
            mesi.append(f"{mesi_ita[mese]} {anno}")
            vendite_mensili.append(row['vendite'])

        return mesi, vendite_mensili
    finally:
        conn.close()

def get_abbonamenti_by_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                a.id,
                a.cliente_id,
                a.data_inizio,
                c.nome || ' ' || c.cognome as nome_cliente
            FROM abbonamenti a
            JOIN clienti c ON a.cliente_id = c.id
            WHERE a.pacchetto_id = %s
            ORDER BY a.data_inizio DESC
            LIMIT 10
        ''', (pacchetto_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        abbonamenti = [dict(zip(columns, row)) for row in rows]
        return abbonamenti
    finally:
        conn.close()

def registra_pagamento_rata(rata_id, data_pagamento):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE rate 
            SET pagato = TRUE,
                data_pagamento = %s
            WHERE id = %s
        ''', (data_pagamento, rata_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la registrazione del pagamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_rata(rata_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*,
                   a.cliente_id,
                   c.nome || ' ' || c.cognome as nome_cliente,
                   p.nome as tipo_pacchetto
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE r.id = %s
        ''', (rata_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    finally:
        conn.close()

def migrate_abbonamenti():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Verifica se la colonna esiste già
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='abbonamenti' AND column_name='numero_rate'
        """)
        exists = cursor.fetchone()
        if not exists:
            cursor.execute('ALTER TABLE abbonamenti ADD COLUMN numero_rate INTEGER DEFAULT 1')
            conn.commit()
            print("Migrazione completata con successo")
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
    finally:
        conn.close()

def migrate_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Aggiungi il campo data_scadenza alla tabella pacchetti
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='clienti' AND column_name='provenienza'
                ) THEN
                    ALTER TABLE clienti ADD COLUMN provenienza TEXT;
                END IF;
            END
            $$;
        """)
    except Exception as e:
        print(f"Errore durante la migrazione del database: {e}")
    finally:
        conn.commit()
        conn.close()

def delete_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Prima elimina tutte le rate associate
        cursor.execute('DELETE FROM rate WHERE abbonamento_id = %s', (abbonamento_id,))
        
        # Poi elimina tutte le lezioni associate
        cursor.execute('DELETE FROM lezioni WHERE abbonamento_id = %s', (abbonamento_id,))
        
        # Infine elimina l'abbonamento
        cursor.execute('DELETE FROM abbonamenti WHERE id = %s', (abbonamento_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'eliminazione dell'abbonamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def promuovi_cliente(cliente_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Verifichiamo prima che il cliente sia effettivamente un lead
        cursor.execute('SELECT tipo FROM clienti WHERE id = %s', (cliente_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Il cliente non esiste"
        columns = [desc[0] for desc in cursor.description]
        cliente = dict(zip(columns, row))
        if cliente['tipo'] != 'lead':
            return False, "Il cliente non è un lead"
        
        # Aggiorniamo il tipo del cliente
        cursor.execute('''
            UPDATE clienti 
            SET tipo = 'effettivo'
            WHERE id = %s
        ''', (cliente_id,))
        conn.commit()
        return True, "Cliente promosso con successo"
    except Exception as e:
        conn.rollback()
        return False, f"Errore durante la promozione: {str(e)}"
    finally:
        conn.close()

#----------------------------------------------------------------------------
def create_user_tables():
    """Crea le tabelle per la gestione degli utenti e della gerarchia"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabella per i franchisor
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS franchisor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabella per gli area manager
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS area_manager (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        franchisor_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (franchisor_id) REFERENCES franchisor(id)
    )
    ''')
    
    # Tabella per le società
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS societa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_manager_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        indirizzo TEXT,  -- Nuovo campo per l'indirizzo
        comune TEXT,     -- Nuovo campo per il comune
        provincia TEXT,  -- Nuovo campo per la provincia
        FOREIGN KEY (area_manager_id) REFERENCES area_manager(id)
    )
    ''')
    
    # Tabella per le sedi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sede (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        societa_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        indirizzo TEXT,
        citta TEXT,
        cap TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (societa_id) REFERENCES societa(id)
    )
    ''')
    
    # Aggiungi una colonna sede_id a tutte le tabelle esistenti
    tables = ['clienti', 'pacchetti', 'abbonamenti', 'lezioni', 'rate']
    for table in tables:
        try:
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN sede_id INTEGER DEFAULT 1')
        except:
            pass  # La colonna potrebbe già esistere
    
    # Crea una sede fittizia per i dati esistenti
    cursor.execute('''
    INSERT OR IGNORE INTO franchisor (id, nome, email, password) 
    VALUES (1, 'Franchisor Default', 'franchisor@example.com', 'password')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO area_manager (id, franchisor_id, nome, email, password) 
    VALUES (1, 1, 'Area Manager Default', 'area@example.com', 'password')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO societa (id, area_manager_id, nome, email, password) 
    VALUES (1, 1, 'Società Default', 'societa@example.com', 'password')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO sede (id, societa_id, nome, email, password) 
    VALUES (1, 1, 'Sede Default', 'sede@example.com', 'password')
    ''')
    
    conn.commit()
    conn.close()

def authenticate_user(email, password):
    """Autentica un utente dalla tabella utenti in base a email e password."""
    conn = get_db_connection()
    try:
        query = '''
        SELECT id, nome, cognome, email, ruolo 
        FROM utenti 
        WHERE email = %s AND password = %s AND attivo = TRUE
        '''
        cursor = conn.cursor()
        cursor.execute(query, (email, password))
        user = cursor.fetchone()
        if user:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, user))
        else:
            return None
    finally:
        conn.close()

def get_franchisor(franchisor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM franchisor WHERE id = %s', (franchisor_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

def get_area_managers_by_franchisor(franchisor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM area_manager WHERE franchisor_id = %s', (franchisor_id,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    area_managers = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return area_managers

def get_societa_by_area_manager(area_manager_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM societa WHERE area_manager_id = %s', (area_manager_id,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    societa = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return societa

def get_sedi_by_societa(societa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sede WHERE societa_id = %s', (societa_id,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    sedi = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return sedi

def get_franchisors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM franchisor')
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    franchisors = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return franchisors

def get_all_data():
    """Retrieve all franchisors, area managers, companies, and locations."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get all franchisors
        cursor.execute('SELECT * FROM franchisor')
        franchisors = cursor.fetchall()
        franchisors_columns = [desc[0] for desc in cursor.description]
        franchisors = [dict(zip(franchisors_columns, row)) for row in franchisors]

        # Get all area managers
        cursor.execute('SELECT * FROM area_manager')
        area_managers = cursor.fetchall()
        area_managers_columns = [desc[0] for desc in cursor.description]
        area_managers = [dict(zip(area_managers_columns, row)) for row in area_managers]

        # Get all companies
        cursor.execute('SELECT * FROM societa')
        societa = cursor.fetchall()
        societa_columns = [desc[0] for desc in cursor.description]
        societa = [dict(zip(societa_columns, row)) for row in societa]

        # Get all locations
        cursor.execute('SELECT * FROM sede')
        sedi = cursor.fetchall()
        sedi_columns = [desc[0] for desc in cursor.description]
        sedi = [dict(zip(sedi_columns, row)) for row in sedi]

        return franchisors, area_managers, societa, sedi
    finally:
        conn.close()

def build_hierarchy(user_role=None, user_email=None):
    """Build a filtered hierarchy based on the user's role and email."""
    hierarchy = []

    # Determine the franchisor ID for the logged-in user
    franchisor_id = None
    if user_role == 'franchisor':
        franchisor = get_franchisor_by_email(user_email)
        if franchisor:
            franchisor_id = franchisor['id']
    elif user_role == 'area manager':
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM area_manager WHERE email = %s', (user_email,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                area_manager = dict(zip(columns, row))
                franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()
    elif user_role == 'societa':
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM societa WHERE email = %s', (user_email,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                societa = dict(zip(columns, row))
                cursor.execute('SELECT * FROM area_manager WHERE id = %s', (societa['area_manager_id'],))
                row_am = cursor.fetchone()
                if row_am:
                    columns_am = [desc[0] for desc in cursor.description]
                    area_manager = dict(zip(columns_am, row_am))
                    franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()
    elif user_role == 'sede':
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sede WHERE email = %s', (user_email,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                sede = dict(zip(columns, row))
                cursor.execute('SELECT * FROM societa WHERE id = %s', (sede['societa_id'],))
                row_soc = cursor.fetchone()
                if row_soc:
                    columns_soc = [desc[0] for desc in cursor.description]
                    societa = dict(zip(columns_soc, row_soc))
                    cursor.execute('SELECT * FROM area_manager WHERE id = %s', (societa['area_manager_id'],))
                    row_am = cursor.fetchone()
                    if row_am:
                        columns_am = [desc[0] for desc in cursor.description]
                        area_manager = dict(zip(columns_am, row_am))
                        franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()
    elif user_role == 'trainer':
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM trainer WHERE email = %s', (user_email,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                trainer = dict(zip(columns, row))
                cursor.execute('SELECT * FROM sede WHERE id = %s', (trainer['sede_id'],))
                row_sede = cursor.fetchone()
                if row_sede:
                    columns_sede = [desc[0] for desc in cursor.description]
                    sede = dict(zip(columns_sede, row_sede))
                    cursor.execute('SELECT * FROM societa WHERE id = %s', (sede['societa_id'],))
                    row_soc = cursor.fetchone()
                    if row_soc:
                        columns_soc = [desc[0] for desc in cursor.description]
                        societa = dict(zip(columns_soc, row_soc))
                        cursor.execute('SELECT * FROM area_manager WHERE id = %s', (societa['area_manager_id'],))
                        row_am = cursor.fetchone()
                        if row_am:
                            columns_am = [desc[0] for desc in cursor.description]
                            area_manager = dict(zip(columns_am, row_am))
                            franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()
    # Build the hierarchy for the determined franchisor
    if franchisor_id:
        franchisor = get_franchisor(franchisor_id)
        if franchisor:
            franchisor_dict = {
                'id': franchisor['id'],
                'nome': franchisor['nome'],
                'email': franchisor['email'],
                'type': 'franchisor',
                'area_managers': []
            }
            area_managers = get_area_managers_by_franchisor(franchisor['id'])
            for area_manager in area_managers:
                area_manager_dict = {
                    'id': area_manager['id'],
                    'nome': area_manager['nome'],
                    'cognome': area_manager['cognome'],
                    'email': area_manager['email'],
                    'type': 'area_manager',
                    'societa': []
                }
                societa = get_societa_by_area_manager(area_manager['id'])
                for company in societa:
                    company_dict = {
                        'id': company['id'],
                        'nome': company['nome'],
                        'type': 'societa',
                        'email': company['email'],
                        'password': company['password'],
                        'indirizzo': company['indirizzo'],
                        'comune': company['comune'],
                        'provincia': company['provincia'],
                        'sedi': []
                    }
                    sedi = get_sedi_by_societa(company['id'])
                    for sede in sedi:
                        sede_dict = {
                            'id': sede['id'],
                            'nome': sede['nome'],
                            'email': sede['email'],
                            'indirizzo': sede['indirizzo'],
                            'citta': sede['citta'],
                            'cap': sede['cap'],
                            'type': 'sede',
                            'trainers': get_trainers_by_sede(sede['id'])
                        }
                        company_dict['sedi'].append(sede_dict)
                    area_manager_dict['societa'].append(company_dict)
                franchisor_dict['area_managers'].append(area_manager_dict)
            hierarchy.append(franchisor_dict)
        else:
            hierarchy.append({'area_managers': []})  # Ensure consistent structure for franchisor

    return hierarchy

def get_user_by_email(email):
    """Retrieve a user by their email."""
    conn = get_db_connection()
    try:
        query = 'SELECT * FROM utenti WHERE email = %s'
        cursor = conn.cursor()
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        if user:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, user))
        else:
            return None
    finally:
        conn.close()

def update_franchisor(franchisor_id, nome, email, password):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera la vecchia email
        cursor.execute('SELECT email FROM franchisor WHERE id = %s', (franchisor_id,))
        row = cursor.fetchone()
        old_email = row[0] if row else None

        # Aggiorna franchisor
        cursor.execute('''
            UPDATE franchisor 
            SET nome = %s, email = %s, password = %s
            WHERE id = %s
        ''', (nome, email, password, franchisor_id))

        # Aggiorna utente associato usando la vecchia email
        if old_email:
            cursor.execute('''
                UPDATE utenti
                SET nome = %s, email = %s, password = %s
                WHERE ruolo = 'franchisor' AND email = %s
            ''', (nome, email, password, old_email))

        conn.commit()
    except Exception as e:
        print(f"Error updating franchisor: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_franchisor(franchisor_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera l'email del franchisor
        cursor.execute('SELECT email FROM franchisor WHERE id = %s', (franchisor_id,))
        row = cursor.fetchone()
        franchisor_email = row[0] if row else None

        # First, get all area managers associated with the franchisor
        cursor.execute('SELECT id FROM area_manager WHERE franchisor_id = %s', (franchisor_id,))
        area_managers = cursor.fetchall()
        
        # Delete all associated companies and their locations
        for area_manager in area_managers:
            area_manager_id = area_manager[0]
            # Delete all associated locations
            cursor.execute('DELETE FROM sede WHERE societa_id IN (SELECT id FROM societa WHERE area_manager_id = %s)', (area_manager_id,))
            # Delete all associated companies
            cursor.execute('DELETE FROM societa WHERE area_manager_id = %s', (area_manager_id,))
        
        # Finally, delete the area managers
        cursor.execute('DELETE FROM area_manager WHERE franchisor_id = %s', (franchisor_id,))
        
        # Then, delete the franchisor
        cursor.execute('DELETE FROM franchisor WHERE id = %s', (franchisor_id,))

        # Cancella anche l'utente associato
        if franchisor_email:
            cursor.execute('DELETE FROM utenti WHERE email = %s AND ruolo = %s', (franchisor_email, 'franchisor'))
        
        conn.commit()
    except Exception as e:
        print(f"Error deleting franchisor: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_area_manager(area_manager_id, nome, cognome, email, password):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera la vecchia email
        cursor.execute('SELECT email FROM area_manager WHERE id = %s', (area_manager_id,))
        row = cursor.fetchone()
        old_email = row[0] if row else None

        # Aggiorna area manager
        cursor.execute('''
            UPDATE area_manager 
            SET nome = %s, cognome = %s, email = %s, password = %s
            WHERE id = %s
        ''', (nome, cognome, email, password, area_manager_id))

        # Aggiorna utente associato usando la vecchia email
        if old_email:
            cursor.execute('''
                UPDATE utenti
                SET nome = %s, cognome = %s, email = %s, password = %s
                WHERE ruolo = 'area manager' AND email = %s
            ''', (nome, cognome, email, password, old_email))

        conn.commit()
    except Exception as e:
        print(f"Error updating area manager: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_area_manager(area_manager_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM area_manager WHERE id = %s', (area_manager_id,))
        row = cursor.fetchone()
        area_manager_email = row[0] if row else None
        # Controlla se l'area manager è di default
        cursor.execute('SELECT "default" FROM area_manager WHERE id = %s', (area_manager_id,))
        row = cursor.fetchone()
        if row and row[0]:
            flash("Non è possibile cancellare l'area manager di default.", "danger")
            return False
        # Elimina tutte le sedi e società collegate
        cursor.execute('SELECT id FROM societa WHERE area_manager_id = %s', (area_manager_id,))
        companies = cursor.fetchall()
        for company in companies:
            company_id = company[0]
            cursor.execute('DELETE FROM sede WHERE societa_id = %s', (company_id,))
        cursor.execute('DELETE FROM societa WHERE area_manager_id = %s', (area_manager_id,))
        # Elimina l'area manager
        cursor.execute('DELETE FROM area_manager WHERE id = %s', (area_manager_id,))
        # Cancella anche l'utente associato
        if area_manager_email:
            cursor.execute('DELETE FROM utenti WHERE email = %s AND ruolo = %s', (area_manager_email, 'area manager'))
        conn.commit()
        return True
    except Exception as e:
        if 'violates foreign key constraint' in str(e) or 'chiave esterna' in str(e):
            flash("Cancellazione non possibile: l'area manager ha delle sotto-componenti ancora presenti.", "danger")
        else:
            flash(f"Errore durante la cancellazione dell'area manager: {e}", "danger")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_company(company_id, nome, email, password, indirizzo, provincia, comune):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera la vecchia email
        cursor.execute('SELECT email FROM societa WHERE id = %s', (company_id,))
        row = cursor.fetchone()
        old_email = row[0] if row else None

        # Aggiorna la società
        cursor.execute('''
            UPDATE societa 
            SET nome = %s, email = %s, password = %s, indirizzo = %s, provincia = %s, comune = %s
            WHERE id = %s
        ''', (nome, email, password, indirizzo, provincia, comune, company_id))

        # Aggiorna utente associato usando la vecchia email
        if old_email:
            cursor.execute('''
                UPDATE utenti
                SET nome = %s, email = %s, password = %s
                WHERE ruolo = 'societa' AND email = %s
            ''', (nome, email, password, old_email))

        conn.commit()
    except Exception as e:
        print(f"Error updating company: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_company(company_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM societa WHERE id = %s', (company_id,))
        row = cursor.fetchone()
        company_email = row[0] if row else None
        # Controlla se la società è di default
        cursor.execute('SELECT "default" FROM societa WHERE id = %s', (company_id,))
        row = cursor.fetchone()
        if row and row[0]:
            flash("Non è possibile cancellare la società di default.", "danger")
            return False
        # First, delete all associated locations
        cursor.execute('DELETE FROM sede WHERE societa_id = %s', (company_id,))
        # Then, delete the company
        cursor.execute('DELETE FROM societa WHERE id = %s', (company_id,))
        # Cancella anche l'utente associato
        if company_email:
            cursor.execute('DELETE FROM utenti WHERE email = %s AND ruolo = %s', (company_email, 'societa'))
        conn.commit()
        return True
    except Exception as e:
        # Se l'errore è di vincolo di chiave esterna, mostra il messaggio custom
        if 'violates foreign key constraint' in str(e) or 'chiave esterna' in str(e):
            flash("Cancellazione non possibile: la società ha delle sotto-componenti (es. sedi o trainer) ancora presenti.", "danger")
        else:
            flash(f"Errore durante la cancellazione della società: {e}", "danger")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_sede(sede_id, nome, indirizzo, citta, cap, email, password):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera la vecchia email
        cursor.execute('SELECT email FROM sede WHERE id = %s', (sede_id,))
        row = cursor.fetchone()
        old_email = row[0] if row else None

        # Aggiorna la sede
        cursor.execute('''
            UPDATE sede 
            SET nome = %s, indirizzo = %s, citta = %s, cap = %s, email = %s, password = %s
            WHERE id = %s
        ''', (nome, indirizzo, citta, cap, email, password, sede_id))

        # Aggiorna utente associato usando la vecchia email
        if old_email:
            cursor.execute('''
                UPDATE utenti
                SET nome = %s, email = %s, password = %s
                WHERE ruolo = 'sede' AND email = %s
            ''', (nome, email, password, old_email))

        conn.commit()
    except Exception as e:
        print(f"Error updating sede: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_sede(sede_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM sede WHERE id = %s', (sede_id,))
        row = cursor.fetchone()
        sede_email = row[0] if row else None
        # Controlla se la sede è di default
        cursor.execute('SELECT "default" FROM sede WHERE id = %s', (sede_id,))
        row = cursor.fetchone()
        if row and row[0]:
            flash("Non è possibile cancellare la sede di default.", "danger")
            return False
        cursor.execute('DELETE FROM sede WHERE id = %s', (sede_id,))
        if sede_email:
            cursor.execute('DELETE FROM utenti WHERE email = %s AND ruolo = %s', (sede_email, 'sede'))
        conn.commit()
        return True
    except Exception as e:
        if 'violates foreign key constraint' in str(e) or 'chiave esterna' in str(e):
            flash("Cancellazione non possibile: la sede ha delle sotto-componenti (trainer e/o clienti) ancora presenti.", "danger")
        else:
            flash(f"Errore durante la cancellazione della sede: {e}", "danger")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_trainer(trainer_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera l'email del trainer
        cursor.execute('SELECT email FROM trainer WHERE id = %s', (trainer_id,))
        row = cursor.fetchone()
        trainer_email = row[0] if row else None

        cursor.execute('DELETE FROM trainer WHERE id = %s', (trainer_id,))

        # Cancella anche l'utente associato
        if trainer_email:
            cursor.execute('DELETE FROM utenti WHERE email = %s AND ruolo = %s', (trainer_email, 'trainer'))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting trainer: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_trainer(trainer_id, nome, cognome, email, password):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera la vecchia email
        cursor.execute('SELECT email FROM trainer WHERE id = %s', (trainer_id,))
        row = cursor.fetchone()
        old_email = row[0] if row else None

        # Aggiorna trainer
        cursor.execute('''
            UPDATE trainer
            SET nome = %s, cognome = %s, email = %s, password = %s
            WHERE id = %s
        ''', (nome, cognome, email, password, trainer_id))

        # Aggiorna utente associato usando la vecchia email
        if old_email:
            cursor.execute('''
                UPDATE utenti
                SET nome = %s, cognome = %s, email = %s, password = %s
                WHERE ruolo = 'trainer' AND email = %s
            ''', (nome, cognome, email, password, old_email))

        conn.commit()
    except Exception as e:
        print(f"Error updating trainer: {e}")
        conn.rollback()
    finally:
        conn.close()

def register_franchisor(nome_franchisor, email, password):
    """
    Registra un nuovo franchisor e crea l'utente associato.
    Restituisce True se tutto ok, False altrimenti.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Inserisci il franchisor
        cursor.execute(
            "INSERT INTO franchisor (nome, email, password) VALUES (%s, %s, %s) RETURNING id",
            (nome_franchisor, email, password)
        )
        franchisor_id = cursor.fetchone()[0]

        # Inserisci l'utente associato
        cursor.execute(
            """
            INSERT INTO utenti (nome, cognome, email, password, ruolo)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nome_franchisor, '', email, password, 'franchisor')
        )

        conn.commit()
        return True
    except Exception as e:
        print("Errore durante la registrazione del franchisor:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def register_area_manager(nome, cognome, email, password, franchisor_id):
    """
    Registra un nuovo area manager e crea l'utente associato.
    Restituisce True se tutto ok, False altrimenti.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Inserisci l'area manager
        cursor.execute(
            "INSERT INTO area_manager (nome, cognome, email, password, franchisor_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (nome, cognome, email, password, franchisor_id)
        )
        area_manager_id = cursor.fetchone()[0]

        # Inserisci l'utente associato
        cursor.execute(
            """
            INSERT INTO utenti (nome, cognome, email, password, ruolo)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nome, cognome, email, password, 'area manager')
        )

        conn.commit()
        return True
    except Exception as e:
        print("Errore durante la registrazione dell'area manager:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def register_societa(area_manager_id, nome, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO societa (area_manager_id, nome, email, password) VALUES (%s, %s, %s, %s) RETURNING id',
            (area_manager_id, nome, email, password)
        )
        societa_id = cursor.fetchone()[0]
        user_created = create_user(cursor, nome, '', email, password, 'societa')  # Pass cursor instead of creating a new connection

        conn.commit()
        return societa_id if user_created else None
    except Exception as e:
        print(f"Errore durante la registrazione della società: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def register_sede(societa_id, nome, indirizzo, citta, cap, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO sede (societa_id, nome, indirizzo, citta, cap, email, password) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (societa_id, nome, indirizzo, citta, cap, email, password)
        )
        sede_id = cursor.fetchone()[0]
        user_created = create_user(cursor, nome, '', email, password, 'sede')  # Pass cursor instead of creating a new connection

        conn.commit()
        return sede_id if user_created else None
    except Exception as e:
        print(f"Errore durante la registrazione della sede: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def register_trainer(sede_id, nome, cognome, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert the trainer into the trainer table
        cursor.execute(''' 
            INSERT INTO trainer (sede_id, nome, cognome, email, password) 
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (sede_id, nome, cognome, email, password))
        trainer_id = cursor.fetchone()[0]
        
        # Create a new user with the provided credentials using the same connection
        user_created = create_user(cursor, nome, cognome, email, password, 'trainer')  # Pass cursor instead of creating a new connection

        conn.commit()
        return trainer_id if user_created else None
    except Exception as e:
        print(f"Errore durante la registrazione del trainer: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def create_user(cursor, nome, cognome, email, password, role):
    try:
        cursor.execute('''
            INSERT INTO utenti (nome, cognome, email, password, ruolo)
            VALUES (%s, %s, %s, %s, %s)
        ''', (nome, cognome, email, password, role))  # Use the passed cursor
        return True
    except Exception as e:
        print(f"Errore durante la creazione dell'utente: {e}")
        return False

def get_trainer_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trainer WHERE email = %s', (email,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

def get_trainers_by_sede(sede_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trainer WHERE sede_id = %s', (sede_id,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    trainers = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return trainers

def crea_nuova_rata(abbonamento_id, importo, data_scadenza):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO rate (abbonamento_id, importo, data_scadenza, pagato, numero_rata)
            VALUES (%s, %s, %s, %s, (SELECT COALESCE(MAX(numero_rata), 0) + 1 FROM rate WHERE abbonamento_id = %s))
        ''', (abbonamento_id, importo, data_scadenza, False, abbonamento_id))
        conn.commit()
    except Exception as e:
        print(f"Errore durante la creazione della nuova rata: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_franchisor_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM franchisor WHERE email = %s", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None

def get_sede_by_email(email):
    """Fetch the sede details by email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sede WHERE email = %s', (email,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

def get_sedi_by_societa_email(email):
    """Fetch all sedi under a societa by the societa's email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM societa WHERE email = %s', (email,))
    societa = cursor.fetchone()
    if societa:
        societa_id = societa[0]  # Assumendo che l'id sia la prima colonna
        cursor.execute('SELECT * FROM sede WHERE societa_id = %s', (societa_id,))
        sedi_rows = cursor.fetchall()
        sedi_columns = [desc[0] for desc in cursor.description]
        sedi = [dict(zip(sedi_columns, row)) for row in sedi_rows]
    else:
        sedi = []
    conn.close()
    return sedi

def get_societa_by_area_manager_email(email):
    """Fetch all societa under an area manager by the area manager's email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM area_manager WHERE email = %s', (email,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        area_manager = dict(zip(columns, row))
        cursor.execute('SELECT * FROM societa WHERE area_manager_id = %s', (area_manager['id'],))
        societa_rows = cursor.fetchall()
        societa_columns = [desc[0] for desc in cursor.description]
        societa = [dict(zip(societa_columns, r)) for r in societa_rows]
    else:
        societa = []
    conn.close()
    return societa

def get_area_managers_by_franchisor_email(email):
    """
    Restituisce una lista di area manager associati al franchisor identificato dall'email.
    Ogni area manager è restituito come dizionario.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # Recupera il franchisor tramite email
    cursor.execute('SELECT id FROM franchisor WHERE email = %s', (email,))
    franchisor_row = cursor.fetchone()
    if not franchisor_row:
        conn.close()
        return []
    franchisor_id = franchisor_row[0]
    # Recupera gli area manager associati
    cursor.execute('SELECT * FROM area_manager WHERE franchisor_id = %s', (franchisor_id,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    area_managers = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return area_managers

def get_sedi_by_franchisor_email(email):
    """Fetch all sedi under a franchisor by the franchisor's email."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM franchisor WHERE email = %s', (email,))
        franchisor = cursor.fetchone()
        if franchisor:
            franchisor_id = franchisor[0]
            cursor.execute('''
                SELECT s.* 
                FROM sede s
                JOIN societa so ON s.societa_id = so.id
                JOIN area_manager am ON so.area_manager_id = am.id
                WHERE am.franchisor_id = %s
            ''', (franchisor_id,))
            sedi = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in sedi]
        return []
    finally:
        conn.close()

def get_area_manager_by_email(email):
    """Fetch the area manager details by email."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM area_manager WHERE email = %s', (email,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    finally:
        conn.close()

def get_sede_by_trainer_email(email):
    """Fetch the sede associated with a trainer by their email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trainer WHERE email = %s', (email,))
    trainer_row = cursor.fetchone()
    if trainer_row:
        columns_trainer = [desc[0] for desc in cursor.description]
        trainer = dict(zip(columns_trainer, trainer_row))
        cursor.execute('SELECT * FROM sede WHERE id = %s', (trainer['sede_id'],))
        sede_row = cursor.fetchone()
        if sede_row:
            columns_sede = [desc[0] for desc in cursor.description]
            sede = dict(zip(columns_sede, sede_row))
        else:
            sede = None
    else:
        sede = None
    conn.close()
    return sede

def get_societa_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM societa WHERE email = %s', (email,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    conn.close()
    return None

def get_user_email_by_id(user_id):
    """
    Fetch the email of a user based on their ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM utenti WHERE id = %s', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def log_event(utente_id, email, azione, dettagli=None):
    """Inserisce un evento nella tabella eventi."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO eventi (utente_id, email, azione, dettagli)
            VALUES (%s, %s, %s, %s)
        ''', (utente_id, email, azione, dettagli))
        conn.commit()
    finally:
        conn.close()

def get_all_eventi():
    """Recupera tutti gli eventi dalla tabella eventi."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM eventi ORDER BY data_evento DESC')
        eventi = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in eventi]
    finally:
        conn.close()

def is_trainer_present(trainer_id):
    """Check if the trainer's last action was 'entra'."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT azione FROM eventi
            WHERE utente_id = %s AND (azione = 'entra' OR azione = 'esci')
            ORDER BY data_evento DESC
            LIMIT 1
        ''', (trainer_id,))
        row = cursor.fetchone()
        if row:
            return row[0] == 'entra'
        return False
    finally:
        conn.close()

def get_trainers_with_status(sede_ids):
    """Fetch trainers and their current status (entered or not) for the given sede_ids."""
    conn = get_db_connection()
    try:
        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f'''
            SELECT 
                t.id, 
                t.nome, 
                t.cognome, 
                t.email,
                COALESCE((
                    SELECT e.azione
                    FROM eventi e
                    WHERE e.email = t.email AND (e.azione = 'entra' OR e.azione = 'esci')
                    ORDER BY e.data_evento DESC
                    LIMIT 1
                ), 'esci') AS stato
            FROM trainer t
            WHERE t.sede_id IN ({placeholders})
            ORDER BY t.cognome, t.nome
        '''
        cursor = conn.cursor()
        cursor.execute(query, sede_ids)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        trainers = [dict(zip(columns, row)) for row in rows]
        return trainers
    finally:
        conn.close()

def add_resoconto(trainer_id, data, ore_lavoro, ore_buca, attivita_buca):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resoconti (trainer_id, data, ore_lavoro, ore_buca, attivita_buca)
        VALUES (%s, %s, %s, %s, %s)
    ''', (trainer_id, data, ore_lavoro, ore_buca, attivita_buca))
    conn.commit()
    conn.close()

def get_resoconti_by_trainer(trainer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM resoconti WHERE trainer_id = %s ORDER BY data DESC
    ''', (trainer_id,))
    resoconti = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    result = [dict(zip(columns, row)) for row in resoconti]
    conn.close()
    return result

def get_resoconto(resoconto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM resoconti WHERE id = %s
    ''', (resoconto_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

def create_appointments_table():
    conn = get_db_connection()
    try:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            notes TEXT,
            date_time DATETIME NOT NULL,
            appointment_type TEXT NOT NULL,
            status TEXT NOT NULL,
            is_trial BOOLEAN DEFAULT 0,
            is_recovery BOOLEAN DEFAULT 0,
            is_lesson_zero BOOLEAN DEFAULT 0,
            FOREIGN KEY (trainer_id) REFERENCES trainer (id),
            FOREIGN KEY (client_id) REFERENCES clienti (id)
        )
        ''')
        conn.commit()
    finally:
        conn.close()

from dateutil.parser import parse  # Importa il parser per gestire i formati ISO 8601

def get_appointments_by_users(user_ids, start_date):
    if not user_ids:
        return []
    conn = get_db_connection()
    try:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = start_date_dt + timedelta(days=365)
        start_date_str = start_date_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_date_str = end_date_dt.strftime('%Y-%m-%d %H:%M:%S')

        placeholders = ','.join(['%s'] * len(user_ids))
        query = f'''
            SELECT DISTINCT a.*, 
                c.nome || ' ' || c.cognome AS client_name, 
                u.nome || ' ' || u.cognome AS trainer_name,
                c.tipo AS client_tipo,
                ab.numero_lezioni,
                ab.lezioni_utilizzate,
                ab.pacchetto_id
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            JOIN utenti u ON a.created_by = u.id
            LEFT JOIN abbonamenti ab ON a.client_id = ab.cliente_id AND a.package_id = ab.id
            WHERE a.created_by IN ({placeholders})
            AND a.date_time BETWEEN %s AND %s
            ORDER BY a.client_id, a.package_id, a.date_time ASC
        '''
        params = user_ids + [start_date_str, end_date_str]
        cursor = conn.cursor()
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        appointments = [dict(zip(columns, row)) for row in appointments]

        # Calcolo progressivo X/N
        # Calcolo progressivo X/N
        # Usa il progressivo fisso salvato nel DB
        for app in appointments:
            if app['appointment_type'] in ['Allenamento Funzionale', 'Allenamento EMS', 'Allenamento VacuLab']:
                app['lezione_numero'] = app.get('progressivo_lezione')
                app['numero_lezioni'] = app.get('numero_lezioni', 0) or 0
            else:
                app['lezione_numero'] = None
                app['numero_lezioni'] = None

        return appointments
    finally:
        conn.close()

def get_appointments_by_clienti(clienti_ids, start_date):
    """
    Recupera gli appuntamenti per una lista di clienti a partire da una data specifica.
    :param clienti_ids: Lista di ID dei clienti.
    :param start_date: Data di inizio (stringa in formato 'YYYY-MM-DD').
    :return: Lista di appuntamenti.
    """
    if not clienti_ids:
        return []
    conn = get_db_connection()
    try:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = start_date_dt + timedelta(days=60)
        start_date_str = start_date_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_date_str = end_date_dt.strftime('%Y-%m-%d %H:%M:%S')
        placeholders = ','.join(['%s'] * len(clienti_ids))
        query = f'''
            SELECT a.*, c.nome || ' ' || c.cognome AS client_name
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            WHERE a.client_id IN ({placeholders})
            AND a.date_time BETWEEN %s AND %s
            ORDER BY a.date_time ASC
        '''
        params = clienti_ids + [start_date_str, end_date_str]
        cursor = conn.cursor()
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        parsed_appointments = []
        for row in appointments:
            appointment = dict(zip(columns, row))
            try:
                appointment['date_time'] = datetime.strptime(str(appointment['date_time']), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['date_time'] = datetime.strptime(str(appointment['date_time']), '%Y-%m-%dT%H:%M')
            parsed_appointments.append(appointment)
        return parsed_appointments
    finally:
        conn.close()


def add_appointment(user_id, client_id, title, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        progressivo_lezione = None
        # Calcola il progressivo solo per le lezioni vere
        if appointment_type in ['Allenamento Funzionale', 'Allenamento EMS', 'Allenamento VacuLab'] and package_id:
            # Conta lezioni completate
            cursor.execute('''
                SELECT COUNT(*) FROM appointments
                WHERE client_id = %s AND package_id = %s AND completed = TRUE
            ''', (client_id, package_id))
            completate = cursor.fetchone()[0]
            # Conta appuntamenti futuri non completati
            cursor.execute('''
                SELECT COUNT(*) FROM appointments
                WHERE client_id = %s AND package_id = %s AND completed = FALSE
            ''', (client_id, package_id))
            non_completate = cursor.fetchone()[0]
            progressivo_lezione = completate + non_completate + 1

        cursor.execute('''
            INSERT INTO appointments (
                created_by, client_id, title, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id, progressivo_lezione
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, client_id, title, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id, progressivo_lezione))
        appointment_id = cursor.fetchone()[0]
        conn.commit()
        return appointment_id
    except Exception as e:
        print(f"Errore durante l'aggiunta dell'appuntamento: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_appointment_by_id(appointment_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                a.*, 
                c.nome || ' ' || c.cognome AS client_name, 
                u.nome || ' ' || u.cognome AS trainer_name,
                ab.id AS package_id,
                ab.numero_lezioni,
                ab.lezioni_utilizzate
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            JOIN utenti u ON a.created_by = u.id
            LEFT JOIN abbonamenti ab ON a.package_id = ab.id
            WHERE a.id = %s
        ''', (appointment_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            appointment = dict(zip(columns, row))
            try:
                appointment['date_time'] = datetime.strptime(str(appointment['date_time']), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['date_time'] = datetime.strptime(str(appointment['date_time']), '%Y-%m-%dT%H:%M')
            try:
                appointment['end_date_time'] = datetime.strptime(str(appointment['end_date_time']), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['end_date_time'] = datetime.strptime(str(appointment['end_date_time']), '%Y-%m-%dT%H:%M')
            return appointment
        return None
    finally:
        conn.close()

def delete_appointment(appointment_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM appointments WHERE id = %s', (appointment_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore eliminazione appuntamento: {e}")
        return False
    finally:
        conn.close()

def get_appointments_by_trainers(trainer_ids, start_date):
    """Retrieve appointments for multiple trainers starting from a specific date (PostgreSQL version)."""
    conn = get_db_connection()
    try:
        # Calculate the end date (7 days from the start date)
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = start_date_dt + timedelta(days=7)
        start_date_str = start_date_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_date_str = end_date_dt.strftime('%Y-%m-%d %H:%M:%S')

        # Query to fetch appointments
        placeholders = ','.join(['%s'] * len(trainer_ids))
        query = f'''
            SELECT a.*, c.nome || ' ' || c.cognome AS client_name
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            WHERE a.trainer_id IN ({placeholders})
            AND a.date_time BETWEEN %s AND %s
            ORDER BY a.date_time ASC
        '''
        params = trainer_ids + [start_date_str, end_date_str]
        cursor = conn.cursor()
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Parse date_time and end_date_time into datetime objects
        parsed_appointments = []
        for row in appointments:
            appointment = dict(zip(columns, row))
            try:
                appointment['date_time'] = datetime.strptime(str(appointment['date_time']), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['date_time'] = datetime.strptime(str(appointment['date_time']), '%Y-%m-%dT%H:%M')
            try:
                appointment['end_date_time'] = datetime.strptime(str(appointment['end_date_time']), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['end_date_time'] = datetime.strptime(str(appointment['end_date_time']), '%Y-%m-%dT%H:%M')
            parsed_appointments.append(appointment)

        return parsed_appointments
    finally:
        conn.close()

def migrate_appointments_table():
    conn = get_db_connection()
    try:
        conn.execute('''
        ALTER TABLE appointments ADD COLUMN package_id INTEGER
        ''')
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("La colonna 'package_id' esiste già.")
        else:
            print(f"Errore durante la migrazione: {e}")
    finally:
        conn.close()

def update_appointment(appointment_id, title, client_id, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero):
    """
    Aggiorna un appuntamento esistente nel database.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE appointments
        SET title = %s,
            client_id = %s,          
            notes = %s, 
            date_time = %s, 
            end_date_time = %s, 
            appointment_type = %s, 
            status = %s, 
            is_trial = %s, 
            is_recovery = %s, 
            is_lesson_zero = %s
        WHERE id = %s
        ''', (title, client_id, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, appointment_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento dell'appuntamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_appointments_by_sedi(sede_ids, da=None, a=None):
    """
    Recupera gli appuntamenti per un elenco di sedi tra le date da e a.
    Se da e a non sono specificate, mostra il mese corrente.
    """
    conn = get_db_connection()
    try:
        if da and a:
            start_date = datetime.strptime(da, '%Y-%m-%d')
            end_date = datetime.strptime(a, '%Y-%m-%d') + timedelta(days=1)
        elif da:
            start_date = datetime.strptime(da, '%Y-%m-%d')
            end_date = start_date + timedelta(days=31)
        elif a:
            end_date = datetime.strptime(a, '%Y-%m-%d') + timedelta(days=1)
            start_date = end_date - timedelta(days=31)
        else:
            today = datetime.now()
            start_date = today.replace(day=1)
            next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_date = next_month

        start_date_str = start_date.strftime('%Y-%m-%d 00:00:00')
        end_date_str = end_date.strftime('%Y-%m-%d 23:59:59')

        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f'''
            SELECT 
                a.*, 
                c.nome || ' ' || c.cognome AS client_name, 
                u.nome || ' ' || u.cognome AS user_name
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            JOIN utenti u ON a.created_by = u.id
            WHERE c.sede_id IN ({placeholders})
            AND a.date_time BETWEEN %s AND %s
            ORDER BY a.date_time ASC
        '''
        params = sede_ids + [start_date_str, end_date_str]
        cursor = conn.cursor()
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in appointments]
    finally:
        conn.close()

def mark_appointment_completed(appointment_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE appointments SET completed = TRUE WHERE id = %s', (appointment_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante il completamento dell'appuntamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def ensure_minimum_hierarchy():
    """
    Garantisce che esista almeno un franchisor, area manager, societa, sede e relativi utenti.
    Se non esistono, li crea con dati di default.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Franchisor
        cursor.execute("SELECT id, email, password FROM franchisor LIMIT 1")
        franchisor = cursor.fetchone()
        if not franchisor:
            franchisor_email = "franchisor@example.com"
            franchisor_password = "password"
            cursor.execute(
                'INSERT INTO franchisor (nome, email, password, "default") VALUES (%s, %s, %s, %s) RETURNING id',
                ("Franchisor Default", franchisor_email, franchisor_password, True)
            )
            franchisor_id = cursor.fetchone()[0]
            # Crea utente franchisor
            cursor.execute(
                "INSERT INTO utenti (nome, cognome, email, password, ruolo) VALUES (%s, %s, %s, %s, %s)",
                ("Franchisor", "Default", franchisor_email, franchisor_password, "franchisor")
            )
        else:
            franchisor_id = franchisor[0]
            franchisor_email = franchisor[1]
            franchisor_password = franchisor[2]

        # 2. Area Manager
        cursor.execute("SELECT id, email, password FROM area_manager WHERE franchisor_id = %s LIMIT 1", (franchisor_id,))
        area_manager = cursor.fetchone()
        if not area_manager:
            area_manager_email = "areamanager@example.com"
            area_manager_password = "password"
            cursor.execute(
                'INSERT INTO area_manager (nome, cognome, email, password, franchisor_id, "default") VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                ("Area", "Manager", area_manager_email, area_manager_password, franchisor_id, True)
            )
            area_manager_id = cursor.fetchone()[0]
            # Crea utente area manager
            cursor.execute(
                "INSERT INTO utenti (nome, cognome, email, password, ruolo) VALUES (%s, %s, %s, %s, %s)",
                ("Area", "Manager", area_manager_email, area_manager_password, "area manager")
            )
        else:
            area_manager_id = area_manager[0]
            area_manager_email = area_manager[1]
            area_manager_password = area_manager[2]

        # 3. Societa
        cursor.execute("SELECT id, email, password FROM societa WHERE area_manager_id = %s LIMIT 1", (area_manager_id,))
        societa = cursor.fetchone()
        if not societa:
            societa_email = "societa@example.com"
            societa_password = "password"
            cursor.execute(
                'INSERT INTO societa (area_manager_id, nome, email, password, "default") VALUES (%s, %s, %s, %s, %s) RETURNING id',
                (area_manager_id, "Società Default", societa_email, societa_password, True)
            )
            societa_id = cursor.fetchone()[0]
            # Crea utente societa
            cursor.execute(
                "INSERT INTO utenti (nome, cognome, email, password, ruolo) VALUES (%s, %s, %s, %s, %s)",
                ("Società", "Default", societa_email, societa_password, "societa")
            )
        else:
            societa_id = societa[0]
            societa_email = societa[1]
            societa_password = societa[2]

        # 4. Sede
        cursor.execute("SELECT id, email, password FROM sede WHERE societa_id = %s LIMIT 1", (societa_id,))
        sede = cursor.fetchone()
        if not sede:
            sede_email = "sede@example.com"
            sede_password = "password"
            cursor.execute(
                'INSERT INTO sede (societa_id, nome, indirizzo, citta, cap, email, password, "default") VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
                (societa_id, "Sede Default", "Via Roma 1", "Milano", "20100", sede_email, sede_password, True)
            )
            sede_id = cursor.fetchone()[0]
            # Crea utente sede
            cursor.execute(
                "INSERT INTO utenti (nome, cognome, email, password, ruolo) VALUES (%s, %s, %s, %s, %s)",
                ("Sede", "Default", sede_email, sede_password, "sede")
            )
        # Se vuoi puoi aggiungere anche un trainer di default qui

        conn.commit()
    except Exception as e:
        print(f"Errore in ensure_minimum_hierarchy: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_appointment_status_and_notes(appointment_id, new_status, notes):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE appointments
            SET status = %s, notes = %s
            WHERE id = %s
        ''', (new_status, notes, appointment_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento dello stato e delle note dell'appuntamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_abbonamenti_upgrade(sede_ids, da, a):
    conn = get_db_connection()
    try:
        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f'''
            SELECT ab.*, c.nome, c.cognome, p.nome AS pacchetto_nome
            FROM abbonamenti ab
            JOIN clienti c ON ab.cliente_id = c.id
            JOIN pacchetti p ON ab.pacchetto_id = p.id
            WHERE ab.sede_id IN ({placeholders})
            AND ab.data_inizio BETWEEN %s AND %s
            AND LOWER(p.nome) = 'upgrade'
            ORDER BY ab.data_inizio DESC
        '''
        params = sede_ids + [da, a]
        cursor = conn.cursor()
        cursor.execute(query, params)
        abbonamenti = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in abbonamenti]
    finally:
        conn.close()

def get_rinnovi_effettuati(sede_ids, da, a):
    """
    Restituisce tutti gli abbonamenti che NON sono il primo per ciascun cliente,
    con data_inizio tra da e a e sede tra quelle indicate.
    """
    conn = get_db_connection()
    try:
        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f"""
            SELECT ab.*, c.nome, c.cognome, p.nome AS pacchetto_nome
            FROM abbonamenti ab
            JOIN clienti c ON ab.cliente_id = c.id
            JOIN pacchetti p ON ab.pacchetto_id = p.id
            WHERE ab.sede_id IN ({placeholders})
            AND ab.data_inizio BETWEEN %s AND %s
            AND p.nome NOT LIKE 'Upgrade'
            AND ab.id NOT IN (
                SELECT MIN(id) FROM abbonamenti
                WHERE sede_id IN ({placeholders})
                GROUP BY cliente_id
            )
            ORDER BY ab.data_inizio DESC
        """
        params = sede_ids + [da, a] + sede_ids
        cursor = conn.cursor()
        cursor.execute(query, params)
        abbonamenti = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in abbonamenti]
    finally:
        conn.close()


def get_rinnovi_non_effettuati(sede_ids, da, a):
    """
    Restituisce tutti gli abbonamenti che sono terminati (lezioni_utilizzate = numero_lezioni)
    e per cui NON esiste un altro abbonamento per lo stesso cliente con data_inizio successiva.
    """
    conn = get_db_connection()
    try:
        placeholders = ','.join(['%s'] * len(sede_ids))
        query = f"""
            SELECT ab.*, c.nome, c.cognome, p.nome AS pacchetto_nome
            FROM abbonamenti ab
            JOIN clienti c ON ab.cliente_id = c.id
            JOIN pacchetti p ON ab.pacchetto_id = p.id
            WHERE ab.sede_id IN ({placeholders})
            AND ab.data_inizio BETWEEN %s AND %s
            AND ab.lezioni_utilizzate = ab.numero_lezioni
            AND NOT EXISTS (
                SELECT 1 FROM abbonamenti ab2
                WHERE ab2.cliente_id = ab.cliente_id
                AND ab2.data_inizio > ab.data_inizio
                AND ab2.sede_id = ab.sede_id
            )
            ORDER BY ab.data_inizio DESC
        """
        params = sede_ids + [da, a]
        cursor = conn.cursor()
        cursor.execute(query, params)
        abbonamenti = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in abbonamenti]
    finally:
        conn.close()


def get_abbonamenti_venduti_mese(sede_ids, data_inizio, data_fine):
    """
    Restituisce un dizionario {nome_pacchetto: numero_venduti} per il mese corrente.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Recupera tutti i pacchetti
        cursor.execute("SELECT id, nome FROM pacchetti")
        pacchetti = cursor.fetchall()
        abbonamenti_venduti = {}
        for pacchetto_id, nome in pacchetti:
            # Conta abbonamenti venduti per pacchetto, sede e mese
            placeholders = ','.join(['%s'] * len(sede_ids))
            query = f"""
                SELECT COUNT(*) FROM abbonamenti
                WHERE pacchetto_id = %s
                AND sede_id IN ({placeholders})
                AND data_inizio BETWEEN %s AND %s
            """
            params = [pacchetto_id] + sede_ids + [data_inizio, data_fine]
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            abbonamenti_venduti[nome] = count
        return abbonamenti_venduti
    finally:
        conn.close()