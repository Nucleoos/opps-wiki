# -*- coding: utf-8 -*-

import pickle

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import get_current_site
from django.forms.models import modelform_factory
from django.db.models import get_model
from django.http import Http404
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from .models import Suggestion, Wiki


class BaseWikiView(object):
    def get_site(self):
         return get_current_site(self.request)

    def get_queryset(self):
        qs = super(BaseWikiView, self).get_queryset()
        return qs.filter(
            site=self.get_site(),
            published=True,
            date_available__lte=timezone.now()
        )

    def get_template_names(self):
        names = super(BaseWikiView, self).get_template_names()
        wiki_name = u'wiki/wiki{}.html'.format(self.template_name_suffix)
        if wiki_name not in names:
            names.append(wiki_name)
        return self.get_domain_template_names(names) + names

    def get_domain_template_names(self, template_names):
        domain_names = []
        site = self.get_site()
        for name in template_names:
            domain_names.append(u'{}/{}'.format(site.domain, name))
        return domain_names

    def get_context_data(self, **kwargs):
        context = super(BaseWikiView, self).get_context_data(**kwargs)
        context['wiki_models'] = [(w.add_url(), w._meta.verbose_name) for w \
                                  in Wiki.get_wiki_models()]
        return context


class WikiListView(BaseWikiView, ListView):
    model = Wiki

    def get_queryset(self):
        qs = super(WikiListView, self).get_queryset()
        return qs.filter(parent__isnull=True)


class WikiDetailView(BaseWikiView, DetailView):
    model = Wiki
    slug_field = 'long_slug'
    slug_url_kwarg = 'long_slug'

    def get_object(self, queryset=None):
        wiki_obj = super(WikiDetailView, self).get_object(queryset)

        for parent in wiki_obj.get_ancestors():
            if not parent.published:
                raise Http404()
        return wiki_obj.get_child_object()


class WikiCreateView(BaseWikiView, CreateView):
    success_url = None

    @property
    def model(self):
        model = get_model(self.kwargs['app_label'], self.kwargs['child_class'])
        if not issubclass(model, Wiki):
            raise Http404()
        return model

    def get_queryset(self):
        return self.model._default_manager.all()

    def get_form_class(self):
        return modelform_factory(self.model, fields=self.model.PUBLIC_FIELDS)

    def form_valid(self, form):
        Suggestion.objects.create(
            user=self.request.user,
            title=form.cleaned_data['title'],
            content_type=ContentType.objects.get_for_model(self.model),
            serialized_data=pickle.dumps(form.cleaned_data),
            status='pending',
        )

class WikiUpdateView(BaseWikiView, UpdateView):
    model = Wiki
    success_url = None
    slug_field = 'long_slug'
    slug_url_kwarg = 'long_slug'

    def get_object(self, queryset=None):
        wiki_obj = super(WikiUpdateView, self).get_object(queryset)

        for parent in wiki_obj.get_ancestors():
            if not parent.published:
                raise Http404()
        return wiki_obj.get_child_object()

    def get_form_class(self):
        obj = self.get_object()
        return modelform_factory(obj.__class__, fields=obj.PUBLIC_FIELDS)

    def form_valid(self, form):
        Suggestion.objects.create(
            user=self.request.user,
            title=form.cleaned_data['title'],
            content_object=self.get_object(),
            serialized_data=pickle.dumps(form.cleaned_data),
            status='pending',
        )
