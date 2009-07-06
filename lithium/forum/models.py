import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from lithium.forum.managers import ForumManager, ThreadManager

class Forum(models.Model):
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'))
    description = models.TextField(_('description'), blank=True)
    is_category = models.BooleanField(_('is category'), default=False, help_text=_('Categories cannot contain threads/posts'))
    
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children')
    position = models.PositiveIntegerField(_('position'), editable=False, default=0)
    level = models.PositiveIntegerField(_('level'), editable=False, default=0)
    
    objects = ForumManager()
    
    class Meta:
        ordering = ('position',)
    
    def __str__(self):
        return self.title
    
    def siblings(self, include_self=False):
        """
        Every forum on the current 'level'.
        """
        qs = Forum.objects.all()
        
        if not self.parent:
            qs = qs.filter(parent__isnull=True)
        else:
            qs = qs.filter(parent=self.parent)
        
        if not include_self:
            qs = qs.exclude(pk=self.pk)
        
        return qs
    
    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                # Although we dont actually want to include ourselfs, since we are not
                # inserted to the db, we cannot be excluded from the query.
                self.position = self.siblings(include_self=True).only('position').order_by('-position')[0].position + 1
            except IndexError:
                if self.parent:
                    self.position = self.parent.position + 1
                else:
                    try:
                        self.position = Forum.objects.only('position').order_by('-position')[0].position + 1
                    except IndexError:
                        self.position = 1
            
            if self.position != 1:
                Forum.objects.update_position(self.position)
            
            if self.parent:
                self.level = self.parent.level + 1
        super(Forum, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        for child in self.children.all():
            child.delete()
        
        # Our position could have changed due to children
        position = Forum.objects.get(pk=self.pk).position
        super(Forum, self).delete(*args, **kwargs)
        
        Forum.objects.update_position(position, increment=False)
    
    def get_next_forum(self):
        try:
            return self.siblings().filter(position__gt=self.position).order_by('position')[0]
        except IndexError:
            return None
    
    def get_previous_forum(self):
        try:
            return self.siblings().filter(position__lt=self.position).order_by('-position')[0]
        except IndexError:
            return None
    
    def get_position_range(self):
        """
        This method gets the range of the position
        over all children.
        """
        position_range = [self.position]
        
        for child in self.children.all():
            position_range += child.get_position_range()
        
        return position_range
    
    def move(self, direction='down'):
        swap = None
        
        if direction == 'up':
            swap = self.get_previous_forum()
            increment = False
        
        if direction == 'down':
            swap = self.get_next_forum()
            increment = True
        
        if not swap:
            return False
        
        self_range = self.get_position_range()
        swap_range = swap.get_position_range()
        
        base = Forum.objects.only('position').order_by('-position')[0].position * 2
        
        if direction == 'up':
            addition = base - len(self_range)
        else:
            addition = base + len(self_range)
        
        # Move to safe position.
        Forum.objects.update_position(swap_range, base)
        
        # Move ourself to where we should go.
        Forum.objects.update_position(self_range, len(swap_range), increment)
        
        # Move the swap to where it should go.
        Forum.objects.update_position(base, addition, False)
        
        return True

class Thread(models.Model):
    forum = models.ForeignKey(Forum)
    
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'))
    
    is_sticky = models.BooleanField(_('is sticky'), default=False)
    is_locked = models.BooleanField(_('is locked'), default=False)
    
    objects = ThreadManager()
    
    def __unicode__(self):
        return self.title

class Post(models.Model):
    content = models.TextField(_('content'))
    
    thread = models.ForeignKey(Thread)
    author = models.ForeignKey(User, related_name='forum_post_set', null=True, blank=True)
    pub_date = models.DateTimeField(_('published date'), default=datetime.datetime.now)
    
    class Meta:
        ordering = ('pub_date',)
    
    def __unicode__(self):
        return u'%s' % self.content[:20]
