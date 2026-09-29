from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Question, Topic
from .study_plan import (
    PlanValidationError,
    StudyPlanRequest,
    StudyPlanResponse,
    build_plan,
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="StudyPilot API",
    version="1.0.0",
)


# Allow the React frontend to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Basic Routes
# -------------------------

@app.get("/")
def root():
    return {
        "name": "StudyPilot",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# -------------------------
# Topic Routes
# -------------------------

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
        raise HTTPException(
            status_code=404,
            detail="Topic not found",
        )

    topic.completed = True
    db.commit()
    db.refresh(topic)

    return topic


# -------------------------
# Question Routes
# -------------------------

@app.get("/questions")
def get_questions(db: Session = Depends(get_db)):
    return db.query(Question).all()


# -------------------------
# Study Plan Route
# -------------------------

@app.post(
    "/study-plan",
    response_model=StudyPlanResponse,
)
def generate_study_plan(
    request: StudyPlanRequest,
) -> StudyPlanResponse:
    try:
        daily = build_plan(
            request.subject,
            request.topics,
            request.days,
            request.hours_per_day,
        )
    except PlanValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return StudyPlanResponse(
        subject=request.subject,
        days=daily,
    )
