from django import template

register = template.Library()

@register.filter
def replace_target(request, arg):
    """Removes all values of arg from the given string"""
    newrequest =  request.rsplit('/',3)
    return newrequest[0] + "/" + arg + newrequest[2]

@register.filter
def called_id(request):
    newrequest =  request.rsplit('/',2)
    return newrequest[1]
