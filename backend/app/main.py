from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Question, Topic

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StudyPilot API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "name": "StudyPilot",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/topics")
def get_topics(db: Session = Depends(get_db)):
    return db.query(Topic).all()


@app.post("/topics")
def create_topic(
    name: str,
    subject: str,
    db: Session = Depends(get_db),
):
    topic = Topic(
        name=name,
        subject=subject,
    )

    db.add(topic)
    db.commit()
    db.refresh(topic)

    return topic


@app.patch("/topics/{topic_id}/complete")
def complete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()

    if not topic:
        return {"error": "Topic not found"}

    topic.completed = True
    db.commit()
    db.refresh(topic)

    return topic


@app.get("/questions")
def get_questions(db: Session = Depends(get_db)):
    return db.query(Question).all()
