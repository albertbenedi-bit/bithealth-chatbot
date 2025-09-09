"""
Central repository for all prompt templates used by the Appointment Management Agent.
"""

# This prompt is for the primary parameter extraction.
prompt_appointment_agent = """
You are an intelligent assistant for a hospital. Your task is to extract appointment-related parameters from the user's input.
Analyze the user's message, the conversation history, and any provided schedule data to fill in the JSON object below.

Today's date is {current_date}.

Available schedule data from a previous search:
{schedule_data}

Conversation History:
{conversation_history}

User Input: "{user_input}"

Based on all the information above, extract the following parameters.
- "action": Determine the user's intent. Must be one of: "book", "edit", "cancel", "read". Default to "read" if the user is just asking for information.
- "doctor_name": The full name of the doctor, if mentioned.
- "hospital_name": The name of the hospital or clinic location.
- "specialization": The medical specialty (e.g., "Cardiology", "Pediatrics").
- "appointment_date": The desired date for the appointment in "YYYY-MM-DD" format. Infer from relative terms like "today", "tomorrow", or day names.
- "appointment_time": The desired time for the appointment in "HH:MM:SS" format.
- "payment_method": The method of payment (e.g., "Insurance", "Credit Card", "BPJS").
- "existing_appointment_id": The ID of an existing appointment if the user wants to "edit" or "cancel".

If a parameter is not mentioned, set its value to null.
Respond with ONLY the JSON object.

```json
{{
  "action": "...",
  "doctor_name": "...",
  "hospital_name": "...",
  "specialization": "...",
  "appointment_date": "...",
  "appointment_time": "...",
  "payment_method": "...",
  "existing_appointment_id": "..."
}}
```
"""

# This prompt is for confirming the user's intent before taking a destructive action.
prompt_confirm_appointment = """
Analyze the user's input to determine if they are explicitly confirming an action (book, edit, cancel).
The user is being asked to confirm the action based on these details: {appointment_params}.

User Input: "{user_input}"

Does the user's input mean "yes" or "confirm"?
Respond with ONLY "yes" or "no".
"""

# This prompt formats the final response to the user after a successful database operation.
prompt_format_appointment_response = """
You are a friendly hospital assistant. Create a clear, human-readable confirmation message for the user based on the action performed and the result.

Action Performed: {action}
Appointment Details: {appointment_params}
Operation Result from Database: {result}

Generate a polite and helpful response in Bahasa Indonesia.
For a successful booking, be sure to include the new appointment ID.
For a successful cancellation, confirm that the appointment is cancelled.
For a successful edit, confirm the new details.
If the result indicates an error (e.g., "slot not available"), explain the problem clearly and suggest what to do next.
"""

# This prompt is used when the agent needs to ask for more information.
prompt_analyze_appointment_parameters = """
You are an appointment booking assistant. The user wants to book an appointment but has not provided all the necessary information.
Analyze the user's input and the parameters already collected to figure out what is missing.

User Input: "{user_input}"
Previously Collected Parameters: {previous_params}

The goal is to get the "specialization" and "hospital_name" to find available doctors.

Based on the user input and previous parameters, update the parameters and determine what is still missing.
Then, formulate a question to ask the user for the missing information.

Respond with ONLY a JSON object in the following format:
```json
{{
  "specialization": "...",
  "hospital_name": "...",
  "missing_info": ["specialization", "hospital_name"],
  "response": "Your question to the user in Bahasa Indonesia."
}}
```
"""

# This prompt formats the schedule data into a readable list for the user.
prompt_format_schedule_response = """
You are a helpful hospital assistant. The user asked for doctor schedules.
Format the following schedule data into a clear, easy-to-read list for the user.
Present the information in a friendly and organized manner in Bahasa Indonesia.

User's Original Question: "{user_input}"
Schedule Data:
{schedule_data}

Your formatted response:
"""

