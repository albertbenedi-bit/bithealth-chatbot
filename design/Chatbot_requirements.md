# [cite\_start]Chatbot Requirements: Appointment Management, Information Dissemination & L1 Receptionist Functions [cite: 1]

## [cite\_start]Executive Summary [cite: 2]

[cite\_start]This document outlines the functional and non-functional requirements for a chatbot system designed to streamline patient interactions related to appointment management, pre-admission information, post-discharge instructions, and general information dissemination, acting as a Level 1 (L1) receptionist[cite: 3]. [cite\_start]The primary goal is to enhance the patient experience by providing accessible, timely, and personalized information and services through automated communication channels, offloading common queries from human staff, while strictly avoiding medical recommendations[cite: 4].

## [cite\_start]Stakeholders & Roles [cite: 5]

  * [cite\_start]**Patient/User**: Primary end-user interacting with the chatbot for scheduling, rescheduling, cancellations, and receiving information, as well as general inquiries[cite: 6].
  * [cite\_start]**Healthcare Administrator/Staff**: Responsible for configuring appointment slots, updating information, maintaining the general information knowledge base, and handling human handoffs[cite: 7].
  * [cite\_start]**IT/Development Team**: Responsible for implementation, maintenance, and integration[cite: 8].

## [cite\_start]Functional Requirements [cite: 9]

### [cite\_start]Feature: Appointment Scheduling & Reminders [cite: 10]

[cite\_start]**Description**: The chatbot will allow patients to schedule, reschedule, and cancel appointments, and receive automated reminders[cite: 11].

```json
{
  "story_id": "REQ-US-001",
  "story_title": "Patient Schedules a New Appointment",
  "persona": "As a patient",
  "action": "I want to schedule a new appointment via the chatbot",
  "benefit": "so that I can easily book my medical visits without direct human intervention.",
  "priority": "Critical",
  "acceptance_criteria": [
    "Given the patient has successfully verified their identity and provided consent,",
    "When the patient requests to book an appointment,",
    "Then the chatbot presents available clinics, specialties, and doctors.",
    "And the chatbot allows the patient to select preferred date and time slots.",
    "And the chatbot confirms the appointment details to the patient.",
    "And the appointment is successfully recorded in the backend system."
  ],
  "edge_cases": [
    "If no suitable slots are available, then the chatbot offers alternative dates/times or prompts for human agent assistance.",
    "If the patient provides invalid input, then the chatbot re-prompts for correct information."
  ],
  "dependencies": ["REQ-US-003", "REQ-US-007", "REQ-FR-001"]
}
```

[cite\_start][cite: 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

```json
{
  "story_id": "REQ-US-002",
  "story_title": "Patient Receives Appointment Reminders",
  "persona": "As a patient",
  "action": "I want to receive automated reminders for my upcoming appointments",
  "benefit": "so that I do not miss my scheduled visits.",
  "priority": "High",
  "acceptance_criteria": [
    "Given an upcoming appointment is scheduled,",
    "When the configured reminder interval is reached (e.g., 24 hours, 2 hours, 30 minutes prior),",
    "Then the chatbot sends a reminder notification via the patient's preferred communication channel (SMS, WhatsApp, hospital app).",
    "And the reminder includes appointment details (date, time, clinic, specialty, doctor)."
  ],
  "edge_cases": [
    "If the patient has opted out of reminders, then no reminders should be sent.",
    "If a reminder fails to send (e.g., invalid phone number), then the system logs the failure and alerts an administrator."
  ],
  "dependencies": ["REQ-FR-002"]
}
```

[cite\_start][cite: 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52]

```json
{
  "story_id": "REQ-US-003",
  "story_title": "Patient Verifies Identity for Secure Interactions",
  "persona": "As a patient",
  "action": "I want to verify my identity securely",
  "benefit": "so that my personal and medical information remains private and accurate during chatbot interactions.",
  "priority": "Critical",
  "acceptance_criteria": [
    "Given a patient initiates an action requiring identity verification (e.g., scheduling, rescheduling, accessing personalized info),",
    "When the chatbot prompts for identity details (e.g., patient ID, Date of Birth, registered phone number),",
    "Then the patient provides the requested information.",
    "And the system verifies the provided information against the patient's record.",
    "And upon successful verification, the patient gains access to personalized services.",
    "And upon failed verification, the chatbot prompts for re-entry or suggests human agent assistance."
  ],
  "edge_cases": [
    "If multiple failed attempts occur, then the chatbot locks the session and requires human assistance or a new verification method (e.g., OTP to registered phone)."
  ],
  "dependencies": []
}
```

[cite\_start][cite: 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73]

```json
{
  "story_id": "REQ-US-007",
  "story_title": "Patient Provides Consent for Data Sharing",
  "persona": "As a patient",
  "action": "I want to explicitly provide consent for my details to be used for appointment booking and related communications",
  "benefit": "so that I am aware and in control of my personal information.",
  "priority": "Critical",
  "acceptance_criteria": [
    "Given a patient is about to book or reschedule an appointment,",
    "When the chatbot requests personal details for the booking,",
    "Then the chatbot presents a clear consent request regarding the use and sharing of their information for this purpose.",
    "And the patient must explicitly confirm their consent (e.g., by typing 'Yes' or clicking a 'Confirm' button).",
    "And if consent is not given, the chatbot informs the patient that the booking cannot proceed and offers human agent assistance."
  ],
  "edge_cases": [
    "If consent is implicitly assumed or not explicitly captured, then the system should halt the process and flag for human review.",
    "What happens if consent is revoked later? (Needs clarification on future phases)."
  ],
  "dependencies": []
}
```

[cite\_start][cite: 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94]

[cite\_start]**Feature Specifications for Appointment Scheduling & Reminders**: [cite: 96]

  * [cite\_start]**Appointment Booking Parameters**: [cite: 97]
      * [cite\_start]**Clinic**: User selects from a predefined list of clinics[cite: 98].
      * [cite\_start]**Specialty**: User selects from a predefined list of medical specialties[cite: 99].
      * [cite\_start]**Doctor**: User selects from available doctors within the chosen specialty/clinic[cite: 100].
      * [cite\_start]**Date/Time Preferences**: User specifies preferred dates, and the chatbot displays available time slots (e.g., 15-minute intervals)[cite: 101].
      * [cite\_start]**Scheduling/Rescheduling Window**: Appointments can be scheduled or rescheduled up to 90 days in advance and no less than 4 hours before the original appointment time[cite: 102].
  * [cite\_start]**Cancellation Policies Enforcement**: [cite: 103]
      * [cite\_start]Cancellations allowed up to 2 hours before the appointment[cite: 104].
      * [cite\_start]If a patient attempts to cancel within 2 hours, the chatbot will inform them of the policy and suggest contacting a human agent[cite: 105].
      * [cite\_start]For no-shows or late cancellations, the chatbot will record the incident in the patient's record, and the system may apply predefined penalties (e.g., limit future self-service bookings after X instances)[cite: 106].
  * [cite\_start]**Communication Channels for Reminders**: [cite: 107]
      * [cite\_start]Prioritized channels for initial deployment: SMS, WhatsApp, and hospital application in-app notifications[cite: 108].
  * [cite\_start]**Reminder Intervals**: [cite: 109]
      * [cite\_start]First reminder: 24 hours before the appointment[cite: 110].
      * [cite\_start]Second reminder: 2 hours before the appointment[cite: 111].
      * [cite\_start]Optional third reminder: 30 minutes before the appointment (configurable per patient preference)[cite: 112].

### [cite\_start]Feature: Pre-admission Information Dissemination [cite: 113]

[cite\_start]**Description**: The chatbot provides patients with necessary pre-admission instructions and information before their scheduled procedures[cite: 114].

```json
{
  "story_id": "REQ-US-004",
  "story_title": "Patient Receives Pre-admission Information",
  "persona": "As a patient with a scheduled procedure",
  "action": "I want to receive relevant pre-admission information through the chatbot",
  "benefit": "so that I am well-prepared for my hospital visit.",
  "priority": "High",
  "acceptance_criteria": [
    "Given a patient has a scheduled procedure requiring pre-admission information,",
    "When the pre-admission information is due for delivery (e.g., 7 days prior to procedure),",
    "Then the chatbot sends the relevant information to the patient via their preferred communication channel.",
    "And the information is personalized based on their specific procedure and doctor's instructions.",
    "And the patient can access a comprehensive guide or FAQs via a link provided by the chatbot."
  ],
  "edge_cases": [
    "If the patient's contact information is outdated, then the system logs the delivery failure and flags for manual follow-up."
  ],
  "dependencies": ["REQ-FR-003"]
}
```

[cite\_start][cite: 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133]

[cite\_start]**Feature Specifications for Pre-admission Information**: [cite: 135]

  * [cite\_start]**Source of Information**: Pre-admission information will be sourced from a structured database maintained by hospital staff[cite: 136]. [cite\_start]For highly specific or dynamic instructions, integration with a content management system (CMS) or direct input forms will be considered[cite: 137].
  * [cite\_start]**Information Granularity**: Information should be personalized based on the specific procedure, doctor's requirements, and patient's medical history (if accessible and relevant)[cite: 138]. [cite\_start]It includes general instructions (e.g., fasting, what to bring) and specific details (e.g., medication adjustments)[cite: 139].
  * [cite\_start]**Process for Updating Information**: Hospital staff will update information via a secure web portal[cite: 140]. [cite\_start]Changes are reflected immediately upon approval[cite: 141].
  * [cite\_start]**Frequency of Change**: Expected to change quarterly for general guidelines, and on-demand for specific procedural updates (e.g., new protocols, doctor preferences)[cite: 142].

### [cite\_start]Feature: Post-Discharge Instructions Dissemination [cite: 143]

[cite\_start]**Description**: The chatbot provides personalized post-discharge instructions, medication reminders, and follow-up care plans to patients after their hospital stay[cite: 144].

```json
{
  "story_id": "REQ-US-005",
  "story_title": "Patient Receives Post-Discharge Instructions and Reminders",
  "persona": "As a recently discharged patient",
  "action": "I want to receive clear post-discharge instructions and medication reminders",
  "benefit": "so that I can effectively manage my recovery and adhere to my care plan.",
  "priority": "High",
  "acceptance_criteria": [
    "Given a patient has been discharged from the hospital,",
    "When the discharge instructions are finalized by clinical staff,",
    "Then the chatbot delivers personalized instructions and medication reminders to the patient's preferred channel.",
    "And the medication reminders integrate with an existing e-prescribing system to ensure accuracy.",
    "And the chatbot provides options for follow-up care plan details (e.g., next appointment booking)."
  ],
  "edge_cases": [
    "If a patient reports an adverse reaction via a chatbot prompt, then the chatbot escalates to a human agent immediately.",
    "If medication adherence cannot be tracked due to patient non-response, then the system flags for manual follow-up."
  ],
  "dependencies": ["REQ-FR-004"]
}
```

[cite\_start][cite: 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164]

[cite\_start]**Feature Specifications for Post-Discharge Instructions**: [cite: 166]

  * [cite\_start]**Generation Process & Integration**: Personalized discharge instructions and medication reminders will be generated by integrating with the hospital's Electronic Health Record (EHR) system (specifically e-prescribing modules and doctor notes)[cite: 167].
  * [cite\_start]**Patient Adherence Tracking**: The chatbot will track adherence through interactive prompts (e.g., "Have you taken your medication? Yes/No") and by logging patient responses[cite: 168]. [cite\_start]Non-response or negative responses will trigger alerts for human review[cite: 169].
  * [cite\_start]**Follow-up Care Plans**: Chatbot will deliver: [cite: 170]
      * [cite\_start]Next appointment booking prompts (with direct scheduling link)[cite: 171].
      * [cite\_start]Wound care instructions (text, images, or links to videos)[cite: 172].
      * [cite\_start]Dietary advice tailored to post-procedure needs[cite: 173].
      * [cite\_start]Symptoms to monitor and when to seek emergency care[cite: 174].
  * [cite\_start]**Frequency and Duration of Post-Discharge Communication**: [cite: 175]
      * [cite\_start]Medication reminders: Daily, based on prescribed schedule, for the duration of the prescription (up to 30 days)[cite: 176].
      * [cite\_start]Follow-up instructions: Daily for the first 3 days, then every 3 days for 2 weeks, then weekly for 1 month, or until the next scheduled follow-up appointment[cite: 177].

### [cite\_start]Feature: General Information & L1 Receptionist [cite: 178]

[cite\_start]**Description**: The chatbot will provide general information about the hospital and its services, acting as a first line of contact for common inquiries, and will **not** provide medical advice[cite: 179].

```json
{
  "story_id": "REQ-US-006",
  "story_title": "Patient Accesses General Hospital Information",
  "persona": "As a patient or visitor",
  "action": "I want to quickly find general information about the hospital",
  "benefit": "so that I can get answers to common questions without waiting to speak to a human.",
  "priority": "High",
  "acceptance_criteria": [
    "Given a user asks a general question (e.g., \"What are visiting hours?\", \"Where is the Cardiology department?\"),",
    "When the chatbot identifies the intent as a general information query,",
    "Then the chatbot provides an accurate and concise answer from its knowledge base.",
    "And for complex or multi-part questions, the chatbot offers to direct the user to specific resources or a human agent."
  ],
  "edge_cases": [
    "If the chatbot does not understand the query, then it will politely ask for clarification or offer human assistance.",
    "If the information requested is not in the knowledge base, then the chatbot indicates it cannot answer and provides options for escalation."
  ],
  "dependencies": ["REQ-FR-005"]
}
```

[cite\_start][cite: 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199]

[cite\_start]**Feature Specifications for General Information & L1 Receptionist**: [cite: 201]

  * [cite\_start]**General Information Scope**: The chatbot will be able to answer frequently asked questions (FAQs) about: [cite: 202]
      * [cite\_start]Hospital operating hours[cite: 203].
      * [cite\_start]Department locations and contact numbers[cite: 204].
      * [cite\_start]Available medical services and specialties[cite: 205].
      * [cite\_start]Visiting hours and policies[cite: 206].
      * [cite\_start]Parking information[cite: 207].
      * [cite\_start]General patient guidelines[cite: 208].
      * [cite\_start]Basic administrative processes (e.g., how to request medical records)[cite: 209].
  * [cite\_start]**Medical Advice Restriction**: The chatbot **must never** provide direct medical diagnoses, treatment recommendations, or advice[cite: 210]. [cite\_start]If a user's query suggests they are seeking medical advice (e.g., describing symptoms), the chatbot must explicitly state it cannot provide medical solutions and immediately offer to: [cite: 211]
      * [cite\_start]Recommend a doctor or specialty department based on the general area of concern (e.g., "For persistent cough, you might consider seeing a pulmonologist. Would you like to see available pulmonologists?")[cite: 212].
      * [cite\_start]Forward the session to a human agent for further support or to schedule an urgent consultation[cite: 213].
  * [cite\_start]**Information Source**: General information will be managed via a dedicated knowledge base system (e.g., a CMS or a specialized chatbot knowledge base platform)[cite: 214].
  * [cite\_start]**Content Updates**: Hospital staff will manage and update the knowledge base through an administrative interface[cite: 215]. [cite\_start]Updates should be reflected in the chatbot within 30 minutes of approval[cite: 216].
  * [cite\_start]**Query Understanding**: The chatbot should use Natural Language Understanding (NLU) to interpret user queries and map them to appropriate answers or intents[cite: 217].
  * [cite\_start]**Direction and Routing**: For queries related to specific departments or services, the chatbot will provide relevant contact information (phone number, email) or direct links to hospital website pages[cite: 218].
  * [cite\_start]**L1 Handoff Criteria**: [cite: 219]
      * [cite\_start]When the user's query is outside the chatbot's defined scope[cite: 220].
      * [cite\_start]When the user explicitly requests to speak to a human[cite: 221].
      * [cite\_start]After a predefined number of failed attempts by the chatbot to answer a query[cite: 222].
      * [cite\_start]For sensitive, emergency inquiries, or queries requiring medical interpretation[cite: 223].

## [cite\_start]Non-Functional Requirements (NFRs) [cite: 224]

### [cite\_start]Security Requirements [cite: 225]

  * [cite\_start]**Identity Verification Method**: A combination of patient ID, Date of Birth (DOB), and One-Time Password (OTP) sent to the registered phone number will be used for patient identity verification across all modules[cite: 226].
  * [cite\_start]**Data Encryption**: All patient identifiable information (PII) and Protected Health Information (PHI) must be encrypted at rest (AES-256) and in transit (TLS 1.2 or higher)[cite: 227].
  * [cite\_start]**Access Control**: Role-based access control must be implemented for administrative interfaces, ensuring only authorized personnel can update information or access patient logs[cite: 228].
  * [cite\_start]**Audit Logging**: All sensitive actions (e.g., appointment changes, identity verification attempts, data access, consent records) must be logged for auditing and compliance purposes[cite: 229].

### [cite\_start]Performance Requirements [cite: 230]

  * [cite\_start]**Response Time**: 95% of chatbot responses must be delivered within 2 seconds under typical load (estimated 500 concurrent users)[cite: 231].
  * [cite\_start]**Throughput**: The system must support at least 100 appointment-related transactions per minute and 500 general information queries per minute[cite: 232].
  * [cite\_start]**Scalability**: The infrastructure must be capable of scaling to handle seasonal peaks in patient inquiries (e.g., flu season, public health campaigns) with minimal degradation in performance[cite: 233].

### [cite\_start]Usability Requirements [cite: 234]

  * [cite\_start]**Preferred Communication Channels**: Initial deployment will prioritize SMS, WhatsApp, and the existing hospital mobile application widget[cite: 235].
  * [cite\_start]**Human Handoff Integration**: Seamless integration with the hospital's existing CRM (e.g., Salesforce Service Cloud) or live chat platform (e.g., LiveChat) for complex queries or when the chatbot cannot resolve an issue[cite: 236]. [cite\_start]The chatbot must be able to transfer the conversation history to the human agent[cite: 237].
  * [cite\_start]**Error Messages**: Clear, concise, and actionable error messages must be provided to the user[cite: 238].
  * [cite\_start]**Conversational Flow**: The chatbot should maintain a natural and intuitive conversational flow, minimizing user frustration[cite: 239].

### [cite\_start]Operability/Monitoring Requirements [cite: 240]

  * [cite\_start]**Analytics & Reporting**: Key metrics critical for monitoring chatbot performance and patient engagement include: [cite: 241]
      * [cite\_start]Successful appointments booked (daily, weekly, monthly)[cite: 242].
      * [cite\_start]Handoff rates to human agents (per module, per query type)[cite: 243].
      * [cite\_start]Chatbot conversation completion rates[cite: 244].
      * [cite\_start]Patient satisfaction scores (collected via post-interaction surveys)[cite: 245].
      * [cite\_start]Reminder delivery success/failure rates[cite: 246].
      * [cite\_start]Adherence tracking rates for post-discharge instructions[cite: 247].
      * [cite\_start]Top general information queries[cite: 248].
      * [cite\_start]Knowledge base hit rate (percentage of queries answered by the chatbot without handoff)[cite: 249].
      * [cite\_start]Unanswered query rates (queries where chatbot couldn't provide an answer)[cite: 250].
  * [cite\_start]**System Monitoring**: Automated alerts for system outages, performance degradation, and critical error logs[cite: 251].

### [cite\_start]Accessibility Requirements [cite: 252]

  * [cite\_start]**Accessibility Standards Compliance**: The chatbot interface (especially if a web widget or in-app interface is developed) must comply with WCAG 2.1 Level AA conformance[cite: 253]. [cite\_start]This includes considerations for screen readers, keyboard navigation, and color contrast[cite: 254].

### [cite\_start]Internationalization (I18n) [cite: 255]

  * [cite\_start]**Language Support**: The chatbot must support Bahasa Indonesia (primary) and English languages[cite: 256]. [cite\_start]All responses and prompts must be available in both languages, with the primary language defaulting to Bahasa Indonesia based on system or user preference[cite: 257].

### [cite\_start]Continuous Improvement & Query Enhancement [cite: 258]

  * [cite\_start]**Feedback Loop for Unanswered Queries**: A process must be established to review unanswered queries and chatbot handoffs to human agents[cite: 259]. [cite\_start]This review should inform updates to the knowledge base and NLU model[cite: 260].
  * [cite\_start]**User Feedback Mechanism**: Implement a simple feedback mechanism within the chatbot (e.g., "Was this helpful? Yes/No" or a rating system) to collect direct user satisfaction data on responses[cite: 261].
  * [cite\_start]**A/B Testing Capability**: The platform should support A/B testing of different conversational flows, response phrasing, or NLU model versions to identify improvements[cite: 262].
  * [cite\_start]**NLU Model Retraining**: Establish a regular schedule (e.g., monthly) for retraining the NLU model with new query patterns, updated general information, and corrected misinterpretations identified from logs[cite: 263].
  * [cite\_start]**Response Quality Review**: Regular manual review of chatbot responses for accuracy, clarity, tone, and adherence to medical advice restrictions[cite: 264].
  * [cite\_start]**Query Suggestion/Refinement**: The chatbot should have mechanisms to help users formulate better queries (e.g., "Did you mean X or Y?", "Please provide more details about Z")[cite: 265].

## [cite\_start]Assumptions & Constraints [cite: 266]

  * [cite\_start]**Existing Backend Systems**: Assumption that existing EHR, e-prescribing, and CRM systems have APIs or integration points available for the chatbot to interact with[cite: 267].
  * [cite\_start]**Data Accuracy**: Assumption that patient data (contact info, medical history) and general hospital information in backend systems/knowledge bases are accurate and up-to-date[cite: 268].
  * [cite\_start]**Patient Engagement**: Assumes a reasonable level of patient engagement with automated communication channels[cite: 269].
  * [cite\_start]**No Offline Capability**: The chatbot will not support offline functionality; an internet connection is required for all interactions[cite: 270].
  * [cite\_start]**Budget & Timeline**: Implementation must align with a moderate budget and a 6-month initial rollout timeline[cite: 271].

## [cite\_start]Open Questions / Pending Decisions [cite: 272]

  * [cite\_start]**Consent Management Audit**: What is the detailed audit trail requirement for patient consent? [cite: 273] [cite\_start]How long must consent records be retained? [cite: 274]
  * [cite\_start]**AI Model Training Data Governance**: What are the policies for data privacy and security related to training data used for the chatbot's AI/NLU models? [cite: 275]
  * [cite\_start]**Emergency Protocol**: What is the specific protocol for the chatbot to handle and escalate emergency medical queries (e.g., a patient stating they are experiencing severe symptoms)? [cite: 276]
  * [cite\_start]**Integration with Hospital Website/App**: How tightly will the chatbot be integrated visually and functionally into the existing hospital website and mobile application? [cite: 277]

## [cite\_start]Process Flowchart: Appointment Scheduling via Chatbot [cite: 278]

```mermaid
graph TD
    A[Start Chatbot Session] --> B{Patient Initiates Booking (e.g., "Schedule an Appt")};
    B --> C{Chatbot: "Please verify your identity." (REQ-US-003)};
    C --> D[Patient Enters Patient ID, DOB, Phone No., OTP];
    D --> E{Is Identity Valid?};
    E -- No --> F[Chatbot: "Verification failed. Please try again or contact support."];
    F --> G[End Chatbot Session (or Handoff to Human)];
    E -- Yes --> H{Chatbot: "Please consent to use your details for booking." (REQ-US-007)};
    H -- No --> I[Chatbot: "Booking requires consent. Contact support."];
    I --> G;
    H -- Yes --> J{Chatbot: "What specialty / clinic?" (REQ-US-001)};
    J --> K[Patient Selects Options (Clinic, Specialty, Doctor)];
    K --> L{Chatbot: "Preferred date/ time?" (REQ-US-001)};
    L --> M[Patient Selects Date/Time];
    M --> N{Chatbot: "Confirm appt details?" (REQ-US-001)};
    N --> O[Patient Confirms];
    O --> P{Chatbot: "Appointment booked!" (REQ-US-001)};
    P --> Q[End Chatbot Session];
```

