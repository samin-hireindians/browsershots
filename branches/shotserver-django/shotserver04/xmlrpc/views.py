import sys
from django.http import HttpResponse
from shotserver04 import settings
from shotserver04.xmlrpc.dispatcher import SignatureDispatcher


def xmlrpc(request):
    response = HttpResponse()
    if len(request.POST):
        response.write(dispatcher._dispatch_request(request))
    response['Content-length'] = str(len(response.content))
    return response


if sys.version_info[0:2] <= (2, 4):
    dispatcher = SignatureDispatcher()
else:
    dispatcher = SignatureDispatcher(allow_none=False, encoding=None)
dispatcher.register_introspection_functions()


for app in settings.INSTALLED_APPS:
    try:
        module = __import__(app + '.xmlrpc', globals(), locals(), ['xmlrpc'])
    except ImportError:
        continue
    for name, item in module.__dict__.items():
        if callable(item):
            function_name = '%s.%s' % (app.split('.')[-1], name)
            dispatcher.register_function(item, function_name)
