import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIChat:
    def __init__(self):
        self.model_name = Config.AI_MODEL_NAME
        self.max_length = Config.MAX_RESPONSE_LENGTH
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.initialize_model()
        
        # Mental health focused response templates for different sentiment levels
        self.empathetic_starters = {
            'positive': [
                "I'm so glad to hear that! ",
                "That sounds wonderful! ",
                "It's great that you're feeling positive! "
            ],
            'negative': [
                "I hear that you're going through a difficult time. ",
                "That sounds really challenging. ",
                "I understand this must be hard for you. "
            ],
            'neutral': [
                "I appreciate you sharing that with me. ",
                "Thank you for telling me about this. ",
                "I'm here to listen and support you. "
            ]
        }
        
        self.supportive_endings = [
            " How can I support you further?",
            " What would be most helpful for you right now?",
            " Is there anything specific you'd like to talk about?",
            " I'm here for you whenever you need to talk."
        ]
    
    def initialize_model(self):
        """Initialize the DialoGPT model and tokenizer"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model.to(self.device)
            logger.info("AI Chat model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading AI model: {str(e)}")
            raise e
    
    def generate_response(self, user_message, sentiment_label='neutral', conversation_history=None):
        """Generate an empathetic response based on user message and sentiment"""
        try:
            # Prepare context with conversation history
            context = self._prepare_context(user_message, conversation_history)
            
            # Encode the input
            input_ids = self.tokenizer.encode(context + self.tokenizer.eos_token, return_tensors='pt').to(self.device)
            
            # Generate response
            with torch.no_grad():
                response_ids = self.model.generate(
                    input_ids,
                    max_length=input_ids.shape[1] + self.max_length,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    attention_mask=torch.ones_like(input_ids)
                )
            
            # Decode response
            response = self.tokenizer.decode(response_ids[:, input_ids.shape[1]:][0], skip_special_tokens=True)
            
            # Add empathetic framing based on sentiment
            empathetic_response = self._add_empathetic_framing(response, sentiment_label)
            
            return empathetic_response.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response(sentiment_label)
    
    def _prepare_context(self, user_message, conversation_history=None):
        """Prepare conversation context for the model"""
        if conversation_history:
            # Include last few messages for context (limit to avoid token overflow)
            context_messages = conversation_history[-3:]  # Last 3 exchanges
            context = ""
            for msg in context_messages:
                if msg.get('is_user_message'):
                    context += f"Human: {msg.get('message', '')} "
                else:
                    context += f"AI: {msg.get('response', '')} "
            context += f"Human: {user_message} AI:"
        else:
            context = f"Human: {user_message} AI:"
        
        return context
    
    def _add_empathetic_framing(self, response, sentiment_label):
        """Add empathetic context to the AI response"""
        import random
        
        # Choose appropriate starter based on sentiment
        starters = self.empathetic_starters.get(sentiment_label, self.empathetic_starters['neutral'])
        starter = random.choice(starters)
        
        # Choose supportive ending
        ending = random.choice(self.supportive_endings)
        
        # Clean up the response
        response = response.strip()
        if not response:
            response = "I'm here to listen and support you."
        
        # Combine with empathetic framing
        return f"{starter}{response}{ending}"
    
    def _get_fallback_response(self, sentiment_label):
        """Provide fallback responses when AI model fails"""
        fallback_responses = {
            'positive': "I'm so glad you're feeling good! It's wonderful to hear positive thoughts. How can I help you maintain this positive mood?",
            'negative': "I hear that you're going through a tough time, and I want you to know that your feelings are valid. I'm here to support you. What would be most helpful right now?",
            'neutral': "Thank you for sharing with me. I'm here to listen and provide support. What's on your mind today?"
        }
        
        return fallback_responses.get(sentiment_label, fallback_responses['neutral'])
    
    def get_conversation_summary(self, messages):
        """Generate a brief summary of the conversation"""
        if not messages:
            return "No conversation history"
        
        # Simple summary based on message count and sentiment trends
        user_messages = [msg for msg in messages if msg.get('is_user_message')]
        total_messages = len(user_messages)
        
        if total_messages == 0:
            return "No user messages"
        
        # Calculate average sentiment
        sentiments = [msg.get('sentiment_score', 0) for msg in user_messages if msg.get('sentiment_score') is not None]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        if avg_sentiment > 0.1:
            mood_trend = "generally positive"
        elif avg_sentiment < -0.1:
            mood_trend = "struggling with negative feelings"
        else:
            mood_trend = "experiencing mixed emotions"
        
        return f"Conversation with {total_messages} messages, user appears to be {mood_trend}"