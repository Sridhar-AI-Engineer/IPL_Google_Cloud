from ipl_agentic_coach.backend.app.main import app


def main():
    print("Run the backend with:")
    print("uvicorn main:app --reload")
    print("uvicorn ipl_agentic_coach.backend.app.main:app --reload")
    print("Then open: http://127.0.0.1:8000/dashboard")


if __name__ == "__main__":
    main()