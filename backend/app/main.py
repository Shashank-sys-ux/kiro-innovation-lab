from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Question, Topic
from .study_plan import build_plan


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
# Study Plan Schemas
# -------------------------

class StudyPlanRequest(BaseModel):
    subject: str = Field(min_length=1)
    topics: list[str]
    days: int = Field(gt=0)
    hours_per_day: float = Field(gt=0)


class StudyPlanDayResponse(BaseModel):
    day: int
    topics: list[str]
    hours: float


class StudyPlanResponse(BaseModel):
    subject: str
    days: list[StudyPlanDayResponse]


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
def generate_study_plan(request: StudyPlanRequest):
    # Validate subject
    if not request.subject.strip():
        raise HTTPException(
            status_code=422,
            detail="Subject cannot be blank",
        )

    # Remove empty topic names
    topics = [
        topic.strip()
        for topic in request.topics
        if topic.strip()
    ]

    # Validate topics
    if not topics:
        raise HTTPException(
            status_code=422,
            detail="Topics cannot be empty",
        )

    try:
        plan = build_plan(
            topics=topics,
            days=request.days,
            hours_per_day=request.hours_per_day,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    return StudyPlanResponse(
        subject=request.subject.strip(),
        days=[
            StudyPlanDayResponse(
                day=item.day,
                topics=item.topics,
                hours=item.hours,
            )
            for item in plan
        ],
    )
