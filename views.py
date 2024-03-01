###################CODE FOR MCQS STARTING FROM HERE ###########################################
# django_to_api 

from datetime import datetime
from operator import is_
from pydoc import doc
from django.urls import reverse
import ast
from unicodedata import east_asian_width
from django.db.models import JSONField
from django.shortcuts import redirect, render
from django.http import HttpResponse,JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Question, UserExamAccess, UserAssessment,CustomUser
from .serializers import QuestionSerializer, UserExamAccessSerializer
# from datetime import timezone, timedelta
import pymongo, random
from rest_framework.decorators import api_view
from .models import Question
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.contrib.auth.models import User 
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from bson import ObjectId

import configparser
import os
from pathlib import Path
#from django.views.decorators.http import require_http_methods

BASE_DIR = Path(__file__).resolve().parent.parent
config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'config.ini'))


# Create your views here.
MAX_LEVELS = int(config["CONSTANTS"]["MAX_LEVELS"])
questions_per_level = int(config["CONSTANTS"]["QUESTIONS_PER_LEVEL"])
questions_per_asse_type = int(config["CONSTANTS"]["QUESTIONS_PER_ASSE_TYPE"])

def start_exam():
    start_time = datetime.now()
    return start_time

def end_exam():
    end_time = datetime.now()
    return end_time

def get_mongo_connection():
    client = pymongo.MongoClient("mongodb://10.0.0.14:27017/")
    db = client["nesplConfig"]
    # print("server_connected")
    return db
    
@require_http_methods(["GET"])
def get_or_create_assessment_session(request, user_name, assessment_name):

    correct_answers_for_loop = 0
    total_questions_asked=0
    next_difficulty_level = 1
    # table_users = get_mongo_connection().users
    db = get_mongo_connection()
    table_users = db["users"]
    user = table_users.find_one({'username': user_name})
    # print(user)

    candidate_checking = db["candidate_assessment_history"]
    user_checking = candidate_checking.find_one({'username': user_name,'assessment_name':assessment_name})
    if user_checking:
        response_data = {'message': f"Sorry {user_name}!! You have already taken this assessment!!"}
        return JsonResponse(response_data)
        
    if user:  
        difficulty = "Easy"  
        total_score = 0 
        try:
                    db = get_mongo_connection()
                    collection_question = db["Testquestionans59"]
                    query = {
                        "difficulty": difficulty,
                        "assessment": assessment_name
                    }
                    document = collection_question.find_one(query)
                    # print("i am document",document)
                    # print("i am qid", document["qno"])
                    # print("i am que_txt", document["que"])
                    opt = [document['que'][f'option{i}'] for i in range(1, 5)]
                    # print("i am optinos",opt)
                    current_question = document['que']
                    serial_no = document["qno"]
                    total_questions_asked = total_questions_asked+1
                    start_time = start_exam()
                    response_data = {
                        'message': f"Question {total_questions_asked}:",
                        "start_time": start_time,
                        # 'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
                    
                    
                    collection_traking = db["bj_history"]
                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name})
                    
                    if existing_document:
                            # Update existing document
                            collection_traking.update(
                                {"user_name": user_name, "assessment_name": assessment_name},
                                {
                                    "$push": {
                                        # "asked_question": {
                                        #     "sno": current_question["qno"],
                                        # },
                                        "question_list":[serial_no]
                                    },
                                    "$set": {
                                        "total_questions_asked": total_questions_asked,
                                    }
                                }
                            )
                    else:
                            # Insert new document
                            assessment_document = {
                                "_id": ObjectId(),
                                "user_name": user_name,
                                "assessment_name": assessment_name,
                                "start_time": start_time,
                                "total_score": total_score,
                                "correct_answers_for_loop": correct_answers_for_loop,
                                "total_questions_asked": total_questions_asked,
                                "next_difficulty_level": next_difficulty_level,
                                # "end_time": end_time,
                                "question_list":[serial_no],
                                # "asked_question": [
                                #     {
                                #         "sno": current_question["qno"],
                                #         # "user_answer": is_correct,
                                #         # "assessment_date": datetime.now()
                                #     }
                                # ]
                            }
                            collection_traking.insert_one(assessment_document)

                    score_save_table = db['candidate_assessment_history']
                    save_document = { 
                                            "username": user_name,
                                            "assessment_name": assessment_name,
                                            "start_time": start_time,
                                        }
                    score_save_table.insert_one(save_document)
                    
                    
                    return JsonResponse(response_data)

        except Exception as e:
                    return HttpResponse(f"Error in initialize_session: {str(e)}")
    else:
            return JsonResponse({"message": "Username does not exist!"}, safe=False)
   

def get_answer(request,user_name,assessment_name,user_answers,operation,serial_no):
     
    end_time = end_exam()
    user_answers = user_answers.split(',')
    db = get_mongo_connection()
    collection_question = db["Testquestionans59"]
    collection_traking = db["bj_history"]
    query = {"qno": serial_no}
    document = collection_question.find_one(query)
    question = document['que']
    correct_answers = [question[f'correct{i}'] for i in range(1,5)]
    correct_answers_set = set(str(i + 1) for i, ans in enumerate(correct_answers) if ans.lower() == 'true')
    # print("we are correct answers set :",correct_answers_set)
    is_correct = (set(user_answers) == correct_answers_set)
    next_difficulty_level = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("next_difficulty_level")
    asked_questions_list = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("total_score")
    
    if operation =="Start":
        current_difficulty = 1
        try:
            if 1 <= len(user_answers) <= 4:
                
                if is_correct:                           # selected_option == question['data']['correct']

                    total_score += (int(current_difficulty)*2)-1  # Increase the score for each correct answer
                    correct_answers_for_loop += 1
                    
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level=2
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1 
                                # questions = question_easy
                                
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1 
                                    # questions = question_easy

                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name})
                    
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now()
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)

                
                else: 
                    #print(f"Wrong! \n")
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3 
                                # questions = question_hard
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2 
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1
                            # questions = question_easy
                            
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                        
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium 
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1
                                    # questions = question_easy
                    
                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now()
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)

            else:
                return HttpResponse("Please select the correct options ")     # print("Invalid input. Please enter a number between 1 and 4.\n")

        except Question.DoesNotExist:
                return Response({"error": "Question not found"}, status=404)
            
    if operation =="Next":

        current_difficulty = next_difficulty_level
        try:
            if 1 <= len(user_answers) <= 4:
                
                if is_correct:                           # selected_option == question['data']['correct']

                    total_score += (int(current_difficulty)*2)-1  # Increase the score for each correct answer
                    correct_answers_for_loop += 1
                    
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level=2
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1 
                                # questions = question_easy
                                
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1 
                                    # questions = question_easy

                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name})
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now()
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)

                  
                else: 
                    #print(f"Wrong! \n")
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3 
                                # questions = question_hard
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2 
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1
                            # questions = question_easy
                            
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                        
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium 
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1
                                    # questions = question_easy
                    
                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now()
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)

                    
                if total_questions_asked == questions_per_level:
                        max_score = int(config["CONSTANTS"]["MAX_SCORE"])
                        grade = ''
                        if (total_score >= int((85/100)*(max_score))):
                            grade = 'A+'
                        elif (total_score >= int((75/100)*(max_score))) and (total_score <= int((85/100)*(max_score))):
                            grade = 'A'
                        elif (total_score >= int((60/100)*(max_score))) and (total_score <= int((75/100)*(max_score))):
                            grade = 'B'
                        elif (total_score < int((60/100)*(max_score))):
                            grade = 'C'

                        db = get_mongo_connection()
                        score_save_table = db['candidate_assessment_history']
                        query_score = {"username": user_name,
                                        "assessment_name": assessment_name}
                        update_query = {"$set":{
                                            "end_time": end_time,
                                            "score" : total_score,
                                            "grade" : grade
                        }}
                        # save_document = {
                        #                     "_id": ObjectId(),
                        #                     "username": user_name,
                        #                     "assessment_name": assessment_name,
                        #                     # "start_time": start_time,
                                            
                        #                 }
                       
                        score_save_table.update_one(query_score,update_query)
                        response_data = {'message': f"Thank you for your precious time {user_name}!! We will get back to you soon. "}
                        return JsonResponse(response_data)
                     
        
            else:
                return HttpResponse("Please select the correct options ")     # print("Invalid input. Please enter a number between 1 and 4.\n")

        except Question.DoesNotExist:
                return Response({"error": "Question not found"}, status=404)
     
    if next_difficulty_level == 3 :
         difficulty = "High"
        #  questions = [range(questions_per_asse_type - questions_per_level+1,questions_per_asse_type+1)]
    elif next_difficulty_level == 2:
         difficulty = "Medium"
        #  questions=[range(questions_per_level+1,questions_per_level - questions_per_level+1)]
    else :
         difficulty = "Easy"   
    
    asked_questions_list = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name})).get("total_score")   

    db = get_mongo_connection()
    collection_question = db["Testquestionans59"]
    query = {
                        "difficulty": difficulty,
                        "assessment": assessment_name,
                        "qno":{"$nin": asked_questions_list}
                    }
        # document = collection_question.find_one(query)
    # print(query)
    cursor = collection_question.aggregate([
            {"$match": query},
            {"$sample": {"size": 1}} # Use the $sample operator to get a random document
        ])
    # print(cursor)
    document = next(cursor, None)
    current_question = document.get('que',{})
    serial_no = document.get('qno',{})
    total_questions_asked = total_questions_asked + 1
    response_data = {
                        'message': f"Question {total_questions_asked}:",
                        # 'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
    
    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name})
    
    start_time = start_exam()
    if existing_document:
        collection_traking.update(
                                {"user_name": user_name, "assessment_name": assessment_name},
                                {
                                    "$push": {
                                        # "asked_question": {
                                        #     "sno": current_question["qno"],
                                        #     # "user_answer": is_correct,
                                        #     # "assessment_date": datetime.now()
                                        # },
                                        "question_list":serial_no
                                    },
                                    "$set": {
                                        # "end_time": end_time,
                                        # "correct_answers_for_loop": correct_answers_for_loop,
                                        "total_questions_asked": total_questions_asked,
                                        # "next_difficulty_level": next_difficulty_level
                                    }
                                }
                            )
    else:
        assessment_document = {
                                "_id": ObjectId(),
                                "user_name": user_name,
                                "assessment_name": assessment_name,
                                "start_time": start_time,
                                "total_score": total_score,
                                "correct_answers_for_loop": correct_answers_for_loop,
                                "total_questions_asked": total_questions_asked,
                                "next_difficulty_level": next_difficulty_level,
                                # "end_time": end_time,
                                "question_list":serial_no,
                                # "asked_question": [
                                #     {
                                #         "sno": question["qno"],
                                #         # "user_answer": is_correct,
                                #         # "assessment_date": datetime.now()
                                #     }
                                # ]
                            }
        collection_traking.insert_one(assessment_document)

    
    return JsonResponse(response_data)
    


@require_http_methods(["GET"])
def industry_get_or_create_assessment_session(request, industry_name, user_name, assessment_name):

    correct_answers_for_loop = 0
    total_questions_asked=0
    next_difficulty_level = 1
    # table_users = get_mongo_connection().users
    db = get_mongo_connection()
    table_users = db["users"]

    candidate_checking = db["industry_candidate_assessment_history"]
    user_checking = candidate_checking.find_one({'username': user_name,'assessment':assessment_name,'industry_name':industry_name})
    if user_checking:
        response_data = {'message': f"Sorry {user_name}!! You have already taken this assessment!!"}
        return JsonResponse(response_data)
        
    user = table_users.find_one({'username': user_name,'name':industry_name})
    # print(user)
    if user:  
        difficulty = "Easy"  
        total_score = 0 
        try:
                    db = get_mongo_connection()
                    collection_question = db["industry_questionans"]
                    query = {
                        "difficulty": difficulty,
                        "assessment": assessment_name,
                        "industry_name": industry_name
                    }
                    document = collection_question.find_one(query)

                    # print(" i am document",document)
                    
                    opt = [document['que'][f'option{i}'] for i in range(1, 5)]
                    # print("i am optinos",opt)
                    current_question = document['que']
                    serial_no = document["qno"]
                    total_questions_asked = total_questions_asked+1
                    start_time = start_exam()
                    print("i am above the response data")
                    response_data = {
                        'message': f"Question {total_questions_asked}:",
                        "start_time": start_time,
                        # 'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
                    
                    print(response_data)

                    collection_traking = db["industry_bj_history"]
                    existing_document = collection_traking.find_one({"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name})
                    
                    if existing_document:
                            # Update existing document
                            collection_traking.update(
                                {"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name},
                                {
                                    "$push": {
                                        
                                        "question_list":[serial_no]
                                    },
                                    "$set": {
                                        "total_questions_asked": total_questions_asked,
                                    }
                                }
                            )
                    else:
                            # Insert new document
                            assessment_document = {
                                "_id": ObjectId(),
                                "user_name": user_name,
                                "assessment_name": assessment_name,
                                "industry_name": industry_name,
                                "start_time": start_time,
                                "total_score": total_score,
                                "correct_answers_for_loop": correct_answers_for_loop,
                                "total_questions_asked": total_questions_asked,
                                "next_difficulty_level": next_difficulty_level,
                                # "end_time": end_time,
                                "question_list":[serial_no],
                                
                            }
                            collection_traking.insert_one(assessment_document)

                    score_save_table = db['industry_candidate_assessment_history'] #industry_candidate_assessment_history
                    save_document = { 
                                            "username": user_name,
                                            "assessment_name": assessment_name,
                                            "industry_name": industry_name, 
                                            "start_time": start_time,
                                        }
                    score_save_table.insert_one(save_document)
                    
                    
                    return JsonResponse(response_data)

        except Exception as e:
                    return HttpResponse(f"Error in initialize_session: {str(e)}")
    else:
            return JsonResponse({"message": "Username does not exist!"}, safe=False)
   


def industry_get_answer(request,industry_name,user_name,assessment_name,user_answers,operation,serial_no):
     
    end_time = end_exam()
    user_answers = user_answers.split(',')
    db = get_mongo_connection()
    collection_question = db["industry_questionans"]
    collection_traking = db["industry_bj_history"]
    query = {"qno": serial_no}
    document = collection_question.find_one(query)
    question = document['que']
    correct_answers = [question[f'correct{i}'] for i in range(1,5)]
    correct_answers_set = set(str(i + 1) for i, ans in enumerate(correct_answers) if ans.lower() == 'true')
    # print("we are correct answers set :",correct_answers_set)
    is_correct = (set(user_answers) == correct_answers_set)
    next_difficulty_level = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("next_difficulty_level")
    asked_questions_list = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("total_score")
    
    if operation =="Start":
        current_difficulty = 1
        try:
            if 1 <= len(user_answers) <= 4:
                
                if is_correct:                           # selected_option == question['data']['correct']

                    total_score += (int(current_difficulty)*2)-1  # Increase the score for each correct answer
                    correct_answers_for_loop += 1
                    
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level=2
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1 
                                # questions = question_easy
                                
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1 
                                    # questions = question_easy

                    existing_document = collection_traking.find_one({"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name})
                    
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now(),
                                        "industry_name": industry_name
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            "industry_name": industry_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)

                
                else: 
                    #print(f"Wrong! \n")
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3 
                                # questions = question_hard
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2 
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1
                            # questions = question_easy
                            
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                        
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium 
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1
                                    # questions = question_easy
                    
                    existing_document = collection_traking.find_one({"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now(),
                                        "industry_name": industry_name
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            "industry_name": industry_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)
                        
            else:
                return HttpResponse("Please select the correct options ")     # print("Invalid input. Please enter a number between 1 and 4.\n")

        except Question.DoesNotExist:
                return Response({"error": "Question not found"}, status=404)
            
    if operation =="Next":

        current_difficulty = next_difficulty_level
        try:
            if 1 <= len(user_answers) <= 4:
                
                if is_correct:                           # selected_option == question['data']['correct']

                    total_score += (int(current_difficulty)*2)-1  # Increase the score for each correct answer
                    correct_answers_for_loop += 1
                    
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level=2
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1 
                                # questions = question_easy
                                
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1 
                                    # questions = question_easy

                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name})
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now()
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            "industry_name": industry_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)

                  
                else: 
                    #print(f"Wrong! \n")
                    if (total_questions_asked % 3 == 0) and (correct_answers_for_loop >= 2) :
                            correct_answers_for_loop = 0
                            if current_difficulty == 3:
                                next_difficulty_level = 3 
                                # questions = question_hard
                                
                            elif current_difficulty < MAX_LEVELS:
                                current_difficulty += 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2 
                                    # questions = question_medium
                                elif current_difficulty == 3:
                                    next_difficulty_level = 3
                                    # questions = question_hard

                    elif (total_questions_asked % 3 == 0)and (correct_answers_for_loop <=1):
                            correct_answers_for_loop = 0
                            if current_difficulty == 1:
                                next_difficulty_level = 1
                            # questions = question_easy
                            
                            elif current_difficulty > 1: # Comparing with min level of difficulty 
                        
                                current_difficulty -= 1
                                if current_difficulty == 2:
                                    next_difficulty_level = 2
                                    # questions = question_medium 
                                elif current_difficulty == 1:
                                    next_difficulty_level = 1
                                    # questions = question_easy
                    
                    existing_document = collection_traking.find_one({"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now()
                                    }
                                },
                                "$set": {
                                    "end_time": end_time,
                                    "correct_answers_for_loop": correct_answers_for_loop,
                                    "total_score": total_score,
                                    "next_difficulty_level": next_difficulty_level
                                }
                            }
                        )
                    else:
                        # Insert new document
                        assessment_document = {
                            "_id": ObjectId(),
                            "user_name": user_name,
                            "assessment_name": assessment_name,
                            "industry_name": industry_name,
                            # "start_time": start_time,
                            "end_time": end_time,
                            "correct_answers_for_loop": correct_answers_for_loop,
                            "total_score": total_score,
                            "next_difficulty_level": next_difficulty_level,
                            "asked_question": [
                                {
                                    "question": question["qno"],
                                    "user_answer": is_correct,
                                    "assessment_date": datetime.now()
                                }
                            ]
                        }
                        collection_traking.insert_one(assessment_document)

                    
                if total_questions_asked == questions_per_level:
                        max_score = int(config["CONSTANTS"]["MAX_SCORE"])
                        grade = ''
                        if (total_score >= int((85/100)*(max_score))):
                            grade = 'A+'
                        elif (total_score >= int((75/100)*(max_score))) and (total_score <= int((85/100)*(max_score))):
                            grade = 'A'
                        elif (total_score >= int((60/100)*(max_score))) and (total_score <= int((75/100)*(max_score))):
                            grade = 'B'
                        elif (total_score < int((60/100)*(max_score))):
                            grade = 'C'

                        db = get_mongo_connection()
                        score_save_table = db['industry_candidate_assessment_history']
                        query_score = {"industry_name": industry_name,"username": user_name,
                                        "assessment_name": assessment_name}
                        update_query = {"$set":{
                                            "end_time": end_time,
                                            "industry_score" : total_score,
                                            "grade" : grade
                        }}
                        
                       
                        score_save_table.update_one(query_score,update_query)
                        response_data = {'message': f"Thank you for your precious time {user_name}!! We will get back to you soon. "}
                        return JsonResponse(response_data)
                     
        
            else:
                return HttpResponse("Please select the correct options ")     # print("Invalid input. Please enter a number between 1 and 4.\n")

        except Question.DoesNotExist:
                return Response({"error": "Question not found"}, status=404)
     
    if next_difficulty_level == 3 :
         difficulty = "High"
        #  questions = [range(questions_per_asse_type - questions_per_level+1,questions_per_asse_type+1)]
    elif next_difficulty_level == 2:
         difficulty = "Medium"
        #  questions=[range(questions_per_level+1,questions_per_level - questions_per_level+1)]
    else :
         difficulty = "Easy"   
    
    asked_questions_list = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"industry_name": industry_name,"user_name":user_name,"assessment_name":assessment_name})).get("total_score")   

    db = get_mongo_connection()
    collection_question = db["industry_questionans"]
    query = {
                        "difficulty": difficulty,
                        "assessment": assessment_name,
                        "industry_name": industry_name,
                        "qno":{"$nin": asked_questions_list}
                    }
        # document = collection_question.find_one(query)
    # print(query)
    cursor = collection_question.aggregate([
            {"$match": query},
            {"$sample": {"size": 1}} # Use the $sample operator to get a random document
        ])
    # print(cursor)
    document = next(cursor, None)

    current_question = document.get('que',{})
    serial_no = document.get('qno',{})
    total_questions_asked = total_questions_asked + 1
    response_data = {
                        'message': f"Question {total_questions_asked}:",
                        # 'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
    
    existing_document = collection_traking.find_one({"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name})
    
    start_time = start_exam()
    if existing_document:
        collection_traking.update(
                                {"industry_name": industry_name,"user_name": user_name, "assessment_name": assessment_name},
                                {
                                    "$push": {
                                      
                                        "question_list":serial_no
                                    },
                                    "$set": {
                                       
                                        "total_questions_asked": total_questions_asked,
                                      
                                    }
                                }
                            )
    else:
        assessment_document = {
                                "_id": ObjectId(),
                                "user_name": user_name,
                                "assessment_name": assessment_name,
                                "industry_name": industry_name,
                                "start_time": start_time,
                                "total_score": total_score,
                                "correct_answers_for_loop": correct_answers_for_loop,
                                "total_questions_asked": total_questions_asked,
                                "next_difficulty_level": next_difficulty_level,
                                # "end_time": end_time,
                                "question_list":serial_no,
                               
                            }
        collection_traking.insert_one(assessment_document)

    
    return JsonResponse(response_data)
    