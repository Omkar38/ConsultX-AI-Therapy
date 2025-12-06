# ConsultX - Frontend

A web application for AMS691 Project.
 
## Requirements
-   [Node.js](https://nodejs.org/en/download/) (LTS recommended)
-   `npm` package manager

## Quick Start

1. **Install dependencies:**
    ```bash
    npm install
    ```

2.  **Run the application locally:**
    ```bash
    npm run dev
    ```
    The application should open automatically in your browser, typically at `http://localhost:3000`.

## Routes

- `/login`: Authentication page for existing users
- `/signup`: Registration page
- `/chat-old`: Basic video chat interface
- `/chat-new`: Improved UI video chat screen
- `/feedback`: Placeholder for giving user feedback after session
- `/dashboard`: Central page for user profile, session history, and overall metrics

## To-Do (as of 11/17)
- [x] Create `login` and `signup`.
- [ ] Implement `/dashboard` page.
- [ ] Expand `/chat` interface (controls, layout, connection handling)
- [ ] Build `/feedback` page after deciding what's being shown there