from django.shortcuts import render
import json

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from haystack.query import SearchQuerySet

# TODO error handling, validation, analytics
class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        from django.template.defaultfilters import date, time
        q = request.GET.get('q') if request.GET.get('q') else ""

        sqs = SearchQuerySet()

        vocab = []
        for result in sqs:
            if result.title:
                vocab.extend(result.title.split(' '))
            if result.subject:
                vocab.extend(result.subject)

        vocab = [x for x in vocab if len(x) > 2]
        vocab = list(set(vocab))
        vocab = sorted(vocab)

        if q:
            sqs = sqs.filter(content=q).boost('keyword', 2.0)

        resources = []
        for result in sqs:
            resources.append({
                "name": result.title,
                "link": result.absolute_url,
                "availability": result.availability,
                "type": result.resource_type_exact,
                "author": result.author,
                "author_link": result.author_url,
                "abstract": result.abstract,
                "created": date(result.created, "M d, Y") + " at " + time(result.created),
                "modified": date(result.modified, "M d, Y") + " at " + time(result.modified)
            })

        itemcount = len(resources)
        resources = json.dumps(resources)

        if request.GET.get('mode') == 'advanced':
            return render(request, 'hs_discover/advanced_search.html')
        else:
            return render(request, 'hs_discover/search.html', {
                'resources': resources,
                'q': q,
                'itemcount': itemcount,
                'vocab': vocab
            })
