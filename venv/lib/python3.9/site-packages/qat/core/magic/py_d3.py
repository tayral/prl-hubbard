# -*- coding: utf-8 -*-

"""
@namespace  qat.core.magic.py_d3
@authors    Gabriel Proust <gabriel.proust@atos.net>
@copyright  2019 Bull S.A.S - All rights reserved
            This is not Free or Open Source software.
            Please contact Bull SAS for details about its license.
            Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois

Description Module defining and registering D3Magics magic.
"""

# Standard Python libraries
from __future__ import print_function
from re import sub

from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.display import HTML, display
from IPython import get_ipython


@magics_class
class D3Magics(Magics):
    """
    D3Magics is a magic used by jsqatdisplay
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Used to ensure that the current group selection is unique
        self.max_id = 0

        # D3 main library source path
        self.src = None

        # Print rendered internal javascript at cell execution.
        # Useful for debugging
        self.verbose = False

        self._cdnjs_d3_source_template = "/custom/d3.min"

    def _build_output_code(self, cell):
        """
        Builds the output code
        """
        code_template = (
            '''
<script>
requirejs.config({
    paths: {
        d3: "'''
            + self.src
            + """"
    }
"""
        )
        # Dependencies injection. See:
        # https://stackoverflow.com/questions/39061334/whats-the-easy-way-to-load-d3-selection-multi-along-with-d3-v4-in-requirejs
        code_template += (
            """});

require(["d3"], function(d3) {
    window.d3 = d3;
});
</script>
<script>
_select = d3.select;

d3.select"""
            + str(self.max_id)
            + """ = function(selection) {
    return _select("#d3-cell-"""
            + str(self.max_id)
            + """").select(selection);
}
d3.selectAll"""
            + str(self.max_id)
            + """ = function(selection) {
    return _select("#d3-cell-"""
            + str(self.max_id)
            + """").selectAll(selection);
}
</script>

<g id="d3-cell-"""
            + str(self.max_id)
            + """">
        """
        )
        cell = sub(r"d3.select\((?!this)", "d3.select" + str(self.max_id) + "(", cell)
        cell = sub(r"d3.selectAll\((?!this)", "d3.selectAll" + str(self.max_id) + "(", cell)
        return code_template + cell + "\n</g>"

    @property
    def last_release(self):
        """Obtain last stable D3 release from cdnjs API.
        If is not possible, return last hardcoded release.
        """
        return "d3.min"

    @property
    def version(self):
        """Returns version actually in use in the current notebook."""
        return self.last_release

    @cell_magic
    def qatd3(self, line="", cell=None):
        """D3 line and cell magics. Starting point for all commands."""

        local_import, initialized = (False, self.src is not None)
        if "-v" in line or " -v" in line:
            self.verbose = True
            line = line.replace(" -v", "").replace("-v", "")
        else:
            self.verbose = False

        if not local_import:
            _src = self._cdnjs_d3_source_template
        else:
            _src = line

        if self.src is not None:
            if _src != self.src and not initialized:
                msg = (
                    "The first source of D3 used in this notebook is"
                    + f" {self.src}. You can't use different versions of"
                    + " D3 library in the same Notebook. Please restart the"
                    + " kernel and load your desired version at first."
                )
                raise EnvironmentError(msg)
        else:
            from notebook import notebookapp  # pylint: disable=import-outside-toplevel

            base_url = ""
            for i in notebookapp.list_running_servers():
                if notebookapp.check_pid(i["pid"]):
                    base_url = i["base_url"]
                    if base_url[-1] == "/":
                        base_url = base_url[:-1]
            self.src = base_url + _src

        code = self._build_output_code(cell)
        if self.verbose:
            print(code)  # Useful for debugging.
        _html = HTML(code)
        self.max_id += 1
        display(_html)


def load_ipython_extension(ipython):
    """
    Register D3Magics
    """
    ipython.register_magics(D3Magics)


if __name__ == "__main__":
    load_ipython_extension(get_ipython())
