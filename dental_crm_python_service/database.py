import mysql.connector
from mysql.connector import Error
from config import config
from datetime import datetime

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
        except Error as e:
            print(f"Database connection error: {e}")
            raise e
    
    def ensure_connection(self):
        """Ensure database connection is alive"""
        try:
            if not self.connection.is_connected():
                self.connect()
        except:
            self.connect()
    
    def create_chat_session(self, user_id):
        """Create a new chat session"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            query = """
                INSERT INTO chat_sessions (user_id, started_at, status)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (user_id, datetime.now(), 'active'))
            self.connection.commit()
            session_id = cursor.lastrowid
            print(f"✅ Chat session created successfully: {session_id}")
            return session_id
        except Error as e:
            print(f"❌ Error creating chat session: {e}")
            print(f"❌ Error type: {type(e)}")
            print(f"❌ User ID: {user_id}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def save_message(self, session_id, sender, message):
        """Save a chat message"""
        self.ensure_connection()
        cursor = self.connection.cursor()
        try:
            query = """
                INSERT INTO chat_messages (session_id, sender, message, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (session_id, sender, message, datetime.now()))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error saving message: {e}")
            return False
        finally:
            cursor.close()
    
    def get_session_history(self, session_id, limit=10):
        """Get chat history for a session"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
                SELECT sender, message, timestamp
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (session_id, limit))
            results = cursor.fetchall()
            return list(reversed(results))  # Return in chronological order
        except Error as e:
            print(f"Error fetching history: {e}")
            return []
        finally:
            cursor.close()
    
    def create_appointment_from_chat(self, user_id, appointment_date, notes):
        """Create an appointment from chatbot conversation"""
        self.ensure_connection()
        cursor = self.connection.cursor()
        try:
            query = """
                INSERT INTO appointments (user_id, appointment_date, notes, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, appointment_date, notes, 'scheduled', datetime.now()))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error creating appointment: {e}")
            return None
        finally:
            cursor.close()
    
    def get_user_info(self, user_id):
        """Get user information"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = "SELECT id, name, email, role FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
        finally:
            cursor.close()
    
    def find_appointment_by_date_time(self, user_id, appointment_date, appointment_time=None):
        """Find appointment by date and optionally time"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            if appointment_time:
                # Search with specific time
                query = """
                    SELECT id, user_id, appointment_date, notes, status 
                    FROM appointments 
                    WHERE user_id = %s 
                    AND DATE(appointment_date) = %s 
                    AND TIME(appointment_date) = %s
                    AND status != 'cancelled'
                    ORDER BY appointment_date DESC
                    LIMIT 1
                """
                cursor.execute(query, (user_id, appointment_date, appointment_time))
            else:
                # Search by date only
                query = """
                    SELECT id, user_id, appointment_date, notes, status 
                    FROM appointments 
                    WHERE user_id = %s 
                    AND DATE(appointment_date) = %s
                    AND status != 'cancelled'
                    ORDER BY appointment_date DESC
                    LIMIT 1
                """
                cursor.execute(query, (user_id, appointment_date))
            
            result = cursor.fetchone()
            if result:
                print(f"✅ Found appointment: ID={result['id']}, Date={result['appointment_date']}")
            else:
                print(f"❌ No appointment found for user {user_id} on {appointment_date}")
            return result
        except Error as e:
            print(f"❌ Error finding appointment: {e}")
            return None
        finally:
            cursor.close()
    
    def reschedule_appointment(self, appointment_id, new_appointment_date, notes=None):
        """Reschedule an existing appointment"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            if notes:
                query = """
                    UPDATE appointments 
                    SET appointment_date = %s, notes = %s, updated_at = %s
                    WHERE id = %s
                """
                cursor.execute(query, (new_appointment_date, notes, datetime.now(), appointment_id))
            else:
                query = """
                    UPDATE appointments 
                    SET appointment_date = %s, updated_at = %s
                    WHERE id = %s
                """
                cursor.execute(query, (new_appointment_date, datetime.now(), appointment_id))
            
            self.connection.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Appointment {appointment_id} rescheduled to {new_appointment_date}")
                return True
            else:
                print(f"❌ Failed to reschedule appointment {appointment_id}")
                return False
        except Error as e:
            print(f"❌ Error rescheduling appointment: {e}")
            return False
        finally:
            cursor.close()
    
    def get_user_appointments(self, user_id, limit=10):
        """Get all appointments for a user"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, appointment_date, notes, status, created_at 
                FROM appointments 
                WHERE user_id = %s 
                ORDER BY appointment_date DESC
                LIMIT %s
            """
            cursor.execute(query, (user_id, limit))
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Error fetching user appointments: {e}")
            return []
        finally:
            cursor.close()
    
    def validate_working_hours_and_days(self, appointment_date, appointment_time):
        """Validate if appointment is within working hours and days"""
        from datetime import datetime
        
        try:
            # Parse appointment date
            if isinstance(appointment_date, str):
                apt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            else:
                apt_date = appointment_date
            
            # Parse appointment time
            appointment_time_lower = appointment_time.lower().strip()
            time_obj = None
            
            if ':' in appointment_time:
                try:
                    time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                except:
                    try:
                        time_obj = datetime.strptime(appointment_time, '%I:%M %p').time()
                    except:
                        time_obj = datetime.strptime(appointment_time, '%I:%M%p').time()
            else:
                # Handle simple hour format (2pm, 11am, etc.)
                hour = int(''.join(filter(str.isdigit, appointment_time)))
                
                if 'pm' in appointment_time_lower:
                    if hour != 12:
                        hour += 12
                elif 'am' in appointment_time_lower:
                    if hour == 12:
                        hour = 0
                
                time_obj = datetime.strptime(f"{hour:02d}:00", '%H:%M').time()
            
            # Check working days (Monday = 0, Sunday = 6)
            weekday = apt_date.weekday()
            if weekday >= 5:  # Saturday = 5, Sunday = 6
                return False, f"We're closed on weekends. Please select Monday-Friday."
            
            # Check working hours (9 AM to 5 PM)
            start_time = datetime.strptime("09:00", '%H:%M').time()
            end_time = datetime.strptime("17:00", '%H:%M').time()
            
            if time_obj < start_time or time_obj >= end_time:
                return False, f"Our working hours are 9:00 AM to 5:00 PM. Please select a time within these hours."
            
            return True, "Valid"
            
        except Exception as e:
            print(f"❌ Error validating working hours/days: {e}")
            return False, f"Invalid date or time format."
    
    def check_time_slot_availability(self, appointment_date, appointment_time):
        """Check if a specific time slot is available"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Parse the appointment time to standard format
            from datetime import datetime
            time_obj = None
            
            # Handle different time formats
            appointment_time_lower = appointment_time.lower().strip()
            
            if ':' in appointment_time:
                try:
                    # Try 24-hour format first (14:30)
                    time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                except:
                    try:
                        # Try 12-hour format with space (2:30 PM)
                        time_obj = datetime.strptime(appointment_time, '%I:%M %p').time()
                    except:
                        try:
                            # Try 12-hour format without space (2:30PM)
                            time_obj = datetime.strptime(appointment_time, '%I:%M%p').time()
                        except:
                            # Fallback to simple parsing
                            hour = int(''.join(filter(str.isdigit, appointment_time)))
                            if 'pm' in appointment_time_lower and hour != 12:
                                hour += 12
                            elif 'am' in appointment_time_lower and hour == 12:
                                hour = 0
                            time_obj = datetime.strptime(f"{hour:02d}:00", '%H:%M').time()
            else:
                # Handle simple hour format (2pm, 11am, etc.)
                try:
                    # Extract hour number
                    hour = int(''.join(filter(str.isdigit, appointment_time)))
                    
                    # Handle AM/PM
                    if 'pm' in appointment_time_lower:
                        if hour != 12:  # 1pm = 13:00, 2pm = 14:00, etc.
                            hour += 12
                        # 12pm stays 12 (noon)
                    elif 'am' in appointment_time_lower:
                        if hour == 12:  # 12am = 00:00 (midnight)
                            hour = 0
                        # Other AM hours stay the same
                    
                    time_obj = datetime.strptime(f"{hour:02d}:00", '%H:%M').time()
                except Exception as e:
                    print(f"❌ Error parsing time '{appointment_time}': {e}")
                    # Default fallback
                    time_obj = datetime.strptime("09:00", '%H:%M').time()
            
            # Check for existing appointments at the same date and time
            query = """
                SELECT COUNT(*) as count 
                FROM appointments 
                WHERE DATE(appointment_date) = %s 
                AND TIME(appointment_date) = %s
                AND status != 'cancelled'
            """
            cursor.execute(query, (appointment_date, time_obj))
            result = cursor.fetchone()
            
            is_available = result['count'] == 0
            print(f"🔍 Time slot availability check: {appointment_date} {time_obj} - {'Available' if is_available else 'Booked'}")
            return is_available
            
        except Error as e:
            print(f"❌ Error checking time slot availability: {e}")
            return False
        except Exception as e:
            print(f"❌ Error parsing time format: {e}")
            return False
        finally:
            cursor.close()
    
    def get_available_time_slots(self, appointment_date, preferred_time=None):
        """Get available time slots for a specific date"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Get all appointments for the date
            query = """
                SELECT TIME(appointment_date) as time_slot 
                FROM appointments 
                WHERE DATE(appointment_date) = %s 
                AND status != 'cancelled'
                ORDER BY TIME(appointment_date)
            """
            cursor.execute(query, (appointment_date,))
            booked_slots = [row['time_slot'] for row in cursor.fetchall()]
            
            # Define clinic hours (9 AM to 5 PM)
            from datetime import time, timedelta
            clinic_hours = []
            current_time = time(9, 0)  # 9:00 AM
            end_time = time(17, 0)    # 5:00 PM
            
            # Generate hourly slots
            while current_time < end_time:
                clinic_hours.append(current_time)
                # Add 1 hour
                hour = current_time.hour + 1
                if hour >= 24:
                    break
                current_time = time(hour, 0)
            
            # Filter out booked slots
            available_slots = []
            for slot in clinic_hours:
                if slot not in booked_slots:
                    available_slots.append(slot)
            
            # If preferred time is provided, prioritize it
            if preferred_time:
                try:
                    # Parse preferred time using same logic as above
                    preferred_time_lower = preferred_time.lower().strip()
                    
                    if ':' in preferred_time:
                        try:
                            pref_time = datetime.strptime(preferred_time, '%H:%M').time()
                        except:
                            try:
                                pref_time = datetime.strptime(preferred_time, '%I:%M %p').time()
                            except:
                                pref_time = datetime.strptime(preferred_time, '%I:%M%p').time()
                    else:
                        # Handle simple hour format (2pm, 11am, etc.)
                        hour = int(''.join(filter(str.isdigit, preferred_time)))
                        
                        # Handle AM/PM
                        if 'pm' in preferred_time_lower:
                            if hour != 12:  # 1pm = 13:00, 2pm = 14:00, etc.
                                hour += 12
                            # 12pm stays 12 (noon)
                        elif 'am' in preferred_time_lower:
                            if hour == 12:  # 12am = 00:00 (midnight)
                                hour = 0
                            # Other AM hours stay the same
                        
                        pref_time = time(hour, 0)
                    
                    # If preferred time is available, put it first
                    if pref_time in available_slots:
                        available_slots.remove(pref_time)
                        available_slots.insert(0, pref_time)
                    
                except Exception as e:
                    print(f"❌ Error parsing preferred time: {e}")
            
            print(f"📅 Available slots for {appointment_date}: {len(available_slots)} slots")
            return available_slots
            
        except Error as e:
            print(f"❌ Error getting available time slots: {e}")
            return []
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")

# Singleton instance
db = Database()

