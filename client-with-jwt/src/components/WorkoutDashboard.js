import React, { useCallback, useEffect, useState } from "react";
import { Button, Error, FormField, Input, Label } from "../styles";
import "./WorkoutDashboard.css";

const today = () => {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
};

const emptyWorkout = () => ({
  exercise: "",
  duration_minutes: "",
  calories_burned: "",
  date: today(),
});

async function responseError(response) {
  let body;
  try {
    body = await response.json();
  } catch {
    return `Request failed (${response.status}).`;
  }
  if (Array.isArray(body.errors) && body.errors.length) return body.errors.join(", ");
  return body.error || body.msg || `Request failed (${response.status}).`;
}

function WorkoutDashboard({ user, onUnauthorized }) {
  const [workouts, setWorkouts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [listError, setListError] = useState("");
  const [newWorkout, setNewWorkout] = useState(emptyWorkout);
  const [editingId, setEditingId] = useState(null);
  const [editingWorkout, setEditingWorkout] = useState(emptyWorkout);

  const request = useCallback(async (url, options = {}) => {
    const token = localStorage.getItem("token");
    const response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });
    if (response.status === 401) {
      onUnauthorized();
      throw new Error("Your session expired. Please log in again.");
    }
    if (!response.ok) throw new Error(await responseError(response));
    if (response.status === 204) return null;
    return response.json();
  }, [onUnauthorized]);

  const loadWorkouts = useCallback(async () => {
    setIsLoading(true);
    setListError("");
    try {
      const data = await request("/workouts?page=1&per_page=100");
      if (!Array.isArray(data.workouts)) {
        throw new Error("The API returned an unexpected workout list.");
      }
      setWorkouts(data.workouts);
    } catch (error) {
      setListError(error.message);
    } finally {
      setIsLoading(false);
    }
  }, [request]);

  useEffect(() => {
    loadWorkouts();
  }, [loadWorkouts]);

  function updateForm(setForm, event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function workoutPayload(values) {
    return {
      exercise: values.exercise.trim(),
      duration_minutes: Number(values.duration_minutes),
      calories_burned: Number(values.calories_burned),
      date: values.date,
    };
  }

  async function createWorkout(event) {
    event.preventDefault();
    setIsSaving(true);
    setFormError("");
    try {
      const created = await request("/workouts", {
        method: "POST",
        body: JSON.stringify(workoutPayload(newWorkout)),
      });
      setWorkouts((current) => [created, ...current]);
      setNewWorkout(emptyWorkout());
    } catch (error) {
      setFormError(error.message);
    } finally {
      setIsSaving(false);
    }
  }

  function startEditing(workout) {
    setEditingId(workout.id);
    setEditingWorkout({
      exercise: workout.exercise,
      duration_minutes: String(workout.duration_minutes),
      calories_burned: String(workout.calories_burned),
      date: workout.date,
    });
    setFormError("");
  }

  async function saveWorkout(event) {
    event.preventDefault();
    setIsSaving(true);
    setFormError("");
    try {
      const updated = await request(`/workouts/${editingId}`, {
        method: "PATCH",
        body: JSON.stringify(workoutPayload(editingWorkout)),
      });
      setWorkouts((current) => current.map((item) => item.id === updated.id ? updated : item));
      setEditingId(null);
    } catch (error) {
      setFormError(error.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteWorkout(id) {
    if (!window.confirm("Delete this workout? This cannot be undone.")) return;
    setFormError("");
    try {
      await request(`/workouts/${id}`, { method: "DELETE" });
      setWorkouts((current) => current.filter((item) => item.id !== id));
    } catch (error) {
      setFormError(error.message);
    }
  }

  return (
    <main className="workout-page">
      <section className="workout-welcome">
        <div>
          <p className="workout-eyebrow">YOUR ACTIVITY</p>
          <h2 className="workout-heading">Workout dashboard</h2>
          <p className="workout-subtitle">Welcome, {user.username}. Track your progress one workout at a time.</p>
        </div>
        <div className="workout-count" aria-label={`${workouts.length} workouts`}>
          <strong>{workouts.length}</strong>
          <span>{workouts.length === 1 ? "workout" : "workouts"}</span>
        </div>
      </section>

      <div className="workout-columns">
        <section className="workout-panel">
          <h3 className="workout-panel__title">Add a workout</h3>
          <form className="workout-form" onSubmit={createWorkout}>
            <FormField>
              <Label htmlFor="new-exercise">Exercise</Label>
              <Input id="new-exercise" name="exercise" value={newWorkout.exercise}
                onChange={(event) => updateForm(setNewWorkout, event)} required maxLength="100"
                placeholder="e.g. Swimming" />
            </FormField>
            <div className="workout-form-grid">
              <FormField>
                <Label htmlFor="new-duration">Duration (minutes)</Label>
                <Input id="new-duration" name="duration_minutes" type="number" min="1"
                  value={newWorkout.duration_minutes}
                  onChange={(event) => updateForm(setNewWorkout, event)} required />
              </FormField>
              <FormField>
                <Label htmlFor="new-calories">Calories burned</Label>
                <Input id="new-calories" name="calories_burned" type="number" min="0"
                  value={newWorkout.calories_burned}
                  onChange={(event) => updateForm(setNewWorkout, event)} required />
              </FormField>
            </div>
            <FormField>
              <Label htmlFor="new-date">Date</Label>
              <Input id="new-date" name="date" type="date" value={newWorkout.date}
                onChange={(event) => updateForm(setNewWorkout, event)} required />
            </FormField>
            {formError && <Error role="alert">{formError}</Error>}
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Saving..." : "Add workout"}
            </Button>
          </form>
        </section>

        <section className="workout-panel">
          <div className="workout-list-header">
            <h3 className="workout-panel__title">Your workouts</h3>
            <button className="workout-refresh" type="button" onClick={loadWorkouts} disabled={isLoading}>
              {isLoading ? "Loading..." : "Refresh"}
            </button>
          </div>
          {listError && (
            <Error role="alert">
              {listError}{" "}
              <button type="button" onClick={loadWorkouts}>Try again</button>
            </Error>
          )}
          {formError && <Error role="alert">{formError}</Error>}
          {isLoading ? (
            <p className="workout-empty">Loading your workouts...</p>
          ) : !listError && workouts.length === 0 ? (
            <p className="workout-empty">No workouts yet. Add your first workout using the form.</p>
          ) : (
            <ul className="workout-list">
              {workouts.map((workout) => (
                <li className="workout-item" key={workout.id}>
                  {editingId === workout.id ? (
                    <form className="workout-form" onSubmit={saveWorkout}>
                      <FormField>
                        <Label htmlFor={`exercise-${workout.id}`}>Exercise</Label>
                        <Input id={`exercise-${workout.id}`} name="exercise"
                          value={editingWorkout.exercise}
                          onChange={(event) => updateForm(setEditingWorkout, event)}
                          required maxLength="100" />
                      </FormField>
                      <div className="workout-form-grid">
                        <FormField>
                          <Label htmlFor={`duration-${workout.id}`}>Duration (minutes)</Label>
                          <Input id={`duration-${workout.id}`} name="duration_minutes" type="number"
                            min="1" value={editingWorkout.duration_minutes}
                            onChange={(event) => updateForm(setEditingWorkout, event)} required />
                        </FormField>
                        <FormField>
                          <Label htmlFor={`calories-${workout.id}`}>Calories burned</Label>
                          <Input id={`calories-${workout.id}`} name="calories_burned" type="number"
                            min="0" value={editingWorkout.calories_burned}
                            onChange={(event) => updateForm(setEditingWorkout, event)} required />
                        </FormField>
                      </div>
                      <FormField>
                        <Label htmlFor={`date-${workout.id}`}>Date</Label>
                        <Input id={`date-${workout.id}`} name="date" type="date"
                          value={editingWorkout.date}
                          onChange={(event) => updateForm(setEditingWorkout, event)} required />
                      </FormField>
                      <div className="workout-actions">
                        <Button type="submit" disabled={isSaving}>
                          {isSaving ? "Saving..." : "Save changes"}
                        </Button>
                        <button className="workout-secondary" type="button" onClick={() => setEditingId(null)}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <div className="workout-item__top">
                        <h4 className="workout-item__name">{workout.exercise}</h4>
                        <time className="workout-item__date">{workout.date}</time>
                      </div>
                      <div className="workout-item__details">
                        <span>{workout.duration_minutes} min</span>
                        <span>{workout.calories_burned} calories</span>
                      </div>
                      <div className="workout-actions">
                        <button className="workout-secondary" type="button" onClick={() => startEditing(workout)}>
                          Edit
                        </button>
                        <button className="workout-delete" type="button" onClick={() => deleteWorkout(workout.id)}>
                          Delete
                        </button>
                      </div>
                    </>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}

export default WorkoutDashboard;
