from django.shortcuts import render
from django.views.generic import View
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from .utils import *
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template import TemplateDoesNotExist
from online_classes.models import classesInfo, emailInfo, userInfo, user_catagory, country, userComments, classesDateTime, demoClass, status, staticInfo, messages, userConversation, country, state, city, userProfileSettings
from . import forms
from urllib.parse import unquote, quote
from django.db.models import Q
from datetime import datetime
import os
import json

class BaseClass(View):

    def init(self,data):
        if self.getLoginObj(data) :
            self.getCartCount(data)
            self.getFriendsInfo(data)
            data['taskCount'] = len(data['loginObj'].democlassField.all())
        data['ERRORS'] = []
        data['defaultUserImage'] = os.path.join("online_classes/images/default.png")
        if 'ERROR' in data['request'].session.keys():
            data['ERRORS'].append(data['request'].session['ERROR'])
            del data['request'].session['ERROR']

    def getLoginObj(self,data):
        try:
            emailObj = emailInfo.objects.get(name=data['request'].session['emailId'])
            data['loginObj'] = userInfo.objects.get(email=emailObj.id)
            return True
        except :
            if 'emailId' in data['request'].session:
                del data['request'].session['emailId']
            data['loginObj'] = None
            return False

    def getCartCount(self,data):
        total_amount = 0
        data['cartCount'] = 0
        if data['loginObj'] != None:
            count = 0
            for classesInfoObj in data['loginObj'].cart.filter(userinfo=data['loginObj'].id):
                total_amount = total_amount + classesInfoObj.amount
                count = count+1
            data['cartCount'] = count
        data['cartSum'] = total_amount
        return "%s,%s" %(data['cartCount'],data['cartSum'])

    def getFriendsInfo(self,data):
        friendsObj = []
        lastMessageObj = []
        unreadMessageCount = []
        unreadAllMsgCount = 0
        for friendObj in data['loginObj'].friends.all():
            friendsObj.append(friendObj)
            conversationObj = userConversation.getUserConversationObj(friendObj,data['loginObj'])
            lastMessage = None
            messageCount  = 0
            if conversationObj != None:
                lastMessage = conversationObj.messagesField.latest('sent_on')
                messageCount = len(conversationObj.getFriendNewMessage(friendObj))
            lastMessageObj.append(lastMessage)
            unreadMessageCount.append(messageCount)
            unreadAllMsgCount  = unreadAllMsgCount + messageCount 
        data['friendsObj'] = friendsObj
        data['lastMessageObj'] = lastMessageObj
        data['unreadMessageCount'] = unreadMessageCount
        data['unreadAllMsgCount'] = unreadAllMsgCount

    def get(self, request, *args, **kwargs):
        return render(request, 'online_classes/index.html', {})

    def post(self, request, *args, **kwargs):
        return render(request, 'online_classes/index.html', {})
        
class AuthView(BaseClass):
    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        return HttpResponse(data.htmlprint())
        return render(request, 'online_classes/auth.html', {})

    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        return render(request, 'online_classes/auth.html', {})

class AdminView(BaseClass):

    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        if data['loginObj'] != None:
            return render(request, 'online_classes/user-profile.html', {'data':data})
        else:
            return HttpResponseRedirect(index)

    def post(self, request, *args, **kwargs):
        return render(request, 'online_classes/index.html', {})


class CheckoutView(BaseClass):
    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        return render(request, 'online_classes/'+request.META['PATH_INFO']+".html", {'data':data})
            #return render(request, 'online_classes/page-404.html', {})
    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        return HttpResponseRedirect("product")
    
class ConversationView(BaseClass):
    
    def unreadMsg(self,data):
        for obj in data['messageObj']:
            # if page user is not sender then not make unread false
            if obj.sender != data['loginObj'] and obj.is_unread:
                obj.is_unread=False
                obj.save()

    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        if 'state' in data.keys() and data['state'] == 'allFriendsNewMsg':
            return HttpResponse(json.dumps(userConversation.getAllFriendsMsg(data['loginObj'])))

        try:
            recieverObj = userInfo.objects.get(userid=data['reciever'])
        except userInfo.DoesNotExist:
            return HttpResponse("ERROR")

        conversationObj = userConversation.getUserConversationObj(data['loginObj'],recieverObj)
        if conversationObj  == None:
            return HttpResponse("")

        if 'state' in data.keys() and data['state'] == "lastMsg":
            data['messageObj'] = conversationObj.messagesField.filter(sender=data['loginObj']).order_by('-sent_on')[:1]
        elif 'state' in data.keys() and data['state'] == "newMsg":
            data['messageObj'] = conversationObj.getFriendNewMessage(recieverObj)
            if len(data['messageObj']) > 0 :
                self.unreadMsg(data)
            else:
                return HttpResponse("")
        else:
            data['messageObj'] = conversationObj.getFriendNewMessage(recieverObj)
            if len(data['messageObj']) > 0 :
                self.unreadMsg(data)
            data['messageObj'] = conversationObj.messagesField.all()

        if data['loginObj'] != None:
            return render(request, 'online_classes/'+data['page']+'.html', {'data':data})
        else:
            return HttpResponseRedirect("index")

    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        return HttpResponse(data.htmlprint())
        return HttpResponseRedirect(data['page'])

class MessagesView(BaseClass):
    
    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        if not data['loginObj'] :
            return HttpResponseRedirect("index")
        #data['loginObj'].makeFriend(userInfo.objects.get(userid="shiv1"))
        #data['loginObj'].makeFriend(userInfo.objects.get(userid="shiv2"))
        #data['loginObj'].makeFriend(userInfo.objects.get(userid="shikha"))

        unreadMessageCount, friendsObj, lastMessageObj = (list(x) for x in zip(*sorted(zip(data['unreadMessageCount'], data['friendsObj'], data['lastMessageObj']), key=lambda pair: pair[0])))
        data['friendsInfo'] = zip(reversed(unreadMessageCount), reversed(friendsObj), reversed(lastMessageObj))
        
        return render(request, 'online_classes/'+data['page']+'.html', {'data':data})

    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        try:
            recieverObj = userInfo.objects.get(userid=data['reciever'])
        except userInfo.DoesNotExist:
            return HttpResponse(data['reciever'])
            return HttpResponse("ERROR")

        message = data['message']
        messageObj = messages.objects.create(name=message,sender=data['loginObj'])
        messageObj.save()

        conversationObj = userConversation.getOrCreateUserConversationObj(data['loginObj'],recieverObj)
        conversationObj.messagesField.add(messageObj)
        conversationObj.save()
        return HttpResponse(data.print())
        return HttpResponseRedirect(data['page'])

class ProfileView(BaseClass):
    
    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)

        if data['loginObj'] != None:
            return render(request, 'online_classes/profile.html', {'data':data})
        else:
            return HttpResponse("ERROR")

    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        form = forms.profileSettings(data)
        dataError = {}
        fields = ['userid','firstname', 'lastname', 'gender', 'dateofbirth', 'countryField', 'stateField', 'cityField', 'phoneno']

        is_error = False

        for field in fields:
            dataError[field] = ""
            if field not in data.keys() or not re.search("\S+",data[field]) :
                dataError[field] = "This field is required."
                is_error = True
            elif re.search("countryField|stateField|cityField",field) and not re.search("^[a-zA-Z\s]+$",data[field]):
                dataError[field] = "This field is required."
                is_error = True
            elif field == 'userid' and data['loginObj'].userid != data['userid']:
                if not re.search("^[a-zA-Z0-9_]+$",data['userid']):
                    dataError['userid'] = "User Id contains extra symbol. Allowed values are letters, numbers and underscore"
                    is_error = True
                elif re.search("^_",data['userid']):
                    dataError['userid'] = "User Id should start from letters or numbers."
                    is_error = True
                else:
                    try:
                        obj = userInfo.objects.get(userid=data['userid'])
                        dataError['userid'] = "User ID already exists."
                        is_error = True
                    except userInfo.DoesNotExist:
                        pass
            elif field == 'dateofbirth':
                age = get_age(data['dateofbirth'])
                if not (age > 3 and age < 90):
                    is_error = True
                    dataError[field] = "Invalid date of birth."
            elif field == 'phoneno' and data['loginObj'].phoneno != data['phoneno'] and not re.search("^\+\d{9}\d+",data['phoneno']):
                dataError['phoneno'] = "Invalid Phone number."
                is_error = True


        if not is_error :
            personalInfoObj = data['loginObj'].personalInfo
            if  personalInfoObj == None or personalInfoObj == "" :
                personalInfoObj = userProfileSettings()
            data['loginObj'].userid = data['userid']
            data['loginObj'].phoneno = data['phoneno']
            personalInfoObj.firstname = (data['firstname']).title()
            personalInfoObj.lastname = (data['lastname']).title()
            personalInfoObj.gender = data['gender']
            personalInfoObj.dateofbirth = data['dateofbirth']
            personalInfoObj.countryField = country().update(data['countryField'])
            personalInfoObj.stateField = state().update(data['stateField'])
            personalInfoObj.cityField  = city().update((data['cityField']).title())
            personalInfoObj.save()
            data['loginObj'].personalInfo = personalInfoObj 
            data['loginObj'].save()
        return HttpResponse(json.dumps(dataError))

class UserProfileView(BaseClass):
    
    def userUploadPicture(self,data):
        form = forms.ProfileImage(data,data['request'].FILES)
        if not form.is_valid():
            data['request'].session['ERROR'] = form['image'].errors
        else:
            try:
                previous_image = data['loginObj'].image
                os.remove(previous_image.path)
            except:
                pass
            data['loginObj'].image = form.cleaned_data["image"]
            data['loginObj'].save()

    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)

        if data['loginObj'] != None:
            return render(request, 'online_classes/user-profile.html', {'data':data})
        else:
            return HttpResponseRedirect("index")

    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.getLoginObj(data)
        self.userUploadPicture(data)
        return HttpResponseRedirect(data['page'])

class UnixTerminalView(BaseClass):
    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        return render(request, 'online_classes/unix-terminal.html', {'data':data})
    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        return render(request, 'online_classes/unix-terminal.html', {'data':data})
class AddToCartView(BaseClass):

    def getAddToCart(self,data):
        if 'emailId' in data['request'].session.keys() and re.search("\S+",data['request'].session['emailId']):
            try:
                emailObj = emailInfo.objects.get(name=data['request'].session['emailId'])
                loginObj = userInfo.objects.get(email_id=emailObj.id)
                return loginObj.cart.filter(userinfo=loginObj.id)
            except:
                return None 

    def removeAddToCart(self,data):
        if 'emailId' in data['request'].session.keys() and re.search("\S+",data['request'].session['emailId']):
            try:
                emailObj = emailInfo.objects.get(name=data['request'].session['emailId'])
                loginObj = userInfo.objects.get(email_id=emailObj.id)
                if 'prdId' in data.keys() and re.search("\S+",data['prdId']):
                    classesInfoObj = classesInfo.objects.get(id=data['prdId'])
                    loginObj.cart.remove(classesInfoObj)
                else:
                    for addToCartObj in loginObj.cart.all():
                        loginObj.cart.remove(addToCartObj)
                loginObj.save()
            except userInfo.DoesNotExist:
                pass

    def setAddToCart(self,data):
        if 'emailId' in data['request'].session.keys() and re.search("\S+",data['request'].session['emailId']):
            try:
                emailObj = emailInfo.objects.get(name=data['request'].session['emailId'])
                loginObj = userInfo.objects.get(email_id=emailObj.id)
                if 'prdId' in data.keys():
                    classesInfoObj = classesInfo.objects.get(id=data['prdId'])
                    loginObj.cart.add(classesInfoObj)
                    loginObj.save()
            except userInfo.DoesNotExist:
                pass

    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.getLoginObj(data)
        if 'state' in data.keys():
            if data['state'] == "remove":
                self.removeAddToCart(data)
            elif data['state'] == "add":
                self.setAddToCart(data)

        return HttpResponse(self.getCartCount(data))

    def post(self, request, *args, **kwargs):
        return render(request, 'online_classes/index.html', {})

class ProfileImageView(BaseClass):
    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        return render(request, 'online_classes/image.html', {'data':data})
    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.getLoginObj(data)
        form = forms.ProfileImage(data,data['request'].FILES)
        dataError = {}
        if not form.is_valid():
            dataError['ErrorId'] = form['image'].errors
        else:
            try:
                previous_image = data['loginObj'].image
                os.remove(previous_image.path)
            except:
                pass
            data['loginObj'].image = form.cleaned_data["image"]
            data['loginObj'].save()
        return render(request, 'online_classes/image.html', {'data':data})
      
class LoginView(BaseClass):
    def returnData(self,dataError,data):
        value = ""
        for id in dataError.keys():
            value = "%s\n%s%s:%s" %(value,data['state'],id,dataError[id]) 
        return value

    def userUploadPicture(self,data):
        #return HttpResponse(data['request'].FILES)
        form = forms.ProfileImage(data,'image')
        dataError = {}
        if not form.is_valid():
            dataError['ErrorId'] = form['image'].errors
        else:
            try:
                previous_image = data['loginObj'].image
                os.remove(previous_image.path)
            except:
                pass
            data['loginObj'].image = form.cleaned_data["image"]
            data['loginObj'].save()
        return 
        return (self.returnData(dataError,data))
        
    def userRegister(self,data):

        form1 = forms.EmailValidateForm(data)
        form2 = forms.LoginForm(data)
        dataError = {}
        dataError['EmailErrorId'] = ""
        dataError['PwdErrorId'] = ""
        dataError['PhNoErrorId'] = ""
        dataError['UsrnameErrorId'] = ""

        if not form1.is_valid() or not form2.is_valid() or ('userid' in data.keys() and not re.search("\S+",data['userid'])) :
            if 'userid' in data.keys() :
                if not re.search("\S+",data['userid']):
                    dataError['UsrnameErrorId'] = "This field is required."
                elif not re.search("^[a-zA-Z0-9_]+$",data['userid']):
                    dataError['UsrnameErrorId'] = "User Id contains extra symbol. Allowed values are letters, numbers and underscore"
                elif re.search("^[_",data['userid']):
                    dataError['UsrnameErrorId'] = "User Id should start from letters or numbers."
            if 'phno' in data.keys() and not re.search("^\+\d{9}\d+",data['phno']):
                dataError['PhNoErrorId'] = "Invalid Phone number."
            dataError['EmailErrorId'] = form1['name'].errors
            dataError['PwdErrorId'] = form2['password'].errors
            return HttpResponse(self.returnData(dataError,data))

        emailObj = emailInfo().update(data['name'])
        try:
            obj = userInfo.objects.get(email_id=emailObj.id)
            dataError['EmailErrorId'] = "E-mail id already exists"
            return HttpResponse("HERE1")
            return (self.returnData(dataError,data))
        except:
            emailObj.save()
            obj = userInfo()
            obj.userid=data['userid']
            obj.phoneno = data['phno']
            obj.email=emailObj
            obj.password=data['password']
            obj.last_login = timezone.now()
            obj.catagory= user_catagory().update("student")
            #obj.country= country().update("India")
            obj.save()
        
        return (self.returnData(dataError,data))

    def userLogin(self,data):

        form1 = forms.EmailValidateForm(data)
        form2 = forms.LoginForm(data)
        dataError = {}
        dataError['EmailErrorId'] = ""
        dataError['PwdErrorId'] = ""

        if not form1.is_valid() or not form2.is_valid() :
            dataError['EmailErrorId'] = form1['name'].errors
            dataError['PwdErrorId'] = form2['password'].errors
            return HttpResponse(self.returnData(dataError,data))

        emailObj = None
        try:
            # here data['name'] is emailID 
            emailObj = emailInfo.objects.get(name=data['name'])
        except emailInfo.DoesNotExist:
            dataError['EmailErrorId'] = "E-mail id or password doesn't exist"
            return (self.returnData(dataError,data))
        
        try:
            obj = userInfo.objects.get(email_id=emailObj.id,password=data['password'])
        except userInfo.DoesNotExist:
            dataError['EmailErrorId'] = "E-mail id or password doesn't exist"
            return (self.returnData(dataError,data))

        data['request'].session['emailId'] = data['name']
        if data['rememberMe'] == "false": 
            data['request'].session.set_expiry(0)
        
        return (self.returnData(dataError,data))

    def userForgetPassword(self,data):

        form1 = forms.EmailValidateForm(data)
        dataError = {}
        dataError['EmailErrorId'] = ""

        if not form1.is_valid() :
            dataError['EmailErrorId'] = form1['name'].errors
            return HttpResponse(self.returnData(dataError,data))

        emailObj = None
        try:
            # here data['name'] is emailID 
            emailObj = emailInfo.objects.get(name=data['name'])
        except:
            dataError['EmailErrorId'] = "E-mail id doesn't exist"
        
        return (self.returnData(dataError,data))

    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.getLoginObj(data)
        if 'redirect' in data.keys() and 'clear' in data.keys():
            del request.session['emailId']
        return HttpResponseRedirect(data['redirect'])
    
    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        if 'email' in data.keys():
            data['name'] = data['email']
        if not 'state' in data.keys():
            return HttpResponse("ERROR")

        if data['state'] == "login":
            return HttpResponse(self.userLogin(data))
        elif data['state'] == "register":
            return HttpResponse(self.userRegister(data))
        elif data['state'] == "forgetPwd":
            return HttpResponse(self.userForgetPassword(data))
        elif data['state'] == "uploadImage" and self.getLoginObj(data):
            return HttpResponse(self.userUploadPicture(data))
        else:
            return HttpResponse("ERROR")

class MainView(BaseClass):

    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)

        #if data['loginObj'] != None:
        #    return HttpResponseRedirect("product")
        #else:
        #    return render(request, 'online_classes/index.html', {'data':data})

        data['popularClasses'] = classesInfo.objects.all()
        return render(request, 'online_classes/index.html', {'data':data})

    def post(self, request, *args, **kwargs):
        return render(request, 'online_classes/index.html', {})

class AllProductsView(BaseClass):

    def extended_init(self,data):
        data['minAmount'] = 0
        data['maxAmount'] = 10000
        data['lowRange'] = 3000
        data['highRange'] =9000
        self.init(data)

    def getRange(self,data):
        data['range'] = unquote(data['range'])
        m = re.search("(\S+)\s*-\s*(\S+)",data['range'])
        if m:
            data['lowRange'] = m.group(1)
            data['highRange'] = m.group(2)
    
    def get(self, request, *args, **kwargs):

        data = get_form_data(request)
        self.extended_init(data)

        if not 'searchItem' in data.keys() or data['searchItem'] == None:
            data['searchItem'] = ""

        data['classesNames'] = classesInfo().getAllClassesNames()

        if 'range' in data.keys() and data['range'] != None:
            self.getRange(data)

        data['classesInfoObj'] = classesInfo.objects.all()

        """
        if 'search' in data.keys() and data['search'] != "":
            data['search'] = unquote(data['search'])
            data['classesInfoObj'] = classesInfo.objects.filter( Q(displayName__icontains=data['search']) & Q(amount__gte=data['lowRange'])  & Q(amount__lte=data['highRange']) )
        else:
            data['classesInfoObj'] = classesInfo.objects.filter( Q(amount__gte=data['lowRange'])  & Q(amount__lte=data['highRange']) )
        """
        return render(request, 'online_classes/product.html', {'data':data})

    def post(self, request, *args, **kwargs):
        data = get_form_data(request)

        query = "%s?" %(data['page'])
        if 'searchItem' in data.keys() and re.search("\S+",data['searchItem']):
            data['searchItem'] = quote(data['searchItem'])
            query = "%s&search=%s" %(query,quote(data['searchItem']))
        
        if 'range' in data.keys() and re.search("\S+",data['range']):
            query = "%s&range=%s" %(query,data['range'])

        return HttpResponseRedirect(query)

class CommentsView(BaseClass):

    def get(self, request, *args, **kwargs):
        return HttpResponse("ERROR")

    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        if 'prdId' in data.keys() and re.search("\S+",data['prdId']):
            classesInfoObj = classesInfo.objects.get(id=data['prdId'])
            try:
                commentsObj = classesInfoObj.comments.get(name=data['comments'],userInfoid=data['loginObj'],rating=data['rating'])
            except userComments.DoesNotExist:
                commentsObj = userComments.objects.create(name=data['comments'],userInfoid=data['loginObj'],rating=data['rating'])
                commentsObj.save()
                classesInfoObj.comments.add(commentsObj)
                classesInfoObj.comments.save()
            return HttpResponse("OK")
        else:
            return HttpResponse("ERROR")
    
class DemoClassView(BaseClass):
    
    def get(self, request, *args, **kwargs):

        data = get_form_data(request)
        self.getLoginObj(data)
        classesInfoObj = classesInfo.objects.get(id=data['prdId'])
        if 'dt' in data.keys():
            startdate = datetime.strptime(data['dt'], '%m%d%Y').date()
        if 'tm' in data.keys():
            timeinfo = datetime.strptime(data['tm'], '%H%M%S').time()

        try:
            classesDateTimeObj = classesDateTime.objects.get(startdate=startdate,timeinfo=timeinfo,classesInfoField=classesInfoObj)
        except classesDateTime.DoesNotExist:
            return HttpResponse("ERROR")
            
        for obj in demoClass.objects.filter(classesInfoField = classesInfoObj):
            if data['loginObj'] in obj.userInfoField.all():
                obj.userInfoField.remove(data['loginObj'])
            if obj in data['loginObj'].democlassField.all():
                data['loginObj'].democlassField.remove(obj)

        try:
            democlassObj = demoClass.objects.get(classesInfoField = classesInfoObj,dataTimeField=classesDateTimeObj)

        except demoClass.DoesNotExist:
            statusObj = status().update("initial")
            democlassObj = demoClass.objects.create(classesInfoField = classesInfoObj,dataTimeField=classesDateTimeObj,status=statusObj)
            democlassObj.save()

        democlassObj.userInfoField.add(data['loginObj'])
        data['loginObj'].democlassField.add(democlassObj)
        data['loginObj'].save()
        return HttpResponse("OK")


    def post(self, request, *args, **kwargs):
        return HttpResponse("GET")
        return HttpResponseRedirect(query)

class ImageView(BaseClass):
    def get(self, request, *args, **kwargs):
        from PIL import Image, ImageDraw

        size = (100,50)             # size of the image to create
        im = Image.new('RGB', size) # create the image
        draw = ImageDraw.Draw(im)   # create a drawing object that is
                                    # used to draw on the new image
        red = (255,0,0)    # color of our text
        text_pos = (10,10) # top-left position of our text
        text = "Hello World!" # text to draw
        # Now, we'll do the drawing: 
        draw.text(text_pos, text, fill=red)
        
        del draw # I'm done drawing so I don't need this anymore
        
        # We need an HttpResponse object with the correct mimetype
        response = HttpResponse(mimetype="image/png")
        # now, we tell the image to save as a PNG to the 
        # provided file-like object
        im.save(response, 'PNG')

        return response # and we're done!

class SingleProductView(BaseClass):

    def getOverallRating(self,data):
        
        totCount = 0
        totRating = 0
        ratingDict = {}
        for obj in data['commentsObj']:
            ratingNum = obj.rating
            totCount = totCount + 1
            totRating = totRating + ratingNum
            if not obj.rating in ratingDict.keys():
                ratingDict[ratingNum] = 1
            else:
                ratingDict[ratingNum] = ratingDict[ratingNum] + 1

        averageRatingNum = 0
        if totCount != 0:
            averageRatingNum = round(totRating/totCount,1)

        ratingBreakdown = []
        for cnt,state in zip([5,4,3,2,1],['success','primary','info','warning','danger']):
            percent = 20*cnt
            ratingCnt = 0
            if cnt in ratingDict.keys():
                ratingCnt = ratingDict[cnt]
            ratingBreakdown.append([cnt,ratingCnt,percent,state])
        data['ratingBreakdown'] = ratingBreakdown
        data['averageRating'] = [1,2,3,4,5]
        data['averageRatingNum'] = averageRatingNum

    def getDemoClassInfo(self,data):

        remainingStudent = []
        studentRegistered = []
        classdatetimeObjList = []
        demoClassObjList = []
        for classdatetimeObj in classesDateTime.objects.filter(classesInfoField=data['classesInfoObj']).order_by('startdate','timeinfo'):
            registered = 0
            try:
                demoClassObj = demoClass.objects.get(classesInfoField=data['classesInfoObj'],dataTimeField=classdatetimeObj)
                registered = len(demoClassObj.userInfoField.all())
            except demoClass.DoesNotExist:
                demoClassObj = None
            remaining = staticInfo.max_student - registered
            demoClassObjList.append(demoClassObj)
            remainingStudent.append(remaining)
            classdatetimeObjList.append(classdatetimeObj)
        
        data['classdatetimeObj'] = zip(classdatetimeObjList,demoClassObjList,remainingStudent)

    def get(self, request, *args, **kwargs):
        data = get_form_data(request)
        self.init(data)
        data['classesInfoObj'] = classesInfo.objects.get(id=data['n'])
        self.getDemoClassInfo(data)
        data['commentsObj'] = data['classesInfoObj'].comments.order_by('id').reverse()
        self.getOverallRating(data)
        return render(request, 'online_classes/'+request.META['PATH_INFO']+".html", {'data':data})

    def post(self, request, *args, **kwargs):
        return render(request, 'online_classes/index.html', {})


class StaticPageView(BaseClass):
    def get(self, request, *args, **kwargs):

        data = get_form_data(request)
        self.init(data)


        try:
            return render(request, 'online_classes/'+request.META['PATH_INFO']+".html", {'data':data})
        except:
            return HttpResponseRedirect("404-page")
    def post(self, request, *args, **kwargs):
        data = get_form_data(request)
        classesInfoObj = classesInfoObj.getAllClassesName()
        return HttpResponseRedirect("product")
