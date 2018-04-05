from django.db import models
from .utils import *
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
import re, os
from uuid import uuid4
from django.db.models import Q
from django.contrib.humanize.templatetags.humanize import naturaltime
    
def path_and_rename(instance, filename):
    upload_to = 'profile-image'
    ext = filename.split('.')[-1]
    # get filename
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
    # return the whole path to the file
    imagepath = os.path.join(upload_to, filename)
    if os.path.exists(imagepath):
        path_and_rename(instance, filename)
  
    return imagepath


class DbNormsShared(models.Model):
    def update(self,name):
        obj = None
        try:
            obj = eval(self.__class__.__name__).objects.get(name=name)
        except:
            obj = eval(self.__class__.__name__).objects.create(name=name)
            obj.save()
        return obj

    class Meta:
        abstract = True


class staticInfo():
    max_student = 8


class languageInfo(DbNormsShared):
    name = models.CharField(max_length=26)

class emailInfo(DbNormsShared):
    name = models.CharField(max_length=100)
    
class user_catagory(DbNormsShared):
    name = models.CharField(max_length=26)
    
class city(DbNormsShared):
    name = models.CharField(max_length=26)

class state(DbNormsShared):
    name = models.CharField(max_length=26)

class country(DbNormsShared):
    name = models.CharField(max_length=26)


class userProfileSettings(DbNormsShared):
    firstname = models.CharField(max_length=26,default="",blank=False,null=False)
    lastname = models.CharField(max_length=26,default="",blank=False,null=False)
    gender = models.CharField(max_length=10,default="",blank=False,null=False)
    dateofbirth =  models.DateField(default="",blank=False,null=False)
    countryField = models.ForeignKey(country,default="",blank=False,null=False)
    stateField = models.ForeignKey(state,default="",blank=False,null=False)
    cityField = models.ForeignKey(city,default="",blank=False,null=False)


class userInfo(AbstractBaseUser):
    userid = models.CharField(max_length=26)
    email = models.ForeignKey(emailInfo)
    phoneno = models.CharField(max_length=26,default="")
    catagory = models.ForeignKey(user_catagory,default="student")
    image = models.ImageField(upload_to=path_and_rename, max_length=255,default="",blank=True,null=True)
    personalInfo = models.ForeignKey(userProfileSettings,default="",blank=True,null=True)
    cart = models.ManyToManyField("classesInfo")
    democlassField = models.ManyToManyField("demoClass")
    friends = models.ManyToManyField("userInfo")

    def makeFriend(self,friendObj):
        friendObj.friends.add(self)
        friendObj.save()
        self.friends.add(friendObj)
        self.save()
    
    USERNAME_FIELD = 'email'
    # password already exist in AbstractBaseUser
    def __unicode__(self):
        return self.email.name
    def __str__(self):
        return self.email.name

class class_catagory(DbNormsShared):
    name = models.CharField(max_length=26)

class general_faq(DbNormsShared):
    name = models.CharField(max_length=26)
    catagory =  models.ForeignKey(class_catagory)

class classFaq(DbNormsShared):
    name = models.CharField(max_length=1024,default="")

class userComments(DbNormsShared):
    userInfoid = models.ForeignKey(userInfo,blank=False,null=False)
    name = models.CharField(max_length=1024,default="")
    created_on = models.DateTimeField(auto_now=True)
    rating = models.FloatField(max_length=10,default=0)

class classesDateTime(DbNormsShared):
    classesInfoField = models.ForeignKey("classesInfo",blank=False,null=False)
    timeinfo =  models.TimeField(blank=False,null=False)
    startdate =  models.DateField(blank=False,null=False)

class status(DbNormsShared):
    name = models.CharField(max_length=25,default="initial")

class demoClass(DbNormsShared):
    classesInfoField = models.ForeignKey("classesInfo",blank=False,null=False)
    userInfoField = models.ManyToManyField(userInfo)
    created_on = models.DateTimeField(auto_now=True)
    status = models.ForeignKey(status,blank=False,null=False)
    dataTimeField = models.ForeignKey(classesDateTime,blank=False,null=False)
    
class classesInfo(models.Model):
    displayName = models.CharField(max_length=52,default="",blank=False,null=False)
    amount = models.FloatField(max_length=52,default=0,blank=False,null=False)
    comments =  models.ManyToManyField(userComments)
    faq =  models.ManyToManyField(classFaq)
    catagory =  models.ForeignKey(class_catagory) # Programming

    def getAllClasses(self):
        return eval(self.__class__.__name__).objects.all()

    def getAllClassesNames(self):
        names = []
        for obj in eval(self.__class__.__name__).objects.all():
            names.append(obj.displayName)
        return names

    def getPopularClasses(self):
        return self.getAllClasses()

    def getSearchedClasses(self,searchNames):
        if searchNames == "":
            return self.getAllClasses()

        objs = []
        for searchName in re.split("\s*,\s*",searchNames):
            for obj in eval(self.__class__.__name__).objects.all():
                if searchName.lower() in obj.displayName.lower():
                    objs.append(obj)
        return objs

    def getClassInfo(self,existName):
        for obj in self:
            if obj.displayName == existName:
                return obj
        raise pageNotFound()

class messages(models.Model):
    name = models.CharField(max_length=1024,default="")
    is_unread = models.BooleanField(default=True,blank=False,null=False)
    sent_on = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(userInfo, related_name="sender",default="")

class userConversation(models.Model):
    friend1 = models.ForeignKey(userInfo, related_name="friend1",default="")
    friend2 = models.ForeignKey(userInfo, related_name="friend2",default="")
    messagesField =  models.ManyToManyField(messages)

    
    @staticmethod
    def arrangeFriends(friend1Obj,friend2Obj):
        dict = {}
        dict[friend1Obj.userid] = friend1Obj
        dict[friend2Obj.userid] = friend2Obj
        sortList = [friend1Obj.userid,friend2Obj.userid]
        sortList.sort()
        obj1 = dict[sortList[0]]
        obj2 = dict[sortList[1]]
        return obj1,obj2

    @staticmethod
    def getOrCreateUserConversationObj(friend1Obj,friend2Obj):
        obj1,obj2 = userConversation.arrangeFriends(friend1Obj,friend2Obj)
        try:
            return userConversation.objects.get(friend1=obj1,friend2=obj2)
        except userConversation.DoesNotExist:
            obj = userConversation.objects.create(friend1=obj1,friend2=obj2)
            obj.save()
            return obj 

    @staticmethod
    def getUserConversationObj(friend1Obj,friend2Obj):
        
        obj1,obj2 = userConversation.arrangeFriends(friend1Obj,friend2Obj)
        try:
            return userConversation.objects.get(friend1=obj1,friend2=obj2)
        except userConversation.DoesNotExist:
            return None
        
    @staticmethod
    def getAllFriendsMsg(loginObj):
        
        friend_msg = {}
        for friendObj in loginObj.friends.all():
            try:
                userConversationObj = userConversation.getUserConversationObj(friendObj,loginObj)
            except userConversation.DoesNotExist:
                userConversationObj = None
            if userConversationObj != None:
                msgObj = userConversationObj.getFriendNewMessage(friendObj)
                cnt = len(msgObj)
                if cnt > 0:
                    msg = msgObj.latest("sent_on")
                    date = naturaltime(msg.sent_on)
                    friend_msg[friendObj.userid]  = [cnt,msg.name,date]
        return friend_msg
    def getFriendNewMessage(self,friendObj):
        return self.messagesField.filter( Q(is_unread=True) & Q(sender=friendObj) ).order_by('-sent_on')
