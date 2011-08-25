# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import datetime

from osv import fields, osv

STATE = [
    ('none', 'Non Member'),
    ('canceled', 'Canceled Member'),
    ('old', 'Old Member'),
    ('waiting', 'Waiting Member'),
    ('invoiced', 'Invoiced Member'),
    ('free', 'Free Member'),
    ('paid', 'Paid Member'),
]

STATE_PRIOR = {
        'none' : 0,
        'canceled' : 1,
        'old' : 2,
        'waiting' : 3,
        'invoiced' : 4,
        'free' : 6,
        'paid' : 7
        }

class membership_line(osv.osv):
    _inherit = 'membership.membership_line'

    def _state(self, cr, uid, ids, name, args, context=None):
        '''Compute the state lines'''
        # this method replaces the super() method because we want to change to status of invoice partially
        # paid via a out_refund : the invoice is considered as paid and not more canceled by the partial out_refund
        res = {}
        for line in self.browse(cr, uid, ids):
            cr.execute('''
            SELECT i.state, i.id FROM
            account_invoice i 
            WHERE
            i.id = (
                SELECT l.invoice_id FROM
                account_invoice_line l WHERE
                l.id = (
                    SELECT  ml.account_invoice_line FROM
                    membership_membership_line ml WHERE
                    ml.id = %s
                    )
                )
            ''', (line.id,))
            fetched = cr.fetchone()
            if not fetched :
                res[line.id] = 'canceled'
                continue
            istate = fetched[0]
            state = 'none'
            if (istate == 'draft') | (istate == 'proforma'):
                state = 'waiting'
            elif istate == 'open':
                state = 'invoiced'
            elif istate == 'paid':
                state = 'paid'
                inv = self.pool.get('account.invoice').browse(cr, uid, fetched[1])
                out_refund = other = False
                for payment in inv.payment_ids:
                    if payment.invoice and payment.invoice.type == 'out_refund':
                        out_refund = True
                    else:
                        other = True
                if out_refund and not other:
                    state = 'canceled'
            elif istate == 'cancel':
                state = 'canceled'
            res[line.id] = state
        return res

    _columns = {
        'subtotal': fields.related('account_invoice_line', 'price_subtotal', type='float', string='Subtotal', readonly=True),
        'invoice_id': fields.related('account_invoice_line', 'invoice_id', type='many2one', string='Account', relation='account.invoice', readonly=True),
        'number': fields.related('invoice_id', 'number', type='char', string='Invoice Number', relation='account.invoice', readonly=True),
        'date_invoice': fields.related('invoice_id', 'date_invoice', type='date', string="Date Invoiced", readonly=True),
        'state': fields.function(_state, method=True, string='State', type='selection', selection=STATE),
                }

membership_line()

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _description = 'Partner'

    def _membership_state_job(self, cr, uid, ids=False, context={}):
        #today = datetime.date.today()
        #yesterday = today - datetime.timedelta(days=4)
        #membership_line_ids = self.pool.get('membership.membership_line').search(cr, uid, ['|', ('date_to','=', yesterday), ('date_from','=', today)], context=context)
        #partner_tmp_ids = self.pool.get('membership.membership_line').read(cr, uid, membership_line_ids, ['partner'], context=context)
        #partner_ids = partner_tmp_ids and map(lambda x:x['partner'][0],partner_tmp_ids) or False
        #print "_membership_state_job"
        #partner_ids = self.pool.get('res.partner').search(cr,uid,[],context=context)
        #if partner_ids:
        #    self.write(cr, uid, partner_ids, {}, context)
        #return True
        # this method is partially copied from the method cci_membership=>wizard/cci_check_membership.py=>_check_membership()
        partner_ids = self.pool.get('res.partner').search(cr, uid, ['|',('active','=','True'),('active','=','False')], context=context)
        partner_obj = self.pool.get('res.partner')
        if partner_ids:
            partners = partner_obj.read(cr, uid, partner_ids, ['id','membership_state'] )
            new_mstates = partner_obj._membership_state(cr, uid, partner_ids, '', args=None, context=None)
            changed_lines = []
            for partner in partners:
                if new_mstates.has_key( partner['id'] ):
                    if partner['membership_state'] <> new_mstates[partner['id']]:
                        partner_name = partner_obj.read(cr, uid, [partner['id']], ['name'] )[0]['name']
                        changed_lines.append( u"Partenaire '%s' (id=%s) passe de '%s' à '%s'" % (partner_name, str(partner['id']),partner['membership_state'],new_mstates[partner['id']]) )
                        partner_obj.write(cr, uid, [partner['id']], {}, context )
            if changed_lines:
                final_text = u'Changements hebdomadaires : \n' + ( u'\n'.join( changed_lines ) )
            else:
                final_text = u"Changements hebdomadaires : aucun"
            membership_check_obj = self.pool.get('cci_membership.membership_check')
            today = datetime.datetime.today()
            id = membership_check_obj.create(cr, uid, {
                'name': today.strftime('%Y-%m-%d-%H:%M:%S'),
                'count' : len(changed_lines),
                'status': final_text,
                })
        return True

    def _membership_vcs(self, cr, uid, ids, field_name=None, arg=None, context={}):
        '''To obtain the ID of the partner in the form of a belgian VCS for a membership offer'''
        res = {}
        for id in ids:
            value_digits = 1000000000 + id
            check_digits = value_digits % 97
            if check_digits == 0:
                check_digits = 97
            pure_string = str(value_digits) + ( str(check_digits).zfill(2) )
            res[id] = '***' + pure_string[0:3] + '/' + pure_string[3:7] + '/' + pure_string[7:] + '***'
        return res

    def _membership_state(self, cr, uid, ids, name, args, context=None):
        #the call to super is deactivated because of unresolved conflicts with the 5.0 version
        #of the membership module in state priorities. It is replaced by the ugly copy/paste below
        #res = super(res_partner, self)._membership_state(cr, uid, ids, name, args, context)
        res = {}
        for id in ids:
            res[id] = 'none'
        today = time.strftime('%Y-%m-%d')
        for id in ids:
            partner_data = self.browse(cr,uid,id)
            # commented by Philmer - the membership_cancel field is always filled if there is only one membership_line
            # with a date_cancel even if there is more membership_line more recent not canceled
            #if partner_data.membership_cancel and today > partner_data.membership_cancel:
            #    res[id] = 'canceled'
            #    continue
            if partner_data.state_id.id not in (1,) or not partner_data.active:
                res[id] = 'none'
                continue
            if partner_data.refuse_membership:
                res[id] = 'canceled'
                continue
            if partner_data.free_member:
                res[id] = 'free'
                continue
            s = 4
            if partner_data.member_lines:
                for mline in partner_data.member_lines:
                    if mline.date_from <= today and mline.date_to >= today and mline.account_invoice_line and mline.account_invoice_line.invoice_id and mline.account_invoice_line.invoice_id.type == 'out_invoice':
                            mstate = mline.account_invoice_line.invoice_id.state
                            if mstate == 'paid':
                                #TOCHECK : if paid by a credit nota : s = 2
                                # A quick way to check this is to check the state of the membership_line is 'canceled' or not
                                if mline.state == 'canceled':
                                    if s!=0 and s!=1:
                                        s = 2
                                else:
                                    s = 0
                                    break
                            elif mstate == 'open' and s!=0:
                                s = 1
                            elif mstate == 'cancel' and s!=0 and s!=1:
                                s = 2
                            elif  (mstate == 'draft' or mstate == 'proforma') and s!=0 and s!=1:
                                s = 3
                if s==4:
                    for mline in partner_data.member_lines:
                        if mline.date_from < today and mline.date_to < today and mline.date_from<=mline.date_to and mline.account_invoice_line and mline.account_invoice_line.invoice_id.state == 'paid' and mline.account_invoice_line.invoice_id.type == 'out_invoice' and mline.state == 'paid':
                            s = 5
                        else:
                            s = 6
                if s==0:
                    res[id] = 'paid'
                elif s==1:
                    res[id] = 'invoiced'
                elif s==2:
                    res[id] = 'canceled'
                elif s==3:
                    res[id] = 'waiting'
                elif s==5:
                    res[id] = 'old'
                elif s==6:
                    res[id] = 'none'
            if partner_data.membership_stop and today > partner_data.membership_stop:
                res[id] = 'old'
                continue
            if partner_data.associate_member and res[id] not in ('paid','invoiced','waiting'):
                res_state = self._membership_state(cr, uid, [partner_data.associate_member.id], name, args, context)
                res[id] = res_state[partner_data.associate_member.id]

        return res

    _columns = {
        'membership_vcs': fields.function( _membership_vcs, method=True,string='VCS number for membership offer', type='char', size=20),
        'refuse_membership': fields.boolean('Refuse to Become a Member'),
        'membership_explanation': fields.text('Membership Explanation',help='Here you can explain the amount asked or the special treatment for the membership of this partner'),
        'membership_first_year': fields.char('First Year of membership',help='To manually give the first year of membership',size=4),
    }

    _default = {
        'refuse_membership': lambda *a: 0,
    }

res_partner()

class membership_check(osv.osv):
    _name = 'cci_membership.membership_check'
    _description = '''Recording of a check'''
    _columns = {
        'name' : fields.char('Date',size=19,required=True),
        'count': fields.integer('Changes count'),
        'status' : fields.text('Status'),
    }
    _order = 'name desc'
membership_check()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

