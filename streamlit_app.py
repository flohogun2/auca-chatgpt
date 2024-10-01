# coding: latin-1
import locale
#locale.setlocale(locale.LC_ALL, 'fr_FR')


#from langchain_openai.llms import OpenAI
from langchain_openai import ChatOpenAI

from langchain.agents import initialize_agent,create_react_agent, Tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.agents import  create_openai_tools_agent
from langchain.chains.conversation.memory import ConversationBufferMemory

from langchain_core.prompts import PromptTemplate, prompt

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain.chains.llm import LLMChain

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.chains import create_history_aware_retriever

# from langchain.chains.llm import PALChain
#from langchain_experimental.pal_chain import PALChain

from faker import Faker
fake = Faker()

import streamlit as st

from dateutil import parser
import datetime
import pytz
import random
import json
import calendar

import requests
from datetime import date, datetime, timedelta
from time import time

import os

schedule = {}
today = datetime.now()
hours = (9, 17)   # open hours
print(os.environ)

API_KEY = os.environ("API_KEY","")
st.write("DB username:", st.secrets["API_KEY"])
# get today's date
def todayDate():
    return today.strftime('%m/%d/%y')

# get day of week for a date (or 'today')
def dayOfWeek(date):
    if date == 'today':
        return calendar.day_name[today.weekday()]
    else:
        try:
            theDate = parser.parse(date)
        except:
            return 'invalid date format, please use format: mm/dd/yy'
        
        return calendar.day_name[theDate.weekday()]
    
#########


# create random schedule
def createSchedule(daysAhead=5, perDay=8):
    schedule = {}
    for d in range(0, daysAhead):
        date = (today + datetime.timedelta(days=d)).strftime('%m/%d/%y')
        schedule[date] = {}

        for h in range(0, perDay -d):
            hour = random.randint(hours[0], hours[1])
            if hour not in schedule[date]:
                schedule[date][hour] = "toto"
                
    return schedule
 
def getAvailTimes(date, num=10):
    if '/' not in date:
        return 'Le paramètre date doit être au format : mm/jj/aa'
    
    if date not in schedule:
         return 'Cette journée est entièrement ouverte, tous les horaires sont disponibles'

      
    hoursAvail = 'Les horaires disponibles pour %s sont ' % date
      
    for h in range(hours[0], hours[1]):
        if str(h) not in schedule[date]:
             hoursAvail += str(h) +':00, '
             num -= 1
             if num == 0:
                 break
    
    if num > 0:
         hoursAvail = hoursAvail[:-2] +' - tous les autres horaires sont réservés'
    else:
         hoursAvail = hoursAvail[:-2]
        
    return hoursAvail

def scheduleTime(dateTime):
    date, time = dateTime.split(',')
    
    if not date or not time:
        return "sorry parameters must be date and time comma separated, for example: `12/31/23, 10:00` would be the input if for Dec 31'st 2023 at 10am"
    if date not in schedule:
        return 'no schedule available yet for this date'

    # get hours
    if ':' in time:
        timeHour = int(time[:time.index(':')])
        print(timeHour)
        
        if timeHour not in schedule[date]:
            if timeHour >= hours[0] and timeHour <= hours[1]:
                schedule[date][timeHour] = fake.name()
               
                return 'thank you, appointment scheduled for %s under name %s' % (time, schedule[date][timeHour])
            else:
                return '%s is after hours, please select a time during business hours' % time
        else:
            return 'sorry that time (%s) on %s is not available' % (time, date)
    else:
        return '%s is not a valid time, time must be in format hh:mm'



llm = ChatOpenAI(temperature=0, verbose=True, openai_api_key=API_KEY)
#pal_chain = PALChain.from_math_prompt(llm, verbose=True,allow_dangerous_code = True )


# llm = OpenAI(model_name="gpt-3.5-turbo-instruct", openai_api_key=API_KEY)

memory = ConversationBufferMemory(memory_key="chat_history")

#print(schedule)
# json_object = json.loads(schedule)
#json_formatted_str = json.dumps(schedule, indent=2)
#print(json_formatted_str)

ChatOpenAI.api_key = API_KEY
client = ChatOpenAI(openai_api_key=API_KEY)
GPT_MODEL = "gpt-3.5-turbo-instruct"

limit1 = datetime.strptime("10:00:00", "%H:%M:%S").time()
limit2 = datetime.strptime("17:00:00", "%H:%M:%S").time()
limit3 = datetime.strptime("12:00:00", "%H:%M:%S").time()
day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def appointment_booking(arguments):
    try:
        print("appointment_booking" +arguments)
        arguments_array = arguments.split(',')   
        email_address="nemail@gmail.com"
        try:
            email_address=arguments_array[2]
        except IndexError:
            print('no provided_email')   

        provided_date=arguments_array[0]
        provided_time=arguments_array[1]
        
    
        time_string = provided_time.replace("PM","").replace("AM","").strip();
        time_datetime = datetime.strptime(time_string, "%H:%M");
        provided_time = str(time_datetime.time())
        start_date_time = provided_date + " " + provided_time
        timezone = pytz.timezone('Asia/Kolkata')
        start_date_time = timezone.localize(datetime.strptime(start_date_time, "%d/%m/%Y %H:%M:%S"))     

        end_date_time = start_date_time + timedelta(hours=2)
        
        if provided_date and provided_time and email_address:
            slot_checking = appointment_checking(arguments)
            if slot_checking == "Un créneau est disponible pour un rendez-vous. Souhaitez-vous continuer ?":           
                if start_date_time < datetime.now(timezone):
                    return "Veuillez saisir une date et une heure valides."
                else:
                    if day_list[start_date_time.date().weekday()] == "Saturday":
                        if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                            event = {
                                'summary': "Appointment booking Chatbot using OpenAI's function calling feature",
                                'location': "Ahmedabad",
                                'description': "This appointment has been scheduled as the demo of the appointment booking chatbot using OpenAI function calling feature by Pragnakalp Techlabs.",
                                
                                'start': {
                                    'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'end': {
                                    'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'attendees': [
                                {'email': email_address},
                                
                                ],
                                'reminders': {
                                    'useDefault': False,
                                    'overrides': [
                                        {'method': 'email', 'minutes': 24 * 60},
                                        {'method': 'popup', 'minutes': 10},
                                    ],
                                },
                            }
                           # service.events().insert(calendarId='primary', body=event).execute()
                            return "Rendez-vous ajouté avec succès."
                        else:
                            return "Veuillez essayer de prendre rendez-vous pendant les heures d'ouverture, soit de 10h à 14h le samedi."
                    else:
                        if start_date_time.time() >= limit1 and start_date_time.time() <= limit2:
                            event = {
                                'summary': "Appointment booking Chatbot using OpenAI's function calling feature",
                                'location': "Ahmedabad",
                                'description': "This appointment has been scheduled as the demo of the appointment booking chatbot using OpenAI function calling feature by Pragnakalp Techlabs.",
                                
                                'start': {
                                    'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'end': {
                                    'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Asia/Kolkata',
                                },
                                'attendees': [
                                {'email': email_address},
                                
                                ],
                                'reminders': {
                                    'useDefault': False,
                                    'overrides': [
                                        {'method': 'email', 'minutes': 24 * 60},
                                        {'method': 'popup', 'minutes': 10},
                                    ],
                                },
                            }
                          #  service.events().insert(calendarId='primary', body=event).execute()
                            return "Rendez-vous ajouté avec succès."
                        else:
                            return "Veuillez essayer de prendre rendez-vous pendant les heures d'ouverture, soit de 10h00 à 19h00."
            else:
                return slot_checking
        else:
            return "désolé les paramètres doivent être date, heure et adresse email séparés par une virgule, par exemple: `12/31/23, 10:00, adresse@gmail.com` serait une entrée pour 31 décembre 2023 à 10 heures."
    except:
        return "Nous sommes confrontés à une erreur lors du traitement de votre demande. Veuillez réessayer."



def appointment_reschedule(arguments):
     return "Please try to check an appointment within working hours, which is 10 AM to 7 PM."

def appointment_delete(arguments):
     return "Please try to check an appointment within working hours, which is 10 AM to 7 PM."


def appointment_checking(arguments):
    try:
        print("appointment_checking" +arguments)
        arguments_array = arguments.split(',')   
        try:
            provided_email=arguments_array[2]
        except IndexError:
            print('no provided_email')   

        provided_date=arguments_array[0]
        provided_time=arguments_array[1]

        time_string = provided_time.replace("PM","").replace("AM","").strip();
        time_datetime = datetime.strptime(time_string, "%H:%M");
        provided_time = str(time_datetime.time())
        start_date_time = provided_date + " " + provided_time
        timezone = pytz.timezone('Asia/Kolkata')
        start_date_time = timezone.localize(datetime.strptime(start_date_time, "%d/%m/%Y %H:%M:%S"))      

        if start_date_time < datetime.now(timezone):
            return "Veuillez saisir une date et une heure valides."
        else:
            weekday = start_date_time.date().weekday();
            if day_list[weekday] == "Saturday":
                if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                    end_date_time = start_date_time + timedelta(hours=2)
                  #  events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                   # if events_result['items']:
                    #    return "Sorry slot is not available."
                    #else:
                    return "Un créneau est disponible pour un rendez-vous. Souhaitez-vous continuer ?"
                else:
                    return "Veuillez essayer de prendre rendez-vous pendant les heures d'ouverture, soit de 10h00 à 14h00 le samedi."
            else:
                if start_date_time.time() >= limit1 and start_date_time.time() <= limit2:
                    end_date_time = start_date_time + timedelta(hours=2)
                 #   events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                 #   if events_result['items']:
                  #      return "Sorry slot is not available."
                   # else:
                    return "Un créneau est disponible pour un rendez-vous. Souhaitez-vous continuer ?"
                else:
                    return "Veuillez essayer de prendre rendez-vous pendant les heures d'ouverture, soit de 10h00 à 19h00."
    except:
        return "Nous sommes confrontés à une erreur lors du traitement de votre demande. Veuillez réessayer."

  
appointment_booking("28/09/2024, 12:00, ERIC@GMAIL.COM")

tools = [     
     Tool(
      name = 'reservation_rendez-vous',
      func = lambda string: appointment_booking(string),
      description="Utilisez pour planifier un rendez-vous pour une date et une heure données. L'entrée de cet outil doit être une liste de 3 chaînes séparées par des virgules : date et heure au format : jj/mm//aaaa, hh:mm, puis l'adresse email de l'utilisateur utilisée pour l'identification. convertissez la date et l heure dans ces formats. Par exemple, '31/12/2023, 10:00' serait l entrée pour le 31 décembre 2023 à 10h00",
            verbose=True
      ),
      Tool(
      name = 'verification_disponibilites_calendaires_rendez-vous',
      func = lambda string: appointment_checking(string),
      description="cette fonction doit être appelée lorsque l'utilisateur souhaite vérifier si un créneau calendaire pour un rendez-vous est disponible ou non. L'entrée de cet outil doit être une liste de 3 chaînes séparées par des virgules : date et heure au format : jj/mm//aaaa, hh:mm, puis l'adresse email de l'utilisateur utilisée pour l'identification. convertissez la date et l heure dans ces formats. Par exemple, '31/12/2023, 10:00' serait l entrée pour le 31 décembre 2023 à 10h00",
            verbose=True
  ) 
 
 ]



functions = [
{
    "name": "appointment_booking",
    "description": "When user want to book appointment, then this function should be called.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "format": "date",
                "example":"2023-07-23",
                "description": "Date, when the user wants to book an appointment. The date must be in the format of YYYY-MM-DD.",
            },
            "time": {
                "type": "string",
                "example": "20:12:45",
                "description": "time, on which user wants to book an appointment on a specified date. Time must be in %H:%M:%S format.",
            },
            "email_address": {
                "type": "string",
                "description": "email_address of the user gives for identification.",
            }
        },
        "required": ["date","time","email_address"],
    },
},
{
    "name": "appointment_reschedule",
    "description": "When user want to reschedule appointment, then this function should be called.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "format": "date",
                "example":"2023-07-23",
                "description": "It is the date on which the user wants to reschedule the appointment. The date must be in the format of YYYY-MM-DD.",
            },
            "time": {
                "type": "string",
                "description": "It is the time on which user wants to reschedule the appointment. Time must be in %H:%M:%S format.",
            },
            "email_address": {
                "type": "string",
                "description": "email_address of the user gives for identification.",
            }
        },
        "required": ["date","time","email_address"],
    },
},
{
    "name": "appointment_delete",
    "description": "When user want to delete appointment, then this function should be called.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "format": "date",
                "example":"2023-07-23",
                "description": "Date, on which user has appointment and wants to delete it. The date must be in the format of YYYY-MM-DD.",
            },
            "time": {
                "type": "string",
                "description": "time, on which user has an appointment and wants to delete it. Time must be in %H:%M:%S format.",
            },
            "email_address": {
                "type": "string",
                "description": "email_address of the user gives for identification.",
            }
        },
        "required": ["date","time","email_address"],
    },
},
{
    "name": "Disponibilités calendaires pour un rendez-vous",
    "description": "cette fonction doit être appelée lorsque l'utilisateur souhaite vérifier si un créneau calendaire pour un rendez-vous est disponible ou non.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "format": "date",
                "example":"2023-07-23",
                "description": "Date, when the user wants to book an appointment. The date must be in the format of YYYY-MM-DD.",
            },
            "time": {
                "type": "string",
                "example": "20:12:45",
                "description": "time, on which user wants to book an appointment on a specified date. Time must be in %H:%M:%S format.",
            }
        },
        "required": ["date","time"],
    },
}]




formatted_system_message = f"""
Vous êtes une experte en prise de rendez-vous appelée Nathalie qui travaille pour la société AUCA. Les rendez-vous concernent des séances d'essais dans la salle de sport de la société AUCA. Vous devez demander à l'utilisateur la date du rendez-vous, l'heure du rendez-vous et l'identifiant de messagerie. L'utilisateur peut prendre rendez-vous de 10h à 19h du lundi au vendredi, et de 10h à 14h le samedi. Vous devez vous rappeler que la date d'aujourd'hui est {date.today()} et le jour est {day_list[date.today().weekday()]}. Vérifiez si l'heure fournie par l'utilisateur se situe dans les horaires d'ouverture, alors seulement vous pourrez procéder.

Instructions:
- Ne faites pas de suppositions sur les valeurs à intégrer en tant que paramètres des fonctions. Si l'utilisateur ne fournit aucun des paramètres requis, vous devez alors demander des éclaircissements.
- Assurez-vous que l'adresse email qui corespond à l'identifiant de l'utilisateur est valide et non vide.
- Si une demande d'utilisateur est ambiguë, vous devez également demander des éclaircissements.
- Lorsqu'un utilisateur demande une date ou une heure de reprogrammation du rendez-vous en cours, vous devez alors demander uniquement les détails du nouveau rendez-vous.
- Si l'utilisateur n'a pas fourni le jour, le mois et l'année en indiquant l'heure du rendez-vous souhaité, vous devrez alors demander des éclaircissements.

Assurez-vous de suivre attentivement les instructions lors du traitement de la demande.

Si un utilisateur vous pose une question générale, répondez-y puis fournissez une description générique de vos capacités.
Si un utilisateur demande votre fonction, fournissez une description générique de vos capacités basée sur toutes ces informations sous la propriété « résumé ».
        """

# this is a customization of what is pulled down by hub.pull("hwchase17/openai-tools-agent")
prompt = ChatPromptTemplate.from_messages([ 
    SystemMessage(formatted_system_message),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"), 
    MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

llm = ChatOpenAI(model="gpt-3.5-turbo-0125",
                 temperature=0.0,
                 api_key=API_KEY
                 )

#memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

memory = InMemoryChatMessageHistory(session_id="test-session")
# Create session history
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


if 'agent_memory' not in st.session_state:
    st.session_state['agent_memory'] = ConversationBufferMemory(memory_key='chat_history')

st.header("chatbot AUCA pour prise de RDV pour une seance d'essai")
user_input = st.text_input("Vous: ")
    
agent_new = create_openai_tools_agent(llm, tools, prompt)

# Create an agent executor by passing in the agent and tools
agent_executor_new = AgentExecutor(agent=agent_new, tools=tools, verbose=False, handle_parsing_errors=True,return_intermediate_steps=True)

agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor_new,
   get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="output"  # Ensure this key matches the output of your agent
)
  
def chat_completion_request(messages, functions=None, function_call=None):
    json_data = {"model": GPT_MODEL, "messages": messages}
  
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:

        config = {"configurable": {"session_id": "test-session"}}
        completion =agent_executor_new.invoke(messages)              
           
        history = get_session_history("test-session")
     #   print (history.messages)
   
        #completion = client.chat.completions.create(
        #**json_data
        #)
        return completion
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

chat_history = []
# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    print("not in session")

if st.button('Valider'):  
   
    messages =  {"input":user_input,"chat_history":st.session_state.chat_history}
    
    chat_response = chat_completion_request(
    messages, functions=functions
    )
    
    if chat_response["output"]:
        st.session_state.chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=chat_response["output"])
        ]) 

    print('user_input:', user_input)
    
    if chat_response['output']:
        st.markdown(chat_response['output'])

   
user_input = input("Please enter your question here: (if you want to exit then write 'exit' or 'bye'.) ")

while user_input.strip().lower() != "exit" and user_input.strip().lower() != "bye":
   # messages =  {"input":user_input,"chat_history":chat_history}
    messages =  {"input":user_input}
  
    chat_response = chat_completion_request(
    messages, functions=functions
    )
    
    chat_history.extend([
    HumanMessage(content=user_input),
    AIMessage(content=chat_response["output"])
    ])
         
    if chat_response['output']:
        print("Response is: ", chat_response['output'])
    
   
        #   messages.append({"role": "assistant", "content": chat_response.content})

    # fetch response of ChatGPT and call the function
    #  assistant_message = chat_response.json()["choices"][0]["message"]
    # assistant_message = chat_response;
    # if assistant_message['content']:
    #     print("Response is: ", assistant_message['content'])
    #     messages.append({"role": "assistant", "content": assistant_message['content']})
    # else:
    #     fn_name = assistant_message["function_call"]["name"]
    #     arguments = assistant_message["function_call"]["arguments"]
    #     function = locals()[fn_name]
    #     result = function(arguments)
    #     print("Response is: ", result)

    user_input = input("Please enter your question here: ")







