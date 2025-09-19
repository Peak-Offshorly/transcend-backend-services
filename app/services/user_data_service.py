from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from functools import lru_cache
import time

from app.utils.users_crud import get_user_company_details
from app.utils.answers_crud import initial_questions_answers_all_forms_get_all
from app.utils.traits_crud import traits_get_top_bottom_five, chosen_traits_get
from app.utils.dev_plan_crud import dev_plan_get_current
from app.utils.sprints_crud import sprint_get_current
from app.utils.practices_crud import chosen_practices_get
from app.ai.data.format_initial_questions import get_initial_questions_with_answers
from app.ai.data.traits_practices import get_ten_traits, get_chosen_traits, get_chosen_practices
from app.ai.helpers.get_vectorstore import get_vectorstore

class UserDataService:
    def __init__(self):
        self._vectorstore_cache = {}
        self._user_data_cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def _get_cache_key(self, user_id: str, data_type: str) -> str:
        return f"{user_id}:{data_type}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        return time.time() - cache_entry.get('timestamp', 0) < self._cache_ttl
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        if cache_key in self._user_data_cache:
            cache_entry = self._user_data_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry['data']
        return None
    
    def _set_cached_data(self, cache_key: str, data: Any) -> None:
        self._user_data_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_vectorstore(self, index_name: str = "peak-ai"):
        """Get vectorstore with caching"""
        if index_name not in self._vectorstore_cache:
            self._vectorstore_cache[index_name] = get_vectorstore(index_name=index_name)
        return self._vectorstore_cache[index_name]
    
    async def get_user_base_data(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get all basic user data needed for both endpoints"""
        cache_key = self._get_cache_key(user_id, "base_data")
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # Fetch company details
        company_details = get_user_company_details(db=db, user_id=user_id)
        
        # Fetch initial questions with answers
        user_answers = await initial_questions_answers_all_forms_get_all(db=db, user_id=user_id)
        answers_list = user_answers[0].answers
        initial_questions_with_answers = get_initial_questions_with_answers(answers_list)
        
        # Get traits data
        ten_traits = traits_get_top_bottom_five(db=db, user_id=user_id)
        strengths, weaknesses = get_ten_traits(ten_traits)
        
        # Get development plan
        dev_plan = await dev_plan_get_current(db=db, user_id=user_id)
        dev_plan_id = dev_plan["dev_plan_id"]
        
        # Get chosen traits
        chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
        chosen_strength, chosen_weakness = get_chosen_traits(chosen_traits)
        
        # Get current sprint
        current_sprint = await sprint_get_current(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
        
        # Get chosen practices
        chosen_trait_practices = await chosen_practices_get(
            db=db, 
            user_id=user_id, 
            sprint_number=current_sprint['sprint_number'], 
            dev_plan_id=dev_plan_id
        )
        strength_practice, weakness_practice = get_chosen_practices(chosen_trait_practices)
        
        base_data = {
            'company_details': company_details,
            'initial_questions_with_answers': initial_questions_with_answers,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'chosen_strength': chosen_strength,
            'chosen_weakness': chosen_weakness,
            'strength_practice': strength_practice,
            'weakness_practice': weakness_practice,
            'dev_plan_id': dev_plan_id,
            'current_sprint': current_sprint
        }
        
        # Cache the data
        self._set_cached_data(cache_key, base_data)
        
        return base_data
    
    def get_trait_inputs(self, base_data: Dict[str, Any], trait_type: str) -> Tuple[str, str, str, list]:
        """Get trait-specific inputs for AI generation"""
        if trait_type == "strength":
            chosen_trait = base_data['chosen_strength']
            trait_practice = base_data['strength_practice']
            five_traits = base_data['strengths']
        else:  # weakness
            chosen_trait = base_data['chosen_weakness']
            trait_practice = base_data['weakness_practice']
            five_traits = base_data['weaknesses']
        
        return chosen_trait, trait_practice, ",".join(five_traits), five_traits
    
    def build_ai_inputs(self, base_data: Dict[str, Any], trait_type: str, context: str, previous_actions: str = "") -> Dict[str, Any]:
        """Build inputs for AI generation"""
        chosen_trait, trait_practice, five_traits_str, _ = self.get_trait_inputs(base_data, trait_type)
        company_details = base_data['company_details']
        
        inputs = {
            "type": trait_type,
            "context": context,
            "initial_questions": base_data['initial_questions_with_answers'],
            "five_traits": five_traits_str,
            "chosen_trait": chosen_trait,
            "trait_practice": trait_practice,
            "company_size": company_details.company_size,
            "industry": company_details.industry,
            "employee_role": company_details.role,
            "role_description": company_details.role_description
        }
        
        if previous_actions:
            inputs["previous_actions"] = previous_actions
            
        return inputs

# Global instance
user_data_service = UserDataService()
