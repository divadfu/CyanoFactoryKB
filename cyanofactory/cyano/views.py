from copy import deepcopy

# Create your views here.
from django.template import Context, loader
#from polls.models import Choice, Poll
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from biosql.models import Bioentry

from biosql.helpers import get_database_item

from cyano.helpers import render_queryset_to_response
from cyano.helpers import get_queryset_object_or_404

from cyano.models import Genes
from cyano.models import Gene

import itertools

from biosql.helpers import database_name

def index(request):
    return render_queryset_to_response(
        request,
        template = "cyano/index.html",
        )

def organism(request, organism):
    organism = get_queryset_object_or_404(Bioentry.objects.filter(biodatabase__name = database_name).filter(name = organism))
    record = get_database_item(organism)
    #gene_count = len(Seqfeature.filter_by_organism(organism).filter(type_term__name = "gene"))

    contentCol1 = []
    contentCol2 = []
    contentCol3 = []
#===============================================================================
    contentCol1.append([
        [0, 'Genes', len(filter(lambda x : x.type == "gene", record.features)), 'nt', organism.get_genes_url()],
    ])
    
    contentCol2.append([
        [0, 'Chromosomes', 42, None, organism.get_genes_url()],
        [1, 'Length', 100, 'nt'],
        [1, 'GC-content', ('%0.1f' % (0.1 * 100)), '%'],
    ])
    
    contentCol1 = list(itertools.chain.from_iterable(contentCol1))
    contentCol2 = list(itertools.chain.from_iterable(contentCol2))

    return render_queryset_to_response(
                request,
                organism = organism,
                template = "cyano/organism.html",
                data = {
                        "content" : [contentCol1, contentCol2, contentCol3],
                        "contentRows": range(max(len(contentCol1), len(contentCol2), len(contentCol3)))
                       })

def genes(request, organism):
    organism = get_queryset_object_or_404(Bioentry.objects.filter(biodatabase__name = database_name).filter(name = organism))
    record = get_database_item(organism)

    contentHeaders = [x[1] for x in Genes.Meta.field_list]
    content = [[] for x in contentHeaders]
    urls = []
    
    genes = []
    cds = {}
    for item in record.features:
        if item.type == "gene":
            if "gene" in item.qualifiers:
                genes.append(item.qualifiers["gene"][0])
        if item.type == "CDS":
            if "gene" in item.qualifiers:
                cds[item.qualifiers["gene"][0]] = item
    
    for item in genes:
        #print item
        if item in cds:
            val = cds[item].qualifiers
            i = 0
            for x in Genes.Meta.field_list:
                content[i].append(val.get(x[0], [""])[0])
                i += 1
                if (x[0] == Genes.Meta.field_url):
                    urls.append(organism.get_gene_url(val.get(x[0], [""])[0]))
    
    #for item in itertools.ifilter(lambda x : x.type == "gene", record):
    #    if "gene" in item.qualifiers:
    #        contentCol1.append(item.qualifiers["gene"][0])
    #        contentCol2.append(item.qualifiers["locus_tag"][0])
    #        urls.append(organism.get_gene_url(contentCol1[-1]))
    #    else:
    #        print "Missing"
    #        print item.qualifiers

    return render_queryset_to_response(
                request,
                organism = organism,
                template = Genes.Meta.template,
                data = {"contentHeaders" : contentHeaders,
                        "content" : content,
                        "contentRows" : range(len(content[0])),
                        "urls" : urls,
                })
    
def gene(request, organism, gene):
    organism = get_queryset_object_or_404(Bioentry.objects.filter(biodatabase__name = database_name).filter(name = organism))
    gene_name = gene
    gene = Gene(organism, gene)
    
    
    
    print gene.get_databases_html()

    return render_queryset_to_response(
                request,
                organism = organism,
                template = Gene.Meta.template,
                data = {"name": gene_name,
                        "type": "Gene",
                        "fieldsets": gene.fieldsets}
                )
