from app.db.session import Base, engine
from app.models import user, report, biomarker  # noqa: F401 — registers models with Base


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tables created successfully")