""" Module for the Routing System """
import cgi
import importlib
import re
from pydoc import locate

from config import middleware


class Route():
    """ Loads the environ """

    def __init__(self, environ=None):
        self.url_list = []

        if environ:
            self.environ = environ
            self.url = environ['PATH_INFO']


            if self.is_post():
                self.environ['QUERY_STRING'] = self.set_post_params()

    def load_environ(self, environ):
        self.environ = environ
        self.url = environ['PATH_INFO']

        if self.is_post():
            self.environ['QUERY_STRING'] = self.set_post_params()

        return self

    def get(self, route, output=None):
        """ Returns the output """
        return output

    def set_post_params(self):
        """ If the route is a Post, swap the QUERY_STRING """
        fields = None
        if 'POST' == self.environ['REQUEST_METHOD']:
            fields = cgi.FieldStorage(
                fp=self.environ['wsgi.input'], environ=self.environ, keep_blank_values=1)
            return fields

    def is_post(self):
        """ Check to see if the current request is a POST request """
        if self.environ['REQUEST_METHOD'] == 'POST':
            return True

        return False

    def compile_route_to_regex(self, route):
        # Split the route
        split_given_route = route.route_url.split('/')

        # compile the provided url into regex
        url_list = []
        regex = '^'
        for regex_route in split_given_route:
            if '@' in regex_route:
                if ':int' in regex_route:
                    regex += r'(\d+)'
                elif ':string' in regex_route:
                    regex += r'([a-zA-Z]+)'
                else:
                    # default
                    regex += r'(\w+)'
                regex += r'\/'

                # append the variable name passed @(variable):int to a list
                url_list.append(
                    regex_route.replace('@', '').replace(
                        ':int', '').replace(':string', '')
                )
            else:
                regex += regex_route + r'\/'

        self.url_list = url_list
        regex += '$'
        return regex

    def generated_url_list(self):
        return self.url_list


class BaseHttpRoute(object):
    method_type = 'GET'
    output = False
    route_url = None
    request = None
    named_route = None
    required_domain = None
    module_location = 'app.http.controllers'
    list_middleware = []

    def route(self, route, output):
        """ Loads the route into the class """

        # If the output specified is a string controller
        if isinstance(output, str):
            mod = output.split('@')

            # Gets the controller name from the output parameter
            # This is used to add support for additional modules
            # like 'LoginController' and 'Auth.LoginController'
            get_controller = mod[0].split('.')[-1]

            # Import the module
            module = importlib.import_module(
                '{0}.'.format(self.module_location) + get_controller)

            # Get the controller from the module
            controller = getattr(module, get_controller)

            # Get the view from the controller
            view = getattr(controller(), mod[1])
            self.output = view
        else:
            self.output = output
        self.route_url = route
        return self

    def domain(self, domain):
        self.required_domain = domain
        return self

    def module(self, module):
        self.module_location = module
        return self

    def has_required_domain(self):
        if self.request.has_subdomain() and (self.required_domain is '*' or self.request.subdomain == self.required_domain):
            return True
        return False

    def name(self, name):
        """ Specifies the name of the route """
        self.named_route = name
        return self

    def load_request(self, request):
        """ Load the request into this class """
        self.request = request
        return self

    def middleware(self, *args):
        """ Loads a list of middleware to run """
        self.list_middleware = args
        return self

    def run_middleware(self, type_of_middleware):
        """ type_of_middleware should be a string that contains either 'before' or 'after' """

        # Get the list of middleware to run for a route.
        for arg in self.list_middleware:

            # Locate the middleware based on the string specified
            located_middleware = self.request.app().resolve(locate(middleware.ROUTE_MIDDLEWARE[arg]))

            # If the middleware has the specific type of middleware
            # (before or after) then execute that
            if hasattr(located_middleware, type_of_middleware):
                getattr(located_middleware, type_of_middleware)()


class Get(BaseHttpRoute):
    """ Class for specifying GET requests """

    def __init__(self):
        self.method_type = 'GET'


class Post(BaseHttpRoute):
    """ Class for specifying POST requests """

    def __init__(self):
        self.method_type = 'POST'


class Api():
    """ API class docstring """
    def __init__(self):
        self.method_type = 'POST'
        self.continueroute = True
        self.url = False
        self.exclude_list = []
        self.output = False
        self.model_obj = None

    def route(self, route):
        """ Loads the route into the class """
        self.url = route
        return self

    def model(self, model):
        """ Loads the model into the class """
        if not self.url:
            self.url = '/api/' + model.__name__.lower()

        self.model_obj = model
        return self

    def fetch(self, request):
        """ Fetch the API from the model """
        # regex for /api/users/1
        matchregex = re.compile(r"^\/\w+\/\w+\/(\d+)")
        updateregex = re.compile(r"^\/\w+\/\w+\/(\d+)/update")
        match_url = matchregex.match(request.path)
        match_update_url = updateregex.match(request.path)

        if self.url == request.path and request.method == 'GET':
            # if GET /api/user

            model = self.model_obj
            model.__hidden__ = self.exclude_list

            query = model.all()

            self.output = query.to_json()
        elif match_url and request.method == 'GET':
            # if GET /api/user/1
            # query = self.model_obj.get(self.model_obj.id == match_url.group(1))
            model = self.model_obj.find(match_url.group(1))
            if model:
                self.output = model.to_json()
            else:
                self.output = []
        elif self.url == request.path and request.method == 'POST':
            # if POST /api/user
            proxy = self.model_obj()
            for field in request.all():
                setattr(proxy, field, request.input(field))
            proxy.save()
            self.output = proxy.to_json()
        elif match_url and request.method == 'DELETE':
            # if DELETE /api/user/1
            get = self.model_obj.find(match_url.group(1))
            if get:
                query = get.delete()
                self.output = get.to_json()
            else:
                self.output = []
        elif match_update_url and request.method == 'POST':
            # if POST /api/user/1/update
            proxy = self.model_obj.find(match_update_url.group(1))
            for field in request.all():
                setattr(proxy, field, request.input(field))
            proxy.save()
            proxy = self.model_obj.find(match_update_url.group(1))
            self.output = proxy.to_json()
        else:
            self.output = None
        return self

    def exclude(self, exclude_list):
        """ Exclude columns from the model """
        self.exclude_list = exclude_list
        return self
