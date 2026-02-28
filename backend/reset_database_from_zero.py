import os
import sys

# Add base directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal, Base
from backend import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_database():
    print("Atencao: Este script ira apagar TODAS as tabelas e dados do banco.")
    print("Iniciando a exclusao de todas as tabelas (drop_all)...")
    Base.metadata.drop_all(bind=engine)
    print("-> Tabelas apagadas com sucesso.")
    
    print("\nRecriando todas as tabelas a partir do modelo atual (create_all)...")
    Base.metadata.create_all(bind=engine)
    print("-> Tabelas recriadas com sucesso.")
    
    db = SessionLocal()
    try:
        print("\nCriando usuario administrador padrao (admin / admin123)...")
        # Passlib bcrypt has an issue with some python 3.12 versions and bcrypt.
        import hashlib
        hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
        admin_user = models.User(
            username="admin",
            password=hashed_password,
            full_name="Administrador do Sistema",
            email="admin@sga.com",
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("-> Usuario criado com sucesso!")
        
        print("\nBanco de dados resetado com sucesso! O sistema esta limpo e pronto para novos testes.")
    except Exception as e:
        db.rollback()
        print(f"\nErro ao criar o usuario base: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
