# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.

"""
Screenshot models.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

import os
from django.db import models, backend
from django.utils.translation import gettext_lazy as _
from shotserver04.requests.models import Request
from shotserver04.websites.models import Website
from shotserver04.factories.models import Factory
from shotserver04.browsers.models import Browser
from shotserver04.screenshots import storage


class ScreenshotManager(models.Manager):

    def _quote(self, name):
        return '%s.%s' % (
            backend.quote_name(self.model._meta.db_table),
            backend.quote_name(name))

    def recent(self):
        """
        Get recent screenshots, but only one per website.
        """
        from django.db import connection
        cursor = connection.cursor()
        fields = ','.join(
            [self._quote(field.column) for field in self.model._meta.fields])
        cursor.execute("""
            SELECT """ + fields + """
            FROM """ + backend.quote_name(self.model._meta.db_table) + """
            WHERE """ + self._quote('id') + """ IN (
                SELECT MAX(""" + self._quote('id') + """)
                AS """ + backend.quote_name('maximum') + """
                FROM  """ + backend.quote_name(self.model._meta.db_table) + """
                GROUP BY """ + self._quote('website_id') + """
                ORDER BY """ + backend.quote_name('maximum') + """ DESC
                LIMIT 100)
            ORDER BY """ + self._quote('id') + """ DESC
            """)
        for row in cursor.fetchall():
            yield self.model(*row)


class Screenshot(models.Model):
    hashkey = models.SlugField(
        _('hashkey'), maxlength=32, unique=True)
    request = models.ForeignKey(Request,
        verbose_name=_('request'), raw_id_admin=True)
    website = models.ForeignKey(Website,
        verbose_name=_('website'), raw_id_admin=True)
    factory = models.ForeignKey(Factory,
        verbose_name=_('factory'), raw_id_admin=True)
    browser = models.ForeignKey(Browser,
        verbose_name=_('browser'), raw_id_admin=True)
    width = models.IntegerField(
        _('width'))
    height = models.IntegerField(
        _('height'))
    uploaded = models.DateTimeField(
        _('uploaded'), auto_now_add=True)
    objects = ScreenshotManager()

    class Admin:
        fields = (
            (None, {'fields': (
            ('hashkey', 'request'),
            ('factory', 'browser'),
            ('width', 'height'),
            'message',
            )}),
            )
        list_display = ('hashkey', 'factory', 'browser',
                        'width', 'height', 'uploaded')

    class Meta:
        verbose_name = _('screenshot')
        verbose_name_plural = _('screenshots')

    def __str__(self):
        return self.hashkey

    def get_absolute_url(self):
        return '/screenshots/%s/' % self.hashkey

    def get_size_url(self, size='original'):
        return '/png/%s/%s/%s.png' % (size, self.hashkey[:2], self.hashkey)

    def get_large_url(self):
        return self.get_size_url(size=512)

    def preview_img(self, width=160):
        height = self.height * width / self.width
        return ' '.join((
            '<img src="%s" alt="" class="preview absolute"',
            'style="width:%spx;height:%spx;z-index:0"',
            'onmouseover="larger(this,%s,%s)"',
            'onmouseout="smaller(this,%s,%s)" />',
            )) % (self.get_size_url(width),
            width / 2, height / 2, width, height, width, height)

    def get_file_size(self):
        """Get size in bytes of original screenshot file."""
        return os.path.getsize(storage.png_filename(self.hashkey))
