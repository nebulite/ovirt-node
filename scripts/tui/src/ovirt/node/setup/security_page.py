#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# security_page.py - Copyright (C) 2012 Red Hat, Inc.
# Written by Fabian Deutsch <fabiand@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
from ovirt.node import utils, plugins, ui, valid, exceptions
from ovirt.node.config import defaults
from ovirt.node.plugins import ChangesHelper

"""
Configure Security
"""


class Plugin(plugins.NodePlugin):
    _model = None
    _widgets = None

    def name(self):
        return "Security"

    def rank(self):
        return 20

    def model(self):
        cfg = defaults.SSH().retrieve()
        self.logger.debug(cfg)
        model = {
            "ssh.pwauth": cfg["pwauth"] or False,
            "strongrng.aesni": cfg["disable_aesni"] or False,
            "strongrng.num_bytes": cfg["num_bytes"] or "",
            "passwd.admin.password": "",
            "passwd.admin.password_confirmation": "",
        }
        return model

    def validators(self):
        number_or_empty = valid.Number(range=[0, None]) | \
                          valid.Empty()
        return {
                "strongrng.num_bytes": number_or_empty,
                "passwd.admin.password": valid.Text(),
                "passwd.admin.password_confirmation": valid.Text(),
            }

    def ui_content(self):
        widgets = [
            ("header[0]", ui.Header("Remote Access")),
            ("ssh.pwauth", ui.Checkbox("Enable SSH password authentication")),

            ("header[1]", ui.Header("Strong Random Number Generator")),
            ("strongrng.aesni", ui.Checkbox("Enable AES-NI")),
            ("strongrng.num_bytes", ui.Entry("Bytes Used:")),

            ("header[2]", ui.Header("Local Access")),
            ("passwd.admin.password", ui.PasswordEntry("Password:")),
            ("passwd.admin.password_confirmation", ui.PasswordEntry(
                "Confirm Password:")),
        ]
        # Save it "locally" as a dict, for better accessability
        self._widgets = dict(widgets)

        page = ui.Page(widgets)
        return page

    def on_change(self, changes):
        m = self.model()
        m.update(self.pending_changes() or {})
        effective_model = ChangesHelper(m)

        passwd_keys = ["passwd.admin.password",
                       "passwd.admin.password_confirmation"]
        if effective_model.any_key_in_change(passwd_keys):
            passwd, passwdc = effective_model.get_key_values(passwd_keys)
            if passwd != passwdc:
                raise exceptions.InvalidData("Passwords do not match.")

    def on_merge(self, effective_changes):
        self.logger.debug("Saving security page")
        changes = ChangesHelper(self.pending_changes(False))
        model = self.model()
        model.update(effective_changes)
        effective_model = ChangesHelper(model)

        self.logger.debug("Saving security page: %s" % changes.changes)
        self.logger.debug("Remote security model: %s" %
                          effective_model.changes)

        ssh_keys = ["ssh.pwauth", "strongrng.num_bytes", "strongrng.aesni"]
        passwd_keys = ["passwd.admin.password",
                       "passwd.admin.password_confirmation"]

        txs = utils.Transaction("Updating security configuration")

        if changes.any_key_in_change(ssh_keys):
            model = defaults.SSH()
            model.update(*effective_model.get_key_values(ssh_keys))
            txs += model.transaction()

        if changes.any_key_in_change(passwd_keys):
            pw, pwc = effective_model.get_key_values(passwd_keys)
            if pw != pwc:
                raise exceptions.InvalidData("Passwords do not match")
            passwd = utils.security.Passwd()

            class SetAdminPasswd(utils.Transaction.Element):
                def commit(self):
                    self.logger.debug("Setting admin password.")
                    passwd.set_password("admin", pw)
            txs += [SetAdminPasswd()]

        txs.prepare()  # Just to display something in dry mode
        self.dry_or(lambda: txs())