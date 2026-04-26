from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.template.loader import get_template
from business.models import *
from app.models import *
from django.contrib.auth.decorators import login_required

def render_to_pdf(template_src, context_dict={}):
    """
    Render the provided HTML template with the given context and return it as a PDF.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = HttpResponse(content_type='application/pdf')
    
    # Set the filename using the context data
    filename = f'{context_dict.get("filename", "document")}.pdf'  # Default to "document.pdf"
    result['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create the PDF
    pisa_status = pisa.CreatePDF(html, dest=result)
    
    if pisa_status.err:
        return HttpResponse('We had some errors with generating your PDF file.')
    return result

@login_required
def print_invoice_pdf(request, pk):
    """
    View to generate and print an invoice as a PDF.
    """
    # Get the company of the logged-in user
    company = request.user.company

    
    # Fetch the invoice by its primary key
    invoice = get_object_or_404(Invoice, pk=pk)
    customer = invoice.customer 
    
    # Prepare context for the PDF
    context = {
        'invoice': invoice,
        'company': company,
        'customer': customer,
        'filename': f"{company.name}_Invoice_{invoice.invoice_number}"  # Include the filename in the context
    }
    
    # Render the PDF using the template
    return render_to_pdf('invoice_pdf.html', context)


def print_quote_pdf(request, pk):
    """
    View to print a quote as a PDF.
    """
    company = request.user.company
    quote = get_object_or_404(Quote, pk=pk)
    customer = quote.customer 
    context = {
        'quote': quote,
        'company': company,
        'customer': customer,
        'filename': f"Quote_{quote.quote_number}"  # Provide a custom filename
    }
    # Assuming you have a template named 'quote_pdf.html'
    return render_to_pdf('quote_pdf.html', context)