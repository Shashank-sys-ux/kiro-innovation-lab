import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

type Topic = {
  id: number;
  name: string;
  subject: string;
  completed: boolean;
};

type StudyPlanDay = {
  day: number;
  topics: string[];
  hours: number;
};

type StudyPlan = {
  subject: string;
  days: StudyPlanDay[];
};

function App() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [name, setName] = useState("");
  const [subject, setSubject] = useState("DSA");

  const [planSubject, setPlanSubject] = useState("DSA");
  const [planTopics, setPlanTopics] = useState("");
  const [days, setDays] = useState(7);
  const [hoursPerDay, setHoursPerDay] = useState(2);

  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);
  const [planError, setPlanError] = useState("");

  const loadTopics = async () => {
    try {
      const response = await fetch(`${API}/topics`);
      const data = await response.json();
      setTopics(data);
    } catch {
      console.error("Could not connect to backend");
    }
  };

  useEffect(() => {
    loadTopics();
  }, []);

  const addTopic = async () => {
    if (!name.trim()) return;

    await fetch(
      `${API}/topics?name=${encodeURIComponent(
        name
      )}&subject=${encodeURIComponent(subject)}`,
      {
        method: "POST",
      }
    );

    setName("");
    await loadTopics();
  };

  const completeTopic = async (id: number) => {
    await fetch(`${API}/topics/${id}/complete`, {
      method: "PATCH",
    });

    await loadTopics();
  };

  const generateStudyPlan = async () => {
    setPlanError("");
    setStudyPlan(null);

    const topics = planTopics
      .split("\n")
      .map((topic) => topic.trim())
      .filter(Boolean);

    try {
      const response = await fetch(`${API}/study-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          subject: planSubject,
          topics,
          days,
          hours_per_day: hoursPerDay,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setPlanError(
          typeof data.detail === "string"
            ? data.detail
            : "Could not generate study plan."
        );
        return;
      }

      setStudyPlan(data);
    } catch {
      setPlanError("Could not connect to the StudyPilot backend.");
    }
  };

  const completed = topics.filter((topic) => topic.completed).length;

  const progress = topics.length
    ? Math.round((completed / topics.length) * 100)
    : 0;

  return (
    <div className="app">
      <header>
        <div>
          <h1>StudyPilot</h1>
          <p>Your focused study command center.</p>
        </div>

        <div className="badge">Placement Prep</div>
      </header>

      <main>
        {/* Statistics */}

        <section className="stats">
          <div className="card">
            <span>Total Topics</span>
            <strong>{topics.length}</strong>
          </div>

          <div className="card">
            <span>Completed</span>
            <strong>{completed}</strong>
          </div>

          <div className="card">
            <span>Progress</span>
            <strong>{progress}%</strong>
          </div>
        </section>

        {/* Topic Manager */}

        <section className="panel">
          <h2>Add Study Topic</h2>

          <div className="form">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Binary Search"
            />

            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            >
              <option>DSA</option>
              <option>Java</option>
              <option>SQL</option>
              <option>Machine Learning</option>
              <option>Computer Networks</option>
            </select>

            <button onClick={addTopic}>Add Topic</button>
          </div>
        </section>

        {/* Study Plan Generator */}

        <section className="panel planner">
          <div className="section-header">
            <div>
              <h2>Study Plan Generator</h2>
              <p className="muted">
                Turn your topics into a structured daily plan.
              </p>
            </div>
          </div>

          <div className="planner-grid">
            <div>
              <label>Subject</label>

              <input
                value={planSubject}
                onChange={(e) => setPlanSubject(e.target.value)}
                placeholder="e.g. DSA"
              />
            </div>

            <div>
              <label>Study Days</label>

              <input
                type="number"
                min="1"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
              />
            </div>

            <div>
              <label>Hours / Day</label>

              <input
                type="number"
                min="0.5"
                step="0.5"
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="planner-input">
            <label>Topics</label>

            <textarea
              value={planTopics}
              onChange={(e) => setPlanTopics(e.target.value)}
              placeholder={
                "Enter one topic per line:\nArrays\nStrings\nSorting\nSearching\nRecursion"
              }
              rows={7}
            />
          </div>

          <button onClick={generateStudyPlan}>
            Generate Study Plan
          </button>

          {planError && <div className="error">{planError}</div>}

          {studyPlan && (
            <div className="generated-plan">
              <h3>{studyPlan.subject} Study Plan</h3>

              <div className="plan-days">
                {studyPlan.days.map((day) => (
                  <div className="plan-day" key={day.day}>
                    <div className="day-header">
                      <strong>Day {day.day}</strong>
                      <span>{day.hours} hours</span>
                    </div>

                    {day.topics.length === 0 ? (
                      <p className="muted">No topics scheduled.</p>
                    ) : (
                      <ul>
                        {day.topics.map((topic) => (
                          <li key={topic}>{topic}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Topics */}

        <section className="panel">
          <div className="section-header">
            <h2>Study Topics</h2>
            <span>{topics.length} topics</span>
          </div>

          {topics.length === 0 ? (
            <div className="empty">
              <p>No topics yet.</p>
              <small>Add your first study topic above.</small>
            </div>
          ) : (
            <div className="topics">
              {topics.map((topic) => (
                <div className="topic" key={topic.id}>
                  <div>
                    <h3>{topic.name}</h3>
                    <span>{topic.subject}</span>
                  </div>

                  {topic.completed ? (
                    <span className="completed">
                      Completed ✓
                    </span>
                  ) : (
                    <button
                      onClick={() => completeTopic(topic.id)}
                    >
                      Mark Complete
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;