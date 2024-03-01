from rest_framework import serializers 
from api_app.models import UserAssessment,Question,UserExamAccess
 

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

class UserExamAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExamAccess
        fields = '__all__'


class UserAssessmentSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = UserAssessment
        fields = '__all__'


















