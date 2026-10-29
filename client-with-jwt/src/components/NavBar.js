import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../styles";
import "./NavBar.css";

function NavBar({ setUser }) {
  function handleLogoutClick() {
    localStorage.removeItem("token");
    setUser(null);
  }

  return (
    <header className="app-header">
      <h1 className="app-header__logo">
        <Link to="/">Workout Tracker</Link>
      </h1>
      <nav className="app-header__nav">
        <Button variant="outline" onClick={handleLogoutClick}>
          Logout
        </Button>
      </nav>
    </header>
  );
}

export default NavBar;
