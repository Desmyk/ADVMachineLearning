import requests
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from ...core.models import JobRecommendation, User, SkillLevel


@dataclass
class JobSearchFilters:
    """Filters for job search queries"""
    keywords: List[str]
    location: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, remote
    experience_level: Optional[str] = None  # entry, mid, senior
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    remote_ok: bool = False
    posted_within_days: int = 30


class JobSearchAPI:
    """
    Job search API integration that aggregates opportunities from multiple sources
    """
    
    def __init__(self, rapidapi_key: Optional[str] = None):
        self.rapidapi_key = rapidapi_key
        self.base_urls = {
            "indeed": "https://indeed-com.p.rapidapi.com",
            "linkedin": "https://linkedin-jobs-search.p.rapidapi.com",
            "adzuna": "https://api.adzuna.com/v1/api/jobs",
        }
        self.headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "indeed-com.p.rapidapi.com"
        }
    
    def search_jobs(self, filters: JobSearchFilters, max_results: int = 20) -> List[JobRecommendation]:
        """
        Search for jobs using multiple APIs and return aggregated results
        """
        all_jobs = []
        
        # Search Indeed (using RapidAPI)
        try:
            indeed_jobs = self._search_indeed(filters, max_results // 2)
            all_jobs.extend(indeed_jobs)
        except Exception as e:
            print(f"Indeed search failed: {e}")
        
        # Search using demo/mock data for development
        mock_jobs = self._get_mock_jobs(filters, max_results // 2)
        all_jobs.extend(mock_jobs)
        
        # Remove duplicates and rank by relevance
        unique_jobs = self._deduplicate_jobs(all_jobs)
        ranked_jobs = self._rank_jobs_by_relevance(unique_jobs, filters)
        
        return ranked_jobs[:max_results]
    
    def _search_indeed(self, filters: JobSearchFilters, max_results: int) -> List[JobRecommendation]:
        """Search Indeed using RapidAPI"""
        jobs = []
        
        if not self.rapidapi_key:
            return jobs
        
        try:
            # Build query parameters
            params = {
                "query": " ".join(filters.keywords),
                "location": filters.location or "United States",
                "page_id": "1",
                "locality": "us",
                "fromage": str(filters.posted_within_days),
                "limit": str(max_results)
            }
            
            if filters.job_type:
                params["job_type"] = filters.job_type
            
            response = requests.get(
                f"{self.base_urls['indeed']}/search",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for job_data in data.get("hits", []):
                    job = self._parse_indeed_job(job_data)
                    if job:
                        jobs.append(job)
            
        except Exception as e:
            print(f"Indeed API error: {e}")
        
        return jobs
    
    def _parse_indeed_job(self, job_data: Dict) -> Optional[JobRecommendation]:
        """Parse Indeed job data into JobRecommendation"""
        try:
            return JobRecommendation(
                id=f"indeed_{job_data.get('id', '')}",
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                job_type=job_data.get("job_type", "full-time"),
                salary_range=job_data.get("salary", ""),
                description=job_data.get("description", "")[:500],  # Truncate
                required_skills=self._extract_skills(job_data.get("description", "")),
                experience_level=job_data.get("experience_level", "mid"),
                application_url=job_data.get("url", ""),
                match_score=0.0  # Will be calculated later
            )
        except Exception as e:
            print(f"Error parsing Indeed job: {e}")
            return None
    
    def _get_mock_jobs(self, filters: JobSearchFilters, max_results: int) -> List[JobRecommendation]:
        """Generate mock job data for development and demo purposes"""
        mock_jobs_data = [
            {
                "title": "Senior Frontend Developer",
                "company": "TechCorp Inc",
                "location": "San Francisco, CA",
                "job_type": "full-time",
                "salary_range": "$120,000 - $160,000",
                "description": "We're looking for a senior frontend developer with expertise in React, TypeScript, and modern web technologies. You'll work on building scalable user interfaces for our SaaS platform.",
                "required_skills": ["React", "TypeScript", "JavaScript", "CSS", "HTML"],
                "preferred_skills": ["Redux", "Next.js", "GraphQL"],
                "experience_level": "senior",
                "application_url": "https://techcorp.com/careers/frontend-dev"
            },
            {
                "title": "Data Science Intern",
                "company": "Analytics Pro",
                "location": "Remote",
                "job_type": "internship",
                "salary_range": "$25 - $35/hour",
                "description": "Summer internship opportunity for aspiring data scientists. Work with real datasets, build machine learning models, and gain hands-on experience with Python and SQL.",
                "required_skills": ["Python", "SQL", "Statistics", "Pandas"],
                "preferred_skills": ["Machine Learning", "TensorFlow", "Jupyter"],
                "experience_level": "entry",
                "application_url": "https://analyticspro.com/internships"
            },
            {
                "title": "Product Manager",
                "company": "Startup Dynamics",
                "location": "Austin, TX",
                "job_type": "full-time",
                "salary_range": "$100,000 - $130,000",
                "description": "Lead product strategy and roadmap for our mobile application. Collaborate with engineering, design, and marketing teams to deliver exceptional user experiences.",
                "required_skills": ["Product Strategy", "Roadmapping", "User Research", "Analytics"],
                "preferred_skills": ["Agile", "A/B Testing", "SQL"],
                "experience_level": "mid",
                "application_url": "https://startupdynamics.com/jobs/pm"
            },
            {
                "title": "Junior Software Engineer",
                "company": "DevFirst Solutions",
                "location": "New York, NY",
                "job_type": "full-time",
                "salary_range": "$75,000 - $95,000",
                "description": "Entry-level position for new graduates. Work on full-stack web applications using modern technologies. Great mentorship and learning opportunities.",
                "required_skills": ["JavaScript", "Python", "Git", "Problem Solving"],
                "preferred_skills": ["React", "Node.js", "Databases"],
                "experience_level": "entry",
                "application_url": "https://devfirst.com/careers/junior-dev"
            },
            {
                "title": "Machine Learning Engineer",
                "company": "AI Innovations",
                "location": "Seattle, WA",
                "job_type": "full-time",
                "salary_range": "$140,000 - $180,000",
                "description": "Build and deploy machine learning models at scale. Work with large datasets and cutting-edge ML technologies to solve complex business problems.",
                "required_skills": ["Python", "Machine Learning", "TensorFlow", "AWS", "Docker"],
                "preferred_skills": ["MLOps", "Kubernetes", "Spark"],
                "experience_level": "senior",
                "application_url": "https://ai-innovations.com/careers/ml-engineer"
            },
            {
                "title": "UX Designer",
                "company": "Design Studio",
                "location": "Los Angeles, CA",
                "job_type": "contract",
                "salary_range": "$70 - $90/hour",
                "description": "6-month contract to redesign our e-commerce platform. Create user-centered designs that improve conversion rates and user satisfaction.",
                "required_skills": ["UI/UX Design", "Figma", "User Research", "Prototyping"],
                "preferred_skills": ["Design Systems", "A/B Testing", "Sketch"],
                "experience_level": "mid",
                "application_url": "https://designstudio.com/contracts/ux"
            }
        ]
        
        # Filter mock jobs based on search criteria
        filtered_jobs = []
        for job_data in mock_jobs_data:
            if self._matches_filters(job_data, filters):
                job = JobRecommendation(
                    id=f"mock_{len(filtered_jobs)}",
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    job_type=job_data["job_type"],
                    salary_range=job_data["salary_range"],
                    description=job_data["description"],
                    required_skills=job_data["required_skills"],
                    preferred_skills=job_data.get("preferred_skills", []),
                    experience_level=job_data["experience_level"],
                    application_url=job_data["application_url"],
                    match_score=0.0
                )
                filtered_jobs.append(job)
        
        return filtered_jobs[:max_results]
    
    def _matches_filters(self, job_data: Dict, filters: JobSearchFilters) -> bool:
        """Check if a job matches the search filters"""
        
        # Check keywords
        job_text = f"{job_data['title']} {job_data['description']}".lower()
        keyword_match = any(keyword.lower() in job_text for keyword in filters.keywords)
        
        if not keyword_match:
            return False
        
        # Check location
        if filters.location and filters.location.lower() not in job_data["location"].lower():
            if not (filters.remote_ok and "remote" in job_data["location"].lower()):
                return False
        
        # Check job type
        if filters.job_type and filters.job_type != job_data["job_type"]:
            return False
        
        # Check experience level
        if filters.experience_level and filters.experience_level != job_data["experience_level"]:
            return False
        
        return True
    
    def _extract_skills(self, description: str) -> List[str]:
        """Extract technical skills from job description"""
        # Common technical skills to look for
        skill_patterns = [
            r'\bPython\b', r'\bJavaScript\b', r'\bJava\b', r'\bReact\b', r'\bNode\.js\b',
            r'\bSQL\b', r'\bAWS\b', r'\bDocker\b', r'\bGit\b', r'\bHTML\b', r'\bCSS\b',
            r'\bTypeScript\b', r'\bMachine Learning\b', r'\bTensorFlow\b', r'\bKubernetes\b',
            r'\bAngular\b', r'\bVue\b', r'\bRedux\b', r'\bGraphQL\b', r'\bMongoDB\b',
            r'\bPostgreSQL\b', r'\bRedis\b', r'\bElasticsearch\b', r'\bKafka\b'
        ]
        
        skills = []
        description_lower = description.lower()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            skills.extend(matches)
        
        # Remove duplicates and return
        return list(set(skills))
    
    def _deduplicate_jobs(self, jobs: List[JobRecommendation]) -> List[JobRecommendation]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = (job.title.lower(), job.company.lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _rank_jobs_by_relevance(self, jobs: List[JobRecommendation], 
                               filters: JobSearchFilters) -> List[JobRecommendation]:
        """Rank jobs by relevance to search criteria"""
        
        for job in jobs:
            score = 0.0
            
            # Keyword relevance (40% of score)
            job_text = f"{job.title} {job.description}".lower()
            keyword_matches = sum(1 for keyword in filters.keywords 
                                if keyword.lower() in job_text)
            keyword_score = (keyword_matches / len(filters.keywords)) * 0.4
            score += keyword_score
            
            # Location preference (20% of score)
            if filters.location:
                if filters.location.lower() in job.location.lower():
                    score += 0.2
                elif filters.remote_ok and "remote" in job.location.lower():
                    score += 0.15
            else:
                score += 0.2  # No location preference
            
            # Experience level match (20% of score)
            if filters.experience_level:
                if filters.experience_level == job.experience_level:
                    score += 0.2
                elif (filters.experience_level == "entry" and job.experience_level == "mid") or \
                     (filters.experience_level == "mid" and job.experience_level == "senior"):
                    score += 0.1  # Partial match for career progression
            else:
                score += 0.2
            
            # Job type match (10% of score)
            if filters.job_type:
                if filters.job_type == job.job_type:
                    score += 0.1
            else:
                score += 0.1
            
            # Recent posting bonus (10% of score)
            # For mock data, assume all jobs are recent
            score += 0.1
            
            job.match_score = min(1.0, score)
        
        # Sort by match score (descending)
        jobs.sort(key=lambda j: j.match_score, reverse=True)
        return jobs
    
    def get_job_recommendations_for_user(self, user: User, goal_keywords: List[str], 
                                       max_results: int = 10) -> List[JobRecommendation]:
        """Get personalized job recommendations for a user"""
        
        # Combine user skills/interests with goal keywords
        all_keywords = goal_keywords.copy()
        
        # Add user's top skills as keywords
        if user.skills:
            top_skills = [skill for skill, level in user.skills.items() 
                         if level in [SkillLevel.ADVANCED, SkillLevel.EXPERT]]
            all_keywords.extend(top_skills[:3])  # Top 3 skills
        
        # Add user interests
        all_keywords.extend(user.interests[:2])  # Top 2 interests
        
        # Create search filters
        filters = JobSearchFilters(
            keywords=all_keywords,
            location=user.location,
            remote_ok=True,  # Always include remote opportunities
            posted_within_days=14  # Recent postings
        )
        
        # Determine experience level based on user's background
        if user.years_experience:
            if user.years_experience < 2:
                filters.experience_level = "entry"
            elif user.years_experience < 5:
                filters.experience_level = "mid"
            else:
                filters.experience_level = "senior"
        
        return self.search_jobs(filters, max_results)
    
    def analyze_job_market_trends(self, keywords: List[str], 
                                location: Optional[str] = None) -> Dict[str, Any]:
        """Analyze job market trends for given skills/keywords"""
        
        # This would involve more sophisticated analysis in production
        # For now, provide basic insights based on mock data
        
        filters = JobSearchFilters(keywords=keywords, location=location)
        jobs = self.search_jobs(filters, max_results=50)
        
        if not jobs:
            return {"error": "No jobs found for analysis"}
        
        # Analyze salary ranges
        salaries = []
        for job in jobs:
            salary_nums = self._extract_salary_numbers(job.salary_range)
            if salary_nums:
                salaries.extend(salary_nums)
        
        # Analyze common skills
        all_required_skills = []
        all_preferred_skills = []
        
        for job in jobs:
            all_required_skills.extend(job.required_skills)
            all_preferred_skills.extend(job.preferred_skills)
        
        # Count skill frequencies
        from collections import Counter
        required_skill_counts = Counter(all_required_skills)
        preferred_skill_counts = Counter(all_preferred_skills)
        
        analysis = {
            "total_jobs_found": len(jobs),
            "salary_analysis": {
                "min_salary": min(salaries) if salaries else None,
                "max_salary": max(salaries) if salaries else None,
                "avg_salary": sum(salaries) / len(salaries) if salaries else None
            },
            "top_required_skills": dict(required_skill_counts.most_common(10)),
            "top_preferred_skills": dict(preferred_skill_counts.most_common(10)),
            "job_types": Counter([job.job_type for job in jobs]),
            "experience_levels": Counter([job.experience_level for job in jobs]),
            "top_companies": Counter([job.company for job in jobs]),
            "locations": Counter([job.location for job in jobs])
        }
        
        return analysis
    
    def _extract_salary_numbers(self, salary_range: str) -> List[int]:
        """Extract numeric salary values from salary range string"""
        if not salary_range:
            return []
        
        # Look for patterns like "$75,000 - $95,000" or "$25 - $35/hour"
        numbers = re.findall(r'\$([0-9,]+)', salary_range)
        
        salary_nums = []
        for num_str in numbers:
            try:
                # Remove commas and convert to int
                num = int(num_str.replace(',', ''))
                
                # If it looks like an hourly rate, convert to annual
                if "/hour" in salary_range and num < 200:
                    num = num * 40 * 52  # 40 hours/week, 52 weeks/year
                
                salary_nums.append(num)
            except ValueError:
                continue
        
        return salary_nums