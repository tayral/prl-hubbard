# -*- coding: utf-8 -*-

"""
@namespace  qat.magics.install
@authors    Arnaud Gazda <arnaud.gazda@atos.net>
@copyright  2020 Bull S.A.S. - All rights reserved
            This is not Free or Open Source software.
            Please contact Bull SAS for details about its license.
            Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois

Description:
Script used to install magics.


.. warning::

    This file should be a text file (no compilation)
"""

from qat.core.magic.install import install_qlm_magics


if __name__ == "__main__":
    # Install magics
    install_qlm_magics()
