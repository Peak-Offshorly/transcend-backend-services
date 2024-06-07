from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema
from app.database.connection import get_db
from app.ai.helpers.get_vectorstore import get_vectorstore
from app.ai.helpers.get_documents import get_docs
from app.ai.helpers.chains import generate_actions

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-actions", tags=["development-actions"])

@router.get("/get-actions")
async def get_actions():
  try:
    vectorstore = get_vectorstore(index_name="peak-ai")

    # retriever = vectorstore.as_retriever()
    retriever = vectorstore.as_retriever(search_type="mmr")
    # retriever = vectorstore.as_retriever(
    #   search_type="similarity_score_threshold", search_kwargs={"score_threshold": 0.7, "k": 10}
    # )

    chosen_strength = "Delegation and Empowerment"
    chosen_weakness = "Creating Buy-In"
    strengths = [chosen_strength, "Creating Buy-In", "Delegation and Empowerment", "RESILIENCE AND STRESS MANAGEMENT", "STRATEGIC FOCUS"]
    weaknesses = [chosen_weakness, "PLANNING, PRIORITIZING, AND MAINTAINING FOCUS", "INSPIRATIONAL ROLE MODEL", "HOLDING PEOPLE ACCOUNTABLE"]
    
    strength_docs = get_docs(vectorstore=vectorstore, input_data=chosen_strength)
    weakness_docs = get_docs(vectorstore=vectorstore, input_data=chosen_weakness)
    final_docs = f"""
      Strength Context
      {strength_docs}

      Weakness Context
      {weakness_docs}
    """

    #todo: add the answers from the initial questions, add: chosen 1 practice
    #Company size, title, role description, specific (3x a week) -- give different suggestions for different roles
    response = generate_actions(final_docs, strengths, weaknesses, chosen_strength, chosen_weakness)

    return { "response": response}
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))