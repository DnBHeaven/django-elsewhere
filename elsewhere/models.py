from datetime import datetime

from django.db import connection
from django.db import models
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify


GOOGLE_PROFILE_URL = 'http://www.google.com/s2/favicons?domain_url=%s'
SN_CACHE_KEY = 'elsewhere_sn_data'
IM_CACHE_KEY = 'elsewhere_im_data'


class Network(models.Model):
    """ 
    Abstract model for storing networks. 
    """
    class Meta:
        abstract = True

    name = models.CharField(max_length=100)
    url = models.URLField(verify_exists=False)
    identifier = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True)

    @property
    def icon_url(self):
        """
        Icon URL or link to Google icon service
        """
        if self.icon:
            return reverse('elsewhere_img', args=[self.icon])
        return GOOGLE_PROFILE_URL % self.url

    def __unicode__(self):
        return self.name

class SocialNetwork(Network):
    class Meta:
        verbose_name_plural = 'social networks'

    def save(self, *args, **kwargs):
        cache.delete(SN_CACHE_KEY)
        super(SocialNetwork, self).save(*args, **kwargs)

class InstantMessenger(Network):
    class Meta:
        verbose_name_plural = 'instant messanger networks'

    def save(self, *args, **kwargs):
        cache.delete(IM_CACHE_KEY)
        super(InstantMessenger, self).save(*args, **kwargs)

#-- Object Managers for Profiles
class ProfileManager(models.Manager):
    """
    Manager for Profiles
    """
    def get_for_object(self, obj):
        """
        Create a queryset matching all profiles associated with the given
        object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk,
                           object_id=obj.pk)


#-- Profiles
class Profile(models.Model):
    """
    Common profile model pieces. 
    """
    objects = ProfileManager()

    class Meta:
        abstract = True

    date_added = models.DateTimeField(_('date added'), auto_now_add=True)
    date_verified = models.DateTimeField(_('date verified'), default=datetime.now)
    is_verified = models.BooleanField(default=False)


class NetworkProfile(Profile):
    """
    Abstract profile for a network provided by a known third-party
    """
    class Meta:
        abstract = True

    username = models.CharField(max_length=64)

    @property
    def url(self):
        """
        Profile URL with username
        """
        return "%s%s" % (self.network.url, self.username)

    def __unicode__(self):
        return "%s profile for %s" % (self.network,
                                      self.object)
    

class SocialNetworkProfile(NetworkProfile):
    """
    A profile for a social network
    """
    content_type = models.ForeignKey(ContentType, related_name='social_network_profiles')
    object_id = models.PositiveIntegerField(db_index=True)
    object = generic.GenericForeignKey('content_type', 'object_id')

    network = models.ForeignKey(SocialNetwork, related_name='profiles')


class InstantMessengerProfile(NetworkProfile):
    """
    A profile for an instant messenging network
    """
    content_type = models.ForeignKey(ContentType, related_name='instant_messenger_profiles')
    object_id = models.PositiveIntegerField(db_index=True)
    object = generic.GenericForeignKey('content_type', 'object_id')

    network = models.ForeignKey(InstantMessenger, related_name='profiles')


class WebsiteProfile(Profile):
    """
    A profile for an external, generic website
    """
    content_type = models.ForeignKey(ContentType, related_name='website_profiles')
    object_id = models.PositiveIntegerField(db_index=True)
    object = generic.GenericForeignKey('content_type', 'object_id')

    name = models.CharField(max_length=64)
    url = models.URLField(verify_exists=True)

    @property
    def icon_url(self):
        # No known icons! Just return the Google service URL.
        return GOOGLE_PROFILE_URL % self.url

    def __unicode__(self):
        return self.url
