import os
import json
import logging
import re
from typing import Dict
from groq import Groq
from backend.services.lightweight_parser import parse_resume_lightweight, parse_jd_lightweight


logger=logging.getLogger('ats_resume_scorer')


GROQ_MODEL='llama-3.3-70b-versatile'

_client=None

def _get_client()->Groq:
    global _client
    if _client is None:
        api_key=os.getenv('GROQ_API_KEY', '').strip()

        if not api_key or api_key.startswith('your_'):
            return None
        try:
            _client=Groq(api_key=api_key)
        except:
            return None
    return _client




RESUME_SYSTEM_PROMPT = (
    "Extract resume data as JSON only. No markdown, no explanation."
)

RESUME_USER_PROMPT = """Parse resume to JSON:
{{
  "name": "full name",
  "email": "email",
  "phone": "phone",
  "linkedin": "URL or null",
  "github": "URL or null",
  "professional_summary": "summary text or empty",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{"job_title": "", "company": "", "duration_months": 0, "description": ""}}
  ],
  "education": [{{"degree": "", "institution": ""}}],
  "projects": [{{"title": "", "technologies": ["tech1"]}}],
  "action_verbs": ["developed", "implemented"],
  "keywords": ["keyword1", "keyword2"]
}}

Resume:
{raw_text}"""




def _call_groq(client:Groq, system_prompt:str, user_prompt:str)->str:

    response=client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        temperature=0.0,
        max_tokens=2048
    )

    return response.choices[0].message.content.strip()

def _try_parse_json(text: str) -> dict | None:

    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):

        # Remove opening fence (```json or ```)
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        # Remove closing fence
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    
def parse_resume(raw_text: str)->Dict:
    client = _get_client()
    
    # If no API key, use lightweight fallback
    if not client:
        logger.info("GROQ_API_KEY not set, using lightweight fallback parser")
        return _parse_resume_lightweight(raw_text)
    
    prompt=RESUME_USER_PROMPT.format(raw_text=raw_text)
    raw_response=_call_groq(client, RESUME_SYSTEM_PROMPT, prompt)
    result=_try_parse_json(raw_response)

    if result is None:
        return _validate_resume_result(result)
    

    logger.warning("Groq resume parse: first attempt returned invalid JSON, retrying...")
    strict_prompt = (
        "Your previous response was not valid JSON. "
        "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
        + prompt
    )
    raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, strict_prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_resume_result(result)

    # Fallback to lightweight parser if Groq fails
    logger.warning("Groq failed, falling back to lightweight parser")
    return _parse_resume_lightweight(raw_text)
    
JD_SYSTEM_PROMPT = (
    "Extract JD data as JSON only. No markdown, no explanation."
)

JD_USER_PROMPT = """Parse job description to JSON:
{{
  "job_title": "",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill3"],
  "keywords": ["keyword1", "keyword2"]
}}

Job Description:
{raw_text}"""

def parse_job_description(raw_text: str) -> Dict:
    client = _get_client()
    
    # If no API key, use lightweight fallback
    if not client:
        logger.info("GROQ_API_KEY not set, using lightweight fallback parser for JD")
        return _parse_job_description_lightweight(raw_text)
    
    prompt = JD_USER_PROMPT.format(raw_text=raw_text)

    raw_response = _call_groq(client, JD_SYSTEM_PROMPT, prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_jd_result(result)

    logger.warning("Groq JD parse: first attempt returned invalid JSON, retrying...")
    strict_prompt = (
        "Your previous response was not valid JSON. "
        "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
        + prompt
    )
    raw_response = _call_groq(client, JD_SYSTEM_PROMPT, strict_prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_jd_result(result)

    # Fallback to lightweight parser if Groq fails
    logger.warning("Groq failed, falling back to lightweight parser")
    return _parse_job_description_lightweight(raw_text)

#it will make sure, that the parse json has all the valid fields we expect
def _validate_jd_result(result: dict) -> dict:
    
    defaults = {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "keywords": [],
    }

    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    return result


#to make sure the parse json has all the valid json fields
def _validate_resume_result(result: dict) -> dict:

    defaults = {
        "name": "",
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "professional_summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "action_verbs": [],
        "keywords": [],
    }
    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
            
        # Ensure list fields are actually lists
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    #Validate experience entries
    for exp in result.get("experience", []):
        if not isinstance(exp, dict):
            continue
        exp.setdefault("job_title", "")
        exp.setdefault("company", "")
        exp.setdefault("start_date", "")
        exp.setdefault("end_date", "")
        exp.setdefault("duration_months", 0)
        exp.setdefault("description", "")
        #Ensure duration_months is an int
        try:
            exp["duration_months"] = int(exp["duration_months"])
        except (ValueError, TypeError):
            exp["duration_months"] = 0

    #Validate project entries
    for proj in result.get("projects", []):
        if not isinstance(proj, dict):
            continue
        proj.setdefault("title", "")
        proj.setdefault("description", "")
        proj.setdefault("technologies", [])

    return result


def _parse_resume_lightweight(text: str) -> Dict:
    """Fallback resume parser - no API required"""
    result = parse_resume_lightweight(text)
    return _validate_resume_result(result)


def _parse_job_description_lightweight(text: str) -> Dict:
    """Fallback JD parser - no API required"""
    result = parse_jd_lightweight(text)
    return _validate_jd_result(result)