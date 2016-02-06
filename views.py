'''
 Generating graphical representation of application data model
'''

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render

from django.conf import settings
from django.db.models.fields import related
from django.template.loader import get_template
from django.template import Context
import json

#pylint: disable=E1101, C0330 
#pylint: disable=W0212

def dbmodel(request):
    '''
    Generate database model visualization for specified applications
    '''
    graph_settings = getattr(settings, 'DBMODEL_SETTINGS', {})
    apps = graph_settings.get('apps', [])

    excludes = ['%s__%s' % (app, model)
                for app, models in graph_settings.get('exclude', {}).items()
                for model in models]
    #pylint: disable=E1101 
    models = ContentType.objects.filter(app_label__in=apps)

    nodes = []
    edges = []

    for model in models:
        if not model.model_class():
            continue

        model.doc = model.model_class().__doc__
        
        _id = "%s__%s" % (model.app_label, model.model)
        if _id in excludes:
            continue
        
        label = "%s" % (model.model)
        fields = [f for f in model.model_class(). _meta.fields]
        many = [f for f in model.model_class()._meta. many_to_many]
        if graph_settings.get('show_fields', True):
            label += "\n%s\n"%("-"*len(model.model))
            label += "\n".join([str(f.name) for f in fields])

        edge_color = {'inherit': 'from'}

        for field_ in fields + many:
            if field_.rel:
                metaref = field_.rel.to._meta
                if metaref.app_label != model.app_label:
                    edge_color = {'inherit':'both'}
                edge = {
                        'from': _id,
                        'to': "%s__%s" % (metaref.app_label, metaref.model_name),
                        'color': edge_color,
                       }

                if str(field_.name).endswith('_ptr'):
                    #fields that end in _ptr are pointing to a parent object
                    edge.update({
                        'arrows': {'to': {'scaleFactor':0.75}}, #needed to draw from-to
                        'font':   {'align': 'middle'},
                        'label':  'is a',
                        'dashes': True
                        })
                elif isinstance(field_, related.ForeignKey):
                    edge.update({
                            'arrows': {'to': {'scaleFactor':0.75}}
                        })
                elif isinstance(field_, related.OneToOneField):
                    edge.update({
                            'font':  {'align': 'middle'},
                            'label': '|'
                        })
                elif isinstance(field_, related.ManyToManyField):
                    edge.update({
                            'color':  {'color':'gray'},
                            'arrows': {'to': {'scaleFactor':1}, 'from': {'scaleFactor': 1}},
                        })

                edges.append(edge)

        nodes.append(
            {
                'id':    _id,
                'label': label,
                'shape': 'box',
                'group': model.app_label,
                'title': get_template("dbmodel/dbnode.html").render(
                    Context({'model':model, 'fields':fields,})
                    )

            }
        )

    data = {
        'nodes': json.dumps(nodes),
        'edges': json.dumps(edges)
    }
    return render(request, 'dbmodel/dbdiagram.html', data)
