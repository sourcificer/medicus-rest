from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status

from .serializers import UserSerializer
from .models import User

# Okay ! So hear me out on this one. After a discussion about this, with champa
# "we" concluded that the entire workflow of this application will be based
# on REST ful services, but since the guidelines for developing a RESTfull
# service are a bit shaky, we will be utilizing both tokens as well as a
# cookie based workflow. During Sign up and Login process the backend will be
# responsible for setting and deleting cookies with the respective `auth_token`
# on the client side. The same `auth_tokens` will also be sent with the
# response body in JSON format.
#
# Although doing so will break the consistency of this RESTful service since,
# now this service cannot be consumed by any application which does not
# implement a cookie interface. So we will work on an assumption that this,
# API will only be consumed by a web based application rendering the entire
# RESTfull service kinda useless.
# Man ! that's depressing. :-(


class UserModelViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            auth_token = response.data['auth_token']
            response.set_cookie(key='auth_token', value=auth_token)
        return response


class UserLogin(TokenCreateView):

    def post(self, request, **kwargs):
        response = super().post(request, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            auth_token = response.data['auth_token']
            response.set_cookie(key='auth_token', value=auth_token)
        return response


class UserLogout(TokenDestroyView):

    def post(self, request, **kwargs):
        response = super().post(request, **kwargs)
        # This is expected behaviour
        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.delete_cookie(key='auth_token')
        return response


@api_view(['POST'])
def check_user_logged_in(request):
    # The only way to verify whether a user is logged in, is to verify
    # whether the user instance have a corresponding token instance
    # associated with it. The presence of `token` instance means that
    # the user is logged in, and to logout user just delete the `user.token`

    # NOTE: The djoser backend implements a default tokenAuthentication which
    # can be found in settings, because of which this function cannot be used
    # anyone without `auth_token` making half of this function useless.
    # probably remove the useless part later during the development.
    auth_token = request.data.get('auth_token', None)
    if auth_token is None:
        return Response({
            'error': '`auth_token` not provided !'
        }, status=status.HTTP_400_BAD_REQUEST, content_type='json')

    is_logged_in = Token.objects.filter(key=auth_token).exists()

    if is_logged_in:
        login_status = status.HTTP_200_OK
    else:
        login_status = status.HTTP_401_UNAUTHORIZED

    return Response({
        'logged_in': is_logged_in
    }, status=login_status, content_type='json')
