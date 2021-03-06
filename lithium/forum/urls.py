from django.conf.urls.defaults import *
from lithium.forum.models import Forum
from lithium.forum.feeds import *

urlpatterns = patterns('lithium.forum.views',
    url(r'^$', 'forum_index', name='forum.forum_index'),
    url(r'^threads/$', 'thread_list', name='forum.threads'),
    url(r'^all.rss$', LatestPostFeed()),
    url(r'^(?P<slug>[-\w]+).rss$', LatestPostFeed()),
    url(r'^(?P<forum>[-\w]+)/$', 'forum_detail', name='forum.forum_detail'),
    url(r'^(?P<forum>[-\w]+)/create/$', 'thread_create', name='forum.thread_create'),
    url(r'^(?P<forum>[-\w]+)/(?P<slug>[-\w]+)/$', 'thread_detail', name='forum.thread_detail'),
    url(r'^(?P<forum>[-\w]+)/(?P<slug>[-\w]+)/reply/$', 'thread_detail', dict(display_posts=False, template_name='forum/thread_reply.html'), 'forum.thread_reply'),
)
