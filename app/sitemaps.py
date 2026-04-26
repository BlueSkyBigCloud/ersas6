# app/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ['home', 'security_crm', 'security_software', 'security_solutions']

    def location(self, item):
        return reverse(item)