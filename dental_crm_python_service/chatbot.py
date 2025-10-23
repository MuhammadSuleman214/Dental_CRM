from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.chains import LLMChain
from config import config
from datetime import datetime, timedelta
import re
import json

class DentalChatbot:
    def __init__(self):
        """Initialize the dental assistant chatbot"""
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_date_formatted = datetime.now().strftime('%A, %B %d, %Y')
        
        self.system_prompt = """You are an intelligent multilingual dental clinic assistant. Your role is to:

**CURRENT DATE**: Today is {} ({})

1. **MULTILINGUAL SUPPORT**: Respond in the same language the user writes in (English/Urdu/Hindi)
2. **UNDERSTAND CONTEXT**: Always read the user's message carefully and respond appropriately
3. **SCHEDULE APPOINTMENTS**: Help patients book appointments by extracting date, time, and reason
4. **ANSWER QUESTIONS**: Provide helpful information about dental services
5. **BE CONTEXTUAL**: If user mentions a specific time/date, acknowledge it and ask for confirmation

**Available Services (in both English and Urdu):**
- General Checkup & Consultation / عمومی چیک اپ اور مشاورہ
- Teeth Cleaning & Scaling / دانت صاف کرنا
- Cavity Filling / کیویٹی بھرنا
- Root Canal Treatment / روٹ کینال علاج
- Teeth Whitening / دانت سفید کرنا
- Orthodontics (Braces) / دانتوں کا علاج
- Emergency Dental Care / ہنگامی دانتوں کا علاج
- Dental Implants / دانت لگانا

**Office Hours:**
- Monday-Friday: 9:00 AM - 5:00 PM / پیر سے جمعہ: صبح 9 بجے سے شام 5 بجے
- Saturday: 9:00 AM - 1:00 PM / ہفتہ: صبح 9 بجے سے دوپہر 1 بجے
- Sunday: Closed / اتوار: بند

**LANGUAGE RESPONSE RULES:**
- If user writes in Urdu/Hindi: Respond in Urdu/Hindi
- If user writes in English: Respond in English
- If mixed language: Use the dominant language
- Always maintain professional and empathetic tone

**IMPORTANT INSTRUCTIONS:**
- Detect user's language and respond accordingly
- If user mentions a specific date/time, acknowledge it and ask for confirmation
- Always be conversational and natural
- Ask clarifying questions when needed
- Be empathetic and patient-focused
- **DATE HANDLING**: When user says "tomorrow", calculate the correct date based on the current date above
- **DATE FORMAT**: Always use YYYY-MM-DD format for dates in appointment data

**Appointment Extraction:**
When you identify appointment details, respond with JSON in this format:
APPOINTMENT_DATA: {{"date": "YYYY-MM-DD", "time": "HH:MM", "reason": "reason for visit"}}

**Examples of Good Responses:**

**English:**
- User: "Monday 11am" → "Perfect! You'd like to schedule for Monday at 11:00 AM. What type of appointment would you like to book?"
- User: "I need cleaning" → "Great! We offer professional teeth cleaning. When would be convenient for you?"

**Urdu:**
- User: "پیر کو صبح 11 بجے" → "بہترین! آپ پیر کو صبح 11 بجے کا وقت چاہتے ہیں۔ آپ کیا قسم کا اپائنٹمنٹ چاہتے ہیں؟"
- User: "مجھے صفائی چاہیے" → "بہت اچھا! ہم پیشہ ورانہ دانت صاف کرنے کی سروس پیش کرتے ہیں۔ آپ کے لیے کون سا وقت مناسب ہوگا؟"

Always be helpful, professional, and contextually aware while maintaining the user's language preference.""".format(current_date, current_date_formatted)
    
    def extract_appointment_data(self, message):
        """Extract appointment information from user message"""
        import re
        from datetime import datetime, timedelta
        
        # Look for date patterns - ORDER MATTERS! Most specific first
        date_patterns = [
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}',  # Oct 13, 2025
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',  # October 13, 2025
            r'\d{1,2}(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}',  # 13oct 2025
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(tomorrow|today|next week|کل|آج|اگلے ہفتے)',  # Relative dates
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|پیر|منگل|بدھ|جمعرات|جمعہ|ہفتہ|اتوار)',  # Day names
        ]
        
        # Look for time patterns (English and Urdu)
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',  # 2:30 PM
            r'(\d{1,2}\s*(?:AM|PM|am|pm))',  # 2 PM
            r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',  # 11am, 11:30am
            r'(\d{1,2}\s*baje?)',  # 2 baje (Urdu/Hindi)
            r'(\d{1,2}\s*بجے)',  # 2 بجے (Urdu)
            r'(\d{1,2}:\d{2}\s*بجے)',  # 2:30 بجے (Urdu)
            r'(صبح\s*\d{1,2})',  # صبح 2
            r'(دوپہر\s*\d{1,2})',  # دوپہر 2
            r'(شام\s*\d{1,2})',  # شام 2
            r'(رات\s*\d{1,2})',  # رات 2
        ]
        
        extracted_date = None
        extracted_time = None
        
        # Try to extract date
        print(f"🔍 Extracting date from message: '{message}'")
        for i, pattern in enumerate(date_patterns):
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted_date = match.group(1)
                print(f"📅 Date pattern {i+1} matched: '{extracted_date}' from pattern: {pattern}")
                break
        else:
            print(f"❌ No date pattern matched for message: '{message}'")
        
        # Try to extract time
        print(f"🕐 Extracting time from message: '{message}'")
        for i, pattern in enumerate(time_patterns):
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted_time = match.group(1).strip()
                print(f"🕐 Time pattern {i+1} matched: '{extracted_time}' from pattern: {pattern}")
                # Convert Urdu time formats to standard format
                if 'بجے' in extracted_time:
                    # Extract number from "2 بجے" or "2:30 بجے"
                    time_match = re.search(r'(\d{1,2}(?::\d{2})?)', extracted_time)
                    if time_match:
                        time_part = time_match.group(1)
                        if ':' not in time_part:
                            extracted_time = f"{time_part}:00"
                        else:
                            extracted_time = time_part
                elif any(period in extracted_time for period in ['صبح', 'دوپہر', 'شام', 'رات']):
                    # Convert Urdu periods to AM/PM
                    time_match = re.search(r'(\d{1,2})', extracted_time)
                    if time_match:
                        hour = int(time_match.group(1))
                        if 'صبح' in extracted_time:  # Morning
                            extracted_time = f"{hour}:00 AM"
                        elif 'دوپہر' in extracted_time:  # Afternoon
                            extracted_time = f"{hour}:00 PM"
                        elif 'شام' in extracted_time:  # Evening
                            extracted_time = f"{hour}:00 PM"
                        elif 'رات' in extracted_time:  # Night
                            extracted_time = f"{hour}:00 PM"
                break
        
        # Handle relative dates, day names, and month names
        if extracted_date:
            # Use real-time current date
            today = datetime.now()
            day_name = extracted_date.lower()
            print(f"Using real-time current date: {today.strftime('%Y-%m-%d')}")
            
            if day_name == 'today' or day_name == 'آج':
                extracted_date = today.strftime('%Y-%m-%d')
                print(f"Today parsed: {extracted_date}")
            elif day_name == 'tomorrow' or day_name == 'کل':
                tomorrow = today + timedelta(days=1)
                extracted_date = tomorrow.strftime('%Y-%m-%d')
                print(f"Tomorrow parsed: {extracted_date}")
            elif day_name == 'next week' or day_name == 'اگلے ہفتے':
                next_week = today + timedelta(days=7)
                extracted_date = next_week.strftime('%Y-%m-%d')
                print(f"Next week parsed: {extracted_date}")
            elif day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                # Calculate next occurrence of the day
                days_ahead = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(day_name) - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                extracted_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                print(f"Day name parsed: {day_name} -> {extracted_date}")
            elif day_name in ['پیر', 'منگل', 'بدھ', 'جمعرات', 'جمعہ', 'ہفتہ', 'اتوار']:
                # Urdu day names mapping
                urdu_to_english = {
                    'پیر': 'monday', 'منگل': 'tuesday', 'بدھ': 'wednesday',
                    'جمعرات': 'thursday', 'جمعہ': 'friday', 'ہفتہ': 'saturday', 'اتوار': 'sunday'
                }
                english_day = urdu_to_english[day_name]
                days_ahead = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(english_day) - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                extracted_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                print(f"Urdu day parsed: {day_name} -> {extracted_date}")
            else:
                # Handle month names like "Oct 15, 2025" or "October 15, 2025"
                try:
                    # Month name mapping
                    month_mapping = {
                        'jan': '01', 'january': '01',
                        'feb': '02', 'february': '02',
                        'mar': '03', 'march': '03',
                        'apr': '04', 'april': '04',
                        'may': '05',
                        'jun': '06', 'june': '06',
                        'jul': '07', 'july': '07',
                        'aug': '08', 'august': '08',
                        'sep': '09', 'september': '09',
                        'oct': '10', 'october': '10',
                        'nov': '11', 'november': '11',
                        'dec': '12', 'december': '12'
                    }
                    
                    # Parse month name format
                    import re
                    
                    # Try format: "Oct 15, 2025" or "October 15, 2025"
                    month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})', day_name, re.IGNORECASE)
                    if month_match:
                        month_name = month_match.group(1).lower()
                        day_num = month_match.group(2).zfill(2)
                        year = month_match.group(3)
                        
                        # Validate year (should be reasonable, not 1970)
                        if int(year) >= 2024 and int(year) <= 2030:
                            if month_name in month_mapping:
                                month_num = month_mapping[month_name]
                                extracted_date = f"{year}-{month_num}-{day_num}"
                                print(f"📅 Parsed date: {extracted_date} from '{day_name}'")
                            else:
                                print(f"❌ Month name not found: {month_name}")
                        else:
                            print(f"❌ Invalid year: {year} (should be 2024-2030)")
                    else:
                        # Try format: "13oct 2025"
                        compact_match = re.search(r'(\d{1,2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})', day_name)
                        if compact_match:
                            day_num = compact_match.group(1).zfill(2)
                            month_name = compact_match.group(2).lower()
                            year = compact_match.group(3)
                            
                            # Validate year (should be reasonable, not 1970)
                            if int(year) >= 2024 and int(year) <= 2030:
                                if month_name in month_mapping:
                                    month_num = month_mapping[month_name]
                                    extracted_date = f"{year}-{month_num}-{day_num}"
                                    print(f"📅 Parsed date (compact): {extracted_date} from '{day_name}'")
                                else:
                                    print(f"❌ Month name not found: {month_name}")
                            else:
                                print(f"❌ Invalid year (compact): {year} (should be 2024-2030)")
                except:
                    # If parsing fails, keep original
                    pass
        
        print(f"📋 Final extracted data: Date='{extracted_date}', Time='{extracted_time}'")
        return extracted_date, extracted_time
    
    def detect_language(self, text):
        """Detect if text is in Urdu/Hindi or English"""
        urdu_indicators = ['ہے', 'ہیں', 'کیا', 'کے', 'کو', 'میں', 'پر', 'سے', 'تک', 'بجے', 'صبح', 'شام', 'رات', 'دوپہر', 'پیر', 'منگل', 'بدھ', 'جمعرات', 'جمعہ', 'ہفتہ', 'اتوار', 'کل', 'آج', 'اگلے']
        hindi_indicators = ['है', 'हैं', 'क्या', 'के', 'को', 'में', 'पर', 'से', 'तक', 'बजे', 'सुबह', 'शाम', 'रात', 'दोपहर']
        
        text_lower = text.lower()
        urdu_count = sum(1 for indicator in urdu_indicators if indicator in text_lower)
        hindi_count = sum(1 for indicator in hindi_indicators if indicator in text_lower)
        
        if urdu_count > hindi_count and urdu_count > 0:
            return 'urdu'
        elif hindi_count > urdu_count and hindi_count > 0:
            return 'hindi'
        else:
            return 'english'
    
    def analyze_conversation_context(self, conversation_history, current_message):
        """Analyze conversation history to understand context"""
        context_info = {
            'is_booking': False,
            'is_confirmation': False,
            'is_reschedule': False,
            'appointment': None,
            'old_appointment': None,
            'new_appointment': None
        }
        
        if not conversation_history:
            return context_info
        
        current_lower = current_message.lower()
        
        # Check if current message is a confirmation
        if any(word in current_lower for word in ['yes', 'yeah', 'yep', 'confirm', 'ok', 'okay']):
            context_info['is_confirmation'] = True
        
        # Check if current message is about booking
        if any(word in current_lower for word in ['book', 'schedule', 'appointment']):
            context_info['is_booking'] = True
        
        # Check if current message is about rescheduling (English and Urdu)
        if any(word in current_lower for word in ['reschedule', 'shift', 'change', 'move', 'postpone', 'تبدیل', 'شفٹ', 'منتقل', 'ملتوی']):
            context_info['is_reschedule'] = True
        
        # Analyze conversation history for appointment details
        appointment_details = []
        reschedule_details = []
        
        for msg in conversation_history:
            if msg['sender'] == 'user':
                msg_text = msg['message'].lower()
                
                # Extract appointment data
                extracted_date, extracted_time = self.extract_appointment_data(msg['message'])
                if extracted_date and extracted_time:
                    # Determine service type
                    reason = "General Checkup"
                    if 'rct' in msg_text or 'root canal' in msg_text:
                        reason = "Root Canal Treatment"
                    elif 'cleaning' in msg_text or 'clean' in msg_text:
                        reason = "Teeth Cleaning"
                    elif 'filling' in msg_text or 'cavity' in msg_text:
                        reason = "Cavity Filling"
                    elif 'checkup' in msg_text or 'check' in msg_text:
                        reason = "General Checkup"
                    elif 'pain' in msg_text or 'hurt' in msg_text:
                        reason = "Pain Consultation"
                    
                    appointment_data = {
                        "date": extracted_date,
                        "time": extracted_time,
                        "reason": reason
                    }
                    
                    # Check if this is a reschedule request (English and Urdu)
                    if any(word in msg_text for word in ['shift', 'change', 'move', 'reschedule', 'from', 'to', 'تبدیل', 'شفٹ', 'منتقل', 'سے', 'کو']):
                        reschedule_details.append(appointment_data)
                    else:
                        appointment_details.append(appointment_data)
        
        # Handle reschedule context
        if len(reschedule_details) >= 2:
            context_info['old_appointment'] = reschedule_details[0]
            context_info['new_appointment'] = reschedule_details[1]
        
        # Handle booking context
        elif appointment_details:
            context_info['appointment'] = appointment_details[-1]  # Use most recent
        
        return context_info
    
    def generate_response(self, user_message, conversation_history=None, user_name=None):
        """Generate chatbot response using LangChain"""
        try:
            # Check if OpenAI API key is properly set
            if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith('sk-your'):
                # Intelligent mock responses for testing without OpenAI key
                message_lower = user_message.lower()
                
                # Advanced conversation context analysis
                context_info = self.analyze_conversation_context(conversation_history, user_message)
                print(f"🧠 Context Analysis:")
                print(f"  - Is Booking: {context_info['is_booking']}")
                print(f"  - Is Confirmation: {context_info['is_confirmation']}")
                print(f"  - Is Reschedule: {context_info['is_reschedule']}")
                print(f"  - Appointment: {context_info['appointment']}")
                print(f"  - Old Appointment: {context_info['old_appointment']}")
                print(f"  - New Appointment: {context_info['new_appointment']}")
                
                # Detect user language
                user_language = self.detect_language(user_message)
                print(f"🌍 Detected Language: {user_language}")
                
                # Handle rescheduling requests
                if context_info['is_reschedule'] and context_info['new_appointment']:
                    if user_language == 'urdu':
                        response = f"بہترین! میں آپ کا اپائنٹمنٹ {context_info['old_appointment']['date']} کو {context_info['old_appointment']['time']} سے {context_info['new_appointment']['date']} کو {context_info['new_appointment']['time']} میں تبدیل کر رہا ہوں۔ آپ کا اپائنٹمنٹ اپڈیٹ ہو گیا ہے! آپ کو جلد ہی تصدیقی ای میل موصول ہوگی۔"
                    else:
                        response = f"Perfect! I'll reschedule your appointment from {context_info['old_appointment']['date']} at {context_info['old_appointment']['time']} to {context_info['new_appointment']['date']} at {context_info['new_appointment']['time']}. Your appointment has been updated! You'll receive a confirmation email shortly."
                    
                    return {
                        "response": response,
                        "appointment_data": context_info['new_appointment'],
                        "is_reschedule": True,
                        "old_appointment_data": context_info['old_appointment']
                    }
                
                # Handle confirmation requests with context
                if context_info['is_confirmation'] and context_info['appointment']:
                    if user_language == 'urdu':
                        response = f"بہترین! میں نے آپ کا {context_info['appointment']['reason']} کا اپائنٹمنٹ {context_info['appointment']['date']} کو {context_info['appointment']['time']} کے لیے تصدیق کر دیا ہے۔ آپ کا اپائنٹمنٹ اب تصدیق شدہ ہے! کیا میں آپ کی کوئی اور مدد کر سکتا ہوں؟"
                    else:
                        response = f"Excellent! I've confirmed your {context_info['appointment']['reason']} appointment for {context_info['appointment']['date']} at {context_info['appointment']['time']}. Your appointment is now confirmed! Is there anything else I can help you with?"
                    
                    return {
                        "response": response,
                        "appointment_data": context_info['appointment']
                    }
                
                # Handle booking requests with context
                if context_info['is_booking'] and context_info['appointment']:
                    if user_language == 'urdu':
                        response = f"بہترین! میں آپ کا {context_info['appointment']['reason']} کا اپائنٹمنٹ {context_info['appointment']['date']} کو {context_info['appointment']['time']} کے لیے بک کر رہا ہوں۔ آپ کا اپائنٹمنٹ تصدیق شدہ ہے! آپ کو جلد ہی تصدیقی ای میل موصول ہوگی۔ کیا میں آپ کی کوئی اور مدد کر سکتا ہوں؟"
                    else:
                        response = f"Perfect! I'll book your {context_info['appointment']['reason']} appointment for {context_info['appointment']['date']} at {context_info['appointment']['time']}. Your appointment has been confirmed! You'll receive a confirmation email shortly. Is there anything else I can help you with?"
                    
                    return {
                        "response": response,
                        "appointment_data": context_info['appointment']
                    }

                # Date/time patterns with appointment extraction (including tomorrow)
                if any(keyword in message_lower for keyword in ['tomorrow', 'today', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'کل', 'آج']):
                    if any(time in message_lower for time in ['am', 'pm', 'morning', 'afternoon', 'evening', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']):
                        # Extract date and time
                        extracted_date, extracted_time = self.extract_appointment_data(user_message)
                        appointment_data = None
                        
                        if extracted_date and extracted_time:
                            # Determine service type from message
                            reason = "General Checkup"
                            if 'rct' in message_lower or 'root canal' in message_lower:
                                reason = "Root Canal Treatment"
                            elif 'cleaning' in message_lower or 'clean' in message_lower:
                                reason = "Teeth Cleaning"
                            elif 'filling' in message_lower or 'cavity' in message_lower:
                                reason = "Cavity Filling"
                            elif 'checkup' in message_lower or 'check' in message_lower:
                                reason = "General Checkup"
                            elif 'pain' in message_lower or 'hurt' in message_lower:
                                reason = "Pain Consultation"
                            
                            appointment_data = {
                                "date": extracted_date,
                                "time": extracted_time,
                                "reason": reason
                            }
                            
                            # Generate proper confirmation response
                            confirmation = self.confirm_appointment(appointment_data, user_name or "Patient")
                            return {
                                "response": confirmation,
                                "appointment_data": appointment_data
                            }
                
                # Service requests
                if any(service in message_lower for service in ['cleaning', 'clean', 'checkup', 'check', 'filling', 'cavity', 'pain', 'hurt']):
                    return {
                        "response": f"Great! I can help you with that. For {user_message}, when would be convenient for you? Our available hours are Monday-Friday 9AM-5PM and Saturday 9AM-1PM.",
                        "appointment_data": None
                    }
                
                # Appointment requests
                if any(word in message_lower for word in ['appointment', 'book', 'schedule', 'visit', 'come', 'اپائنٹمنٹ', 'بک', 'شیڈول', 'وزٹ', 'ملاقات', 'آنا']):
                    if user_language == 'urdu':
                        response = "میں آپ کا اپائنٹمنٹ بک کرنے میں خوشی محسوس کروں گا! آپ کے لیے کون سا تاریخ اور وقت بہتر ہوگا؟ نیز، آپ کو کس قسم کا اپائنٹمنٹ چاہیے؟"
                    else:
                        response = "I'd be happy to help you schedule an appointment! What date and time would work best for you? Also, what type of appointment do you need?"
                    
                    return {
                        "response": response,
                        "appointment_data": None
                    }
                
                # Greetings
                if any(greet in message_lower for greet in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'السلام علیکم', 'سلام', 'ہیلو', 'صبح بخیر', 'شام بخیر']):
                    if user_language == 'urdu':
                        response = "السلام علیکم! ہمارے ڈینٹل کلینک میں خوش آمدید۔ آج میں آپ کی کیا مدد کر سکتا ہوں؟ میں اپائنٹمنٹ بک کرنے، ہماری سروسز کے بارے میں سوالات کے جوابات دینے، یا عام معلومات فراہم کرنے میں مدد کر سکتا ہوں۔"
                    else:
                        response = "Hello! Welcome to our dental clinic. How can I help you today? I can assist with scheduling appointments, answering questions about our services, or providing general information."
                    
                    return {
                        "response": response,
                        "appointment_data": None
                    }
                
                # Default response
                if user_language == 'urdu':
                    response = f"میں سمجھتا ہوں کہ آپ '{user_message}' کے بارے میں پوچھ رہے ہیں۔ کیا آپ مزید تفصیلات فراہم کر سکتے ہیں؟ میں اپائنٹمنٹ بک کرنے، سروس کی معلومات، یا کوئی بھی ڈینٹل سے متعلق سوالات کے جوابات میں مدد کر سکتا ہوں۔"
                else:
                    response = f"I understand you're asking about '{user_message}'. Could you please provide more details? I can help you with appointment scheduling, service information, or answer any dental-related questions."
                
                return {
                    "response": response,
                    "appointment_data": None
                }
            
            # Build conversation context
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history:
                    if msg['sender'] == 'user':
                        messages.append(HumanMessage(content=msg['message']))
                    elif msg['sender'] == 'bot':
                        messages.append(AIMessage(content=msg['message']))
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            # Get response from LLM
            response = self.llm.invoke(messages)
            bot_response = response.content
            
            # Check if appointment data is present in response
            appointment_data = None
            if "APPOINTMENT_DATA:" in bot_response:
                try:
                    # Extract JSON from response
                    json_start = bot_response.index("{")
                    json_end = bot_response.rindex("}") + 1
                    json_str = bot_response[json_start:json_end]
                    appointment_data = json.loads(json_str)
                    
                    # Clean response to remove JSON
                    bot_response = bot_response[:bot_response.index("APPOINTMENT_DATA:")].strip()
                except Exception as e:
                    print(f"Error parsing appointment data: {e}")
            
            # Alternatively, try to extract from user message
            if not appointment_data:
                extracted_date, extracted_time = self.extract_appointment_data(user_message)
                if extracted_date and extracted_time:
                    appointment_data = {
                        "date": extracted_date,
                        "time": extracted_time,
                        "reason": "General Checkup"  # Default
                    }
            
            return {
                "response": bot_response,
                "appointment_data": appointment_data
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "appointment_data": None
            }
    
    def confirm_appointment(self, appointment_data, user_name):
        """Generate appointment confirmation message"""
        date = appointment_data.get('date', 'N/A')
        time = appointment_data.get('time', 'N/A')
        reason = appointment_data.get('reason', 'N/A')
        
        # Format date properly for display
        try:
            from datetime import datetime
            if date != 'N/A':
                parsed_date = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = parsed_date.strftime('%Y-%m-%d')
            else:
                formatted_date = date
        except:
            formatted_date = date
        
        confirmation = f"""
Perfect! I've scheduled your appointment:

👤 Patient: {user_name}
📅 Date: {formatted_date}
🕐 Time: {time}
🦷 Reason: {reason}

Your appointment has been confirmed! You'll receive a confirmation email shortly.
Is there anything else I can help you with?
"""
        return confirmation.strip()

# Singleton instance
chatbot = DentalChatbot()

