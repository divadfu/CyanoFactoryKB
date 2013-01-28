from django.http import HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import Context, loader
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

database_name = "cyano"

def get_database_url_from_organism(organism):
    stri = organism.split(':', 1)
    return reverse("db_xref.views.dbxref", args=[stri[0], stri[1]])

def get_database_url(database, organism):
    database = database.lower()
    
    return {
        "asap": lambda : "https://asap.ahabs.wisc.edu/annotation/php/feature_info.php?FeatureID=" + organism,
        "ecocyc": lambda : "http://biocyc.org/ECOLI/new-image?type=GENE&object=" + organism,
        "ecogene": lambda : "http://ecogene.org/geneInfo.php?eg_id=" + organism,
        "geneid": lambda : "http://www.ncbi.nlm.nih.gov/sites/entrez?db=gene&cmd=Retrieve&dopt=full_report&list_uids=" + organism,
        "gi": lambda: "http://www.ncbi.nlm.nih.gov/nuccore/" + organism,
        "project": lambda: "http://www.ncbi.nlm.nih.gov/bioproject/" + organism,
        "bioproject": lambda: "http://www.ncbi.nlm.nih.gov/bioproject?term=" + organism,
        "pubmed": lambda: "http://www.ncbi.nlm.nih.gov/pubmed/" + organism,
        "uniprotkb/swiss-prot" : lambda : "http://www.uniprot.org/uniprot/" + organism,        
            }.get(database, lambda : "")

def index(request):
    data = {"db" : "ECOCYC",
            "value": "G7954",
            "item" : "ECOCYC:G7954",
            "formats" : ["txt", "html", "xml", "json", "redirect"]
            }
    
    return render_to_response("db_xref/index.html", data)

def dbxref(request, database, organism):
    _format = request.GET.get('format', 'redirect')
    
    data = {
        "database" : database,
        "item" : organism,
        "url" : get_database_url(database, organism)()
    }
    print data["url"]
    
    template = "db_xref/output." + _format

    do_error = False

    if _format == "txt":
        mimetype = "text/plain"
    elif _format == "json":
        mimetype = "application/json"
    elif _format == "xml":
        mimetype = "application/xml"
    elif _format == "html":
        mimetype = "application/xhtml+xml"
    elif _format == "redirect":
        if len(data["url"]) == 0:
            do_error = True
            data["error"] = "Unsupported Database " + database
        else:
            return redirect(data["url"])
    else:
        do_error = True
        data["error"] = "Unknown format " + _format
        
    if do_error:
        t = loader.get_template('db_xref/error.html')
        c = Context(data)
        return HttpResponseBadRequest(
            t.render(c),
            mimetype = 'text/html; charset=UTF-8',
            content_type = 'text/html; charset=UTF-8')

    return render_to_response(template, data, mimetype = mimetype)
