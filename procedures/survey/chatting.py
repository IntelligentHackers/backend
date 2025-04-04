from datetime import datetime
from fastapi import HTTPException
from openai import Client
from procedures.survey.prompts import product_prompt, start_conversation, continue_conversation, finalize_conversation
from procedures.survey.struct import UserSurveyResult
from settings import OPENAI_KEY
from database import db
from utils.object_id import validate_object_id

client = Client(api_key=OPENAI_KEY)


async def finalize_output(id: str):
    data = await db.registrations.find_one({
        '_id': validate_object_id(id)
    })
    prompts = data['conversations']
    prompts.append({
        'role': 'developer',
        'content': finalize_conversation()
    })
    result = client.beta.chat.completions.parse(
        model='gpt-4o',
        messages=prompts,
        response_format=UserSurveyResult
    )
    info = result.choices[0].message.parsed
    await db.registrations.update_one(
        {'_id': validate_object_id(id)},
        {'$set': {
            'status': 'completed',
            'result': info
        }}
    )
    return info


async def initiate_conversation(lang: str, email: str, ip: str):
    if await db.registrations.find_one({'email': email}):
        raise HTTPException(status_code=400, detail='Email already registered')
    prompts = [
        {
            'role': 'developer',
            'content': product_prompt()
        },
        {
            'role': 'user',
            'content': start_conversation(lang, email, ip)
        }
    ]
    inserted_result = await db.registrations.insert_one({
        'time': datetime.now(),
        'lang': lang,
        'email': email,
        'ip': ip,
        'status': 'started',
        'conversations': prompts,
        'result': None,
    })
    result = client.chat.completions.create(
        model='gpt-4o',
        messages=prompts
    )
    response = result.choices[0].message.content
    await db.registrations.update_one(
        {'_id': inserted_result.inserted_id},
        {'$push': {
            'conversations': {
                'time': datetime.now(),
                'role': 'assistant',
                'message': response
            }
        }}
    )
    return response


async def develop_conversation(id: str, message: str):
    data = await db.registrations.find_one({
        '_id': validate_object_id(id)
    })
    if not data:
        raise HTTPException(status_code=404, detail='Conversation not found')
    if data['status'] == 'completed':
        raise HTTPException(status_code=400, detail='Conversation already completed')
    prompts = data['conversations']
    prompts.append({
        'role': 'user',
        'content': continue_conversation(message)
    })
    await db.registrations.update_one(
        {'_id': validate_object_id(id)},
        {'$push': {
            'conversations': {
                'time': datetime.now(),
                'role': 'user',
                'message': message
            }
        }}
    )
    result = client.chat.completions.create(
        model='gpt-4o',
        messages=prompts
    )
    response = result.choices[0].message.content
    await db.registrations.update_one(
        {'_id': validate_object_id(id)},
        {'$push': {
            'conversations': {
                'time': datetime.now(),
                'role': 'assistant',
                'message': response
            }
        }}
    )
    return response
