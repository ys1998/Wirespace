# Middleware to authenticate token and expire keys
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from .models import *

CHECK_LIST = [
	'/share/open/',
	'/share/upload/',
	'/share/download/',
	'/share/delete/',
	'/share/create_folder/',
	'/share/search/',
]

class AuthenticateTokenMiddleware(MiddlewareMixin):
	def process_request(self,request):
		global CHECK_LIST
		if request.get_full_path() in CHECK_LIST:
			if request.method == "POST":
				if 'token' not in request.session:
					return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
				elif Token.objects.filter(token=request.session['token']).count()==0:
					return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
				else:
					return None
			else:
				return JsonResponse({'status':'false','message':"Invalid request format."}, status=404)
		else:
			return None