# from fastapi import FastAPI, Depends
# from sqlalchemy.orm import Session
# from db.database import SessionLocal

# # Dependency to get the database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# # Add a global dependency for the database session

# async def db_session_middleware(request, call_next):
#     request.state.db = SessionLocal()
#     response = await call_next(request)
#     request.state.db.close()
#     return response
