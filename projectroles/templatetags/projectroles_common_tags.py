"""Template tags provided by projectroles for use in other apps"""

from importlib import import_module
import mistune

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.urls import reverse

import projectroles
from projectroles.plugins import get_backend_api

site = import_module(settings.SITE_PACKAGE)

register = template.Library()


@register.simple_tag
def site_version():
    if hasattr(site, '__version__'):
        return site.__version__

    return '[UNKNOWN]'


@register.simple_tag
def core_version():
    return projectroles.__version__


@register.simple_tag
def render_markdown(raw_markdown):
    return mistune.markdown(raw_markdown)


@register.simple_tag
def get_history_dropdown(project, obj):
    """Return link to object timeline events within project"""
    timeline = get_backend_api('timeline_backend')

    if not timeline:
        return ''

    url = timeline.get_object_url(project.sodar_uuid, obj)
    return '<a class="dropdown-item" href="{}">\n<i class="fa fa-fw ' \
           'fa-clock-o"></i> History</a>\n'.format(url)


@register.simple_tag
def highlight_search_term(item, term):
    """Return string with search term highlighted"""

    def get_highlights(item):
        pos = item.lower().find(term.lower())
        tl = len(term)

        if pos == -1:
            return item     # Nothing to highlight

        ret = item[:pos]
        ret += '<span class="sodar-search-highlight">' + \
               item[pos:pos + tl] + '</span>'

        if len(item[pos + tl:]) > 0:
            ret += get_highlights(item[pos + tl:])

        return ret

    return get_highlights(item)


@register.simple_tag
def get_project_title_html(project):
    """Return HTML version of the full project title including parents"""
    ret = ''

    if project.get_parents():
        ret += ' / '.join(project.get_full_title().split(' / ')[:-1]) + ' / '

    ret += project.title
    return ret

@register.simple_tag
def get_user_html(user):
    """Return standard HTML representation for a User object"""
    return '<a title="{}" href="mailto:{}" data-toggle="tooltip" ' \
           'data-placement="top">{}</a>'.format(
                user.get_full_name(), user.email, user.username)


@register.simple_tag
def get_project_link(project):
    """Return link to project with simple title"""
    return '<a href="{}">{}</a>'.format(
        reverse('projectroles:detail', kwargs={'project': project.sodar_uuid}),
        project.title)


@register.simple_tag
def get_class(obj, lower=False):
    """Return object class as string"""
    c = obj.__class__.__name__
    return c.lower() if lower else c


@register.filter
def force_wrap(s, length):
    # If string contains spaces or hyphens, leave wrapping to browser
    if not {' ', '-'}.intersection(s) and len(s) > length:
        return '<wbr />'.join(
            [s[i:i + length] for i in range(0, len(s), length)])

    return s


@register.simple_tag
def get_full_url(request, url):
    """Get full URL based on a local URL"""
    return request.scheme + '://' + request.get_host() + url


@register.simple_tag
def check_backend(name):
    """Return True if backend app is available, else False"""
    return True if get_backend_api(name) else False


@register.simple_tag
def get_setting(name):
    """Return value of Django setting by name or None if it is not found"""
    return getattr(settings, name) if hasattr(settings, name) else None


@register.simple_tag
def static_file_exists(path):
    """Return True/False based on whether a static file exists"""
    return True if finders.find(path) else False


@register.simple_tag
def template_exists(path):
    """Return True/False based on whether a template exists"""
    try:
        get_template(path)
        return True

    except template.TemplateDoesNotExist:
        return False
