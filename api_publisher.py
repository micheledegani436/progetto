import asyncio
import json
import tornado.web
from pymongo import AsyncMongoClient

# Connessione al database
client = AsyncMongoClient("mongodb://localhost:27017")
db = client["publishing_db"]
publishers = db["publishers"]
books = db["books"]


# Classe per la gestione delle case editrici
class PublisherHandler(tornado.web.RequestHandler):
    def get(self, p_id=None):
        self.set_header("Content-Type", "application/json")

        # Se non è fornito un ID specifico, ritorna tutte le case editrici con eventuali filtri
        filters = {}
        name_filter = self.get_query_argument('name', None)
        country_filter = self.get_query_argument('country', None)

        if name_filter:
            filters['name'] = name_filter
        if country_filter:
            filters['country'] = country_filter

        if p_id is None:
            results = []
            for doc in publishers.find(filters):
                doc['_id'] = str(doc['_id'])  # Converte _id in stringa per la risposta
                results.append(doc)
            self.write(json.dumps(results))
            self.set_status(200)
        else:
            # Se l'ID è fornito, ritorna solo quella casa editrice
            publisher = publishers.find_one({"_id": p_id})
            if publisher:
                publisher['_id'] = str(publisher['_id'])  # Converte _id in stringa
                self.write(json.dumps(publisher))
                self.set_status(200)
            else:
                self.set_status(404)
                self.write("Casa editrice non trovata")

    def post(self):
        # Aggiungi una nuova casa editrice
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)

        new_publisher = {
            "name": data["name"],
            "founded_year": data["founded_year"],
            "country": data["country"]
        }

        result = publishers.insert_one(new_publisher)
        new_publisher['_id'] = str(result.inserted_id)  # Converte _id in stringa
        self.write(json.dumps({
            "message": "Casa editrice aggiunta con successo",
            "publisher": new_publisher
        }))
        self.set_status(201)

    def put(self, p_id):
        # Modifica una casa editrice
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)

        updated_publisher = {
            "name": data.get("name"),
            "founded_year": data.get("founded_year"),
            "country": data.get("country")
        }

        result = publishers.update_one(
            {"_id": p_id},
            {"$set": updated_publisher}
        )

        if result.modified_count > 0:
            updated_publisher["_id"] = p_id
            self.write(json.dumps({
                "message": "Casa editrice aggiornata con successo",
                "publisher": updated_publisher
            }))
            self.set_status(200)
        else:
            self.set_status(404)
            self.write("Casa editrice non trovata")

    def delete(self, p_id):
        # Elimina una casa editrice
        result = publishers.delete_one({"_id": p_id})

        if result.deleted_count > 0:
            self.write(json.dumps({"message": "Casa editrice eliminata con successo"}))
            self.set_status(200)
        else:
            self.set_status(404)
            self.write("Casa editrice non trovata")


# Classe per la gestione dei libri
class BookHandler(tornado.web.RequestHandler):
    def get(self, p_id, b_id=None):
        self.set_header("Content-Type", "application/json")

        filters = {}
        title_filter = self.get_query_argument('title', None)
        author_filter = self.get_query_argument('author', None)
        genre_filter = self.get_query_argument('genre', None)

        if title_filter:
            filters['title'] = title_filter
        if author_filter:
            filters['author'] = author_filter
        if genre_filter:
            filters['genre'] = genre_filter

        # Se b_id è None, ritorna tutti i libri per quella casa editrice
        if b_id is None:
            results = []
            for doc in books.find({"publisher_id": p_id, **filters}):
                doc['_id'] = str(doc['_id'])  # Converte _id in stringa
                doc['publisher_id'] = str(doc['publisher_id'])  # Converte publisher_id in stringa
                results.append(doc)
            self.write(json.dumps(results))
            self.set_status(200)
        else:
            # Se b_id è fornito, ritorna solo quel libro
            book = books.find_one({"_id": b_id, "publisher_id": p_id})
            if book:
                book['_id'] = str(book['_id'])  # Converte _id in stringa
                book['publisher_id'] = str(book['publisher_id'])  # Converte publisher_id in stringa
                self.write(json.dumps(book))
                self.set_status(200)
            else:
                self.set_status(404)
                self.write("Libro non trovato")

    def post(self, p_id):
        # Aggiungi un nuovo libro per la casa editrice
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)

        new_book = {
            "title": data["title"],
            "author": data["author"],
            "genre": data["genre"],
            "year": data["year"],
            "publisher_id": p_id  # L'ID del publisher è una stringa
        }

        result = books.insert_one(new_book)
        new_book['_id'] = str(result.inserted_id)  # Converte _id in stringa
        new_book['publisher_id'] = p_id  # publisher_id in stringa
        self.write(json.dumps({
            "message": "Libro aggiunto con successo",
            "book": new_book
        }))
        self.set_status(201)

    def put(self, p_id, b_id):
        # Modifica un libro
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)

        updated_book = {
            "title": data.get("title"),
            "author": data.get("author"),
            "genre": data.get("genre"),
            "year": data.get("year")
        }

        result = books.update_one(
            {"_id": b_id, "publisher_id": p_id},
            {"$set": updated_book}
        )

        if result.modified_count > 0:
            updated_book["_id"] = b_id
            updated_book["publisher_id"] = p_id
            self.write(json.dumps({
                "message": "Libro aggiornato con successo",
                "book": updated_book
            }))
            self.set_status(200)
        else:
            self.set_status(404)
            self.write("Libro non trovato")

    def delete(self, p_id, b_id):
        # Elimina un libro
        result = books.delete_one({"_id": b_id, "publisher_id": p_id})

        if result.deleted_count > 0:
            self.write(json.dumps({"message": "Libro eliminato con successo"}))
            self.set_status(200)
        else:
            self.set_status(404)
            self.write("Libro non trovato")


# Funzione per creare l'applicazione Tornado
def make_app():
    return tornado.web.Application([
        (r"/publishers", PublisherHandler),
        (r"/publishers/([a-fA-F0-9]{24})", PublisherHandler),  # Match string ID
        (r"/publishers/([a-fA-F0-9]{24})/books", BookHandler),
        (r"/publishers/([a-fA-F0-9]{24})/books/([a-fA-F0-9]{24})", BookHandler),
    ], debug=True)


# Funzione per avviare il server
async def main(shutdown_event):
    app = make_app()
    app.listen(8888)
    print("Server attivo su http://localhost:8888/publishers")
    await shutdown_event.wait()


if __name__ == "__main__":
    shutdown_event = asyncio.Event()
    try:
        asyncio.run(main(shutdown_event))
    except KeyboardInterrupt:
        shutdown_event.set()