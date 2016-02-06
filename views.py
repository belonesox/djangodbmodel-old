'''
 Generating graphical representation of application data model
'''

from django.contrib.contenttypes.models import ContentType
from django.contrib.admindocs import utils
from django.shortcuts import render
from django.utils.translation import ugettext as _


from django.conf import settings

from django.db.models.fields import related
from django.template.loader import get_template
from django.template import Context
import json

#pylint: disable=E1101, C0330 
#pylint: disable=W0212, W0612

def dbmodel(request):
    '''
    Generate database model visualization for specified applications
    '''
    def get_id4model(app_label, model):
        '''
         Get id and url for a model
        '''
        url = "../models/" + app_label + "." + model + "/"
        return url
    
    graph_settings = getattr(settings, 'DBMODEL_SETTINGS', {})
    apps = graph_settings.get('apps', [])

    #pylint: disable=E1101 
    models = ContentType.objects.filter(app_label__in=apps)

    nodes = []
    edges = []

    for model in models:

        id_ = get_id4model(model.app_label, model.model)        
        if not model.model_class():
            continue

        doc_ = model.model_class().__doc__
        title, body, metadata = utils.parse_docstring(doc_)
        if title:
            title = utils.parse_rst(title, None, None)
        if body:
            body = utils.parse_rst(body, None, None)
        
        model.rstdoc = title + body
        
       
        label = "%s" % (model.model)
        fields = [f for f in model.model_class(). _meta.fields]
        many = [f for f in model.model_class()._meta. many_to_many]
        # if graph_settings.get('show_fields', True):
        #     label += "\n%s\n"%("-"*len(model.model))
        #     label += "\n".join([str(f.name) for f in fields])

        fields_table = '''
<th><td><span style="background-color:#eeee00;color:#0000ff;font-size:22px">%s</span></td></th>
''' % model.model

        for field in fields:
            color = '#000000'
            if field.unique:
                color = '#0000ff'
            fields_table += '''
        <tr><td><span style="color:%s;">%s</span></td></tr>
                ''' % (color, field.name)

        row_height = 14
        table_height = row_height * (len(fields) + 3) * 1.8

        imagesrc = '''
<svg xmlns="http://www.w3.org/2000/svg" width="150px" height="''' + str(table_height) + '''px">
<rect x="0" y="0" width="100%" height="100%" fill="#ffffff" stroke-width="20" stroke="#ffffff" ></rect>
    <foreignObject x="10" y="10" width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-size:''' + str(row_height) + '''px">
    <table> ''' + fields_table + ''' </table> 
    </div>
    </foreignObject>
</svg>
'''  

        edge_color = {'inherit': 'from'}

        for field_ in fields + many:
            if field_.rel:
                metaref = field_.rel.to._meta
                if metaref.app_label != model.app_label:
                    edge_color = {'inherit':'both'}

                edge = {
                        'from': id_,
                        'to':  get_id4model(metaref.app_label, metaref.model_name),
                            # "%s__%s" % (metaref.app_label, metaref.model_name),
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
                'id':    id_,
                'label': label,
                'imagesrc': imagesrc,
                'shape': 'image',
                'size':  table_height*1.8,
                'group': model.app_label,
                'title': get_template("dbmodel/dbnode.html").render(
                    Context({'model':model, 'fields':fields,})
                    ),
            }
        )

    data = {
        'nodes': json.dumps(nodes),
        'edges': json.dumps(edges)
    }
    return render(request, 'dbmodel/dbdiagram.html', data)
