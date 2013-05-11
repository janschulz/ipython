# encoding: utf-8
"""
Example notebook post_save_hook tosave the notebook as a *.py file

Authors:

* Jan Schulz
* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import os
import io

from IPython.display import display, Javascript

from IPython.utils import py3compat


inject_export_hint_menu = """
(function (IPython) {
    "use strict";

    var CellToolbar = IPython.CellToolbar;
    var autoexporthint_preset = [];

    var select_type = CellToolbar.utils.select_ui_generator([
            ["-"            ,undefined      ],
            ["As-is (default)"        ,"as_is"        ],
            ["Commented"    ,"commented"     ],
            ["Omit"     ,"omit"     ],
            ],
            // setter
            function(cell, value){
                // we check that the auto_export_hint namespace exist and create it if needed
                if (cell.metadata.auto_export_hint == undefined){cell.metadata.auto_export_hint = {}}
                // set the value
                cell.metadata.auto_export_hint.export_type = value
                },
            //geter
            function(cell){ var ns = cell.metadata.auto_export_hint;
                // if the auto_export_hint namespace does not exist return `undefined`
                // (will be interpreted as `false` by checkbox) otherwise
                // return the value
                return (ns == undefined)? undefined: ns.export_type
                },
            "Auto Export Hint");

    CellToolbar.register_callback('auto_export_hint.select',select_type);

    autoexporthint_preset.push('auto_export_hint.select');

    CellToolbar.register_preset('Auto Export Hint',autoexporthint_preset);
    console.log('Auto Export Hint extension for metadata editing loaded.');

}(IPython));
"""

def write_nb_as_py(nb, **kwargs):
    lines = [u'# -*- coding: utf-8 -*-']
 
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == u'code':
                _export = cell.get(u'metadata').get(u'auto_export_hint',{}).get(u'export_type', u'as_is')
                if not _export in [u'as_is', u'omit', u'commented']:
                    _export = u'as_is'
                input = cell.get(u'input')
                if input is not None:
                    if _export == u'as_is':
                        lines.extend([u'# <codecell>',u''])
                        lines.extend(input.splitlines())
                        lines.append(u'')
                    elif _export == u'commented':
                        lines.extend([u'# <codecell>',u''])
                        lines.extend([u'# automatically commented',u''])
                        lines.extend([u'# ' + line for line in input.splitlines()])
                        lines.append(u'')
                    else:
                        lines.extend([u'# <codecell>',u''])
                        lines.extend([u'# automatically omited',u''])            
            elif cell.cell_type == u'html':
                input = cell.get(u'source')
                if input is not None:
                    lines.extend([u'# <htmlcell>',u''])
                    lines.extend([u'# ' + line for line in input.splitlines()])
                    lines.append(u'')
            elif cell.cell_type == u'markdown':
                input = cell.get(u'source')
                if input is not None:
                    lines.extend([u'# <markdowncell>',u''])
                    lines.extend([u'# ' + line for line in input.splitlines()])
                    lines.append(u'')
            elif cell.cell_type == u'raw':
                input = cell.get(u'source')
                if input is not None:
                    lines.extend([u'# <rawcell>',u''])
                    lines.extend([u'# ' + line for line in input.splitlines()])
                    lines.append(u'')
            elif cell.cell_type == u'heading':
                input = cell.get(u'source')
                level = cell.get(u'level',1)
                if input is not None:
                    lines.extend([u'# <headingcell level=%s>' % level,u''])
                    lines.extend([u'# ' + line for line in input.splitlines()])
                    lines.append(u'')
    lines.append('')
    return unicode('\n'.join(lines))

def save_as_script_post_save_hook(self, nb, new_name, old_name, path, notebook_id, filenbmanager):
        pypath = os.path.splitext(path)[0] + '.py'
        filenbmanager.log.debug("saveasscript: writing script %s", pypath)
        with io.open(pypath,'w', encoding='utf-8') as f:
            nbs = write_nb_as_py(nb)
            if not py3compat.PY3 and not isinstance(nbs, unicode):
                # this branch is likely only taken for JSON on Python 2
                nbs = py3compat.str_to_unicode(nbs)
            f.write(nbs)
        if old_name != new_name:
            old_path = filenbmanager.get_path_by_name(old_name)
            old_pypath = os.path.splitext(old_path)[0] + '.py'
            if os.path.isfile(old_pypath):
                filenbmanager.log.debug("saveasscript: unlinking script %s", old_pypath)
                os.unlink(old_pypath)

def load_ipython_extension(ip):
#    ip.set_hook("notebook_manager_post_save_hook", save_as_script_post_save_hook)
    display(Javascript(inject_export_hint_menu))
    print ("Export hint menu loaded")