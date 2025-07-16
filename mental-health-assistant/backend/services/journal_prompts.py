import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class JournalPromptGenerator:
    def __init__(self):
        # Categorized prompts based on different mental health themes
        self.prompt_categories = {
            'gratitude': [
                "What are three things you're grateful for today, and why do they matter to you?",
                "Describe a person who has positively impacted your life and how they've helped you grow.",
                "Write about a small moment from today that brought you joy or peace.",
                "What is something about yourself that you're thankful for?",
                "Describe a place that makes you feel calm and explain why it has that effect."
            ],
            
            'self_reflection': [
                "What emotions have you experienced most strongly this week? What might they be telling you?",
                "Describe a challenge you've overcome recently. What did you learn about yourself?",
                "What are three things you do well, and how can you use these strengths more?",
                "Write about a time when you were kind to yourself. How did it feel?",
                "What would you tell your younger self about handling difficult emotions?"
            ],
            
            'mindfulness': [
                "Take five deep breaths and describe what you notice in your body right now.",
                "What sounds, smells, or sensations are you aware of in this moment?",
                "Describe your current environment using all five senses.",
                "Write about what 'being present' means to you and how you can practice it more.",
                "What thoughts are going through your mind right now? Observe them without judgment."
            ],
            
            'goals_and_growth': [
                "What is one small step you can take tomorrow toward something important to you?",
                "Describe what personal growth means to you right now in your life.",
                "What habit would you like to develop, and why is it important to you?",
                "Write about a goal you're working toward and how you'll celebrate when you achieve it.",
                "What would you like to learn about yourself in the coming month?"
            ],
            
            'relationships': [
                "Describe how you show care and support to the people you love.",
                "Write about a conversation that meant a lot to you recently.",
                "What qualities do you value most in your friendships?",
                "How do you like to receive support when you're going through a difficult time?",
                "Describe someone who makes you feel understood and accepted."
            ],
            
            'coping_and_stress': [
                "What are your most effective strategies for managing stress?",
                "Describe a time when you successfully worked through a difficult situation.",
                "What activities help you feel more relaxed and centered?",
                "Write about what self-care means to you and how you practice it.",
                "What would you like to tell someone else who is going through a tough time?"
            ],
            
            'emotions': [
                "Describe an emotion you've been feeling lately and where you notice it in your body.",
                "Write about a time when you felt really proud of yourself.",
                "What does happiness look like for you in your daily life?",
                "How do you comfort yourself when you're feeling sad or disappointed?",
                "Describe what anger feels like for you and how you express it healthily."
            ],
            
            'future_and_hope': [
                "What are you looking forward to in the near future?",
                "Describe what a good day looks like for you.",
                "What gives you hope when things feel difficult?",
                "Write about something you're excited to experience or learn.",
                "What positive changes have you noticed in yourself over the past year?"
            ]
        }
        
        # Mood-based prompt selection weights
        self.mood_prompt_weights = {
            1: {  # Very Low mood
                'coping_and_stress': 0.3,
                'self_reflection': 0.2,
                'mindfulness': 0.3,
                'emotions': 0.2
            },
            2: {  # Low mood
                'coping_and_stress': 0.25,
                'self_reflection': 0.25,
                'mindfulness': 0.25,
                'gratitude': 0.25
            },
            3: {  # Neutral mood
                'self_reflection': 0.3,
                'mindfulness': 0.2,
                'goals_and_growth': 0.3,
                'relationships': 0.2
            },
            4: {  # Good mood
                'gratitude': 0.3,
                'goals_and_growth': 0.3,
                'relationships': 0.2,
                'future_and_hope': 0.2
            },
            5: {  # Very Good mood
                'gratitude': 0.4,
                'future_and_hope': 0.3,
                'goals_and_growth': 0.3
            }
        }
        
        # Seasonal prompts
        self.seasonal_prompts = {
            'spring': [
                "What new beginnings are you excited about this spring?",
                "How do you feel when you see things growing and blooming around you?"
            ],
            'summer': [
                "What activities bring you the most joy during the warmer months?",
                "Describe a perfect summer day from your perspective."
            ],
            'fall': [
                "What are you ready to let go of as the seasons change?",
                "What lessons have you learned this year that you want to carry forward?"
            ],
            'winter': [
                "How do you find warmth and comfort during the colder months?",
                "What does rest and reflection mean to you right now?"
            ]
        }
    
    def generate_prompt(self, user_mood=None, recent_entries=None, user_preferences=None):
        """
        Generate a personalized journal prompt
        
        Args:
            user_mood: Integer 1-5 representing current mood
            recent_entries: List of recent journal entries to avoid repetition
            user_preferences: Dict with user's preferred prompt categories
            
        Returns:
            dict: Contains prompt text, category, and metadata
        """
        try:
            # Determine prompt category based on mood and preferences
            category = self._select_category(user_mood, user_preferences)
            
            # Get available prompts from the category
            available_prompts = self.prompt_categories[category].copy()
            
            # Remove recently used prompts to avoid repetition
            if recent_entries:
                used_prompts = [entry.get('prompt') for entry in recent_entries if entry.get('prompt')]
                available_prompts = [p for p in available_prompts if p not in used_prompts]
            
            # Fallback if no prompts available
            if not available_prompts:
                available_prompts = self.prompt_categories[category]
            
            # Select a random prompt from available options
            selected_prompt = random.choice(available_prompts)
            
            # Add seasonal variation occasionally
            if random.random() < 0.2:  # 20% chance for seasonal prompt
                seasonal_prompt = self._get_seasonal_prompt()
                if seasonal_prompt:
                    selected_prompt = seasonal_prompt
                    category = 'seasonal'
            
            return {
                'prompt': selected_prompt,
                'category': category,
                'generated_at': datetime.utcnow().isoformat(),
                'mood_context': user_mood,
                'type': 'ai_generated'
            }
            
        except Exception as e:
            logger.error(f"Error generating journal prompt: {str(e)}")
            return self._get_fallback_prompt()
    
    def _select_category(self, user_mood, user_preferences):
        """Select appropriate prompt category based on mood and preferences"""
        
        # Use user preferences if available
        if user_preferences and 'preferred_categories' in user_preferences:
            preferred = user_preferences['preferred_categories']
            if preferred and any(cat in self.prompt_categories for cat in preferred):
                return random.choice([cat for cat in preferred if cat in self.prompt_categories])
        
        # Use mood-based selection
        if user_mood and user_mood in self.mood_prompt_weights:
            weights = self.mood_prompt_weights[user_mood]
            categories = list(weights.keys())
            probabilities = list(weights.values())
            
            # Weighted random selection
            return random.choices(categories, weights=probabilities)[0]
        
        # Default random selection
        return random.choice(list(self.prompt_categories.keys()))
    
    def _get_seasonal_prompt(self):
        """Get a seasonal prompt based on current time of year"""
        now = datetime.now()
        month = now.month
        
        if month in [3, 4, 5]:  # Spring
            season = 'spring'
        elif month in [6, 7, 8]:  # Summer
            season = 'summer'
        elif month in [9, 10, 11]:  # Fall
            season = 'fall'
        else:  # Winter
            season = 'winter'
        
        return random.choice(self.seasonal_prompts[season])
    
    def _get_fallback_prompt(self):
        """Return a fallback prompt when generation fails"""
        return {
            'prompt': "Take a moment to write about how you're feeling right now. What thoughts and emotions are present for you?",
            'category': 'general',
            'generated_at': datetime.utcnow().isoformat(),
            'mood_context': None,
            'type': 'fallback'
        }
    
    def get_prompt_by_category(self, category):
        """Get a random prompt from a specific category"""
        if category not in self.prompt_categories:
            return self._get_fallback_prompt()
        
        return {
            'prompt': random.choice(self.prompt_categories[category]),
            'category': category,
            'generated_at': datetime.utcnow().isoformat(),
            'mood_context': None,
            'type': 'category_specific'
        }
    
    def get_weekly_prompts(self, user_mood_average=None):
        """Generate a set of prompts for the week"""
        weekly_prompts = []
        categories_used = set()
        
        for day in range(7):
            # Ensure variety by avoiding recently used categories
            available_categories = [cat for cat in self.prompt_categories.keys() 
                                  if cat not in categories_used or len(categories_used) >= 6]
            
            category = random.choice(available_categories)
            categories_used.add(category)
            
            prompt_data = self.get_prompt_by_category(category)
            prompt_data['day'] = day + 1
            prompt_data['week_position'] = f"Day {day + 1}"
            
            weekly_prompts.append(prompt_data)
            
            # Reset category tracking if we've used most categories
            if len(categories_used) >= 6:
                categories_used.clear()
        
        return weekly_prompts
    
    def get_available_categories(self):
        """Return list of available prompt categories with descriptions"""
        category_descriptions = {
            'gratitude': 'Focus on thankfulness and positive aspects of life',
            'self_reflection': 'Explore thoughts, feelings, and personal insights',
            'mindfulness': 'Present-moment awareness and body-mind connection',
            'goals_and_growth': 'Personal development and future aspirations',
            'relationships': 'Connections with others and social support',
            'coping_and_stress': 'Managing challenges and building resilience',
            'emotions': 'Understanding and expressing feelings',
            'future_and_hope': 'Optimism and positive future planning'
        }
        
        return [
            {
                'category': category,
                'description': description,
                'prompt_count': len(prompts)
            }
            for category, (description, prompts) in 
            zip(category_descriptions.keys(), 
                [(desc, self.prompt_categories[cat]) for cat, desc in category_descriptions.items()])
        ]