## @file middleware.py
#
# This file contains the description middleware used to authenticate token and expire keys
from django.http import HttpResponse,JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import *
import re

## List of all paths for which the request has to be validated
CHECK_LIST = [
	'/share/',
	'/share/open/',
	'/share/upload/',
	'/share/uploadFolder/',
	'/share/download/',
	'/share/delete/',
	'/share/create_folder/',
	'/share/search/',
	'/share/move/',
]

## List of paths for which the POST requests have to be ignored during validation
POST_IGNORE_LIST = [
	'/share/',
]

## Regex for host/
re_host=re.compile('/host[/]?.*')
## Regex for editor/ 
re_editor=re.compile('/editor[/]?.*')
## Regex to match authentication keys
#re_key=re.compile('/[0-9a-f]{16}[/]?$')
re_key=re.compile('/auth/[0-9a-z]+[/]?$')

## @brief Middleware class to handle token authentication
class AuthenticateTokenMiddleware(MiddlewareMixin):
	## @brief Function to check whether the request contains a valid token or not
	#
	# Only those requests which are specified in CHECK_LIST are validated.
	# @param self An instance of AuthenticateTokenMiddleware class
	# @param request An HttpRequest object containing required metadata
	# @returns None if no error occurs, a JsonResponse describing the error otherwise
	def process_request(self,request):
		global CHECK_LIST
		if request.get_full_path() in CHECK_LIST:
			if request.method == "POST":
				if 'token' not in request.session:
					return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
				elif Token.objects.filter(token=request.session['token']).count()==0:
					return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
				else:
					print("Valid request.")
					return None
			else:
				if request.get_full_path() in POST_IGNORE_LIST:
					print("Valid request.")
					return None
				else:
					return JsonResponse({'status':'false','message':"Invalid request format."}, status=404)
		else:
			path=request.get_full_path()
			if re_host.match(path) is None and re_key.match(path) is None and re_editor.match(path) is None:
				return JsonResponse({'status':'false','message':"Invalid request to {0}.".format(request.get_full_path())}, status=404)
			else:
				return None

## @brief Middleware class to handle expiration of keys
class ExpireKeyMiddleware(MiddlewareMixin):
	## @brief Function to check whether the key associated with the token in the request is still valid or not
	#
	# If the key is found to be expired, it is deleted alongwith all the associated tokens and session objects.
	# @param self An instance of ExpireKeyMiddleware class
	# @param request An HttpRequest object containing required metadata
	# @returns None if no error occurs, a JsonResponse describing the error otherwise
	def process_request(self,request):
		if request.get_full_path() in CHECK_LIST and request.get_full_path()!='/share/':
			# Since this will be called AFTER AuthenticateTokenMiddleware, token verification is already done
			# Assuming here that valid token exists - corresponding key may have expired
			t_Object=Token.objects.get(token=request.session['token'])
			k_Object=t_Object.link
			if timezone.localtime(timezone.now())>timezone.localtime(k_Object.expires_on):
				# Delete all associated sessions
				for s_Object in Session.objects.all():
					s_data=s_Object.get_decoded()
					try:
						temp_t=Token.objects.get(token=s_data['token'])
						if temp_t.link.key==k_Object.key:
							s_Object.delete()
					except:
						s_Object.delete()
				
				# Delete key and all associated tokens
				Key.objects.get(key=k_Object.key).delete()
				return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
			else:
				return None
		else:
			return None
