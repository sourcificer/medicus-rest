from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from .models import Address

from organization.models import Organization
from medical_staff.models import MedicalStaff

User = get_user_model()


class UserSignupTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.second_client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.signup_url = reverse("user-list")
        self.org_name = 'Avenger'
        self.data = {
            'email': 'email.email1@gmail.com',
            'password': 'shititit',
            'user_type': 'OR',
            'contact_detail': 'some@email.com',
            'organization': {
                'name': 'Avenger',
                'description': 'I am Iron Man !',
            },
            'address': {
                'address': 'Some Address or Shit',
                'pincode': '39458',
                'country': 'US',
            },
            'medical_staff': {
                'name': 'John Doe',
                'organization': 'Avenger',
                'role': 'something something',
                'speciality': 'jack squat',
            }
        }

    def get_user(self):
        return User.objects.get(email=self.data['email'])

    def is_user_created(self):
        return User.objects.filter(
            email=self.data['email'], organization__isnull=False
        ).exists()

    def is_organization_created(self):
        return Organization.objects.filter(
            name=self.org_name
        ).exists()

    def create_organization(self):
        return Organization.objects.create(
            **self.data['organization']
        )

    def create_user(self):
        data = dict(self.data)
        data['address'] = Address.objects.create(**data['address'])
        return User.objects.create_user(**data)

    def test_user_signup_without_medical_or_organization(self):
        data = dict(self.data)
        data.pop('organization')
        data.pop('medical_staff')
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEquals(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )

    def test_user_signup_with_medical_or_organization(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEquals(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )

class OrganizationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.second_client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.signup_url = reverse("user-list")
        self.org_url = reverse('organization')
        self.org_name = 'Avenger'
        self.data = {
            'email': 'email.email1@gmail.com',
            'password': 'shititit',
            'user_type': 'OR',
            'contact_detail': 'some@email.com',
            'address': {
                'address': 'Some Address or Shit',
                'pincode': '39458',
                'country': 'US',
            },
            'organization': {
                'name': 'Avenger',
                'description': 'I am Iron Man !',
            }
        }

    def get_user(self):
        return User.objects.get(email=self.data['email'])

    def is_user_created(self):
        return User.objects.filter(email=self.data['email']).exists()

    def is_organization_created(self):
        return Organization.objects.filter(
            name=self.org_name
        ).exists()

    def create_user(self):
        data = dict(self.data)
        data['address'] = Address.objects.create(**data['address'])
        data['organization'] = Organization.objects.create(
            **data['organization']
        )
        return User.objects.create_user(**data)

    def test_organization_signup_with_incorrect_fields(self):
        data = {'title': 'new idea'}
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_organization_response_fields_valid(self):
        response = self.client.post(self.signup_url, self.data, format='json')

        for key in self.data.keys():
            if key not in response.data:
                self.assertEquals(
                    response.status_code, status.HTTP_400_BAD_REQUEST, response.data
                )

    def test_organization_valid_signup(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEquals(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        user = self.get_user()
        self.assertTrue(user.is_authenticated and user.is_active)
        self.assertEqual(user.organization.name, self.org_name)
        self.assertTrue(self.is_organization_created())

    def test_organization_signup_without_address(self):
        data = dict(self.data)
        data.pop('address')  # removed address
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())

    def test_organization_signup_without_organization(self):
        data = dict(self.data)
        data.pop('organization')  # removed organization
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())

    def test_signup_existing_user(self):
        self.create_user()
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_logged_in_user(self):
        self.create_user()
        is_logged_in = self.client.login(
            username=self.data['email'], password=self.data['password']
        )
        self.assertTrue(is_logged_in)
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_set_cookie(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cookie_dict = response.client.cookies
        self.assertTrue(cookie_dict['auth_token'])

    def test_signup_authtoken_creation(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['auth_token'])

    def test_signup_authtoken_creation_invalid(self):
        data = dict(self.data)
        data['address'].pop('address')  # invalid address format
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        token = Token.objects.filter(user__email=data['email'])
        self.assertFalse(len(token))

    def test_get_unauthorized_url_after_signup(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.second_client.get(response.data['url'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_organization_creation_invalid_signup(self):
        # missing `user_type` field
        data = dict(self.data)
        data.pop('user_type')
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())
        self.assertFalse(self.is_organization_created())

    def test_user_creation_invalid_organization(self):
        # missing `name` field from organization
        data = dict(self.data)
        data['organization'].pop('name')
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())
        self.assertFalse(self.is_organization_created())

    def test_organization_exist_login(self):
        self.create_user()
        self.client.login(
            username=self.data['email'], password=self.data['password']
        )
        user = self.get_user()
        self.assertEqual(
            user.organization.name, self.data['organization']['name']
        )

    def test_organization_creation_existing_organization(self):
        self.create_user()
        data = dict(self.data)
        data['email'] = 'some.other_email@email.com'
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_organization_list(self):
        org = Organization.objects.bulk_create([
            Organization(
                name=self.org_name + str(i),
                description='Same Description')
            for i in range(5)
        ])
        response = self.client.get(self.org_url)
        self.assertEqual(len(response.data), len(org))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserLoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.data = {
            'email': 'email.email1@gmail.com',
            'password': 'helloworld123',
            'user_type': 'OR',
            'contact_detail': 'some@email.com',
            'address': {
                'address': 'Some address',
                'pincode': '39458',
                'country': 'US',
            },
            'organization': {
                'name': 'Avenger',
                'description': 'I am Iron Man !',
            }
        }
        self.login_data = {
            'email': 'email.email1@gmail.com',
            'password': 'helloworld123'
        }
        self.user = self.create_user()

    def get_user(self):
        return User.objects.get(email=self.data['email'])

    def create_user(self):
        data = dict(self.data)
        data['address'] = Address.objects.create(**data['address'])
        data['organization'] = Organization.objects.create(
            **data['organization']
        )
        return User.objects.create_user(**data)

    def test_login_user(self):
        response = self.client.post(
            self.login_url, self.login_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['auth_token'])
        user = self.get_user()
        self.assertTrue(user.is_authenticated and user.is_active)

    def test_login_already_logged_in_user(self):
        # If user is already logged in, the same access token will be
        # be returned to the front end
        first_response = self.client.post(
            self.login_url, self.login_data, format='json'
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        second_response = self.client.post(
            self.login_url, self.login_data, format='json'
        )
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(first_response.data, second_response.data)

    def test_login_with_wrong_credentials(self):
        data = {
            'email': 'email.email1@gmail.com',
            'password': 'wrong password',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cookie_after_login(self):
        response = self.client.post(
            self.login_url, self.login_data, format='json'
        )
        cookie_dict = response.client.cookies
        self.assertTrue(cookie_dict['auth_token'])


class UserLogoutTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse("user-list")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.data = {
            'email': 'email.email1@gmail.com',
            'password': 'helloworld123',
            'user_type': 'OR',
            'contact_detail': 'some@email.com',
            'address': {
                'address': 'Some address',
                'pincode': '39458',
                'country': 'US',
            },
            'organization': {
                'name': 'Avenger',
                'description': 'I am Iron Man !',
            }
        }
        self.login_data = {
            'email': 'email.email1@gmail.com',
            'password': 'helloworld123'
        }

    def create_user(self):
        data = dict(self.data)
        data['address'] = Address.objects.create(**data['address'])
        data['organization'] = Organization.objects.create(
            **data['organization']
        )
        return User.objects.create_user(**data)

    def test_logout_user_after_signup(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + response.data['auth_token']
        )
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_token_deleted_after_user_logout(self):
        user = self.create_user()
        response = self.client.post(self.login_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + response.data['auth_token']
        )
        response = self.client.post(self.logout_url)
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_cookie_after_logout(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + response.data['auth_token']
        )
        response = self.client.post(self.logout_url)
        cookie_header = response.client.cookies['auth_token'].output()
        self.assertIn("expires=Thu, 01 Jan 1970 00:00:00 GMT;", cookie_header)


class UserCheckLoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.signup_url = reverse('user-list')
        self.check_url = reverse('check_login')
        self.login_data = {
            'email': 'email.email1@gmail.com',
            'password': 'shititit',
        }
        self.data = {
            'email': 'email.email1@gmail.com',
            'password': 'helloworld123',
            'user_type': 'OR',
            'contact_detail': 'some@email.com',
            'address': {
                'address': 'Some address',
                'pincode': '39458',
                'country': 'US',
            },
            'organization': {
                'name': 'Avenger',
                'description': 'I am Iron Man !',
            }
        }
        self.check_data = {
            'auth_token': '',
        }

    def create_user(self):
        data = dict(self.data)
        data['address'] = Address.objects.create(**data['address'])
        data['organization'] = Organization.objects.create(
            **data['organization']
        )
        return User.objects.create_user(**data)

    def signup_user(self):
        return self.client.post(self.signup_url, self.data, format='json')

    def login_user(self, create_user=False):
        if create_user:
            self.create_user()
        return self.client.post(self.login_url, self.data, format='json')

    def logout_user(self, auth_token):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + auth_token
        )
        return self.client.post(self.logout_url)

    def test_check_user_after_login(self):
        response = self.login_user(create_user=True)
        self.check_data['auth_token'] = response.data['auth_token']
        response = self.client.post(
            self.check_url, self.check_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['logged_in'])

    def check_user_after_signup(self):
        response = self.signup_user()
        self.check_data['auth_token'] = response.data['auth_token']
        response = self.client.post(
            self.check_url, self.check_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['logged_in'])

    def test_check_user_after_logout(self):
        response = self.login_user(create_user=True)
        auth_token = response.data['auth_token']
        self.check_data['auth_token'] = auth_token
        self.logout_user(auth_token=auth_token)
        response = self.client.post(
            self.check_url, self.check_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MedicalStaffTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.second_client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.signup_url = reverse("user-list")
        self.org_name = 'Avenger'
        self.med_staff_name = 'John Doe'
        self.org_data = {
            'name': 'Avenger',
            'description': 'I am Iron Man !',
        }
        self.data = {
            'email': 'email.email1@gmail.com',
            'password': 'shititit',
            'user_type': 'OR',
            'contact_detail': 'some@email.com',
            'address': {
                'address': 'Some Address or Shit',
                'pincode': '39458',
                'country': 'US',
            },
            'medical_staff': {
                'name': 'John Doe',
                'organization': 'Avenger',
                'role': 'something something',
                'speciality': 'jack squat',
            }
        }

    def get_user(self):
        return User.objects.get(email=self.data['email'])

    def is_user_created(self):
        return User.objects.filter(email=self.data['email']).exists()

    def is_organization_created(self):
        return Organization.objects.filter(
            name=self.org_name
        ).exists()

    def is_medical_staff_created(self):
        return MedicalStaff.objects.filter(
            name=self.med_staff_name
        ).exists()

    def create_organization(self):
        return Organization.objects.create(**self.org_data)

    def create_user(self):
        data = dict(self.data)
        data['address'] = Address.objects.create(**data['address'])
        org = self.create_organization()
        data['medical_staff'].update({'organization': org})
        data['medical_staff'] = MedicalStaff.objects.create(
            **data['medical_staff']
        )
        return User.objects.create_user(**data)

    def test_is_medical_staff_created(self):
        self.create_user()
        self.assertTrue(self.is_medical_staff_created())
        self.assertTrue(User.objects.filter(
            medical_staff__name=self.med_staff_name
        ).exists())

    def test_medical_staff_response_fields_valid(self):
        response = self.client.post(self.signup_url, self.data, format='json')

        for key in self.data.keys():
            if key not in response.data:
                self.assertEquals(
                    response.status_code, status.HTTP_400_BAD_REQUEST, response.data
                )

    def test_medical_staff_valid_signup(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEquals(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        user = self.get_user()
        self.assertTrue(user.is_authenticated and user.is_active)
        self.assertEqual(
            user.medical_staff.organization.name, self.org_name
        )
        self.assertTrue(self.is_organization_created())

    def test_medical_staff_creation_invalid_signup(self):
        # missing `user_type` field
        data = dict(self.data)
        data.pop('user_type')
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())
        self.assertFalse(self.is_medical_staff_created())

    def test_medical_staff_signup_with_incorrect_fields(self):
        data = {'title': 'new idea'}
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_medical_staff_signup_without_required_fields(self):
        data = dict(self.data)
        data['medical_staff'].pop('name')  # `medical_staff.name` missing
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())
        self.assertFalse(self.is_medical_staff_created())

    def test_medical_staff_signup_without_medical_staff(self):
        data = dict(self.data)
        data.pop('medical_staff')  # removed medical_staff
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())

    def test_medical_staff_signup_without_address(self):
        data = dict(self.data)
        data.pop('address')  # removed address
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())

    def test_medical_staff_exist_login(self):
        self.create_user()
        self.client.login(
            username=self.data['email'], password=self.data['password']
        )
        user = self.get_user()
        self.assertEqual(
            user.medical_staff.name, self.data['medical_staff']['name']
        )

    def test_medical_staff_creation_existing_medical_staff(self):
        # JSON SERIALIZER ERROR HERE
        self.create_user()
        data = dict(self.data)
        data['email'] = 'some.other_email@email.com'
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_existing_user(self):
        # JSON SERIALIZER ERROR HERE
        data = dict(self.data)
        self.create_user()
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_logged_in_user(self):
        self.create_user()
        is_logged_in = self.client.login(
            username=self.data['email'], password=self.data['password']
        )
        self.assertTrue(is_logged_in)

    def test_signup_invalid(self):
        data = dict(self.data)
        data['address'].pop('pincode')  # removed pincode from address
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.is_user_created())

    def test_signup_set_cookie(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cookie_dict = response.client.cookies
        self.assertTrue(cookie_dict['auth_token'])

    def test_get_unauthorized_url_after_signup(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.second_client.get(response.data['url'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signup_authtoken_creation(self):
        response = self.client.post(self.signup_url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['auth_token'])

    def test_signup_authtoken_creation_invalid(self):
        data = dict(self.data)
        data['address'].pop('address')  # invalid address format
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        token = Token.objects.filter(user__email=data['email'])
        self.assertFalse(len(token))

