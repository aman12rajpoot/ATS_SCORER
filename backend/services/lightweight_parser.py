"""Lightweight regex-based resume and JD parser (no API calls required)"""
import re
from typing import Dict, List


def extract_emails(text: str) -> str:
    """Extract email address"""
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str:
    """Extract phone number"""
    match = re.search(r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', text)
    return match.group(0) if match else None


def extract_urls(text: str, pattern_name: str = None) -> str:
    """Extract URLs (LinkedIn, GitHub, portfolio)"""
    patterns = {
        'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s]+',
        'github': r'(?:https?://)?(?:www\.)?github\.com/[^\s]+',
        'portfolio': r'https?://[^\s]+(?:portfolio|website|site)[^\s]*',
    }
    
    search_pattern = patterns.get(pattern_name) if pattern_name else r'https?://[^\s]+'
    match = re.search(search_pattern, text, re.IGNORECASE)
    return match.group(0) if match else None


def extract_skills(text: str) -> List[str]:
    """Extract skills from text - basic keyword matching"""
    common_skills = [
        'Python', 'Java', 'C++', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue',
        'Node.js', 'Django', 'Flask', 'FastAPI', 'SQL', 'MySQL', 'PostgreSQL', 'MongoDB',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git', 'Linux', 'Windows',
        'HTML', 'CSS', 'REST', 'GraphQL', 'Microservices', 'Agile', 'Scrum', 'JIRA',
        'Excel', 'Power BI', 'Tableau', 'Machine Learning', 'Deep Learning', 'TensorFlow',
        'Communication', 'Leadership', 'Problem Solving', 'Critical Thinking',
    ]
    
    found_skills = []
    for skill in common_skills:
        if re.search(r'\b' + skill + r'\b', text, re.IGNORECASE):
            found_skills.append(skill)
    
    return found_skills


def extract_action_verbs(text: str) -> List[str]:
    """Extract action verbs from resume"""
    verbs = [
        'Developed', 'Implemented', 'Designed', 'Created', 'Built', 'Managed',
        'Led', 'Coordinated', 'Improved', 'Optimized', 'Deployed', 'Automated',
        'Analyzed', 'Increased', 'Reduced', 'Established', 'Collaborated',
        'Mentored', 'Supervised', 'Directed', 'Managed', 'Oversaw',
    ]
    
    found = []
    for verb in verbs:
        if re.search(r'\b' + verb + r'\b', text, re.IGNORECASE):
            found.append(verb)
    
    return found[:10]  # Limit to first 10


def parse_resume_lightweight(text: str) -> Dict:
    """Fast resume parsing without API calls"""
    # Extract summary (first few sentences after "summary" or "about" section)
    summary_match = re.search(
        r'(?:professional\s*)?(?:summary|profile|about|objective)[:\s]*([^.]*\.)',
        text,
        re.IGNORECASE
    )
    summary = summary_match.group(1).strip() if summary_match else text[:200]
    
    return {
        "name": "Unknown",
        "email": extract_emails(text),
        "phone": extract_phone(text),
        "linkedin": extract_urls(text, 'linkedin'),
        "github": extract_urls(text, 'github'),
        "professional_summary": summary,
        "skills": extract_skills(text),
        "experience": [],
        "education": [],
        "projects": [],
        "action_verbs": extract_action_verbs(text),
        "keywords": extract_skills(text),
    }


def parse_jd_lightweight(text: str) -> Dict:
    """Fast JD parsing without API calls"""
    # Extract job title (usually near the top)
    title_match = re.search(r'^(.{10,100})$', text, re.MULTILINE)
    job_title = title_match.group(1).strip() if title_match else ""
    
    return {
        "job_title": job_title,
        "required_skills": extract_skills(text),
        "preferred_skills": [],
        "keywords": extract_skills(text),
    }
