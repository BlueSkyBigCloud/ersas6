
from django.contrib import admin
from django.urls import path, include
from app.views import *
from users.views import *
from finance.views import *
from django.conf.urls.static import static
from userpayment.views import *
from business.views import *
from file_transfer.views import *
from ip_whitelist1.views import *
from requestcalendar.views import *
from googlemap.views import *
from dataupload.views import *
from crm.views import *
from api.views import *
from dj_rest_auth.views import LoginView
from file_store.views import *
from video.views import *

from django.contrib.sitemaps.views import sitemap
from app.sitemaps import StaticViewSitemap

from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'apiobject', APIObjectViewSet, basename='apiobject')
router.register(r'servicerequest', ServiceRequestViewSet, basename='servicerequest')
router.register(r'directmessage', DirectMessageViewSet, basename='directmessage')
router.register(r'invitation', InvitationViewSet, basename='invitation')
router.register(r'video', VideoViewSet, basename='video')


sitemaps = {
    'static': StaticViewSitemap,
}


urlpatterns = [
    path('09A@admin/', admin.site.urls),
    path('businesspartners', businesspartners_view, name='businesspartners'),
    path('92471026814182logged-ips/', list_logged_ips, name='logged_ips'),
    path('8175639&@anjsnom!iplookup/', iplookup_view, name="iplookup"),
    path("make_payment/", make_payment, name="make_payment"),
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),

    path("quotes/<int:pk>/convert/", convert_quote_to_invoice, name="convert_quote_to_invoice"),

    path("prospects/", include("prospects.urls")),
    path("contact/", include("contact.urls")),

    path("priceanalysis/", include("priceanalysis.urls")),
    
    path("inventory/", include("inventory.urls")),

    path("video/", include("video.urls")),

    path("account_billing/", account_billing, name="account_billing"),
    path("app_api/payment/create-payment/", create_payment_session, name="create_payment_session"),
    path("app_api/payment/get-stripe-secret/", get_stripe_secret_key, name="get_stripe_secret"),
    path("app_api/payment/create-checkout/", create_checkout_session, name="create_checkout_session"),
    
    path('ipwhitelist_redflag_view/', ipwhitelist_redflag_view, name='ipwhitelist_redflag_view'),
    
    path('app_api/', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='app_login'),
    path('app_api/register/', create_user, name='create_user'),

    path('app_api/forgot-password/', forgot_password, name='forgot_password'),
    path('app_api/reset-password/', reset_password, name='reset_password'),
    path('about', about_view, name='about'),
    path('about/download/<int:apk_id>/', download_apk, name='download_apk'),

    
    path('opportunities/', opportunity_list, name='opportunity_list'),
    path('opportunities/create/', opportunity_create, name='opportunity_create'),

    path('upload/', dataupload_view, name='upload_file'),
    path('uploads/convert/<uuid:file_id>/', convert_file, name='convert_file'),
    path("upload/success/", upload_success_view, name="upload_success"),

    path('bulkupload/equipment/', bulkupload_equipment_view, name='bulkuploadequipment'),
    path('bulkupload/employees/', bulkupload_employee_view, name='bulkuploademployees'),
    path('bulkupload/locations/', bulkupload_location_view, name='bulkuploadlocations'),
    path('bulkupload/prospects/', bulkupload_prospect_view, name='bulkupprospects'),
    path('bulkupload/pricing/', bulkpricing_upload, name='bulkpricing_upload'),
    path('bulkupload/', bulkupload_view, name='bulkupload'),

    # SEO Landing Pages
    path('security-crm/', security_crm_view, name='security_crm'),
    path('security-software/', security_software_view, name='security_software'),
    path('security-solutions/', security_solutions_view, name='security_solutions'),


    path('', home1_view, name='home'),
    path('home1/', home1_view, name='home1'),
    path('start', start_view, name='start'),
    path('companyonboarding/', companyonboarding_view, name='companyonboarding'),
    path('generate_promo/', generate_promo_code, name='generate_promo'),
    
    path('accounts/', include('allauth.urls')),
    path('accounts/signup/', CustomSocialLoginView.as_view(), name='signup'),
    path('accounts/login/', CustomSocialLoginView.as_view(), name='login'),
    path('accounts/', include('allauth.socialaccount.urls')),

    path('accounts/profile/', account_view, name='account'),
    path('accounts/profileedit/', accountedit_view, name='edit_account'),

    path('logout/', logout_view, name='logout'),

    path('dashboard/', dashboard_view, name='dashboard'),
    path('reports/', reports1_view, name='reports'),
    path('config/', config_view, name='config'),

    path('fetch_service_requests/', fetch_service_requests, name='fetch_service_requests'),  # URL to fetch service requests
    path('service-request/create/', create_service_request, name='create_service_request'),
    path('service_list/', service_request_list, name='service_list'),
    
    path('service-request/detail/<uuid:id>/', servicerequest_detail, name='servicerequest_detail'),
    path('service-request/detail/<uuid:id>/', servicerequest_detail, name='servicerequest_detail'),
    path('service-request/update/<uuid:id>/assign_employee/', assign_employee_servicerequest, name='assign_employee_servicerequest'),
    path('service-request/detail/<uuid:id>/add-notes', add_note, name='add_note'),
    path('service-request/detail/<uuid:id>/delete/', servicerequest_delete, name='servicerequest_delete'),
    path('service-request/edit/<uuid:id>/', edit_service_request, name='servicerequest_edit'),

    path('cost-sheet/<uuid:service_request_id>/', cost_sheet_view, name='cost_sheet_view'),
    path('cost-sheet/<uuid:service_request_id>/edit/', cost_sheet_edit, name='cost_sheet_edit'),
    
    path('invoices/', invoicelist_view, name='invoice_list'),
    path('invoice/<int:id>/', invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:customer_id>/', invoicecustomerlist_view, name='invoice_customer_list'),
    path('service-request/detail/<uuid:id>/create_invoice', create_invoice, name='create_invoice'),
    path('invoice/<int:invoice_id>/edit/', edit_invoice, name='edit_invoice'),

    path('quotes/', quotelist_view, name='quote_list'),
    path('quote/<int:id>/', quote_detail, name='quote_detail'),
    path('quotes/<uuid:customer_id>/', quotecustomerlist_view, name='quote_customer_list'),
    path('service-request/detail/<uuid:id>/create_quote', create_quote, name='create_quote'),
    path('quote/<int:quote_id>/edit/', edit_quote, name='edit_quote'),

    path('locations/', location_list, name='location_list'),
    path('locations/create/', location_create, name='location_create'),
    path('locations/<uuid:location_id>/', location_detail, name='location_detail'),
    path('locations/<uuid:location_id>/edit/', location_edit, name='location_edit'),
    path('locations/delete/<uuid:location_id>/', location_delete, name='location_delete'),

    path('equipment/', equipment_list, name='equipment_list'),
    path('equipment/create/', equipment_create, name='equipment_create'),
    path('equipment/<uuid:equipment_id>/', equipment_detail, name='equipment_detail'),
    path('equipment/<uuid:equipment_id>/edit/', equipment_edit, name='equipment_edit'),
    path('equipment/<uuid:equipment_id>/delete/', equipment_delete, name='equipment_delete'),

    path('employees/', employee_list, name='employee_list'),  # List all employees
    path('employees/create/', employee_create, name='employee_create'),  # Create a new employee
    path('employees/<uuid:employee_id>/', employee_detail, name='employee_detail'),  # Detail view for a specific employee
    path('employees/<uuid:employee_id>/edit/', employee_edit, name='employee_edit'),
    path('employees/<uuid:pk>/delete/', employee_delete, name='employee_delete'),

    path('service-types/', servicetype_list, name='servicetype_list'),
    path('service-type/<uuid:servicetype_id>/', servicetype_detail, name='servicetype_detail'),
    path('create-service-type/', create_servicetype, name='create_servicetype'),
    path('service-type/<uuid:servicetype_id>/edit/', servicetype_edit, name='servicetype_edit'),
    path('service-type/<uuid:servicetype_id>/delete/', servicetype_delete, name='servicetype_delete'),

    path('message_list/', message_list, name='message_list'),
    path('create_posting/', create_posting, name='create_posting'),
    path('create_message/', create_message, name='create_message'),

    path('registration/', registration_view, name='registration'),
    path('finance/', finance_view, name='finance'),

    path('company/', company_view, name='company'),
    path('company/create', company_create, name='create_company'),
    path('company/edit/<uuid:pk>/', company_edit, name='edit_company'),


    path('company/createinvite/', create_invite, name='create_invite'),

    path('products1', products1_view, name='products1'),
    path('digitalsolutions', products1_view, name='digitalsolutions'),

    path('products/', products_view, name='products'),
    path('stripe_webhook/', stripe_webhook, name ='stripe_webhook'),
    path('success/', payment_successful, name ='payment_success'),
    path('cancel/', payment_cancelled, name ='payment_cancel'),

    path("equipmentstore/", store_view4, name="equipmentstore"),

    path('store', store_view, name='store'),
    path("payinvoice/", store1_view, name="store1"),
    path("store1/", store1_view, name="store1"),
    path("store3/", store_view3, name="store3"),
    
    path('store4/', store_view4, name='store_view4'),
    path('cart/', view_cart, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/', remove_from_cart, name='remove_from_cart'),

    path('create-invite/', create_invite, name='create_invite'),
    path('accept-invite/', accept_invite, name='accept_invite'),

    path('businesscenter/', businesscenter_view, name='business_center'),
    path('add-customer/', add_customer_view, name='add_customer'),

    path('customer/<uuid:customer_id>/', businesscustomer_view, name='businesscustomer_view'),
    path('edit-customer/<uuid:id>/', edit_customer_view, name='edit_customer'),
    path('print/', include('print.urls')),

    path('file_transfer/', file_transfer, name='file_transfer'),
    path('file_transfer_list/', file_transfer_list, name='file_transfer_list'),

    path('file_transfer/download/<uuid:file_id>/', download_file, name='download_file'),


    path('calendar/', calendar_view, name='calendar_view'),
    path('calendar/<int:year>/<int:month>/', calendar_view, name='calendar_by_month'),
    path('calendar/<int:year>/<int:month>/<int:day>/', calendar_view_date, name='calendar_by_day'),

    path("map/", geocode5_view, name="map"),
    path('map1/', geocode7_view, name='map1'),

    path('geocode2/', geocode2_view, name='geocode2'),
    path('geocode6/', geocode6_view, name='geocode6'),
    path('geocode3/', geocode3_view, name='geocode3'),
    path("geocode7/", geocode7_view, name="geocode7"),
    path('location/<uuid:location_id>/geocode/', address_to_coordinates, name='address_to_coordinates'),

    path("map_location/", map_location_view, name="map_location"),
    path('map_location/create/', create_map_location, name='create_map_location'),
    path('map_location/list/', map_location_list, name='map_location_list'),
    path('maplocations/', map_locations, name='map_locations'),
    
    path("geocode/", geocode_page, name="geocode_page"),
    path("geocode1/", geocode1_page, name="geocode1_page"),
    path("geocode/address/", geocode_view, name="geocode_address"),
    path("geocodeaddress/", geocode_address, name="geocode_address_address"),

    path('geocode5/', geocode5_view, name='geocode5'),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),

    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
   
 
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
