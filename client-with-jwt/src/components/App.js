import React, { useEffect, useState } from "react";
import NavBar from "./NavBar";
import Login from "../pages/Login";
import WorkoutDashboard from "./WorkoutDashboard";
import "./App.css";

function App() {
  const [user, setUser] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [sessionError, setSessionError] = useState("");

  useEffect(() => {
    let isMounted = true;
    const token = localStorage.getItem("token");

    if (!token) {
      setIsCheckingSession(false);
      return () => {
        isMounted = false;
      };
    }

    fetch("/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (!isMounted) return;
        if (response.ok) {
          setUser(await response.json());
          return;
        }
        if (response.status === 401) {
          localStorage.removeItem("token");
          return;
        }
        setSessionError("Could not verify your session. Please try again.");
      })
      .catch(() => {
        if (isMounted) setSessionError("Could not connect to the API. Check that the backend is running.");
      })
      .finally(() => {
        if (isMounted) setIsCheckingSession(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const onLogin = (token, authenticatedUser) => {
    localStorage.setItem("token", token);
    setSessionError("");
    setUser(authenticatedUser);
  };

  const onLogout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  if (isCheckingSession) {
    return <p className="session-loading">Checking your session...</p>;
  }

  if (!user) {
    return (
      <>
        {sessionError && <p className="session-error" role="alert">{sessionError}</p>}
        <Login onLogin={onLogin} />
      </>
    );
  }

  return (
    <>
      <NavBar user={user} setUser={onLogout} />
      <WorkoutDashboard user={user} onUnauthorized={onLogout} />
    </>
  );
}

export default App;
