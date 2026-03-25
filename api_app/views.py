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
# questions_per_level = int(config["CONSTANTS"]["QUESTIONS_PER_LEVEL"])
# questions_per_asse_type = int(config["CONSTANTS"]["QUESTIONS_PER_ASSE_TYPE"])

def start_exam():
    start_time = datetime.now()
    return start_time

def end_exam():
    end_time = datetime.now()
    return end_time

def get_mongo_connection():
    client = pymongo.MongoClient("mongodb://ec2-3-25-125-96.ap-southeast-2.compute.amazonaws.com:27017/") #10.0.0.14
    db = client["nesplConfig"]
    # print("server_connected")
    return db
    
@require_http_methods(["GET"])
def get_or_create_assessment_session(request, user_name, assessment_name, skill):

    correct_answers_for_loop = 0
    total_questions_asked=0
    next_difficulty_level = 1
    # table_users = get_mongo_connection().users
    db = get_mongo_connection()
    table_users = db["users"]
    user = table_users.find_one({'username': user_name})
    # print('i am user', user)

    table_questions = db["assessmentAndTimeDurationSuper"]
    question_document = table_questions.find_one({"assessmentName": assessment_name, "skill": skill})
    questions_per_asse_type = question_document['numberOfquestionForAssessment']
    questions_per_level = questions_per_asse_type//3 

    candidate_checking = db["candidate_assessment_history"]
    user_checking = candidate_checking.find_one({'username': user_name,'assessmentName':assessment_name,"skill": skill})
    if user_checking:
        response_data = {'message': f"Sorry {user_name}!! You have already taken this assessment!!"}
        return JsonResponse(response_data)
        
    if user:  
        difficulty = "Easy"  
        total_score = 0 
        try:
                    db = get_mongo_connection()
                    collection_question = db["assessmentSuperAdmin"]
                    query = {
                        "difficulty": difficulty,
                        "assessmentName": assessment_name,
                        "skill": skill
                    }
                    document = collection_question.find_one(query)
                    opt = [document['que'][f'option{i}'] for i in range(1, 5)]
                    # print("i am optinos",opt)
                    current_question = document['que']
                    serial_no = document["qno"]
                    total_questions_asked = total_questions_asked + 1
                    start_time = start_exam()
                    response_data = {
                        'message': f"Question {total_questions_asked}:",
                        "start_time": start_time,
                        'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
                    
                    
                    collection_traking = db["bj_history"]
                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name, "skill": skill})
                    
                    if existing_document:
                            # Update existing document
                            collection_traking.update(
                                {"user_name": user_name, "assessment_name": assessment_name, "skill": skill},
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
                                "skill": skill,
                                "start_time": start_time,
                                "total_score": total_score,
                                "correct_answers_for_loop": correct_answers_for_loop,
                                "total_questions_asked": total_questions_asked,
                                "next_difficulty_level": next_difficulty_level,
                                # "end_time": end_time,
                                "question_list":[serial_no],
                            }
                            collection_traking.insert_one(assessment_document)

                    score_save_table = db['candidate_assessment_history']
                    save_document = { 
                                            "username": user_name,
                                            "assessment_name": assessment_name,
                                            "start_time": start_time,
                                            "skill" : skill
                                        }
                    score_save_table.insert_one(save_document)
                    
                    
                    return JsonResponse(response_data)

        except Exception as e:
                    return HttpResponse(f"Error in initialize_session: {str(e)}")
    else:
            return JsonResponse({"message": "Username does not exist!"}, safe=False)
   

def get_answer(request,user_name,assessment_name,skill,user_answers,operation,serial_no):
     
    end_time = end_exam()
    user_answers = user_answers.split(',')
    db = get_mongo_connection()
    collection_question = db["assessmentSuperAdmin"]
    collection_traking = db["bj_history"]

    table_questions = db["assessmentAndTimeDurationSuper"]
    question_document = table_questions.find_one({"assessmentName": assessment_name, "skill": skill})
    questions_per_asse_type = question_document['numberOfquestionForAssessment']
    questions_per_level = questions_per_asse_type//3 


    query = {"qno": serial_no}
    document = collection_question.find_one(query)
    question = document['que']
    correct_answers = [question[f'correct{i}'] for i in range(1,5)]
    correct_answers_set = set(str(i + 1) for i, ans in enumerate(correct_answers) if ans.lower() == 'true')
    # print("we are correct answers set :",correct_answers_set)
    is_correct = (set(user_answers) == correct_answers_set)
    next_difficulty_level = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("next_difficulty_level")
    asked_questions_list = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("total_score")
    
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

                    existing_document = collection_traking.find_one({"user_name": user_name, "assessmentName": assessment_name, "skill": skill})
                    
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name,"skill": skill},
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
                            "skill": skill ,
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
                    
                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name, "skill": skill})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name, "skill": skill},
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
                            "skill": skill ,
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

                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name, "skill": skill})
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name, "skill": skill},
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
                            "skill": skill , 
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
                    
                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name, "skill": skill})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"user_name": user_name, "assessment_name": assessment_name, "skill": skill},
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
                            "skill": skill, 
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


                if total_questions_asked == questions_per_level: # questions_per_level
                    assessmentResponseType = "Finished"
                elif 1 < total_questions_asked < questions_per_level:
                    assessmentResponseType = "Pursuing"
                else:
                    assessmentResponseType = "Recommended"

                # max_score = int(config["CONSTANTS"]["MAX_SCORE"])
                max_score = (MAX_LEVELS*1)+(MAX_LEVELS*3)+(questions_per_level)*5
                
                grade = ''
                if total_score >= int(0.85 * max_score):
                    grade = 'A+'
                elif total_score >= int(0.75 * max_score):
                    grade = 'A'
                elif total_score >= int(0.60 * max_score):
                    grade = 'B'
                elif (total_score < int((60/100)*(max_score))):
                    grade = 'C'

                db = get_mongo_connection()
                score_save_table = db['candidate_assessment_history']
                query_score = {"username": user_name, "assessment_name": assessment_name, "skill": skill}
                update_query = {"$set": {
                    "end_time": end_time,
                    "score": total_score,
                    "grade": grade,
                    "nespl_assessment_submited": "yes" if total_questions_asked == questions_per_level else "No",
                    "assessmentResponseType": assessmentResponseType
                }}

                score_save_table.update_one(query_score, update_query)

                if total_questions_asked == questions_per_level:
                    response_data = {'message': f"Your assessment has been successfully completed. You can view your score on the dashboard."}
                    return JsonResponse(response_data)
                # else:
                #     return HttpResponse("Please select the correct options ")

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
    
    asked_questions_list = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill":skill})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill":skill})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill":skill})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"user_name":user_name,"assessment_name":assessment_name,"skill":skill})).get("total_score")   

    db = get_mongo_connection()
    collection_question = db["assessmentSuperAdmin"]
    query = {
                        "difficulty": difficulty,
                        "assessmentName": assessment_name,
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
                        'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
    
    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name,"skill": skill})
    
    start_time = start_exam()
    if existing_document:
        collection_traking.update(
                                {"user_name": user_name, "assessment_name": assessment_name,"skill": skill},
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
                                "skill": skill, 
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
def industry_get_or_create_assessment_session(request, industry_name, user_name, assessment_name,skill):

    correct_answers_for_loop = 0
    total_questions_asked=0
    next_difficulty_level = 1
    # table_users = get_mongo_connection().users
    db = get_mongo_connection()
    table_users = db["users"]

    table_questions = db["assessmentAndTimeDuration"]
    question_document = table_questions.find_one({"assessmentName": assessment_name, "skill": skill})
    questions_per_asse_type = question_document['numberOfquestionForAssessment']
    questions_per_level = questions_per_asse_type//3 

    # print("hello")
    candidate_checking = db["industry_candidate_assessment_history"]
    user_checking = candidate_checking.find_one({'username': user_name,'assessment_name':assessment_name,'industry':industry_name,"skill": skill}) 
    grade = ''
    if user_checking:
        response_data = {'message': f"Sorry {user_name}!! You have already taken this assessment!!"}
        return JsonResponse(response_data)
        
    user = table_users.find_one({'username': user_name}) # ,'name':industry_name
    # print(user)
    if user:  
        difficulty = "Easy"  
        total_score = 0 
        try:
                    db = get_mongo_connection()
                    # print('i am db', db)
                    collection_question = db["industry_assessment"]
                    query = {
                        "difficulty": difficulty,
                        "assessmentName": assessment_name, # assessment - > assessmentName 
                        "industry": industry_name,
                        "skill":skill
                    }
                    document = collection_question.find_one(query)
                    if document is None:
                        return JsonResponse({"message": "No questions found for the specified assessment."}, status=404)
                    
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
                        'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
                    
                    # print(response_data)

                    collection_traking = db["industry_bj_history"]
                    existing_document = collection_traking.find_one({"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill}) # skill added 
                    
                    if existing_document:
                            # Update existing document
                            collection_traking.update(
                                {"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill},
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
                                "industry": industry_name,
                                "skill": skill, 
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
                                            "industry": industry_name, 
                                            "skill": skill, 
                                            "start_time": start_time,
                                            "skill" : skill
                                        }
                    score_save_table.insert_one(save_document)
                    
                    
                    return JsonResponse(response_data)

        except Exception as e:
                    return HttpResponse(f"Error in initialize_session: {str(e)}")
    else:
            return JsonResponse({"message": "Username does not exist!"}, safe=False)
   


def industry_get_answer(request,industry_name,user_name,assessment_name,skill,user_answers,operation,serial_no):
     
    end_time = end_exam()
    user_answers = user_answers.split(',')
    db = get_mongo_connection()
    
    collection_question = db["industry_assessment"] # industry_questionans -> industry_assessment
    collection_traking = db["industry_bj_history"]

    table_questions = db["assessmentAndTimeDuration"]
    question_document = table_questions.find_one({"assessmentName": assessment_name, "skill": skill})
    questions_per_asse_type = question_document['numberOfquestionForAssessment']
    questions_per_level = questions_per_asse_type//3 
    
    query = {"qno": serial_no}
    document = collection_question.find_one(query)
    question = document['que']
    correct_answers = [question[f'correct{i}'] for i in range(1,5)]
    correct_answers_set = set(str(i + 1) for i, ans in enumerate(correct_answers) if ans.lower() == 'true')
    # print("we are correct answers set :",correct_answers_set)
    is_correct = (set(user_answers) == correct_answers_set)
    next_difficulty_level = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("next_difficulty_level")
    asked_questions_list = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("total_score")
    grade = ''
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

                    existing_document = collection_traking.find_one({"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill})
                    
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name, "skill": skill},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now(),
                                        "industry": industry_name
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
                            "industry": industry_name,
                            "skill": skill, 
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
                    
                    existing_document = collection_traking.find_one({"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name, "skill": skill},
                            {
                                "$push": {
                                    "asked_question": {
                                        "question": question["qno"],
                                        "user_answer": is_correct,
                                        "assessment_date": datetime.now(),
                                        "industry": industry_name
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
                            "industry": industry_name,
                            "skill": skill, 
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

                    existing_document = collection_traking.find_one({"user_name": user_name, "assessment_name": assessment_name,"skill": skill,"industry": industry_name})
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill,"industry": industry_name},
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
                            "industry": industry_name,
                            "skill": skill,
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
                    
                    existing_document = collection_traking.find_one({"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill})
                   
                    if existing_document:
                        # Update existing document
                        collection_traking.update(
                            {"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill},
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
                            "industry": industry_name,
                            "skill": skill, 
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
                    assessmentResponseType = "Finished"
                elif 1 < total_questions_asked < questions_per_level:
                    assessmentResponseType = "Pursuing"
                else:
                    assessmentResponseType = "Recommended"
                    
                if total_questions_asked == questions_per_level: #questions_per_level
                        # max_score = int(config["CONSTANTS"]["MAX_SCORE"])
                        max_score = (3*1)+(3*3)+(questions_per_level-6)*5 
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
                query_score = {"industry": industry_name,"username": user_name,
                                        "assessment_name": assessment_name, "skill": skill}
                update_query = {"$set":{
                                            "end_time": end_time,
                                            "industry_score" : total_score,
                                            "grade" : grade,
                                            "nespl_assessment_submited": "yes" if total_questions_asked == questions_per_level else "No",
                                            "assessmentResponseType": assessmentResponseType
                        }}
                        
                       
                score_save_table.update_one(query_score,update_query)
                
                if total_questions_asked == questions_per_level:
                    response_data = {'message': f"Your assessment has been successfully completed."}
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
    
    asked_questions_list = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("question_list")
    correct_answers_for_loop = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("correct_answers_for_loop")
    total_questions_asked = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("total_questions_asked")
    total_score = (collection_traking.find_one({"industry": industry_name,"user_name":user_name,"assessment_name":assessment_name,"skill": skill})).get("total_score")   

    db = get_mongo_connection()
    collection_question = db["industry_assessment"]
    query = {
                        "difficulty": difficulty,
                        "assessmentName": assessment_name,
                        "industry": industry_name,
                        "skill":skill,
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
                        'difficulty': difficulty,
                        'qid': serial_no,
                        'question_data': current_question['que'],
                        'options': [current_question[f'option{i}'] for i in range(1, 5)]
                    }
    
    existing_document = collection_traking.find_one({"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill})
    
    start_time = start_exam()
    if existing_document:
        collection_traking.update(
                                {"industry": industry_name,"user_name": user_name, "assessment_name": assessment_name,"skill": skill},
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
                                "industry": industry_name,
                                "skill": skill, 
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
    
