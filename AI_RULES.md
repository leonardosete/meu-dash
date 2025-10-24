# 🤖 AI Development Rules for `meu-dash`

This document provides a clear set of rules and guidelines for any AI agent or developer working on this project. The goal is to maintain architectural consistency, ensure code quality, and streamline the development process.

## 1. Core Tech Stack

The application is built on a modern, decoupled architecture. Here is a summary of the primary technologies used:

-   **Backend Framework**: **Python** with **Flask** is used to create the RESTful API.
-   **Data Analysis Engine**: **Pandas** is the exclusive library for all data manipulation, CSV processing, and analysis.
-   **Database**: **SQLAlchemy** serves as the ORM for interacting with the **SQLite** database, which stores report metadata.
-   **Frontend Framework**: The user interface is a Single-Page Application (SPA) built with **React** and **TypeScript**, bundled with **Vite**.
-   **API Communication**: **Axios** is used in the frontend for all HTTP requests to the backend API.
-   **Client-Side Routing**: **React Router** manages all navigation and routing within the React application.
-   **Icons**: The **`lucide-react`** library is the sole source for all icons to ensure visual consistency.
-   **Containerization**: **Docker** and **Docker Compose** are used for creating reproducible development and production environments.
-   **Production Serving**: **Nginx** acts as the web server and reverse proxy, serving the static React build and forwarding API requests to the **Gunicorn** WSGI server.
-   **Code Quality**: **Ruff** is used for Python linting/formatting, while **ESLint** and **Prettier** handle the TypeScript/React codebase.

## 2. Library Usage and Architectural Rules

To maintain consistency, follow these specific rules when adding or modifying code.

| Task                               | Library/Pattern to Use                                                                                                                            | Rule / Justification                                                                                                                                                           |
| :--------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend API Endpoints**          | **Flask**                                                                                                                                         | Keep routes in `app.py` thin. All business logic must be delegated to the service layer (`services.py`).                                                                       |
| **Data Processing & Analysis**     | **Pandas**                                                                                                                                        | All operations on CSV data (loading, cleaning, aggregation, calculation) must be performed using Pandas DataFrames.                                                            |
| **Database Operations**            | **SQLAlchemy**                                                                                                                                    | Define all database tables as models in `models.py`. Use `db.session` for queries and transactions. Schema changes must be handled via Flask-Migrate.                       |
| **API Documentation**              | **Flasgger**                                                                                                                                      | Document every API endpoint using OpenAPI specs directly within the Python docstrings of the route functions in `app.py`.                                                      |
| **Frontend UI Components**         | **React with TypeScript**                                                                                                                         | All components must be functional components using hooks. Use TypeScript for props and state to ensure type safety.                                                          |
| **Frontend Navigation**            | **React Router (`react-router-dom`)**                                                                                                             | All client-side routing must be handled by React Router. Define the main routes in `App.tsx`.                                                                                  |
| **Frontend API Requests**          | **Axios**                                                                                                                                         | Use the pre-configured Axios instance from `frontend/src/services/api.ts` for all backend communication. Do not use `fetch` or other HTTP clients.                           |
| **Icons**                          | **`lucide-react`**                                                                                                                                | To maintain a consistent visual language, all icons must be imported from this library. Do not use SVGs directly or icons from other libraries.                               |
| **Styling**                        | **Plain CSS**                                                                                                                                     | Follow the existing CSS architecture (`index.css` for globals, component-specific styles). Do not introduce CSS-in-JS, utility-class libraries (like Tailwind), or SASS. |
| **Frontend State Management**      | **React Hooks (`useState`, `useContext`)**                                                                                                        | For shared state, use the React Context API, following the pattern established in `AuthContext.tsx`. Do not introduce external state management libraries like Redux or Zustand. |