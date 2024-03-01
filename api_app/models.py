#django_to_api
# from django.db import models
# from django.contrib.auth.models import AbstractUser, BaseUserManager

# # Create your models here. django_to_api 

# class CustomUser(AbstractUser):
#     # _id = models.CharField(max_length=100,default=None)
#     firstname = models.CharField(max_length=100,default="")
#     lastname = models.CharField(max_length=100,default="")
#     username = models.CharField(max_length=100, unique=True)
#     password = models.CharField(max_length=128)
    
#     # objects = CustomUserManager()  # Use the custom user manager  
#     groups = models.ManyToManyField('auth.Group', related_name='custom_users', blank=True)
#     user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_users', blank=True)
    
#     class Meta:
#         db_table = 'users'


# class UserAssessment(models.Model):
#     assessment_name = models.CharField(max_length=100,default='')
#     # user_name = models.CharField(max_length=100)
#     class Meta:
#         db_table = "Testquestionans76"
    
# class Question(models.Model):
#     SerialNumber = models.IntegerField(primary_key=True,default=1)
#     que = models.CharField(max_length=255)
#     ans1 = models.CharField(max_length=255,default='')
#     ans2 = models.CharField(max_length=255,default='')
#     ans3 = models.CharField(max_length=255,default='')
#     ans4 = models.CharField(max_length=255,default='')
#     correct = models.CharField(max_length=255,default='')
#     difficulty = models.IntegerField()
#     is_mca = models.BooleanField(default=False)

#     def __str__(self):
#         return self.que
    
    

# class UserExamAccess(models.Model):
#     user_name = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     start_time = models.DateTimeField()
#     user_answers = models.JSONField(default=list)
#     current_question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)
#     total_questions_asked = models.IntegerField(default=0)
#     asked_question_list = models.JSONField(default=list)
#     current_difficulty = models.JSONField(default=list)
#     end_time = models.DateTimeField()

# class Asse_DND(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     assessment_name = models.ForeignKey(UserAssessment, on_delete=models.CASCADE)
#     score = models.PositiveBigIntegerField(default=0)


#MCQS CODE STARTS FROM HERE ###########################################################################

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here. django_to_api 
class CustomUser(AbstractUser):
    _id = models.CharField(max_length=100,default=None)
    firstname = models.CharField(max_length=100,default="")
    lastname = models.CharField(max_length=100,default="")
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128) 
    # objects = CustomUserManager()  # Use the custom user manager  
    groups = models.ManyToManyField('auth.Group', related_name='custom_users', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_users', blank=True)
    
    class Meta:
        db_table = 'users'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = kwargs.get('username', None)

    # profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

class UserAssessment(models.Model):
    assessment_name = models.CharField(max_length=100,default='')
    # user_name = models.CharField(max_length=100)
    # operation = models.CharField(max_length=100)
    
    class Meta:
        db_table = "Testquestionans59"


class Question(models.Model):
    qno = models.IntegerField(primary_key=True,default=1)
    que = models.CharField(max_length=255)
    correct1 = models.CharField(max_length=255,default='')
    correct2 = models.CharField(max_length=255,default='')
    correct3 = models.CharField(max_length=255,default='')
    correct4 = models.CharField(max_length=255,default='')
    option1 = models.CharField(max_length=255,default='')
    option2 = models.CharField(max_length=255,default='')
    option3 = models.CharField(max_length=255,default='')
    option4 = models.CharField(max_length=255,default='')
    difficulty = models.CharField(max_length=255,default="Easy")
    is_mca = models.BooleanField(default=False)

    def __str__(self):
        return self.que
    


class UserExamAccess(models.Model):
    user_name = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    user_answers = models.JSONField(default=list)
    current_question = models.JSONField(Question,null=True)
    total_questions_asked = models.IntegerField(default=0)
    asked_question_list = models.JSONField(default=list)
    current_difficulty = models.JSONField(default=list)
    question = models.CharField(max_length=255,null=True)
    options = models.JSONField(default=list)  # Store shuffled options
    correct_answers = models.JSONField(null=True)  # Store correct answers
    selected_answers = models.JSONField(default=list)  # Store user's selected answers
    difficulty_level = models.CharField(max_length=255,default="Easy")
    end_time = models.DateTimeField()
    score = models.PositiveBigIntegerField(default=0)


# class Asse_DND(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     assessment_name = models.ForeignKey(UserAssessment, on_delete=models.CASCADE)
#     score = models.PositiveBigIntegerField(default=0)