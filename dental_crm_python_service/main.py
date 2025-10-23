from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from datetime import datetime

from config import config
from database import db
from chatbot import chatbot
from email_service import email_service

# Initialize FastAPI app
app = FastAPI(
    title="Dental CRM Chatbot Service",
    description="AI-powered chatbot for dental appointment scheduling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: int
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: int
    appointment_data: Optional[dict] = None
    timestamp: str

class AppointmentCreate(BaseModel):
    user_id: int
    date: str
    time: str
    reason: str

class PasswordResetRequest(BaseModel):
    email: str
    user_name: str
    reset_token: str

class HealthCheck(BaseModel):
    status: str
    service: str
    timestamp: str

@app.get("/", response_model=HealthCheck)
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Dental CRM Chatbot",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        db.ensure_connection()
        return {
            "status": "healthy",
            "service": "Dental CRM Chatbot",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint"""
    try:
        user_id = message.user_id
        session_id = message.session_id
        
        # Get user info
        user_info = db.get_user_info(user_id)
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create new session if not provided
        if not session_id:
            session_id = db.create_chat_session(user_id)
            if not session_id:
                print(" Warning: Failed to create chat session, using mock session")
                session_id = 999999  # Mock session ID for testing
        
        # Get conversation history
        history = db.get_session_history(session_id, limit=10)
        print(f"Conversation history for session {session_id}: {len(history)} messages")
        for i, msg in enumerate(history):
            print(f"  {i+1}. {msg['sender']}: {msg['message'][:50]}...")
        
        # Save user message (with error handling)
        try:
            db.save_message(session_id, 'user', message.message)
        except Exception as e:
            print(f" Warning: Failed to save user message: {e}")
        
        # Generate bot response
        bot_result = chatbot.generate_response(message.message, history, user_info['name'])
        bot_response = bot_result['response']
        appointment_data = bot_result['appointment_data']
        is_reschedule = bot_result.get('is_reschedule', False)
        old_appointment_data = bot_result.get('old_appointment_data', None)
        
        # Handle reschedule request
        if is_reschedule and appointment_data and old_appointment_data:
            print(f" Reschedule request detected")
            print(f"  Old: {old_appointment_data['date']} {old_appointment_data['time']}")
            print(f"  New: {appointment_data['date']} {appointment_data['time']}")
            
            # Find the existing appointment
            existing_appointment = db.find_appointment_by_date_time(
                user_id,
                old_appointment_data['date'],
                old_appointment_data['time']
            )
            
            if existing_appointment:
                # Reschedule the appointment
                new_appointment_datetime = f"{appointment_data['date']} {appointment_data['time']}"
                notes = f"Rescheduled - Reason: {appointment_data.get('reason', 'Not specified')}"
                
                success = db.reschedule_appointment(
                    existing_appointment['id'],
                    new_appointment_datetime,
                    notes
                )
                
                if success:
                    appointment_data['appointment_id'] = existing_appointment['id']
                    appointment_data['action'] = 'rescheduled'
                    print(f" Appointment rescheduled successfully")
                    
                    # Send reschedule confirmation email
                    try:
                        email_sent = email_service.send_reschedule_confirmation(
                            user_info['email'],
                            user_info['name'],
                            old_appointment_data['date'],
                            old_appointment_data['time'],
                            appointment_data['date'],
                            appointment_data['time'],
                            appointment_data.get('reason', 'General Checkup')
                        )
                        if email_sent:
                            print(f" Reschedule confirmation email sent to {user_info['email']}")
                        else:
                            print(f" Failed to send reschedule email to {user_info['email']}")
                    except Exception as e:
                        print(f" Reschedule email service error: {e}")
                else:
                    print(f" Failed to reschedule appointment")
            else:
                print(f" No existing appointment found to reschedule")
        
        # If appointment data is extracted and it's NOT a reschedule, validate first
        elif appointment_data and not is_reschedule:
            # First validate working hours and days
            is_valid_time, validation_message = db.validate_working_hours_and_days(
                appointment_data['date'], 
                appointment_data['time']
            )
            
            if not is_valid_time:
                # Time is outside working hours or on weekend
                user_language = chatbot.detect_language(message.message)
                
                if user_language == 'urdu':
                    if "weekends" in validation_message:
                        bot_response = f"""معذرت! ہم ہفتے کے آخر میں بند رہتے ہیں۔

📅 ہمارے کام کے دن: پیر سے جمعہ
🕐 کام کے اوقات: صبح 9 بجے سے شام 5 بجے تک

براہ کرم کوئی اور تاریخ منتخب کریں۔"""
                    else:
                        bot_response = f"""معذرت! یہ وقت ہمارے کام کے اوقات سے باہر ہے۔

🕐 ہمارے کام کے اوقات: صبح 9 بجے سے شام 5 بجے تک
📅 کام کے دن: پیر سے جمعہ

براہ کرم کوئی اور وقت منتخب کریں۔"""
                else:
                    bot_response = f"""Sorry! {validation_message}

📅 Our working days: Monday-Friday
🕐 Our working hours: 9:00 AM to 5:00 PM

Please select a different time."""
                
                appointment_data = None
            else:
                # Time is valid, check slot availability
                is_slot_available = db.check_time_slot_availability(
                    appointment_data['date'], 
                    appointment_data['time']
                )
                
                if is_slot_available:
                    # Slot is available, create appointment
                    appointment_datetime = f"{appointment_data['date']} {appointment_data['time']}"
                    notes = f"Reason: {appointment_data.get('reason', 'Not specified')}"
                    
                    appointment_id = db.create_appointment_from_chat(
                        user_id, 
                        appointment_datetime, 
                        notes
                    )
                    
                    if appointment_id:
                        # Generate confirmation message
                        confirmation = chatbot.confirm_appointment(appointment_data, user_info['name'])
                        bot_response = confirmation
                        appointment_data['appointment_id'] = appointment_id
                        
                        # Send confirmation email
                        try:
                            email_sent = email_service.send_appointment_confirmation(
                                user_info['email'],
                                user_info['name'],
                                appointment_data['date'],
                                appointment_data['time'],
                                appointment_data.get('reason', 'General Checkup')
                            )
                            if email_sent:
                                print(f" Confirmation email sent to {user_info['email']}")
                            else:
                                print(f" Failed to send confirmation email to {user_info['email']}")
                        except Exception as e:
                            print(f" Email service error: {e}")
                    else:
                        bot_response = "Sorry, I couldn't create your appointment. Please try again or contact our office directly."
                else:
                    # Slot is not available, suggest alternatives
                    print(f" Time slot not available: {appointment_data['date']} {appointment_data['time']}")
                    
                    # Get alternative time slots
                    available_slots = db.get_available_time_slots(
                        appointment_data['date'], 
                        appointment_data['time']
                    )
                    
                    if available_slots:
                        # Format available slots for display
                        slot_options = []
                        for slot in available_slots[:5]:  # Show first 5 options
                            formatted_time = slot.strftime('%I:%M %p')
                            slot_options.append(formatted_time)
                        
                        if len(available_slots) > 5:
                            slot_options.append("...and more")
                        
                        # Detect user language for response
                        user_language = chatbot.detect_language(message.message)
                        
                        if user_language == 'urdu':
                            bot_response = f"""معذرت! یہ وقت پہلے سے بک ہے: {appointment_data['date']} کو {appointment_data['time']}

📅 دستیاب وقت:
{chr(10).join([f"• {slot}" for slot in slot_options])}

براہ کرم کوئی اور وقت منتخب کریں۔ کیا میں آپ کے لیے کوئی اور وقت بک کر دوں؟"""
                        else:
                            bot_response = f"""Sorry! This time slot is already booked: {appointment_data['date']} at {appointment_data['time']}

📅 Available times:
{chr(10).join([f"• {slot}" for slot in slot_options])}

Please select an alternative time. Would you like me to book one of these slots for you?"""
                        
                        # Clear appointment_data since we couldn't book the requested slot
                        appointment_data = None
                    else:
                        # No slots available for the day
                        user_language = chatbot.detect_language(message.message)
                        
                        if user_language == 'urdu':
                            bot_response = f"""معذرت! {appointment_data['date']} کو کوئی وقت دستیاب نہیں ہے۔

📅 براہ کرم کوئی اور تاریخ منتخب کریں یا ہمارے دفتر سے رابطہ کریں۔"""
                        else:
                            bot_response = f"""Sorry! No time slots are available on {appointment_data['date']}.

📅 Please select a different date or contact our office directly."""
                        
                        appointment_data = None
        
        # Save bot response (with error handling)
        try:
            db.save_message(session_id, 'bot', bot_response)
        except Exception as e:
            print(f"⚠️ Warning: Failed to save bot response: {e}")
        
        return {
            "response": bot_response,
            "session_id": session_id,
            "appointment_data": appointment_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: int, limit: int = 20):
    """Get chat history for a session"""
    try:
        history = db.get_session_history(session_id, limit)
        return {
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@app.post("/api/email/test")
async def test_email(email: str):
    """Test email functionality"""
    try:
        success = email_service.send_test_email(email)
        if success:
            return {"message": f"Test email sent successfully to {email}"}
        else:
            return {"error": f"Failed to send test email to {email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")

@app.post("/api/email/password-reset")
async def send_password_reset_email(request: PasswordResetRequest):
    """Send password reset email"""
    try:
        success = email_service.send_password_reset_email(
            request.email, 
            request.user_name, 
            request.reset_token
        )
        if success:
            return {"message": f"Password reset email sent successfully to {request.email}"}
        else:
            return {"error": f"Failed to send password reset email to {request.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset email failed: {str(e)}")

@app.post("/api/appointments/create")
async def create_appointment(appointment: AppointmentCreate):
    """Manually create an appointment"""
    try:
        appointment_datetime = f"{appointment.date} {appointment.time}"
        notes = f"Reason: {appointment.reason}"
        
        appointment_id = db.create_appointment_from_chat(
            appointment.user_id,
            appointment_datetime,
            notes
        )
        
        if appointment_id:
            return {
                "success": True,
                "appointment_id": appointment_id,
                "message": "Appointment created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create appointment")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating appointment: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(" Starting Dental CRM Chatbot Service...")
    try:
        config.validate()
        print(" Configuration validated")
        print(" Database connection established")
        print(f" Service running on {config.SERVICE_HOST}:{config.SERVICE_PORT}")
    except Exception as e:
        print(f"{e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("Shutting down Dental CRM Chatbot Service...")
    db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        reload=True
    )

