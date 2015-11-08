from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql+psycopg2://adrian@localhost:5432/exam_papers', echo=True)
Session = sessionmaker(bind=engine)