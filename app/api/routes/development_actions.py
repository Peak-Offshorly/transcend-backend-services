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

    initial_answers = ""

    chosen_strength = "Delegation and Empowerment"
    chosen_weakness = "Creating Buy-In"
    strengths = [chosen_strength, "COACHING", "LISTENING", "RESILIENCE AND STRESS MANAGEMENT", "STRATEGIC FOCUS"]
    weaknesses = [chosen_weakness, "PLANNING, PRIORITIZING, AND MAINTAINING FOCUS", "INSPIRATIONAL ROLE MODEL", "HOLDING PEOPLE ACCOUNTABLE"]

    strength_practice = "Assess individual team members' skills and delegate tasks that match their strengths."
    weakness_practice = "Identify and address individual concerns through one-on-one discussions."
    
    strength_docs = get_docs(vectorstore=vectorstore, input_data=chosen_strength)
    weakness_docs = get_docs(vectorstore=vectorstore, input_data=chosen_weakness)

    final_docs = f"""
      Strength Context
      {strength_docs}

      Weakness Context
      {weakness_docs}
    """

    company_size = "50"
    industry = "Tech and IT, Software Development"
    employee_role = "Team Lead in AI Software Development"
    role_description = """
    I spearhead the design, implementation, and optimization of cutting-edge AI solutions, leading a team of engineers and data scientists through complex projects from inception to deployment. I oversee the AI development lifecycle, from data collection and preprocessing to model training, validation, and deployment, leveraging advanced machine learning techniques to solve real-world problems and drive innovation.

    I coordinate with cross-functional teams to align AI initiatives with business goals, manage project timelines, and allocate resources effectively. This requires a deep understanding of AI technologies and business strategies to ensure our projects deliver maximum value.

    I mentor and support junior developers and interns, fostering a collaborative and inclusive environment where team members can thrive. I prioritize continuous learning and professional growth, encouraging my team to stay updated with the latest advancements in AI and machine learning.

    I regularly present project updates, AI capabilities, and potential impacts to senior management and stakeholders, translating complex technical concepts into clear, actionable insights for informed decision-making.

    I focus on creating a culture of innovation and experimentation, advocating for best practices in AI development, including ethical considerations and responsible AI use. My goal is to empower my team to push the boundaries of AI, delivering transformative solutions that meet our clients' needs and exceed expectations.
    """

    #todo: add Company size, title, role description, specific (3x a week) -- give different suggestions for different roles
    # add 
    response = generate_actions(final_docs, strengths, weaknesses, chosen_strength, chosen_weakness, strength_practice, weakness_practice, company_size, industry, employee_role, role_description)

    return { "response": response}
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))