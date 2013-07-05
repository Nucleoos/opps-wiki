# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import get_model, get_models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from taggit.models import TaggedItemBase
from taggit.managers import TaggableManager

from opps.core.models import NotUserPublishable, Slugged, Imaged


class TaggedWiki(TaggedItemBase):
    """Tag for wiki """
    content_object = models.ForeignKey('wiki.Wiki')


class Wiki(NotUserPublishable, Slugged):
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

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            self.child_class = self.__class__.__name__
            self.child_app_label = self._meta.app_label
        super(Wiki, self).save(*args, **kwargs)

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
