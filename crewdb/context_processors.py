from django.core.files.storage import default_storage

def suit_licensed(request):
    return {
        'suit_is_licensed': default_storage.exists('suit_license.eml.asc')
    }

def licensed(request):
  return {
      'crewser_is_licensed': default_storage.exists('crewser_license.eml.asc')
  }

