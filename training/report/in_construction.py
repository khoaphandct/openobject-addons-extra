# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from report import report_sxw

class in_construction(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(in_construction, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

class training_subscription_cancel_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(training_subscription_cancel_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })
report_sxw.report_sxw('report.training.subscription.cancel','training.subscription','addons/training/report/trainining_cancel.rml',parser=training_subscription_cancel_report)

reports = [
    ('report.training.seance.booking.support', 'training.seance'),
    ('report.training.seance.booking.classroom', 'training.seance'),
#    ('report.training.subscription.cancel', 'training.subscription'),
    ('report.training.subscription.confirm', 'training.subscription'),
    ('report.training.course.material.report', 'training.course'),
    ('report.training.course.financial.report', 'training.course')
]

for name, model in reports:
    report_sxw.report_sxw(name, model,
                          'addons/training/report/in_construction.rml',
                          parser=in_construction,
                          header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

