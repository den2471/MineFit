from sqlalchemy import create_engine
from schemas import VersionORM, BaseORM
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///cache/modrinth.db', echo=False)
BaseORM.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()
