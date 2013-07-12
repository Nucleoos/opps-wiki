# -*- coding: utf-8 -*-

import pickle

from django.contrib.auth.models import Permission
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import get_model, get_models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone

from mptt.models import MPTTModel, TreeForeignKey
from taggit.models import TaggedItemBase
from taggit.managers import TaggableManager

from opps.core.models import NotUserPublishable, Slugged, Owned, Date


class TaggedWiki(TaggedItemBase):
    """Tag for wiki """
    content_object = models.ForeignKey('wiki.Wiki')


class Wiki(MPTTModel, NotUserPublishable, Slugged):
    title = models.CharField(_(u"title"), max_length=140)
    tags = TaggableManager(
        blank=True,
        through=TaggedWiki,
        verbose_name=u'Tags'
    )
    child_class = models.CharField(
        _(u'child class'),
        max_length=30,
        db_index=True,
        editable=False
    )
    child_app_label = models.CharField(
        _(u'child app label'),
        max_length=30,
        db_index=True,
        editable=False
    )
    parent = TreeForeignKey(
        'self',
        related_name='subpage',
        null=True,
        blank=True
    )

    long_slug = models.SlugField(
        _(u"Path name"),
        max_length=255,
        db_index=True,
        editable=False
    )

    class Meta:
        permissions = (('can_publish', _(u'User can publish automatically')),)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            self.child_class = self.__class__.__name__
            self.child_app_label = self._meta.app_label

        self.slug = slugify(self.title)
        self.long_slug = self.slug
        parent = self.parent
        while parent:
            self.long_slug = u"{}/{}".format(parent.slug, self.long_slug)
            parent = parent.parent
        super(Wiki, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('wiki-detail', kwargs={'long_slug': self.long_slug})

    @classmethod
    def add_url(cls):
        return reverse('wiki-add', args=(cls._meta.app_label, cls.__name__))

    @classmethod
    def get_wiki_models(cls):
        # Get wiki subclasses
        if not hasattr(cls, '_wiki_models'):
            cls._wiki_models = [m for m in get_models() if m is not Wiki
                                and issubclass(m, Wiki)]
        return cls._wiki_models

    def get_child_object(self):
        child_model = get_model(self.child_app_label, self.child_class)
        if child_model == Wiki:
            return self

        return child_model._default_manager.get(pk=self.pk)

    def get_published_children(self):
        return self.get_children().filter(
            published=True,
            date_available__lte=timezone.now()
        )


class Suggestion(Owned, Date):
    STATUS_CHOICES = (
        ('pending', _(u'Pending')),
        ('reject', _(u'Reject')),
        ('accept', _(u'Accept')),
        ('auto', _(u'Auto accepted')),
    )
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField(verbose_name='object name',
                                            null=True)
    title=models.CharField(_(u'title'), max_length=140)
    content_object = generic.GenericForeignKey()
    serialized_data = models.TextField(_(u'data'))
    status = models.CharField(_(u'status'), max_length=50,
                              choices=STATUS_CHOICES)

    class Meta:
        verbose_name = _(u'suggestion')
        verbose_name_plural = _(u'suggestions')

    def publish(self, is_auto=False):
        if is_auto:
            self.status = 'auto'
        else:
            num = self.user.suggestion_set.filter(status='accept').count()
            if num >= getattr(settings, 'USER_CAN_PUBLISH_NUMBER', 100):
                p = Permission.objects.get_by_natural_key(
                    'can_publish', 'wiki', 'wiki'
                )
                self.user.user_permissions.add(p.pk)

        suggested_data = pickle.loads(self.serialized_data)
        wiki_model = self.content_type.model_class()
        wiki_model.published = True
        wiki_model(**suggested_data).save()

    def save(self, *args, **kwargs):
        if self.status == 'accept':
            self.publish()
        super(Suggestion, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.status
