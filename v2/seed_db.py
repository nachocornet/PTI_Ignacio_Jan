from database import SessionLocal, engine
import models

def seed():
    # Crea las tablas si no existen
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Insertar datos de prueba si la tabla esta vacia
    if db.query(models.CitizenDB).count() == 0:
        nacho = models.CitizenDB(numero_dni="12345678A", nombre="Nacho", fecha_nacimiento="2000-01-01")
        jan = models.CitizenDB(numero_dni="87654321B", nombre="Jan", fecha_nacimiento="2012-01-01")
        db.add_all([nacho, jan])
        db.commit()
        print("Base de datos poblada con exito")
    db.close()

if __name__ == "__main__":
    seed()